"""Packet and job command tests for the thin Card OS client.

Covers the six packet/job commands (``packets list/claim/get/complete``,
``jobs status/events``) against a loopback fixture server: exact routes and
protected headers, single-segment id encoding, closed packet-envelope
validation with the server 0.3.1 digest recomputed independently, safe
``O_EXCL`` packet saves, fail-closed free-concept handling, frozen error-code
pass-through, timeout-triggered status reads (never blind POST replays),
local auth failure before any HTTP, and the process-local doctor gate for
mutations.

Fixture provenance (server app commit
c2a898cba5b8a8948c06688d8c2a387353d7cbbe, copied verbatim shapes into this
module so the suite never depends on the neighboring checkout):

- packet envelope shape: ``src/cognitive_card_server/http/serialization.py``
  (``serialize_packet``);
- closed packet schema: ``src/cognitive_card_server/subscriber/model.py``
  (``GenerationPacket.to_dict``);
- digest algorithm: ``src/cognitive_card_server/subscriber/repository.py``
  (``_canonical_json`` + ``_digest``);
- job/event shapes: ``http/serialization.py`` (``serialize_job`` /
  ``serialize_event``);
- error envelope shape: ``http/serialization.py`` (``error_response``);
- realistic values (job fields, packet issue body, lease timestamps):
  ``tests/test_http_subscriber.py``.

All tokens in this file are obvious fakes.
"""

from __future__ import annotations

import contextlib
import hashlib
import http.server
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "skills" / "cognitive-card-os" / "scripts" / "card_os_client.py"
FAKE_TOKEN = "dummy-fixture-token-not-a-real-secret"
STORED_TOKEN = "dummy-stored-token-not-a-real-secret"
STORED_TOKEN_BYTES = STORED_TOKEN.encode("utf-8")

_spec = importlib.util.spec_from_file_location("card_os_client", CLIENT_PATH)
client = importlib.util.module_from_spec(_spec)
# dataclasses in Python 3.14 resolve cls.__module__ through sys.modules.
sys.modules["card_os_client"] = client
# Never write bytecode into the skill source tree: the release tests require
# it to remain the exact five-file closure.
_dont_write_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    _spec.loader.exec_module(client)
finally:
    sys.dont_write_bytecode = _dont_write_bytecode


# ---------------------------------------------------------------------------
# Fixtures copied from server commit c2a898c (see module docstring).
# ---------------------------------------------------------------------------

PACKET_ID = "gp_0123456789abcdef0123456789abcdef"
JOB_ID = "job_rabbit_v02"


def _packet_dict() -> dict[str, object]:
    """GenerationPacket.to_dict() shape from subscriber/model.py, with the
    realistic values used by tests/test_http_subscriber.py."""
    return {
        "packet_id": PACKET_ID,
        "job_id": JOB_ID,
        "execution_profile": "client_subscription_interactive",
        "stage": "bilingual_projection",
        "content_lock_digest": "sha256:" + "a" * 64,
        "registry_commit": "0123456789abcdef",
        "template_fingerprint": "sha256:" + "b" * 64,
        "age_profile": "age-5-6",
        "language_projection": "cn-observation",
        "instructions": ["Use only declared propositions."],
        "required_outputs": [
            {
                "relative_path": "cards/cn-observation.json",
                "media_type": "application/json",
                "max_bytes": 65536,
            }
        ],
        "forbidden_changes": ["facts"],
        "issued_at": "2026-07-13T10:00:00.000000Z",
        "expires_at": "2026-07-13T11:00:00.000000Z",
        "input_artifacts": [],
        "schema": "cognitive-card-generation-packet-v1",
    }


def _server_canonical(value: object) -> bytes:
    """Repository._canonical_json at c2a898c, copied verbatim."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _server_digest(packet: dict[str, object]) -> str:
    """Repository._digest at c2a898c, copied verbatim."""
    return "sha256:" + hashlib.sha256(_server_canonical(packet)).hexdigest()


def _envelope(
    packet: dict[str, object] | None = None,
    *,
    claimed_by: object = None,
    lease_expires_at: object = None,
    created_at: object = "2026-07-13T10:00:00.000000Z",
    expired_at: object = None,
    digest: object = "auto",
) -> dict[str, object]:
    """serialize_packet shape from http/serialization.py."""
    packet = _packet_dict() if packet is None else packet
    if digest == "auto":
        digest = _server_digest(packet)
    return {
        "packet": packet,
        "packet_digest": digest,
        "claimed_by": claimed_by,
        "lease_expires_at": lease_expires_at,
        "created_at": created_at,
        "expired_at": expired_at,
    }


def _claimed_envelope() -> dict[str, object]:
    # 900-second lease from 2026-07-13T10:00:00Z, as in the server tests.
    return _envelope(
        claimed_by="client-macbook",
        lease_expires_at="2026-07-13T10:15:00.000000Z",
    )


def _job_dict(state: str = "client_generating") -> dict[str, object]:
    """serialize_job shape from http/serialization.py."""
    return {
        "job_id": JOB_ID,
        "execution_profile": "client_subscription_interactive",
        "state": state,
        "content_lock_digest": "sha256:" + "a" * 64,
        "registry_commit": "0123456789abcdef",
        "template_fingerprint": "sha256:" + "b" * 64,
        "age_profile": "age-5-6",
        "created_at": "2026-07-13T10:00:00.000000Z",
        "updated_at": "2026-07-13T10:05:00.000000Z",
    }


def _events_document() -> dict[str, object]:
    """serialize_event list shape from http/serialization.py."""
    return {
        "events": [
            {
                "event_id": 1,
                "job_id": JOB_ID,
                "event_type": "job.created",
                "actor": "admin",
                "reason": "locked-job-imported",
                "details": {"job_id": JOB_ID},
                "occurred_at": "2026-07-13T10:00:00.000000Z",
            },
            {
                "event_id": 2,
                "job_id": JOB_ID,
                "event_type": "packet.issued",
                "actor": "admin",
                "reason": "packet-issued",
                "details": {
                    "packet_id": PACKET_ID,
                    "packet_digest": _server_digest(_packet_dict()),
                },
                "occurred_at": "2026-07-13T10:00:00.000000Z",
            },
        ]
    }


def _error_envelope(code: str, request_id: str = "req-fixture-01") -> dict[str, object]:
    """error_response shape from http/serialization.py."""
    return {"error": {"code": code, "message": code, "request_id": request_id}}


HEALTH_OK = {"status": "ok", "server_version": "0.3.1"}
CAPABILITIES_OK = {
    "schema": "cognitive-card-capabilities-v1",
    "server_version": "0.3.1",
    "protocol": {"minimum": 1, "maximum": 1},
    "packet_schemas": ["cognitive-card-generation-packet-v1"],
    "result_schemas": ["cognitive-card-generation-result-v1"],
    "minimum_skill_release": "0.1.0",
    "features": {
        "locked_job_admin_import": True,
        "subscriber_packet_exchange": True,
        "free_form_job_creation": False,
        "browser_session": False,
        "review": False,
    },
}

PACKETS_AVAILABLE_PATH = "/card-os/api/v1/packets/available"
PACKET_PATH = f"/card-os/api/v1/packets/{PACKET_ID}"
CLAIM_PATH = f"{PACKET_PATH}/claim"
COMPLETE_PATH = f"{PACKET_PATH}/complete"
JOB_PATH = f"/card-os/api/v1/jobs/{JOB_ID}"
EVENTS_PATH = f"{JOB_PATH}/events"


# ---------------------------------------------------------------------------
# Loopback fixture server (same pattern as the transport suite).
# ---------------------------------------------------------------------------


class _FixtureServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _FixtureHandler)
        self.routes = {}
        self.requests: list[dict[str, object]] = []
        self.lock = threading.Lock()

    @property
    def port(self) -> int:
        return self.server_address[1]


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args: object) -> None:
        pass

    def _dispatch(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        with self.server.lock:
            self.server.requests.append(
                {
                    "method": self.command,
                    "path": self.path,
                    "headers": {k: v for k, v in self.headers.items()},
                    "body": body,
                }
            )
        route = self.server.routes.get((self.command, self.path))
        try:
            if route is None:
                self._respond(404, json.dumps(_error_envelope("ROUTE_NOT_FOUND")).encode())
            else:
                route(self)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = _dispatch
    do_POST = _dispatch

    def _respond(
        self,
        status: int,
        body: bytes,
        *,
        content_type: str = "application/json",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _json_route(document: dict[str, object], status: int = 200):
    body = json.dumps(document).encode("utf-8")

    def route(handler: _FixtureHandler) -> None:
        handler._respond(status, body)

    return route


def _stall_route(handler: _FixtureHandler) -> None:
    time.sleep(5)


class FakeStore:
    """In-memory CredentialStore double (same shape as the credential suite)."""

    backend_name = "fake-backend"

    def __init__(self, stored: bytes | None = None) -> None:
        self.stored = stored

    def set(self, token: bytes) -> None:
        self.stored = bytes(token)

    def get(self) -> bytes | None:
        return self.stored

    def delete(self) -> bool:
        had = self.stored is not None
        self.stored = None
        return had


class CommandTestCase(unittest.TestCase):
    """Base class: fixture server, config/credential seams, clean env."""

    def setUp(self) -> None:
        self.server = _FixtureServer()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self._saved_config = client._config
        self._saved_override = client._credential_store_override
        self._saved_doctor = getattr(client, "_doctor_cache", None)
        self.addCleanup(self._restore)
        client._config = client.TransportConfig(
            base_url=f"http://127.0.0.1:{self.server.port}/card-os/",
            timeout_seconds=2.0,
            allow_plain_http_loopback=True,
        )
        self.store = FakeStore(STORED_TOKEN_BYTES)
        client._credential_store_override = self.store
        client._doctor_cache = None
        # Neutralize any real CARD_OS_TOKEN in the process environment.
        self._env_patcher = unittest.mock.patch.dict(
            os.environ, {"CARD_OS_TOKEN": ""}, clear=False
        )
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)

    def _restore(self) -> None:
        client._config = self._saved_config
        client._credential_store_override = self._saved_override
        client._doctor_cache = self._saved_doctor
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _routes(self, routes: dict[tuple[str, str], object]) -> None:
        self.server.routes.update(routes)

    def _serve_doctor(
        self,
        health: dict[str, object] | None = None,
        capabilities: dict[str, object] | None = None,
    ) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(
                    HEALTH_OK if health is None else health
                ),
                ("GET", "/card-os/api/v1/capabilities"): _json_route(
                    CAPABILITIES_OK if capabilities is None else capabilities
                ),
            }
        )

    def run_cli(self, args: list[str]):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = client.main(args)
        return code, out.getvalue(), err.getvalue()

    def assert_no_token(self, *chunks: str) -> None:
        for chunk in chunks:
            self.assertNotIn(FAKE_TOKEN, chunk)
            self.assertNotIn(STORED_TOKEN, chunk)

    def methods_paths(self) -> list[tuple[str, str]]:
        return [(r["method"], r["path"]) for r in self.server.requests]

    def assert_protected_headers(self, record: dict[str, object]) -> None:
        headers = {k.lower(): v for k, v in record["headers"].items()}
        self.assertEqual(f"Bearer {STORED_TOKEN}", headers["authorization"])
        self.assertEqual("1", headers["x-card-os-protocol"])
        self.assertEqual("0.1.1", headers["x-card-os-skill-release"])
        allowed = {
            "host",
            "accept",
            "accept-encoding",
            "connection",
            "content-type",
            "content-length",
            "user-agent",
            "authorization",
            "x-card-os-protocol",
            "x-card-os-skill-release",
        }
        self.assertEqual(set(), set(headers) - allowed)


class RouteAndHeaderTests(CommandTestCase):
    """Each command hits exactly its frozen route with exact protected headers."""

    def _assert_single_protected_request(self, method: str, path: str) -> dict[str, object]:
        matches = [
            r for r in self.server.requests if (r["method"], r["path"]) == (method, path)
        ]
        self.assertEqual(1, len(matches))
        self.assert_protected_headers(matches[0])
        return matches[0]

    def test_packets_list_route_and_headers(self) -> None:
        self._routes({("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": [_envelope()]})})
        code, out, err = self.run_cli(["packets", "list"])
        self.assertEqual(0, code, err)
        record = self._assert_single_protected_request("GET", PACKETS_AVAILABLE_PATH)
        self.assertEqual(b"", record["body"])
        self.assert_no_token(out, err)

    def test_packets_claim_route_headers_and_body(self) -> None:
        self._serve_doctor()
        self._routes({("POST", CLAIM_PATH): _json_route(_claimed_envelope())})
        code, out, err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(0, code, err)
        record = self._assert_single_protected_request("POST", CLAIM_PATH)
        self.assertEqual(b"{}", record["body"])
        headers = {k.lower(): v for k, v in record["headers"].items()}
        self.assertEqual("application/json", headers["content-type"])
        self.assert_no_token(out, err)

    def test_packets_get_route_and_headers(self) -> None:
        self._routes({("GET", PACKET_PATH): _json_route(_envelope())})
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            code, out, err = self.run_cli(
                ["packets", "get", PACKET_ID, "--output", str(target)]
            )
        self.assertEqual(0, code, err)
        self._assert_single_protected_request("GET", PACKET_PATH)
        self.assert_no_token(out, err)

    def test_packets_complete_route_headers_and_body(self) -> None:
        self._serve_doctor()
        self._routes({("POST", COMPLETE_PATH): _json_route(_claimed_envelope())})
        code, out, err = self.run_cli(["packets", "complete", PACKET_ID])
        self.assertEqual(0, code, err)
        record = self._assert_single_protected_request("POST", COMPLETE_PATH)
        self.assertEqual(b"{}", record["body"])
        self.assert_no_token(out, err)

    def test_jobs_status_route_and_headers(self) -> None:
        self._routes({("GET", JOB_PATH): _json_route(_job_dict())})
        code, out, err = self.run_cli(["jobs", "status", JOB_ID])
        self.assertEqual(0, code, err)
        self._assert_single_protected_request("GET", JOB_PATH)
        self.assert_no_token(out, err)

    def test_jobs_events_route_and_headers(self) -> None:
        self._routes({("GET", EVENTS_PATH): _json_route(_events_document())})
        code, out, err = self.run_cli(["jobs", "events", JOB_ID])
        self.assertEqual(0, code, err)
        self._assert_single_protected_request("GET", EVENTS_PATH)
        self.assert_no_token(out, err)


class IdValidationTests(CommandTestCase):
    """IDs are exactly one path segment: reject empty, controls, / and \\."""

    def test_invalid_ids_fail_closed_without_http(self) -> None:
        bad_ids = ["", "a/b", "a\\b", "a\nb", "a\rb", "a\tb", "a\x00b", "a\x7fb"]
        for bad in bad_ids:
            with self.subTest(bad=bad):
                del self.server.requests[:]
                code, out, err = self.run_cli(["packets", "claim", bad])
                self.assertEqual(1, code)
                payload = json.loads(out)
                self.assertEqual("REQUEST_VALIDATION_FAILED", payload["error"]["code"])
                self.assertEqual([], self.server.requests)
                self.assert_no_token(out, err)

    def test_invalid_job_ids_fail_closed_without_http(self) -> None:
        for bad in ("", "a/b", "a\\b", "a\nb"):
            with self.subTest(bad=bad):
                del self.server.requests[:]
                code, out, _err = self.run_cli(["jobs", "status", bad])
                self.assertEqual(1, code)
                self.assertEqual(
                    "REQUEST_VALIDATION_FAILED", json.loads(out)["error"]["code"]
                )
                self.assertEqual([], self.server.requests)

    def test_structurally_valid_id_is_encoded_as_one_segment(self) -> None:
        # "." and "%" are allowed by the server contract ([^/]+); the client
        # must not reject them, and must keep them inside one path segment.
        tricky = "gp_..%2f.stay"
        encoded_path = "/card-os/api/v1/packets/gp_..%252f.stay/claim"
        self._serve_doctor()
        self._routes({("POST", encoded_path): _json_route(_claimed_envelope())})
        code, out, err = self.run_cli(["packets", "claim", tricky])
        self.assertEqual(0, code, err)
        self.assertIn(("POST", encoded_path), self.methods_paths())


class FreeConceptTests(CommandTestCase):
    """Free-concept-shaped invocations fail closed, never fabricating a job."""

    def test_free_concept_claim_is_trusted_upstream_required(self) -> None:
        for concept in ("兔子，5～6岁", "rabbit cards for kids", "汪汪队 任务"):
            with self.subTest(concept=concept):
                del self.server.requests[:]
                code, out, err = self.run_cli(["packets", "claim", concept])
                self.assertEqual(1, code)
                payload = json.loads(out)
                self.assertEqual(
                    "TRUSTED_UPSTREAM_REQUIRED", payload["error"]["code"]
                )
                self.assertEqual([], self.server.requests)
                self.assert_no_token(out, err)

    def test_free_concept_get_and_complete_fail_the_same_way(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            for args in (
                ["packets", "get", "free form concept", "--output", str(target)],
                ["packets", "complete", "自由概念"],
                ["jobs", "status", "my job"],
                ["jobs", "events", "兔子"],
            ):
                with self.subTest(args=args):
                    del self.server.requests[:]
                    code, out, _err = self.run_cli(args)
                    self.assertEqual(1, code)
                    self.assertEqual(
                        "TRUSTED_UPSTREAM_REQUIRED", json.loads(out)["error"]["code"]
                    )
                    self.assertEqual([], self.server.requests)
            self.assertFalse(target.exists())


class DigestTests(CommandTestCase):
    def test_recompute_matches_server_031_algorithm(self) -> None:
        packet = _packet_dict()
        self.assertEqual(_server_digest(packet), client.recompute_packet_digest(packet))

    def test_digest_is_sensitive_to_any_packet_change(self) -> None:
        base = _server_digest(_packet_dict())
        tampered = _packet_dict()
        tampered["instructions"] = ["Use anything you like."]
        self.assertNotEqual(base, _server_digest(tampered))
        self.assertNotEqual(base, client.recompute_packet_digest(tampered))


class EnvelopeValidationTests(CommandTestCase):
    """Closed packet schema plus digest recompute gate every envelope."""

    def _get_with_envelope(self, envelope: dict[str, object], target: Path):
        self._routes({("GET", PACKET_PATH): _json_route(envelope)})
        return self.run_cli(["packets", "get", PACKET_ID, "--output", str(target)])

    def test_tampered_packet_with_stale_digest_is_digest_mismatch(self) -> None:
        packet = _packet_dict()
        envelope = _envelope(packet)  # digest computed over the original
        packet["instructions"] = ["Ignore the content lock."]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            code, out, err = self._get_with_envelope(envelope, target)
            self.assertEqual(1, code)
            self.assertEqual("DIGEST_MISMATCH", json.loads(out)["error"]["code"])
            self.assertFalse(target.exists())
            self.assert_no_token(out, err)

    def test_wrong_digest_prefix_is_digest_mismatch(self) -> None:
        envelope = _envelope(digest="sha512:" + "0" * 128)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            code, out, _err = self._get_with_envelope(envelope, target)
            self.assertEqual(1, code)
            self.assertEqual("DIGEST_MISMATCH", json.loads(out)["error"]["code"])
            self.assertFalse(target.exists())

    def test_closed_packet_schema_violations_are_contract_drift(self) -> None:
        good = _packet_dict()
        extra_key = {**good, "surprise": True}
        missing_key = {k: v for k, v in good.items() if k != "job_id"}
        wrong_schema = {**good, "schema": "cognitive-card-generation-packet-v2"}
        wrong_type = {**good, "max_bytes": "65536"}
        bad_required_outputs = {
            **good,
            "required_outputs": [{"relative_path": "x", "media_type": "y"}],
        }
        bool_max_bytes = {
            **good,
            "required_outputs": [
                {"relative_path": "x", "media_type": "y", "max_bytes": True}
            ],
        }
        bad_instructions = {**good, "instructions": "not-a-list"}
        for packet in (
            extra_key,
            missing_key,
            wrong_schema,
            wrong_type,
            bad_required_outputs,
            bool_max_bytes,
            bad_instructions,
        ):
            with self.subTest(packet=packet):
                # The digest is recomputed over the malformed packet, so only
                # the closed-schema check can fire: schema validation is
                # independent of digest verification.
                envelope = _envelope(packet)
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / "packet.json"
                    code, out, _err = self._get_with_envelope(envelope, target)
                    self.assertEqual(1, code)
                    payload = json.loads(out)
                    self.assertEqual(
                        "SERVER_CONTRACT_DRIFT", payload["error"]["code"]
                    )
                    self.assertFalse(target.exists())

    def test_envelope_shape_violations_are_contract_drift(self) -> None:
        good = _envelope()
        variants = [
            {**good, "extra": 1},
            {k: v for k, v in good.items() if k != "packet_digest"},
            {**good, "packet_digest": 42},
            {**good, "packet": "not-a-dict"},
            ["not", "a", "dict"],
        ]
        for envelope in variants:
            with self.subTest(envelope=str(envelope)[:60]):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / "packet.json"
                    code, out, _err = self._get_with_envelope(envelope, target)
                    self.assertEqual(1, code)
                    self.assertEqual(
                        "SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"]
                    )
                    self.assertFalse(target.exists())

    def test_claim_lease_expiry_types_validated_separately_from_digest(self) -> None:
        # Digest is valid in every variant; only envelope metadata is broken.
        variants = [
            _envelope(claimed_by=42),
            _envelope(lease_expires_at=123),
            _envelope(created_at=None),
            _envelope(expired_at=7),
        ]
        for envelope in variants:
            with self.subTest(envelope=str(envelope)[:80]):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / "packet.json"
                    code, out, _err = self._get_with_envelope(envelope, target)
                    self.assertEqual(1, code)
                    self.assertEqual(
                        "SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"]
                    )
                    self.assertFalse(target.exists())

    def test_claimed_envelope_with_valid_types_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            code, out, _err = self._get_with_envelope(_claimed_envelope(), target)
            self.assertEqual(0, code)
            self.assertTrue(target.exists())

    def test_list_validates_every_envelope(self) -> None:
        tampered = _packet_dict()
        envelope_bad = _envelope(tampered)
        tampered["instructions"] = ["tampered"]
        self._routes(
            {
                ("GET", PACKETS_AVAILABLE_PATH): _json_route(
                    {"packets": [_envelope(), envelope_bad]}
                )
            }
        )
        code, out, _err = self.run_cli(["packets", "list"])
        self.assertEqual(1, code)
        self.assertEqual("DIGEST_MISMATCH", json.loads(out)["error"]["code"])

    def test_claim_response_envelope_is_also_verified(self) -> None:
        packet = _packet_dict()
        envelope = _envelope(packet, claimed_by="client-macbook",
                              lease_expires_at="2026-07-13T10:15:00.000000Z")
        packet["stage"] = "image_generation"  # stale digest now
        self._serve_doctor()
        self._routes({("POST", CLAIM_PATH): _json_route(envelope)})
        code, out, _err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(1, code)
        self.assertEqual("DIGEST_MISMATCH", json.loads(out)["error"]["code"])


class PacketGetWriteTests(CommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.target = Path(self._tmp.name) / "packet.json"

    def _run_get(self, envelope: dict[str, object] | None = None):
        self._routes(
            {("GET", PACKET_PATH): _json_route(_envelope() if envelope is None else envelope)}
        )
        return self.run_cli(["packets", "get", PACKET_ID, "--output", str(self.target)])

    def test_writes_canonical_packet_bytes_matching_the_digest(self) -> None:
        code, out, err = self._run_get()
        self.assertEqual(0, code, err)
        payload_bytes = self.target.read_bytes()
        self.assertEqual(_server_canonical(_packet_dict()), payload_bytes)
        # The saved bytes are exactly what packet_digest covers.
        self.assertEqual(
            _server_digest(_packet_dict()),
            "sha256:" + hashlib.sha256(payload_bytes).hexdigest(),
        )
        payload = json.loads(out)
        self.assertEqual("saved", payload["status"])
        self.assertEqual(PACKET_ID, payload["packet_id"])
        self.assertEqual(_server_digest(_packet_dict()), payload["packet_digest"])
        self.assert_no_token(out, err)

    def test_written_file_is_private_regular_file(self) -> None:
        code, _out, _err = self._run_get()
        self.assertEqual(0, code)
        info = os.lstat(self.target)
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertEqual(0o600, stat.S_IMODE(info.st_mode))

    def test_existing_file_is_never_overwritten(self) -> None:
        self.target.write_bytes(b"dummy-existing-content-not-a-secret")
        code, out, _err = self._run_get()
        self.assertEqual(1, code)
        self.assertEqual(
            "REQUEST_VALIDATION_FAILED", json.loads(out)["error"]["code"]
        )
        self.assertEqual(
            b"dummy-existing-content-not-a-secret", self.target.read_bytes()
        )

    def test_symlink_output_path_is_never_followed(self) -> None:
        victim = Path(self._tmp.name) / "victim.json"
        victim.write_bytes(b"dummy-victim-content-not-a-secret")
        os.symlink(victim, self.target)
        code, out, _err = self._run_get()
        self.assertEqual(1, code)
        self.assertEqual(
            "REQUEST_VALIDATION_FAILED", json.loads(out)["error"]["code"]
        )
        self.assertEqual(b"dummy-victim-content-not-a-secret", victim.read_bytes())

    def test_missing_output_directory_fails_closed(self) -> None:
        self.target = Path(self._tmp.name) / "no-such-dir" / "packet.json"
        code, out, _err = self._run_get()
        self.assertEqual(1, code)
        self.assertEqual(
            "REQUEST_VALIDATION_FAILED", json.loads(out)["error"]["code"]
        )


class TrustedUpstreamTests(CommandTestCase):
    def test_empty_packet_list_is_trusted_upstream_required(self) -> None:
        self._routes({("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": []})})
        code, out, err = self.run_cli(["packets", "list"])
        self.assertEqual(1, code)
        self.assertEqual("TRUSTED_UPSTREAM_REQUIRED", json.loads(out)["error"]["code"])
        self.assert_no_token(out, err)

    def test_malformed_packet_list_is_contract_drift(self) -> None:
        for document in ({"packets": "nope"}, {}, {"packets": [42]}):
            with self.subTest(document=document):
                self._routes(
                    {("GET", PACKETS_AVAILABLE_PATH): _json_route(document)}
                )
                code, out, _err = self.run_cli(["packets", "list"])
                self.assertEqual(1, code)
                self.assertEqual(
                    "SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"]
                )


class ErrorMappingTests(CommandTestCase):
    """Frozen 0.3.1 codes pass through verbatim; request_id is preserved."""

    def _assert_error_passthrough(self, args, method, path, code, status) -> None:
        self._serve_doctor()
        self._routes(
            {(method, path): _json_route(_error_envelope(code), status=status)}
        )
        del self.server.requests[:]
        out_code, out, err = self.run_cli(args)
        self.assertEqual(1, out_code)
        payload = json.loads(out)
        self.assertEqual(code, payload["error"]["code"])
        self.assertEqual("req-fixture-01", payload["error"]["request_id"])
        self.assert_no_token(out, err)

    def test_packet_state_codes_pass_through(self) -> None:
        cases = [
            (["packets", "claim", PACKET_ID], "POST", CLAIM_PATH,
             "PACKET_ALREADY_CLAIMED", 409),
            (["packets", "claim", PACKET_ID], "POST", CLAIM_PATH,
             "AUTH_SCOPE_REQUIRED", 403),
            (["packets", "claim", PACKET_ID], "POST", CLAIM_PATH,
             "PACKET_EXPIRED", 410),
            (["packets", "claim", PACKET_ID], "POST", CLAIM_PATH,
             "LEASE_EXPIRED", 409),
            (["packets", "complete", PACKET_ID], "POST", COMPLETE_PATH,
             "INVALID_STATE_TRANSITION", 409),
            (["packets", "complete", PACKET_ID], "POST", COMPLETE_PATH,
             "LEASE_OWNER_MISMATCH", 409),
            (["jobs", "status", JOB_ID], "GET", JOB_PATH, "JOB_NOT_FOUND", 404),
            (["jobs", "events", JOB_ID], "GET", EVENTS_PATH, "JOB_NOT_FOUND", 404),
        ]
        for args, method, path, code, status in cases:
            with self.subTest(code=code):
                self._assert_error_passthrough(args, method, path, code, status)

    def test_packet_not_found_on_get(self) -> None:
        self._routes(
            {("GET", PACKET_PATH): _json_route(_error_envelope("PACKET_NOT_FOUND"), status=404)}
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            code, out, _err = self.run_cli(
                ["packets", "get", PACKET_ID, "--output", str(target)]
            )
            self.assertEqual(1, code)
            payload = json.loads(out)
            self.assertEqual("PACKET_NOT_FOUND", payload["error"]["code"])
            self.assertFalse(target.exists())

    def test_unknown_safe_code_maps_to_drift_and_is_preserved(self) -> None:
        self._routes(
            {
                ("GET", PACKETS_AVAILABLE_PATH): _json_route(
                    _error_envelope("FUTURE_SAFE_CODE"), status=500
                )
            }
        )
        code, out, _err = self.run_cli(["packets", "list"])
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("SERVER_CONTRACT_DRIFT", payload["error"]["code"])
        self.assertEqual("FUTURE_SAFE_CODE", payload["error"]["server_code"])


class TimeoutStatusReadTests(CommandTestCase):
    """A claim/complete timeout reads state; it never blindly re-POSTs."""

    def _use_short_timeout(self) -> None:
        client._config = client.TransportConfig(
            base_url=f"http://127.0.0.1:{self.server.port}/card-os/",
            timeout_seconds=0.3,
            allow_plain_http_loopback=True,
        )

    def test_claim_timeout_reads_packet_state_and_never_reposts(self) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("POST", CLAIM_PATH): _stall_route,
                ("GET", PACKET_PATH): _json_route(_claimed_envelope()),
            }
        )
        self._use_short_timeout()
        code, out, err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("HTTP_ERROR", payload["error"]["code"])
        # The observed server state is reported for manual reconciliation.
        self.assertIn("client-macbook", payload["error"]["message"])
        posts = [r for r in self.server.requests if r["method"] == "POST"]
        self.assertEqual([("POST", CLAIM_PATH)], [(r["method"], r["path"]) for r in posts])
        # The status read happened after the stalled POST.
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("POST", CLAIM_PATH),
                ("GET", PACKET_PATH),
            ],
            self.methods_paths(),
        )
        self.assert_no_token(out, err)

    def test_complete_timeout_reads_packet_then_job_state(self) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("POST", COMPLETE_PATH): _stall_route,
                ("GET", PACKET_PATH): _json_route(_claimed_envelope()),
                ("GET", JOB_PATH): _json_route(_job_dict(state="awaiting_upload")),
            }
        )
        self._use_short_timeout()
        code, out, err = self.run_cli(["packets", "complete", PACKET_ID])
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("HTTP_ERROR", payload["error"]["code"])
        self.assertIn("awaiting_upload", payload["error"]["message"])
        posts = [r for r in self.server.requests if r["method"] == "POST"]
        self.assertEqual([("POST", COMPLETE_PATH)], [(r["method"], r["path"]) for r in posts])
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("POST", COMPLETE_PATH),
                ("GET", PACKET_PATH),
                ("GET", JOB_PATH),
            ],
            self.methods_paths(),
        )
        self.assert_no_token(out, err)

    def test_timeout_with_failed_status_read_still_never_reposts(self) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("POST", CLAIM_PATH): _stall_route,
                ("GET", PACKET_PATH): _json_route(
                    _error_envelope("INTERNAL_ERROR"), status=500
                ),
            }
        )
        self._use_short_timeout()
        code, out, err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(1, code)
        self.assertEqual("HTTP_ERROR", json.loads(out)["error"]["code"])
        posts = [r for r in self.server.requests if r["method"] == "POST"]
        self.assertEqual(1, len(posts))
        # Doctor reads, the stalled POST, then exactly one status-read GET.
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("POST", CLAIM_PATH),
                ("GET", PACKET_PATH),
            ],
            self.methods_paths(),
        )
        self.assert_no_token(out, err)


class AuthRequiredTests(CommandTestCase):
    """No credential anywhere -> local AUTH_REQUIRED before any HTTP."""

    def setUp(self) -> None:
        super().setUp()
        self.store.stored = None  # no stored credential; env is neutralized

    def test_every_protected_command_fails_locally_without_http(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "packet.json"
            commands = [
                ["packets", "list"],
                ["packets", "claim", PACKET_ID],
                ["packets", "get", PACKET_ID, "--output", str(target)],
                ["packets", "complete", PACKET_ID],
                ["jobs", "status", JOB_ID],
                ["jobs", "events", JOB_ID],
            ]
            for args in commands:
                with self.subTest(args=args):
                    del self.server.requests[:]
                    code, out, err = self.run_cli(args)
                    self.assertEqual(1, code)
                    payload = json.loads(out)
                    self.assertEqual("AUTH_REQUIRED", payload["error"]["code"])
                    self.assertEqual([], self.server.requests)
                    self.assert_no_token(out, err)
            self.assertFalse(target.exists())

    def test_env_token_takes_precedence_for_commands(self) -> None:
        self._routes({("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": [_envelope()]})})
        with unittest.mock.patch.dict(
            os.environ, {"CARD_OS_TOKEN": FAKE_TOKEN}, clear=False
        ):
            code, out, err = self.run_cli(["packets", "list"])
        self.assertEqual(0, code, err)
        headers = {k.lower(): v for k, v in self.server.requests[0]["headers"].items()}
        self.assertEqual(f"Bearer {FAKE_TOKEN}", headers["authorization"])
        # The ephemeral token is used on the wire but never printed.
        self.assertNotIn(FAKE_TOKEN, out)
        self.assertNotIn(FAKE_TOKEN, err)


class FileStoreFallbackEndToEndTests(CommandTestCase):
    """End to end on a simulated linux host without secret-tool: a credential
    stored through auth set --stdin --allow-file-store authorizes protected
    commands through the read-side file fallback."""

    def setUp(self) -> None:
        super().setUp()
        client._credential_store_override = None  # real selection path
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.config_home = Path(self._tmp.name) / "config"
        self._fallback_env = unittest.mock.patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": str(self.config_home)},
            clear=False,
        )
        self._fallback_env.start()
        self.addCleanup(self._fallback_env.stop)
        self._platform_patcher = unittest.mock.patch.object(sys, "platform", "linux")
        self._platform_patcher.start()
        self.addCleanup(self._platform_patcher.stop)
        self._secret_patcher = unittest.mock.patch.object(
            client, "_secret_tool_available", return_value=False
        )
        self._secret_patcher.start()
        self.addCleanup(self._secret_patcher.stop)

    @property
    def credential_path(self) -> Path:
        return self.config_home / "cognitive-card-os" / "credentials.json"

    def _auth_set_file_store(self):
        fake_stdin = type("Stdin", (), {"buffer": io.BytesIO(FAKE_TOKEN.encode() + b"\n")})()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with unittest.mock.patch.object(sys, "stdin", fake_stdin):
                code = client.main(["auth", "set", "--stdin", "--allow-file-store"])
        return code, out.getvalue(), err.getvalue()

    def test_file_store_credential_authorizes_packets_list(self) -> None:
        self._routes(
            {("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": [_envelope()]})}
        )
        code, out, err = self._auth_set_file_store()
        self.assertEqual(0, code, err)
        self.assertEqual("file", json.loads(out)["backend"])

        code, out, err = self.run_cli(["packets", "list"])
        self.assertEqual(0, code, err)
        self.assertEqual(1, len(self.server.requests))
        headers = {
            k.lower(): v for k, v in self.server.requests[0]["headers"].items()
        }
        self.assertEqual(f"Bearer {FAKE_TOKEN}", headers["authorization"])
        self.assert_no_token(out, err)

        code, out, err = self.run_cli(["auth", "status"])
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertEqual("file", payload["backend"])
        self.assertEqual("present", payload["credential"])

        code, out, err = self.run_cli(["auth", "delete"])
        self.assertEqual(0, code, err)
        self.assertTrue(json.loads(out)["deleted"])
        self.assertFalse(self.credential_path.exists())

        # After deletion the protected command fails locally again.
        code, out, err = self.run_cli(["packets", "list"])
        self.assertEqual(1, code)
        self.assertEqual("AUTH_REQUIRED", json.loads(out)["error"]["code"])
        self.assertEqual(1, len(self.server.requests))
        self.assert_no_token(out, err)


class DoctorGateTests(CommandTestCase):
    """Mutations run doctor first, cached within the process only."""

    def test_claim_runs_doctor_before_posting(self) -> None:
        self._serve_doctor()
        self._routes({("POST", CLAIM_PATH): _json_route(_claimed_envelope())})
        code, out, err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(0, code, err)
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("POST", CLAIM_PATH),
            ],
            self.methods_paths(),
        )
        # Doctor reads are unauthenticated.
        for record in self.server.requests[:2]:
            self.assertNotIn("authorization", {k.lower() for k in record["headers"]})

    def test_doctor_result_is_cached_within_the_process(self) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("POST", CLAIM_PATH): _json_route(_claimed_envelope()),
                ("POST", COMPLETE_PATH): _json_route(_claimed_envelope()),
            }
        )
        code, _out, _err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(0, code)
        code, _out, _err = self.run_cli(["packets", "complete", PACKET_ID])
        self.assertEqual(0, code)
        health_reads = [
            r for r in self.server.requests if r["path"] == "/card-os/api/v1/health"
        ]
        capability_reads = [
            r for r in self.server.requests if r["path"] == "/card-os/api/v1/capabilities"
        ]
        self.assertEqual(1, len(health_reads))
        self.assertEqual(1, len(capability_reads))

    def test_incompatible_server_blocks_mutation_before_post(self) -> None:
        self._serve_doctor(
            capabilities={**CAPABILITIES_OK, "protocol": {"minimum": 2, "maximum": 3}}
        )
        code, out, _err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(1, code)
        self.assertEqual(
            "CLIENT_UPGRADE_REQUIRED", json.loads(out)["error"]["code"]
        )
        self.assertEqual([], [r for r in self.server.requests if r["method"] == "POST"])

    def test_read_only_commands_do_not_call_doctor(self) -> None:
        self._routes(
            {
                ("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": [_envelope()]}),
                ("GET", JOB_PATH): _json_route(_job_dict()),
            }
        )
        code, _out, _err = self.run_cli(["packets", "list"])
        self.assertEqual(0, code)
        code, _out, _err = self.run_cli(["jobs", "status", JOB_ID])
        self.assertEqual(0, code)
        self.assertEqual(
            [("GET", PACKETS_AVAILABLE_PATH), ("GET", JOB_PATH)], self.methods_paths()
        )


class OutputShapeTests(CommandTestCase):
    def _assert_canonical_stdout(self, out: str) -> dict[str, object]:
        payload = json.loads(out)
        self.assertEqual(client.canonical_json(payload).decode("utf-8") + "\n", out)
        return payload

    def test_packets_list_summary_shape(self) -> None:
        self._routes({("GET", PACKETS_AVAILABLE_PATH): _json_route({"packets": [_envelope()]})})
        code, out, _err = self.run_cli(["packets", "list"])
        self.assertEqual(0, code)
        payload = self._assert_canonical_stdout(out)
        self.assertEqual("ok", payload["status"])
        self.assertEqual(1, len(payload["packets"]))
        summary = payload["packets"][0]
        self.assertEqual(PACKET_ID, summary["packet_id"])
        self.assertEqual(JOB_ID, summary["job_id"])
        self.assertEqual("bilingual_projection", summary["stage"])
        self.assertEqual("2026-07-13T11:00:00.000000Z", summary["expires_at"])
        self.assertEqual(_server_digest(_packet_dict()), summary["packet_digest"])

    def test_claim_output_reports_lease(self) -> None:
        self._serve_doctor()
        self._routes({("POST", CLAIM_PATH): _json_route(_claimed_envelope())})
        code, out, _err = self.run_cli(["packets", "claim", PACKET_ID])
        self.assertEqual(0, code)
        payload = self._assert_canonical_stdout(out)
        self.assertEqual("claimed", payload["status"])
        self.assertEqual(PACKET_ID, payload["packet_id"])
        self.assertEqual("2026-07-13T10:15:00.000000Z", payload["lease_expires_at"])

    def test_complete_output_is_only_a_state_transition(self) -> None:
        self._serve_doctor()
        self._routes({("POST", COMPLETE_PATH): _json_route(_claimed_envelope())})
        code, out, _err = self.run_cli(["packets", "complete", PACKET_ID])
        self.assertEqual(0, code)
        payload = self._assert_canonical_stdout(out)
        self.assertEqual(PACKET_ID, payload["packet_id"])
        # Never claim the result is accepted or published.
        self.assertNotIn("accepted", out)
        self.assertNotIn("published", out)

    def test_jobs_status_output_shape(self) -> None:
        self._routes({("GET", JOB_PATH): _json_route(_job_dict())})
        code, out, _err = self.run_cli(["jobs", "status", JOB_ID])
        self.assertEqual(0, code)
        payload = self._assert_canonical_stdout(out)
        self.assertEqual("ok", payload["status"])
        self.assertEqual("client_generating", payload["job"]["state"])
        self.assertEqual(JOB_ID, payload["job"]["job_id"])

    def test_jobs_events_output_shape(self) -> None:
        self._routes({("GET", EVENTS_PATH): _json_route(_events_document())})
        code, out, _err = self.run_cli(["jobs", "events", JOB_ID])
        self.assertEqual(0, code)
        payload = self._assert_canonical_stdout(out)
        self.assertEqual("ok", payload["status"])
        self.assertEqual(JOB_ID, payload["job_id"])
        self.assertEqual(2, len(payload["events"]))
        self.assertEqual("packet.issued", payload["events"][1]["event_type"])

    def test_malformed_job_document_is_contract_drift(self) -> None:
        job = _job_dict()
        del job["state"]
        self._routes({("GET", JOB_PATH): _json_route(job)})
        code, out, _err = self.run_cli(["jobs", "status", JOB_ID])
        self.assertEqual(1, code)
        self.assertEqual("SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"])

    def test_malformed_events_document_is_contract_drift(self) -> None:
        document = _events_document()
        document["events"][0]["event_id"] = "not-an-int"
        self._routes({("GET", EVENTS_PATH): _json_route(document)})
        code, out, _err = self.run_cli(["jobs", "events", JOB_ID])
        self.assertEqual(1, code)
        self.assertEqual("SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"])


class CliUsageTests(CommandTestCase):
    def test_usage_errors_exit_2_without_http(self) -> None:
        bad_invocations = [
            ["packets"],
            ["packets", "frobnicate"],
            ["packets", "claim"],
            ["packets", "claim", PACKET_ID, "extra"],
            ["packets", "get", PACKET_ID],
            ["packets", "get", PACKET_ID, "--output"],
            ["packets", "get", "--output", "x"],
            ["packets", "complete"],
            ["jobs"],
            ["jobs", "frobnicate"],
            ["jobs", "status"],
            ["jobs", "events"],
        ]
        for args in bad_invocations:
            with self.subTest(args=args):
                del self.server.requests[:]
                code, out, err = self.run_cli(args)
                self.assertEqual(2, code)
                self.assertEqual("", out)
                self.assertIn("usage:", err)
                self.assertEqual([], self.server.requests)

    def test_unknown_top_level_command_still_exits_2(self) -> None:
        code, out, err = self.run_cli(["frobnicate"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("usage:", err)


if __name__ == "__main__":
    unittest.main()
