#!/usr/bin/env python3
"""Two-stage deployment acceptance using a disposable Card OS token."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence


PROTOCOL = "1"
SKILL_RELEASE = "0.1.0"
MISSING_JOB = "deploy-acceptance-missing"
SUBJECT_PREFIX = "deploy-acceptance-"

STATE_SCHEMA = "card-os-acceptance-v1"


class AcceptanceError(RuntimeError):
    """A safe, stable acceptance failure code."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _subject(value: datetime) -> str:
    return SUBJECT_PREFIX + value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_auth(arguments: list[str], failure_code: str) -> subprocess.CompletedProcess[str]:
    try:
        process = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        raise AcceptanceError(failure_code) from None
    if process.returncode != 0:
        raise AcceptanceError(failure_code)
    return process


def _issue_token(
    auth_command: Path,
    database: Path,
    *,
    subject: str,
    expires_at: str,
) -> dict[str, str]:
    process = _run_auth(
        [
            os.fspath(auth_command),
            "--database",
            os.fspath(database),
            "issue",
            "--subject",
            subject,
            "--scope",
            "admin",
            "--expires-at",
            expires_at,
        ],
        "ISSUE_FAILED",
    )
    try:
        payload = json.loads(process.stdout)
        result = {
            "token": payload["token"],
            "token_id": payload["token_id"],
            "subject": payload["subject"],
            "expires_at": payload["expires_at"],
        }
        if not all(isinstance(value, str) and value for value in result.values()):
            raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise AcceptanceError("ISSUE_FAILED") from None
    return result


def _revoke_token(auth_command: Path, database: Path, token_id: str) -> None:
    _run_auth(
        [
            os.fspath(auth_command),
            "--database",
            os.fspath(database),
            "revoke",
            "--token-id",
            token_id,
        ],
        "REVOKE_FAILED",
    )


def _probe(base_url: str, token: str) -> tuple[int, str | None]:
    url = f"{base_url.rstrip('/')}/api/v1/jobs/{MISSING_JOB}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Card-OS-Protocol": PROTOCOL,
            "X-Card-OS-Skill-Release": SKILL_RELEASE,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        try:
            body = error.read()
        finally:
            error.close()
    except Exception:
        raise AcceptanceError("AUTHENTICATED_READ_FAILED") from None

    try:
        payload = json.loads(body)
        code = payload["error"]["code"]
        if not isinstance(code, str):
            code = None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        code = None
    return status, code


def _require_probe(
    base_url: str,
    token: str,
    *,
    expected_status: int,
    expected_code: str,
    failure_code: str,
) -> int:
    status, code = _probe(base_url, token)
    if status != expected_status or code != expected_code:
        raise AcceptanceError(failure_code)
    return status


def _write_state(state_file: Path, payload: dict[str, str]) -> None:
    parent = state_file.parent
    try:
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent.chmod(0o700)
        descriptor = os.open(
            state_file,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        raise AcceptanceError("STATE_EXISTS") from None
    except Exception:
        raise AcceptanceError("STATE_WRITE_FAILED") from None

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(_canonical_json(payload))
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            state_file.unlink()
        except OSError:
            pass
        raise AcceptanceError("STATE_WRITE_FAILED") from None


def _load_state(state_file: Path) -> dict[str, str]:
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
        required = {
            "schema",
            "token",
            "token_id",
            "subject",
            "expires_at",
            "base_url",
        }
        if set(payload) != required or payload["schema"] != STATE_SCHEMA:
            raise ValueError
        if not all(isinstance(payload[key], str) and payload[key] for key in required):
            raise ValueError
    except Exception:
        raise AcceptanceError("STATE_INVALID") from None
    return payload


def _unlink_state(state_file: Path) -> None:
    try:
        state_file.unlink()
    except Exception:
        raise AcceptanceError("STATE_REMOVE_FAILED") from None


def _emit(payload: dict[str, object]) -> None:
    sys.stdout.write(_canonical_json(payload))


def begin(arguments: argparse.Namespace) -> None:
    state_file = Path(arguments.state_file)
    if os.path.lexists(state_file):
        raise AcceptanceError("STATE_EXISTS")
    if arguments.expires_minutes <= 0:
        raise AcceptanceError("ISSUE_FAILED")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    issued = _issue_token(
        Path(arguments.auth_command),
        Path(arguments.database),
        subject=_subject(now),
        expires_at=_utc_text(now + timedelta(minutes=arguments.expires_minutes)),
    )
    http_status = _require_probe(
        arguments.base_url,
        issued["token"],
        expected_status=404,
        expected_code="JOB_NOT_FOUND",
        failure_code="AUTHENTICATED_READ_FAILED",
    )
    _write_state(
        state_file,
        {
            "schema": STATE_SCHEMA,
            "token": issued["token"],
            "token_id": issued["token_id"],
            "subject": issued["subject"],
            "expires_at": issued["expires_at"],
            "base_url": arguments.base_url,
        },
    )
    _emit(
        {
            "status": "ok",
            "phase": "begin",
            "token_id": issued["token_id"],
            "subject": issued["subject"],
            "http_status": http_status,
        }
    )


def finish(arguments: argparse.Namespace) -> None:
    state_file = Path(arguments.state_file)
    state = _load_state(state_file)
    precheck_error: AcceptanceError | None = (
        AcceptanceError("STATE_INVALID")
        if state["base_url"] != arguments.base_url
        else None
    )
    revoke_succeeded = False
    try:
        if precheck_error is None:
            try:
                _require_probe(
                    arguments.base_url,
                    state["token"],
                    expected_status=404,
                    expected_code="JOB_NOT_FOUND",
                    failure_code="AUTHENTICATED_READ_FAILED",
                )
            except AcceptanceError as error:
                precheck_error = error
    finally:
        _revoke_token(
            Path(arguments.auth_command),
            Path(arguments.database),
            state["token_id"],
        )
        revoke_succeeded = True

    if revoke_succeeded:
        _unlink_state(state_file)
    if precheck_error is not None:
        raise precheck_error

    http_status = _require_probe(
        arguments.base_url,
        state["token"],
        expected_status=403,
        expected_code="AUTH_REVOKED",
        failure_code="REVOCATION_NOT_ENFORCED",
    )
    _emit(
        {
            "status": "ok",
            "phase": "finish",
            "token_id": state["token_id"],
            "subject": state["subject"],
            "http_status": http_status,
        }
    )


def cleanup(arguments: argparse.Namespace) -> None:
    state_file = Path(arguments.state_file)
    state = _load_state(state_file)
    _revoke_token(
        Path(arguments.auth_command),
        Path(arguments.database),
        state["token_id"],
    )
    _unlink_state(state_file)
    _emit(
        {
            "status": "ok",
            "phase": "cleanup",
            "token_id": state["token_id"],
            "subject": state["subject"],
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    begin_parser = commands.add_parser("begin")
    begin_parser.add_argument("--database", required=True)
    begin_parser.add_argument("--base-url", required=True)
    begin_parser.add_argument("--state-file", required=True)
    begin_parser.add_argument("--auth-command", required=True)
    begin_parser.add_argument("--expires-minutes", required=True, type=int)
    begin_parser.set_defaults(handler=begin)

    finish_parser = commands.add_parser("finish")
    finish_parser.add_argument("--database", required=True)
    finish_parser.add_argument("--base-url", required=True)
    finish_parser.add_argument("--state-file", required=True)
    finish_parser.add_argument("--auth-command", required=True)
    finish_parser.set_defaults(handler=finish)

    cleanup_parser = commands.add_parser("cleanup")
    cleanup_parser.add_argument("--database", required=True)
    cleanup_parser.add_argument("--state-file", required=True)
    cleanup_parser.add_argument("--auth-command", required=True)
    cleanup_parser.set_defaults(handler=cleanup)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        arguments.handler(arguments)
    except AcceptanceError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    except Exception:
        sys.stderr.write("INTERNAL_ERROR\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
