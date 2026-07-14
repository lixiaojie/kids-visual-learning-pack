from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "ops"
    / "cognitive-card-server"
    / "card_os_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location("card_os_acceptance", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load acceptance module from {MODULE_PATH}")
acceptance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = acceptance
SPEC.loader.exec_module(acceptance)


ISSUED = {
    "token": "ccos_v1." + "a" * 32 + ".rabbit-secret",
    "token_id": "a" * 32,
    "subject": "deploy-acceptance-20260714T030000Z",
    "scopes": ["admin"],
    "expires_at": "2026-07-14T03:15:00Z",
}


class ProbeHandler(BaseHTTPRequestHandler):
    server: "ProbeServer"

    def do_GET(self) -> None:
        self.server.requests.append(
            {
                "method": self.command,
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "protocol": self.headers.get("X-Card-OS-Protocol"),
                "skill_release": self.headers.get("X-Card-OS-Skill-Release"),
            }
        )
        status, code = self.server.responses.pop(0)
        payload = json.dumps({"error": {"code": code}}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        pass


class ProbeServer(ThreadingHTTPServer):
    requests: list[dict[str, str | None]]
    responses: list[tuple[int, str]]


class RedirectHandler(BaseHTTPRequestHandler):
    server: "RedirectServer"

    def do_GET(self) -> None:
        self.server.requests.append(self.path)
        self.send_response(302)
        self.send_header("Location", self.server.location)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


class RedirectServer(ThreadingHTTPServer):
    location: str
    requests: list[str]


class CardOsAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name)
        self.state_dir = self.base / "state"
        self.state_file = self.state_dir / "acceptance.json"
        self.database = self.base / "card-os.sqlite3"
        self.database.touch()
        self.auth_log = self.base / "auth-log.jsonl"
        self.auth_command = self.base / "fake-auth"
        self.auth_command.write_text(
            """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

issued = {
    'token': 'ccos_v1.' + 'a' * 32 + '.rabbit-secret',
    'token_id': 'a' * 32,
    'subject': 'deploy-acceptance-20260714T030000Z',
    'scopes': ['admin'],
    'expires_at': '2026-07-14T03:15:00Z',
}
with Path(os.environ['CARD_OS_AUTH_LOG']).open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
if 'issue' in sys.argv:
    print(json.dumps(issued))
elif 'revoke' in sys.argv and not os.environ.get('CARD_OS_REVOKE_FAIL'):
    print(json.dumps({'token_id': issued['token_id'], 'revoked_at': '2026-07-14T03:05:00Z'}))
else:
    print('sensitive-auth-runner-error', file=sys.stderr)
    raise SystemExit(1)
""",
            encoding="utf-8",
        )
        self.auth_command.chmod(0o700)
        self.server = ProbeServer(("127.0.0.1", 0), ProbeHandler)
        self.server.requests = []
        self.server.responses = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}/card-os"

    def invoke(self, *arguments: str, revoke_fails: bool = False):
        stdout = io.StringIO()
        stderr = io.StringIO()
        environment = {"CARD_OS_AUTH_LOG": os.fspath(self.auth_log)}
        if revoke_fails:
            environment["CARD_OS_REVOKE_FAIL"] = "1"
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with patch.dict(os.environ, environment, clear=False):
                result = acceptance.main(list(arguments))
        return result, stdout.getvalue(), stderr.getvalue()

    def begin(self, *, revoke_fails: bool = False):
        return self.invoke(
            "begin",
            "--database",
            os.fspath(self.database),
            "--base-url",
            self.base_url,
            "--state-file",
            os.fspath(self.state_file),
            "--auth-command",
            os.fspath(self.auth_command),
            "--expires-minutes",
            "15",
            revoke_fails=revoke_fails,
        )

    def finish(self, *, revoke_fails: bool = False):
        return self.invoke(
            "finish",
            "--database",
            os.fspath(self.database),
            "--base-url",
            self.base_url,
            "--state-file",
            os.fspath(self.state_file),
            "--auth-command",
            os.fspath(self.auth_command),
            revoke_fails=revoke_fails,
        )

    def cleanup(self, *, revoke_fails: bool = False):
        return self.invoke(
            "cleanup",
            "--database",
            os.fspath(self.database),
            "--state-file",
            os.fspath(self.state_file),
            "--auth-command",
            os.fspath(self.auth_command),
            revoke_fails=revoke_fails,
        )

    def auth_calls(self) -> list[list[str]]:
        return [
            json.loads(line)
            for line in self.auth_log.read_text(encoding="utf-8").splitlines()
        ]

    def assert_no_secret(self, stdout: str, stderr: str) -> None:
        for output in (stdout, stderr):
            self.assertNotIn("rabbit-secret", output)
            self.assertNotIn(ISSUED["token"], output)

    def test_begin_issues_token_checks_protected_read_and_writes_private_state(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]

        result, stdout, stderr = self.begin()

        self.assertEqual(0, result)
        self.assertEqual(
            [
                {
                    "method": "GET",
                    "path": "/card-os/api/v1/jobs/deploy-acceptance-missing",
                    "authorization": f"Bearer {ISSUED['token']}",
                    "protocol": "1",
                    "skill_release": "0.1.0",
                }
            ],
            self.server.requests,
        )
        self.assertEqual(0o700, stat.S_IMODE(self.state_dir.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(self.state_file.stat().st_mode))
        self.assertEqual(
            {
                "schema": "card-os-acceptance-v1",
                "token": ISSUED["token"],
                "token_id": ISSUED["token_id"],
                "subject": ISSUED["subject"],
                "expires_at": ISSUED["expires_at"],
                "base_url": self.base_url,
            },
            json.loads(self.state_file.read_text(encoding="utf-8")),
        )
        self.assertEqual(
            {
                "http_status": 404,
                "phase": "begin",
                "status": "ok",
                "subject": ISSUED["subject"],
                "token_id": ISSUED["token_id"],
            },
            json.loads(stdout),
        )
        self.assertEqual("", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_requires_job_not_found_and_does_not_persist_failed_probe(self) -> None:
        self.server.responses = [(404, "SOMETHING_ELSE")]

        result, stdout, stderr = self.begin()

        self.assertNotEqual(0, result)
        self.assertFalse(self.state_file.exists())
        self.assertEqual("", stdout)
        self.assertEqual("AUTHENTICATED_READ_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_revokes_by_id_when_probe_fails_after_issue(self) -> None:
        self.server.responses = [(500, "INTERNAL_ERROR")]

        result, stdout, stderr = self.begin()

        self.assertNotEqual(0, result)
        self.assertEqual(
            [
                "--database",
                os.fspath(self.database),
                "revoke",
                "--token-id",
                ISSUED["token_id"],
            ],
            self.auth_calls()[-1],
        )
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertFalse(self.state_file.exists())
        self.assertEqual("", stdout)
        self.assertEqual("AUTHENTICATED_READ_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_revokes_by_id_when_state_write_fails_after_issue(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]
        state_parent = self.base / "state-write-failure"
        unwritable_state = state_parent / ("x" * 300)

        result, stdout, stderr = self.invoke(
            "begin",
            "--database",
            os.fspath(self.database),
            "--base-url",
            self.base_url,
            "--state-file",
            os.fspath(unwritable_state),
            "--auth-command",
            os.fspath(self.auth_command),
            "--expires-minutes",
            "15",
        )

        self.assertNotEqual(0, result)
        self.assertEqual(
            [
                "--database",
                os.fspath(self.database),
                "revoke",
                "--token-id",
                ISSUED["token_id"],
            ],
            self.auth_calls()[-1],
        )
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertFalse(unwritable_state.exists())
        self.assertEqual("", stdout)
        self.assertEqual("STATE_WRITE_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_reports_stable_error_when_failure_cleanup_revoke_fails(self) -> None:
        self.server.responses = [(500, "INTERNAL_ERROR")]

        result, stdout, stderr = self.begin(revoke_fails=True)

        self.assertNotEqual(0, result)
        self.assertEqual("", stdout)
        self.assertEqual("BEGIN_CLEANUP_FAILED\n", stderr)
        self.assertIn("revoke", self.auth_calls()[-1])
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertFalse(self.state_file.exists())
        self.assert_no_secret(stdout, stderr)

    def test_begin_removes_written_state_after_emit_failure_and_revoke(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]

        with patch.object(
            acceptance,
            "_emit",
            side_effect=BrokenPipeError(ISSUED["token"]),
        ):
            result, stdout, stderr = self.begin()

        self.assertNotEqual(0, result)
        self.assertEqual(
            [
                "--database",
                os.fspath(self.database),
                "revoke",
                "--token-id",
                ISSUED["token_id"],
            ],
            self.auth_calls()[-1],
        )
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertFalse(self.state_file.exists())
        self.assertEqual("", stdout)
        self.assertEqual("INTERNAL_ERROR\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_reports_stable_error_when_written_state_removal_fails(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]

        with patch.object(
            acceptance,
            "_emit",
            side_effect=BrokenPipeError(ISSUED["token"]),
        ):
            with patch.object(
                Path,
                "unlink",
                side_effect=OSError(ISSUED["token"]),
            ):
                result, stdout, stderr = self.begin()

        self.assertNotEqual(0, result)
        self.assertIn("revoke", self.auth_calls()[-1])
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertTrue(self.state_file.exists())
        self.assertEqual("", stdout)
        self.assertEqual("BEGIN_STATE_CLEANUP_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_refuses_redirect_without_sending_bearer_to_receiver(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]
        redirect_server = RedirectServer(("127.0.0.1", 0), RedirectHandler)
        redirect_server.requests = []
        redirect_server.location = (
            f"http://127.0.0.1:{self.server.server_port}"
            "/card-os/api/v1/jobs/deploy-acceptance-missing"
        )
        redirect_thread = threading.Thread(
            target=redirect_server.serve_forever,
            daemon=True,
        )
        redirect_thread.start()
        self.addCleanup(redirect_server.server_close)
        self.addCleanup(redirect_server.shutdown)
        redirect_base_url = (
            f"http://127.0.0.1:{redirect_server.server_port}/card-os"
        )

        result, stdout, stderr = self.invoke(
            "begin",
            "--database",
            os.fspath(self.database),
            "--base-url",
            redirect_base_url,
            "--state-file",
            os.fspath(self.state_file),
            "--auth-command",
            os.fspath(self.auth_command),
            "--expires-minutes",
            "15",
        )

        self.assertNotEqual(0, result)
        self.assertEqual(
            ["/card-os/api/v1/jobs/deploy-acceptance-missing"],
            redirect_server.requests,
        )
        self.assertEqual([], self.server.requests)
        self.assertFalse(self.state_file.exists())
        self.assertEqual("", stdout)
        self.assertEqual("AUTHENTICATED_READ_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_begin_refuses_to_overwrite_existing_state(self) -> None:
        self.state_dir.mkdir(mode=0o700)
        self.state_file.write_text("sentinel", encoding="utf-8")

        result, stdout, stderr = self.begin()

        self.assertNotEqual(0, result)
        self.assertEqual("sentinel", self.state_file.read_text(encoding="utf-8"))
        self.assertEqual([], self.server.requests)
        self.assertFalse(self.auth_log.exists())
        self.assertEqual("STATE_EXISTS\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_finish_rechecks_then_revokes_by_id_and_confirms_rejection(self) -> None:
        self.server.responses = [
            (404, "JOB_NOT_FOUND"),
            (404, "JOB_NOT_FOUND"),
            (403, "AUTH_REVOKED"),
        ]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.finish()

        self.assertEqual(0, result)
        self.assertFalse(self.state_file.exists())
        self.assertEqual(
            ["--database", os.fspath(self.database), "revoke", "--token-id", ISSUED["token_id"]],
            self.auth_calls()[-1],
        )
        self.assertNotIn(ISSUED["token"], self.auth_calls()[-1])
        self.assertEqual([404, 403], [404, json.loads(stdout)["http_status"]])
        self.assertEqual("finish", json.loads(stdout)["phase"])
        self.assertEqual("", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_finish_attempts_revoke_after_precheck_failure_and_removes_on_success(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND"), (500, "INTERNAL_ERROR")]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.finish()

        self.assertNotEqual(0, result)
        self.assertFalse(self.state_file.exists())
        self.assertIn("revoke", self.auth_calls()[-1])
        self.assertEqual("AUTHENTICATED_READ_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_finish_retains_state_when_revoke_fails(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND"), (404, "JOB_NOT_FOUND")]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.finish(revoke_fails=True)

        self.assertNotEqual(0, result)
        self.assertTrue(self.state_file.exists())
        self.assertEqual("REVOKE_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_finish_revokes_after_parsing_state_even_when_base_url_mismatches(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.invoke(
            "finish",
            "--database",
            os.fspath(self.database),
            "--base-url",
            "https://unexpected.invalid/card-os",
            "--state-file",
            os.fspath(self.state_file),
            "--auth-command",
            os.fspath(self.auth_command),
        )

        self.assertNotEqual(0, result)
        self.assertFalse(self.state_file.exists())
        self.assertIn("revoke", self.auth_calls()[-1])
        self.assertEqual("STATE_INVALID\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_finish_requires_auth_revoked_after_successful_revoke(self) -> None:
        self.server.responses = [
            (404, "JOB_NOT_FOUND"),
            (404, "JOB_NOT_FOUND"),
            (404, "JOB_NOT_FOUND"),
        ]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.finish()

        self.assertNotEqual(0, result)
        self.assertFalse(self.state_file.exists())
        self.assertEqual("REVOCATION_NOT_ENFORCED\n", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_cleanup_revokes_by_id_without_http_or_secret_disclosure(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]
        self.assertEqual(0, self.begin()[0])
        request_count = len(self.server.requests)

        result, stdout, stderr = self.cleanup()

        self.assertEqual(0, result)
        self.assertEqual(request_count, len(self.server.requests))
        self.assertFalse(self.state_file.exists())
        revoke_call = self.auth_calls()[-1]
        self.assertEqual(
            ["--database", os.fspath(self.database), "revoke", "--token-id", ISSUED["token_id"]],
            revoke_call,
        )
        self.assertNotIn(ISSUED["token"], revoke_call)
        self.assertEqual("cleanup", json.loads(stdout)["phase"])
        self.assertEqual("", stderr)
        self.assert_no_secret(stdout, stderr)

    def test_cleanup_retains_state_when_revoke_fails(self) -> None:
        self.server.responses = [(404, "JOB_NOT_FOUND")]
        self.assertEqual(0, self.begin()[0])

        result, stdout, stderr = self.cleanup(revoke_fails=True)

        self.assertNotEqual(0, result)
        self.assertTrue(self.state_file.exists())
        self.assertEqual("REVOKE_FAILED\n", stderr)
        self.assert_no_secret(stdout, stderr)


if __name__ == "__main__":
    unittest.main()
