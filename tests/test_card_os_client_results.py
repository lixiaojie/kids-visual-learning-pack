"""Result validation and upload tests for the thin Card OS client.

Covers ``results submit PACKET_ID --directory DIR`` against a loopback
fixture server: local result-directory closure (exactly-once declared
outputs, safe POSIX paths, no link following, media declarations, size and
digest rules, decoded/encoded budget), the credential scan over decoded
payloads, metadata strings and the final canonical body, the frozen
idempotency-key formula, the private ``cognitive-card-submit-attempt-v1``
journal (exact replay, tamper and ownership gates), ``complete`` before
submit, bounded same-key replay after a timeout, and acceptance-receipt
verification (opaque ``result_digest`` shape, per-artifact staged metadata
and content-addressed storage keys). Output never claims publication.

Fixture provenance (server app commit
c2a898cba5b8a8948c06688d8c2a387353d7cbbe, copied verbatim shapes into this
module so the suite never depends on the neighboring checkout):

- result request body: ``src/cognitive_card_server/http/schemas.py``
  (``GenerationResultRequest`` / ``ResultArtifactRequest``) and the
  realistic body in ``tests/test_http_subscriber.py`` (``_result_body``);
- acceptance receipt shape: ``http/serialization.py``
  (``serialize_result_receipt``);
- storage key shape ``sha256/<first-two>/<digest>``:
  ``subscriber/candidate_store.py`` (``_STORAGE_KEY``);
- artifact/path/media rules: ``subscriber/ingestion.py``
  (``verify_candidate_artifacts`` / ``_require_safe_artifact_path``) and
  ``subscriber/media.py`` (``ALLOWED_ARTIFACT_MEDIA_TYPES`` and the image
  signature checks);
- decoded/encoded budgets: ``http/config.py``
  (``DEFAULT_MAX_DECODED_PAYLOAD_BYTES = 20 MiB``) and ``http/schemas.py``
  (``MAX_ENCODED_PAYLOAD_CHARACTERS = 28 MiB``);
- replay semantics (201 then 200 with identical ``result_digest``):
  ``tests/test_http_subscriber.py``
  (``test_result_is_strict_idempotent_and_uses_authenticated_identity``);
- packet envelope / digest algorithm: as in the packets suite
  (``http/serialization.py`` ``serialize_packet``,
  ``subscriber/repository.py`` ``_canonical_json`` + ``_digest``).

All tokens and credential-shaped strings in this file are obvious fakes,
assembled at runtime where a complete credential shape is required.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import http.server
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
import time
import unicodedata
import unittest
import unittest.mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "skills" / "cognitive-card-os" / "scripts" / "card_os_client.py"
STORED_TOKEN = "dummy-stored-token-not-a-real-secret"
STORED_TOKEN_BYTES = STORED_TOKEN.encode("utf-8")
ENV_TOKEN = "dummy-env-token-not-a-real-secret"

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
CLIENT_SURFACE = "codex-cli"

CARD_PATH = "cards/cn-observation.json"
NOTE_PATH = "notes/reading-guide.md"
CARD_BYTES = b'{"proposition_ids":["rabbit.appearance.ears"]}\n'
NOTE_BYTES = "# 兔子观察\n\n耳朵长长的。\n".encode("utf-8")
FILES = {CARD_PATH: CARD_BYTES, NOTE_PATH: NOTE_BYTES}

# 1x1 PNG / minimal JPEG / minimal WebP RIFF headers for signature tests.
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89"
)
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 12
WEBP_BYTES = b"RIFF" + b"\x1a\x00\x00\x00" + b"WEBPVP8 " + b"\x00" * 10


def _credential_shape() -> str:
    """A complete (fake) credential shape, assembled at runtime so no
    assignment-shaped credential literal ever appears in this repository."""
    return "ccos_v1." + "ab" * 16 + "." + "Zz9_" * 6


def _packet_dict(required_outputs: object = None) -> dict[str, object]:
    """GenerationPacket.to_dict() shape from subscriber/model.py with
    required_outputs declarations as issued by the server tests."""
    if required_outputs is None:
        required_outputs = [
            {
                "relative_path": CARD_PATH,
                "media_type": "application/json",
                "max_bytes": 65536,
            },
            {
                "relative_path": NOTE_PATH,
                "media_type": "text/markdown",
                "max_bytes": 16384,
            },
        ]
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
        "required_outputs": required_outputs,
        "forbidden_changes": ["facts"],
        "issued_at": "2026-07-13T10:00:00.000000Z",
        "expires_at": "2099-07-13T11:00:00.000000Z",
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
    claimed_by: object = "client-macbook",
    lease_expires_at: object = "2099-07-13T10:15:00.000000Z",
    created_at: object = "2026-07-13T10:00:00.000000Z",
    expired_at: object = None,
) -> dict[str, object]:
    """serialize_packet shape from http/serialization.py."""
    packet = _packet_dict() if packet is None else packet
    return {
        "packet": packet,
        "packet_digest": _server_digest(packet),
        "claimed_by": claimed_by,
        "lease_expires_at": lease_expires_at,
        "created_at": created_at,
        "expired_at": expired_at,
    }


def _job_dict(state: str = "awaiting_upload") -> dict[str, object]:
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


def _error_envelope(code: str, request_id: str = "req-fixture-01") -> dict[str, object]:
    """error_response shape from http/serialization.py."""
    return {"error": {"code": code, "message": code, "request_id": request_id}}


def _staged_entry(relative_path: str, payload: bytes) -> dict[str, object]:
    """StagedCandidate entry shape from serialize_result_receipt."""
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "relative_path": relative_path,
        "storage_key": f"sha256/{digest[:2]}/{digest}",
        "sha256": digest,
        "size_bytes": len(payload),
    }


RECEIPT_DIGEST = "sha256:" + hashlib.sha256(b"fixture-receipt-digest").hexdigest()


def _receipt(
    *,
    files: dict[str, bytes] | None = None,
    replayed: bool = False,
    result_digest: str = RECEIPT_DIGEST,
) -> dict[str, object]:
    """serialize_result_receipt shape from http/serialization.py."""
    files = FILES if files is None else files
    return {
        "packet_id": PACKET_ID,
        "result_digest": result_digest,
        "staged_artifacts": [
            _staged_entry(path, files[path]) for path in sorted(files)
        ],
        "accepted_at": "2026-07-13T10:05:00.000000Z",
        "replayed": replayed,
    }


def _expected_body(generated_at: str, files: dict[str, bytes] | None = None) -> bytes:
    """Canonical GenerationResultRequest body, built independently of the
    client from the http/schemas.py fixture shape."""
    files = FILES if files is None else files
    artifacts = []
    for path in sorted(files):
        payload = files[path]
        media_type = (
            "application/json" if path.endswith(".json") else "text/markdown"
        )
        artifacts.append(
            {
                "relative_path": path,
                "media_type": media_type,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "payload_base64": base64.b64encode(payload).decode("ascii"),
            }
        )
    return _server_canonical(
        {
            "schema": "cognitive-card-generation-result-v1",
            "content_lock_digest": "sha256:" + "a" * 64,
            "skill_release": "0.1.1",
            "client_surface": CLIENT_SURFACE,
            "generated_at": generated_at,
            "artifacts": artifacts,
            "source_records": [],
            "operator_notes": "",
        }
    )


def _expected_key(packet_id: str, body: bytes) -> str:
    """Frozen idempotency formula from the plan, computed independently."""
    return "ccos-v1-" + hashlib.sha256(
        packet_id.encode("utf-8") + b"\n" + body
    ).hexdigest()


def _write_files(root: Path, files: dict[str, bytes] | None = None) -> None:
    for relative_path, payload in (FILES if files is None else files).items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


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

PACKET_PATH = f"/card-os/api/v1/packets/{PACKET_ID}"
COMPLETE_PATH = f"{PACKET_PATH}/complete"
RESULTS_PATH = f"{PACKET_PATH}/results"
JOB_PATH = f"/card-os/api/v1/jobs/{JOB_ID}"


# ---------------------------------------------------------------------------
# Loopback fixture server (same pattern as the packets suite).
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


def _stateful_route(responses: list[tuple[int, dict[str, object]]]):
    """Serve each queued (status, document) in order; repeat the last one."""
    calls: list[int] = []

    def route(handler: _FixtureHandler) -> None:
        index = min(len(calls), len(responses) - 1)
        calls.append(1)
        status, document = responses[index]
        handler._respond(status, json.dumps(document).encode("utf-8"))

    route.calls = calls
    return route


def _packet_visible_until_acceptance(handler: _FixtureHandler) -> None:
    """Mirror server 0.3.1 get_visible_packet: after a result POST the job
    leaves ACTIVE_CLIENT_PACKET_STATES, so the claimant's GET fails with
    PACKET_NOT_FOUND (service.py:199-228 + policy.py:11-13 at c2a898c)."""
    accepted = any(
        (record["method"], record["path"]) == ("POST", RESULTS_PATH)
        for record in handler.server.requests
    )
    if accepted:
        handler._respond(
            404, json.dumps(_error_envelope("PACKET_NOT_FOUND")).encode()
        )
    else:
        handler._respond(200, json.dumps(_envelope()).encode())


def _stall_then(document: dict[str, object], status: int = 201):
    """Stall the first request past the client timeout, then serve normally."""
    calls: list[int] = []

    def route(handler: _FixtureHandler) -> None:
        calls.append(1)
        if len(calls) == 1:
            time.sleep(5)
            return
        handler._respond(status, json.dumps(document).encode("utf-8"))

    route.calls = calls
    return route


def _stall_route(handler: _FixtureHandler) -> None:
    time.sleep(5)


class FakeStore:
    """In-memory CredentialStore double (same shape as the packets suite)."""

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


# ---------------------------------------------------------------------------
# validate_result_directory: local closure, no server involved.
# ---------------------------------------------------------------------------


class ValidateDirectoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _validate(self, packet: dict[str, object] | None = None):
        return client.validate_result_directory(
            _packet_dict() if packet is None else packet, self.root
        )

    def _assert_code(self, code: str, packet: dict[str, object] | None = None) -> str:
        with self.assertRaises(client.ClientError) as ctx:
            self._validate(packet)
        self.assertEqual(code, ctx.exception.code)
        return str(ctx.exception)

    def test_valid_directory_returns_sorted_artifacts_and_decoded_bytes(self) -> None:
        _write_files(self.root)
        descriptor, decoded = self._validate()
        self.assertEqual(["artifacts", "operator_notes", "source_records"], sorted(descriptor))
        self.assertEqual([], descriptor["source_records"])
        self.assertEqual("", descriptor["operator_notes"])
        artifacts = descriptor["artifacts"]
        self.assertEqual([CARD_PATH, NOTE_PATH], [a["relative_path"] for a in artifacts])
        for artifact in artifacts:
            payload = FILES[artifact["relative_path"]]
            self.assertEqual(hashlib.sha256(payload).hexdigest(), artifact["sha256"])
            self.assertEqual(len(payload), artifact["size_bytes"])
            self.assertEqual(
                base64.b64encode(payload).decode("ascii"), artifact["payload_base64"]
            )
        self.assertEqual(CARD_BYTES + NOTE_BYTES, decoded)

    def test_base64_payloads_never_contain_whitespace(self) -> None:
        _write_files(self.root)
        descriptor, _decoded = self._validate()
        for artifact in descriptor["artifacts"]:
            self.assertIsNotNone(
                re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", artifact["payload_base64"])
            )

    def test_missing_directory_is_rejected(self) -> None:
        self.root = self.root / "no-such-dir"
        self._assert_code("REQUEST_VALIDATION_FAILED")

    def test_plain_file_as_root_is_rejected(self) -> None:
        target = self.root / "file.json"
        target.write_bytes(b"{}")
        self.root = target
        self._assert_code("REQUEST_VALIDATION_FAILED")

    def test_symlink_root_is_rejected(self) -> None:
        real = self.root / "real"
        real.mkdir()
        _write_files(real)
        link = self.root / "link"
        os.symlink(real, link)
        self.root = link
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_missing_declared_output_is_rejected(self) -> None:
        (self.root / "cards").mkdir()
        (self.root / "cards" / "cn-observation.json").write_bytes(CARD_BYTES)
        message = self._assert_code("MISSING_ARTIFACT")
        self.assertNotIn(NOTE_PATH, message)  # never echo path material

    def test_undeclared_file_is_rejected(self) -> None:
        _write_files(self.root)
        (self.root / "extra.txt").write_bytes(b"surprise")
        self._assert_code("UNDECLARED_ARTIFACT")

    def test_undeclared_file_in_subdirectory_is_rejected(self) -> None:
        _write_files(self.root)
        (self.root / "cards" / "extra.json").write_bytes(b"{}")
        self._assert_code("UNDECLARED_ARTIFACT")

    def test_empty_directory_misses_every_declared_output(self) -> None:
        self._assert_code("MISSING_ARTIFACT")

    def test_unsafe_declared_paths_are_rejected(self) -> None:
        bad_paths = [
            "/etc/passwd",
            "../escape.json",
            "cards/../../../etc/passwd",
            "cards\\windows.json",
            "cards//double.json",
            "./dot.json",
            "cards/.",
            "cards/",
            "tab\tname.json",
            "nul\nname.json",
        ]
        for bad in bad_paths:
            with self.subTest(bad=bad):
                packet = _packet_dict(
                    [{"relative_path": bad, "media_type": "application/json", "max_bytes": 64}]
                )
                _write_files(self.root, {"ok.json": b"{}"})
                message = self._assert_code("UNSAFE_ARTIFACT_PATH", packet)
                self.assertNotIn(bad, message)

    def test_duplicate_declared_paths_are_rejected(self) -> None:
        declaration = {
            "relative_path": CARD_PATH,
            "media_type": "application/json",
            "max_bytes": 65536,
        }
        packet = _packet_dict([declaration, dict(declaration)])
        _write_files(self.root)
        self._assert_code("UNDECLARED_ARTIFACT", packet)

    def test_declared_max_bytes_above_server_schema_is_drift(self) -> None:
        packet = _packet_dict(
            [
                {
                    "relative_path": CARD_PATH,
                    "media_type": "application/json",
                    "max_bytes": 21 * 1024 * 1024,
                }
            ]
        )
        _write_files(self.root, {CARD_PATH: CARD_BYTES})
        self._assert_code("SERVER_CONTRACT_DRIFT", packet)

    def test_symlink_file_is_rejected(self) -> None:
        _write_files(self.root)
        note = self.root / NOTE_PATH
        note.unlink()
        os.symlink(self.root / CARD_PATH, note)
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_symlinked_subdirectory_is_rejected(self) -> None:
        real = self.root / "real-notes"
        real.mkdir()
        (real / "reading-guide.md").write_bytes(NOTE_BYTES)
        os.symlink(real, self.root / "notes")
        (self.root / "cards").mkdir()
        (self.root / "cards" / "cn-observation.json").write_bytes(CARD_BYTES)
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_fifo_is_rejected(self) -> None:
        _write_files(self.root)
        note = self.root / NOTE_PATH
        note.unlink()
        os.mkfifo(note)
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_control_character_filename_is_rejected(self) -> None:
        _write_files(self.root)
        (self.root / "bad\tname.txt").write_bytes(b"x")
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_backslash_filename_is_rejected(self) -> None:
        _write_files(self.root)
        (self.root / "bad\\name.txt").write_bytes(b"x")
        self._assert_code("UNSAFE_ARTIFACT_PATH")

    def test_normalization_collision_helper_rejects_nfc_nfd_pairs(self) -> None:
        nfc = "cards/caf\u00e9.json"
        nfd = unicodedata.normalize("NFD", nfc)
        with self.assertRaises(client.ClientError) as ctx:
            client._check_normalization_collisions([nfc, nfd])
        self.assertEqual("UNSAFE_ARTIFACT_PATH", ctx.exception.code)
        # Identical normalization is fine when the paths are identical.
        client._check_normalization_collisions([nfc, nfc])

    def test_normalized_but_not_identical_declared_path_is_missing(self) -> None:
        # The on-disk file uses the NFD form; the packet declares the NFC
        # form. Exact-match only: never silently accept a normalized alias.
        nfc = "cards/caf\u00e9.json"
        nfd = unicodedata.normalize("NFD", nfc)
        packet = _packet_dict(
            [{"relative_path": nfc, "media_type": "application/json", "max_bytes": 64}]
        )
        _write_files(self.root, {nfd: b"{}"})
        self._assert_code("MISSING_ARTIFACT", packet)

    def test_unsupported_declared_media_type_is_rejected(self) -> None:
        packet = _packet_dict(
            [
                {
                    "relative_path": CARD_PATH,
                    "media_type": "application/pdf",
                    "max_bytes": 65536,
                }
            ]
        )
        _write_files(self.root, {CARD_PATH: CARD_BYTES})
        self._assert_code("UNSUPPORTED_ARTIFACT_MEDIA_TYPE", packet)

    def test_image_signature_must_match_the_declared_media_type(self) -> None:
        packet = _packet_dict(
            [
                {
                    "relative_path": "images/card.png",
                    "media_type": "image/png",
                    "max_bytes": 65536,
                }
            ]
        )
        _write_files(self.root, {"images/card.png": b'{"not":"a png"}'})
        self._assert_code("INVALID_ARTIFACT_MEDIA", packet)

    def test_valid_image_signatures_pass(self) -> None:
        cases = [
            ("images/card.png", "image/png", PNG_BYTES),
            ("images/card.jpg", "image/jpeg", JPEG_BYTES),
            ("images/card.webp", "image/webp", WEBP_BYTES),
        ]
        for relative_path, media_type, payload in cases:
            with self.subTest(media_type=media_type):
                # Each case starts from an empty result directory.
                shutil.rmtree(self.root)
                self.root.mkdir()
                packet = _packet_dict(
                    [
                        {
                            "relative_path": relative_path,
                            "media_type": media_type,
                            "max_bytes": 65536,
                        }
                    ]
                )
                _write_files(self.root, {relative_path: payload})
                descriptor, decoded = self._validate(packet)
                self.assertEqual(payload, decoded)
                self.assertEqual(
                    media_type, descriptor["artifacts"][0]["media_type"]
                )

    def test_per_file_max_bytes_is_enforced(self) -> None:
        packet = _packet_dict(
            [
                {
                    "relative_path": CARD_PATH,
                    "media_type": "application/json",
                    "max_bytes": 8,
                }
            ]
        )
        _write_files(self.root, {CARD_PATH: CARD_BYTES})
        self._assert_code("ARTIFACT_TOO_LARGE", packet)

    def test_file_exactly_at_max_bytes_passes(self) -> None:
        payload = b"x" * 64
        packet = _packet_dict(
            [
                {
                    "relative_path": CARD_PATH,
                    "media_type": "application/json",
                    "max_bytes": 64,
                }
            ]
        )
        _write_files(self.root, {CARD_PATH: payload})
        descriptor, _decoded = self._validate(packet)
        self.assertEqual(64, descriptor["artifacts"][0]["size_bytes"])

    def test_empty_file_is_allowed(self) -> None:
        packet = _packet_dict(
            [
                {
                    "relative_path": CARD_PATH,
                    "media_type": "application/json",
                    "max_bytes": 64,
                }
            ]
        )
        _write_files(self.root, {CARD_PATH: b""})
        descriptor, decoded = self._validate(packet)
        self.assertEqual(b"", decoded)
        self.assertEqual(0, descriptor["artifacts"][0]["size_bytes"])

    def test_decoded_total_budget_is_enforced(self) -> None:
        _write_files(self.root)
        with unittest.mock.patch.object(client, "MAX_DECODED_ARTIFACT_BYTES", 16):
            self._assert_code("PAYLOAD_TOO_LARGE")

    def test_media_type_comes_only_from_the_packet_declaration(self) -> None:
        # A .md file declared as text/plain keeps the declared type.
        packet = _packet_dict(
            [
                {
                    "relative_path": NOTE_PATH,
                    "media_type": "text/plain",
                    "max_bytes": 16384,
                }
            ]
        )
        _write_files(self.root, {NOTE_PATH: NOTE_BYTES})
        descriptor, _decoded = self._validate(packet)
        self.assertEqual("text/plain", descriptor["artifacts"][0]["media_type"])


class IdempotencyKeyTests(unittest.TestCase):
    def test_exact_frozen_formula(self) -> None:
        body = _expected_body("2026-07-13T10:04:00.000000Z")
        self.assertEqual(
            _expected_key(PACKET_ID, body),
            client.result_idempotency_key(PACKET_ID, body),
        )

    def test_key_is_bound_to_the_packet_id(self) -> None:
        body = _expected_body("2026-07-13T10:04:00.000000Z")
        self.assertNotEqual(
            client.result_idempotency_key(PACKET_ID, body),
            client.result_idempotency_key("gp_ffffffffffffffffffffffffffffffff", body),
        )

    def test_key_is_bound_to_the_exact_body_bytes(self) -> None:
        first = _expected_body("2026-07-13T10:04:00.000000Z")
        second = _expected_body("2026-07-13T10:04:01.000000Z")
        self.assertNotEqual(
            client.result_idempotency_key(PACKET_ID, first),
            client.result_idempotency_key(PACKET_ID, second),
        )


class CredentialScanUnitTests(unittest.TestCase):
    """The scan helpers reject raw tokens and complete credential shapes."""

    def test_raw_token_bytes_are_detected(self) -> None:
        with self.assertRaises(client.ClientError) as ctx:
            client._scan_for_credentials(
                b"prefix " + STORED_TOKEN_BYTES + b" suffix",
                STORED_TOKEN_BYTES,
                "artifact payload",
            )
        self.assertEqual("CREDENTIAL_IN_RESULT", ctx.exception.code)
        self.assertNotIn(STORED_TOKEN, str(ctx.exception))

    def test_complete_credential_shape_is_detected(self) -> None:
        shape = _credential_shape()
        with self.assertRaises(client.ClientError) as ctx:
            client._scan_for_credentials(
                b"notes: " + shape.encode("utf-8"), b"dummy-other", "request body"
            )
        self.assertEqual("CREDENTIAL_IN_RESULT", ctx.exception.code)
        self.assertNotIn(shape, str(ctx.exception))

    def test_partial_credential_prefix_is_allowed(self) -> None:
        # Only a COMPLETE credential shape matches; the bare prefix is safe.
        client._scan_for_credentials(
            b"ccos_v1.short", b"dummy-other", "artifact payload"
        )

    def test_recursive_value_scan_covers_nested_strings(self) -> None:
        shape = _credential_shape()
        descriptor = {
            "artifacts": [],
            "source_records": [{"source": "https://example.invalid/a", "note": shape}],
            "operator_notes": "",
        }
        with self.assertRaises(client.ClientError) as ctx:
            client._scan_value_for_credentials(
                descriptor, STORED_TOKEN_BYTES, "result metadata"
            )
        self.assertEqual("CREDENTIAL_IN_RESULT", ctx.exception.code)
        self.assertNotIn(shape, str(ctx.exception))

    def test_clean_values_pass_the_scan(self) -> None:
        descriptor = {
            "artifacts": [{"relative_path": CARD_PATH, "media_type": "application/json"}],
            "source_records": [{"source": "https://example.invalid/a"}],
            "operator_notes": "generated with a logged-in chat surface",
        }
        client._scan_value_for_credentials(descriptor, STORED_TOKEN_BYTES, "result metadata")


# ---------------------------------------------------------------------------
# results submit against the loopback fixture server.
# ---------------------------------------------------------------------------


class SubmitTestCase(unittest.TestCase):
    """Base class: fixture server, config/credential seams, isolated XDG state."""

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
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.result_dir = Path(self._tmp.name) / "result"
        self.result_dir.mkdir()
        self.state_home = Path(self._tmp.name) / "state"
        # Neutralize any real CARD_OS_TOKEN and isolate the attempt journal.
        self._env_patcher = unittest.mock.patch.dict(
            os.environ,
            {"CARD_OS_TOKEN": "", "XDG_STATE_HOME": str(self.state_home)},
            clear=False,
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

    def _serve_doctor(self) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(HEALTH_OK),
                ("GET", "/card-os/api/v1/capabilities"): _json_route(CAPABILITIES_OK),
            }
        )

    def _serve_submit(
        self,
        *,
        envelope: dict[str, object] | None = None,
        receipt: dict[str, object] | None = None,
        receipt_status: int = 201,
    ) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(
                    _envelope() if envelope is None else envelope
                ),
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _json_route(
                    _receipt() if receipt is None else receipt, status=receipt_status
                ),
            }
        )

    def _attempt_path(self, packet_id: str = PACKET_ID) -> Path:
        return (
            self.state_home
            / "cognitive-card-os"
            / "attempts"
            / f"{packet_id}.json"
        )

    def _submit(self, args: list[str] | None = None):
        if args is None:
            args = ["results", "submit", PACKET_ID, "--directory", str(self.result_dir)]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = client.main(args)
        return code, out.getvalue(), err.getvalue()

    def _use_short_timeout(self) -> None:
        client._config = client.TransportConfig(
            base_url=f"http://127.0.0.1:{self.server.port}/card-os/",
            timeout_seconds=0.3,
            allow_plain_http_loopback=True,
        )

    def run_cli(self, args: list[str]):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = client.main(args)
        return code, out.getvalue(), err.getvalue()

    def assert_no_token(self, *chunks: str) -> None:
        for chunk in chunks:
            self.assertNotIn(STORED_TOKEN, chunk)
            self.assertNotIn(ENV_TOKEN, chunk)

    def methods_paths(self) -> list[tuple[str, str]]:
        return [(r["method"], r["path"]) for r in self.server.requests]

    def _results_posts(self) -> list[dict[str, object]]:
        return [
            r
            for r in self.server.requests
            if (r["method"], r["path"]) == ("POST", RESULTS_PATH)
        ]

    def _assert_result_request(
        self, record: dict[str, object], *, generated_at: str
    ) -> bytes:
        headers = {k.lower(): v for k, v in record["headers"].items()}
        self.assertEqual(f"Bearer {STORED_TOKEN}", headers["authorization"])
        self.assertEqual("1", headers["x-card-os-protocol"])
        self.assertEqual("0.1.1", headers["x-card-os-skill-release"])
        body = record["body"]
        self.assertEqual(_expected_body(generated_at), body)
        self.assertEqual(_expected_key(PACKET_ID, body), headers["idempotency-key"])
        return body


class HappyPathTests(SubmitTestCase):
    def test_submit_order_headers_body_and_output(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("GET", PACKET_PATH),
                ("POST", COMPLETE_PATH),
                ("POST", RESULTS_PATH),
            ],
            self.methods_paths(),
        )
        # Doctor reads are unauthenticated.
        for record in self.server.requests[:2]:
            self.assertNotIn("authorization", {k.lower() for k in record["headers"]})
        # Complete carries the frozen empty JSON body.
        complete = [
            r for r in self.server.requests if r["path"] == COMPLETE_PATH
        ][0]
        self.assertEqual(b"{}", complete["body"])
        journal = json.loads(self._attempt_path().read_text(encoding="utf-8"))
        self._assert_result_request(
            self._results_posts()[0], generated_at=journal["generated_at"]
        )
        payload = json.loads(out)
        self.assertEqual(client.canonical_json(payload).decode("utf-8") + "\n", out)
        self.assertEqual("candidate_staged", payload["status"])
        self.assertEqual(PACKET_ID, payload["packet_id"])
        self.assertIsNotNone(
            re.fullmatch(r"sha256:[0-9a-f]{64}", payload["result_digest"])
        )
        self.assertEqual(RECEIPT_DIGEST, payload["result_digest"])
        self.assertFalse(payload["replayed"])
        self.assertNotIn("published", out)
        self.assert_no_token(out, err)

    def test_result_body_has_the_frozen_schema_and_release(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        body = json.loads(self._results_posts()[0]["body"].decode("utf-8"))
        self.assertEqual("cognitive-card-generation-result-v1", body["schema"])
        self.assertEqual("0.1.1", body["skill_release"])
        self.assertEqual(CLIENT_SURFACE, body["client_surface"])
        self.assertEqual("sha256:" + "a" * 64, body["content_lock_digest"])
        self.assertEqual([], body["source_records"])
        self.assertEqual("", body["operator_notes"])
        self.assertIsNotNone(
            re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                r"(\.[0-9]{1,6})?Z",
                body["generated_at"],
            )
        )
        self.assertEqual(
            [CARD_PATH, NOTE_PATH], [a["relative_path"] for a in body["artifacts"]]
        )

    def test_result_digest_is_opaque_and_not_the_body_sha(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        body = self._results_posts()[0]["body"]
        body_sha = "sha256:" + hashlib.sha256(body).hexdigest()
        payload = json.loads(out)
        self.assertNotEqual(body_sha, payload["result_digest"])


class AttemptJournalTests(SubmitTestCase):
    def test_journal_is_private_and_contains_only_frozen_fields(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        attempt = self._attempt_path()
        info = os.lstat(attempt)
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertEqual(0o600, stat.S_IMODE(info.st_mode))
        self.assertEqual(os.getuid(), info.st_uid)
        raw = attempt.read_text(encoding="utf-8")
        journal = json.loads(raw)
        self.assertEqual(
            {
                "schema",
                "packet_id",
                "generated_at",
                "body_sha256",
                "idempotency_key",
                # Recorded so a cross-invocation replay can rebuild the body
                # after the accepted packet becomes invisible (gate I-1).
                "content_lock_digest",
                "artifacts",
            },
            set(journal),
        )
        self.assertEqual("cognitive-card-submit-attempt-v1", journal["schema"])
        self.assertEqual(PACKET_ID, journal["packet_id"])
        self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{64}", journal["body_sha256"]))
        self.assertIsNotNone(
            re.fullmatch(r"ccos-v1-[0-9a-f]{64}", journal["idempotency_key"])
        )
        self.assertIsNotNone(
            re.fullmatch(r"sha256:[0-9a-f]{64}", journal["content_lock_digest"])
        )
        media_types = {
            CARD_PATH: "application/json",
            NOTE_PATH: "text/markdown",
        }
        self.assertEqual(
            [
                {
                    "relative_path": path,
                    "media_type": media_types[path],
                    "sha256": hashlib.sha256(FILES[path]).hexdigest(),
                    "size_bytes": len(FILES[path]),
                }
                for path in sorted(FILES)
            ],
            journal["artifacts"],
        )
        # No payload bytes, no token, no absolute working directory.
        self.assertNotIn("payload_base64", raw)
        self.assertNotIn(str(self.result_dir), raw)
        self.assertNotIn(CARD_BYTES.decode("utf-8").strip(), raw)
        self.assert_no_token(raw, err)

    def test_journal_is_written_before_complete_and_upload(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _json_route(
                    _error_envelope("INTERNAL_ERROR"), status=500
                ),
            }
        )
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("INTERNAL_ERROR", json.loads(out)["error"]["code"])
        self.assertTrue(self._attempt_path().exists())
        self.assertEqual([], self._results_posts())

    def test_local_validation_failure_writes_no_journal(self) -> None:
        # Missing NOTE_PATH: the local gate fails before any state is kept.
        (self.result_dir / "cards").mkdir()
        (self.result_dir / "cards" / "cn-observation.json").write_bytes(CARD_BYTES)
        self._serve_submit()
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("MISSING_ARTIFACT", json.loads(out)["error"]["code"])
        self.assertFalse(self._attempt_path().exists())
        self.assertEqual([], self._results_posts())

    def test_exact_replay_reuses_generated_at_key_and_body(self) -> None:
        # The fixture mirrors the real server: once the first result POST is
        # accepted the claimant's packet GET fails with PACKET_NOT_FOUND, so
        # the cross-invocation re-run must replay through the attempt journal.
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _packet_visible_until_acceptance,
                ("POST", COMPLETE_PATH): _stateful_route(
                    [
                        (200, _envelope()),
                        (409, _error_envelope("INVALID_STATE_TRANSITION")),
                    ]
                ),
                ("POST", RESULTS_PATH): _stateful_route(
                    [(201, _receipt(replayed=False)), (200, _receipt(replayed=True))]
                ),
            }
        )
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        first_receipt = json.loads(out)
        requests_before = len(self.server.requests)
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        second_receipt = json.loads(out)
        # The replay issues no new complete and no status read: exactly one
        # packet GET (now 404) and exactly one new POST with the same bytes.
        self.assertEqual(
            [("GET", PACKET_PATH), ("POST", RESULTS_PATH)],
            self.methods_paths()[requests_before:],
        )
        posts = self._results_posts()
        self.assertEqual(2, len(posts))
        first_headers = {k.lower(): v for k, v in posts[0]["headers"].items()}
        second_headers = {k.lower(): v for k, v in posts[1]["headers"].items()}
        # Identical immutable bytes replayed with the same key.
        self.assertEqual(posts[0]["body"], posts[1]["body"])
        self.assertEqual(
            first_headers["idempotency-key"], second_headers["idempotency-key"]
        )
        # The acceptance receipt is stable across the exact replay.
        self.assertEqual(first_receipt["result_digest"], second_receipt["result_digest"])
        self.assertFalse(first_receipt["replayed"])
        self.assertTrue(second_receipt["replayed"])
        self.assertEqual("candidate_staged", second_receipt["status"])

    def test_visible_packet_resubmit_reuses_journal_after_failed_upload(self) -> None:
        # The first attempt wrote the journal and completed the packet, but
        # the results POST failed server-side. The packet is still visible,
        # so the re-run must reuse the recorded journal (successful rebuild
        # branch of load_or_create_attempt), confirm the already-completed
        # state via a job status read, and replay the identical bytes/key.
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _stateful_route(
                    [
                        (200, _envelope()),
                        (409, _error_envelope("INVALID_STATE_TRANSITION")),
                    ]
                ),
                ("GET", JOB_PATH): _json_route(_job_dict(state="awaiting_upload")),
                ("POST", RESULTS_PATH): _stateful_route(
                    [
                        (500, _error_envelope("INTERNAL_ERROR")),
                        (201, _receipt(replayed=False)),
                    ]
                ),
            }
        )
        code, _out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertTrue(self._attempt_path().exists())
        requests_before = len(self.server.requests)
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        self.assertEqual(
            [
                ("GET", PACKET_PATH),
                ("POST", COMPLETE_PATH),
                ("GET", JOB_PATH),
                ("POST", RESULTS_PATH),
            ],
            self.methods_paths()[requests_before:],
        )
        posts = self._results_posts()
        self.assertEqual(2, len(posts))
        # Identical immutable bytes with the same key across both attempts.
        self.assertEqual(posts[0]["body"], posts[1]["body"])
        first_headers = {k.lower(): v for k, v in posts[0]["headers"].items()}
        second_headers = {k.lower(): v for k, v in posts[1]["headers"].items()}
        self.assertEqual(
            first_headers["idempotency-key"], second_headers["idempotency-key"]
        )
        self.assertEqual("candidate_staged", json.loads(out)["status"])

    def test_changed_artifacts_stop_with_attempt_body_changed(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        note = self.result_dir / NOTE_PATH
        note.write_bytes(NOTE_BYTES + b"changed\n")
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        # No new logical submit: still exactly one upload with the first key.
        self.assertEqual(1, len(self._results_posts()))
        self.assert_no_token(out, err)

    def test_tampered_journal_is_rejected_without_echoing_content(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        attempt = self._attempt_path()
        journal = json.loads(attempt.read_text(encoding="utf-8"))
        tampered_variants = [
            {**journal, "body_sha256": "0" * 64},
            {**journal, "idempotency_key": "ccos-v1-" + "0" * 64},
            {**journal, "generated_at": "2026-07-13T10:04:00.000000Z"},
            {**journal, "schema": "cognitive-card-submit-attempt-v2"},
            {**journal, "packet_id": "gp_ffffffffffffffffffffffffffffffff"},
            {**journal, "surprise": True},
            {**journal, "artifacts": list(reversed(journal["artifacts"]))},
        ]
        for variant in tampered_variants:
            with self.subTest(variant=str(sorted(variant))):
                attempt.write_text(json.dumps(variant), encoding="utf-8")
                os.chmod(attempt, 0o600)
                code, out, err = self._submit()
                self.assertEqual(1, code)
                self.assertEqual(
                    "ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"]
                )
                self.assertNotIn(json.dumps(variant), out)
        self.assertEqual(1, len(self._results_posts()))

    def test_wrong_mode_owner_or_link_journal_is_rejected(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        attempt = self._attempt_path()
        raw = attempt.read_bytes()

        os.chmod(attempt, 0o644)
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])

        os.chmod(attempt, 0o600)
        attempt.unlink()
        real = attempt.parent / "real.json"
        real.write_bytes(raw)
        os.chmod(real, 0o600)
        os.symlink(real, attempt)
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        self.assertEqual(1, len(self._results_posts()))

    def test_packet_id_cannot_escape_the_attempts_directory(self) -> None:
        # ".." passes the single-segment route rule, so the attempt-state
        # layer must reject it on its own before touching the filesystem.
        with self.assertRaises(client.ClientError) as ctx:
            client.load_or_create_attempt("..", tuple(), lambda generated_at: b"{}")
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)
        with self.assertRaises(client.ClientError) as ctx:
            client.load_or_create_attempt(".", tuple(), lambda generated_at: b"{}")
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)
        self.assertFalse(
            (self.state_home / "cognitive-card-os" / "attempts").exists()
        )

    def test_dotdot_packet_id_fails_closed_over_the_cli(self) -> None:
        code, out, _err = self.run_cli(
            ["results", "submit", "../escape", "--directory", str(self.result_dir)]
        )
        self.assertEqual(1, code)
        self.assertEqual(
            "REQUEST_VALIDATION_FAILED", json.loads(out)["error"]["code"]
        )
        self.assertEqual([], self.server.requests)

    def test_journal_defaults_to_home_local_state(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        home = Path(self._tmp.name) / "home"
        home.mkdir()
        with unittest.mock.patch.dict(os.environ, {"HOME": str(home)}, clear=False):
            os.environ.pop("XDG_STATE_HOME", None)
            code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        self.assertTrue(
            (
                home
                / ".local"
                / "state"
                / "cognitive-card-os"
                / "attempts"
                / f"{PACKET_ID}.json"
            ).exists()
        )


class CrossInvocationReplayTests(SubmitTestCase):
    """After acceptance the packet is invisible; the attempt journal drives
    the cross-invocation replay, and every local mismatch fails closed."""

    def _serve_accepted_packet(self) -> None:
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _packet_visible_until_acceptance,
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _stateful_route(
                    [(201, _receipt(replayed=False)), (200, _receipt(replayed=True))]
                ),
            }
        )

    def _accepted_submit(self) -> int:
        _write_files(self.result_dir)
        self._serve_accepted_packet()
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        return len(self.server.requests)

    def test_changed_copy_after_acceptance_stops_before_any_post(self) -> None:
        requests_before = self._accepted_submit()
        note = self.result_dir / NOTE_PATH
        note.write_bytes(NOTE_BYTES + b"changed\n")
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        # Only the doomed pre-flight packet GET happened; no new POST.
        self.assertEqual(
            [("GET", PACKET_PATH)], self.methods_paths()[requests_before:]
        )
        self.assertEqual(1, len(self._results_posts()))
        self.assert_no_token(out, err)

    def test_extra_file_after_acceptance_stops_before_any_post(self) -> None:
        requests_before = self._accepted_submit()
        (self.result_dir / "extra.txt").write_bytes(b"surprise")
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        self.assertEqual(
            [("GET", PACKET_PATH)], self.methods_paths()[requests_before:]
        )
        self.assertEqual(1, len(self._results_posts()))
        self.assert_no_token(out, err)

    def test_missing_file_after_acceptance_stops_before_any_post(self) -> None:
        requests_before = self._accepted_submit()
        (self.result_dir / NOTE_PATH).unlink()
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        self.assertEqual(
            [("GET", PACKET_PATH)], self.methods_paths()[requests_before:]
        )
        self.assertEqual(1, len(self._results_posts()))
        self.assert_no_token(out, err)

    def test_tampered_journal_after_acceptance_fails_closed_without_echo(self) -> None:
        requests_before = self._accepted_submit()
        attempt = self._attempt_path()
        journal = json.loads(attempt.read_text(encoding="utf-8"))
        tampered = {**journal, "body_sha256": "0" * 64}
        attempt.write_text(json.dumps(tampered), encoding="utf-8")
        os.chmod(attempt, 0o600)
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("ATTEMPT_BODY_CHANGED", json.loads(out)["error"]["code"])
        self.assertNotIn(json.dumps(tampered), out)
        self.assertEqual(
            [("GET", PACKET_PATH)], self.methods_paths()[requests_before:]
        )
        self.assertEqual(1, len(self._results_posts()))
        self.assert_no_token(out, err)

    def test_missing_journal_keeps_packet_not_found(self) -> None:
        # No attempt was ever recorded: the invisible packet still fails
        # closed with PACKET_NOT_FOUND and nothing is uploaded.
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(
                    _error_envelope("PACKET_NOT_FOUND"), status=404
                )
            }
        )
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("PACKET_NOT_FOUND", json.loads(out)["error"]["code"])
        self.assertEqual([], self._results_posts())
        self.assertFalse(self._attempt_path().exists())
        self.assert_no_token(out, err)

    def test_replayed_receipt_must_carry_the_replayed_flag(self) -> None:
        # A server that answers a journaled replay with replayed=false is
        # contract drift: the same key can never be accepted as a new result.
        requests_before = self._accepted_submit()
        self._routes(
            {
                ("POST", RESULTS_PATH): _json_route(
                    _receipt(replayed=False), status=201
                )
            }
        )
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual(
            "SERVER_CONTRACT_DRIFT", json.loads(out)["error"]["code"]
        )
        self.assertEqual(
            [("GET", PACKET_PATH), ("POST", RESULTS_PATH)],
            self.methods_paths()[requests_before:],
        )
        self.assert_no_token(out, err)


class CredentialInResultTests(SubmitTestCase):
    def test_raw_token_in_payload_is_rejected_before_encoding_upload(self) -> None:
        poisoned = {
            CARD_PATH: CARD_BYTES,
            NOTE_PATH: NOTE_BYTES + STORED_TOKEN_BYTES + b"\n",
        }
        _write_files(self.result_dir, poisoned)
        self._serve_submit()
        code, out, err = self._submit()
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("CREDENTIAL_IN_RESULT", payload["error"]["code"])
        self.assertEqual([], self._results_posts())
        self.assertFalse(self._attempt_path().exists())
        self.assert_no_token(out, err)

    def test_complete_credential_shape_in_payload_is_rejected(self) -> None:
        shape = _credential_shape()
        poisoned = {
            CARD_PATH: CARD_BYTES,
            NOTE_PATH: NOTE_BYTES + shape.encode("utf-8") + b"\n",
        }
        _write_files(self.result_dir, poisoned)
        self._serve_submit()
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("CREDENTIAL_IN_RESULT", json.loads(out)["error"]["code"])
        self.assertNotIn(shape, out)
        self.assertNotIn(shape, err)
        self.assertEqual([], self._results_posts())

    def test_credential_shaped_declared_path_is_rejected_without_echo(self) -> None:
        shape = _credential_shape()
        leaked_path = f"cards/{shape}.json"
        packet = _packet_dict(
            [
                {
                    "relative_path": leaked_path,
                    "media_type": "application/json",
                    "max_bytes": 65536,
                }
            ]
        )
        _write_files(self.result_dir, {leaked_path: CARD_BYTES})
        self._serve_submit(envelope=_envelope(packet))
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("CREDENTIAL_IN_RESULT", json.loads(out)["error"]["code"])
        # Only the code/path category is reported, never the matched text.
        self.assertNotIn(shape, out)
        self.assertNotIn(shape, err)
        self.assertEqual([], self._results_posts())

    def test_env_token_in_payload_is_also_detected(self) -> None:
        poisoned = {
            CARD_PATH: CARD_BYTES + ENV_TOKEN.encode("utf-8"),
            NOTE_PATH: NOTE_BYTES,
        }
        _write_files(self.result_dir, poisoned)
        self._serve_submit()
        with unittest.mock.patch.dict(
            os.environ, {"CARD_OS_TOKEN": ENV_TOKEN}, clear=False
        ):
            code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("CREDENTIAL_IN_RESULT", json.loads(out)["error"]["code"])
        self.assert_no_token(out, err)


class RecheckTests(SubmitTestCase):
    """Claimant/lease/expiry/content-lock recheck before any mutation."""

    def _assert_fails_before_mutations(
        self, envelope: dict[str, object], code: str
    ) -> None:
        _write_files(self.result_dir)
        self._serve_submit(envelope=envelope)
        result_code, out, _err = self._submit()
        self.assertEqual(1, result_code)
        self.assertEqual(code, json.loads(out)["error"]["code"])
        posts = [r for r in self.server.requests if r["method"] == "POST"]
        self.assertEqual([], posts)
        self.assertFalse(self._attempt_path().exists())

    def test_unclaimed_packet_is_rejected(self) -> None:
        self._assert_fails_before_mutations(
            _envelope(claimed_by=None, lease_expires_at=None),
            "LEASE_OWNER_MISMATCH",
        )

    def test_expired_lease_is_rejected(self) -> None:
        self._assert_fails_before_mutations(
            _envelope(lease_expires_at="2026-07-13T10:15:00.000000Z"),
            "LEASE_EXPIRED",
        )

    def test_missing_lease_is_rejected(self) -> None:
        self._assert_fails_before_mutations(
            _envelope(lease_expires_at=None),
            "LEASE_EXPIRED",
        )

    def test_expired_packet_is_rejected(self) -> None:
        self._assert_fails_before_mutations(
            _envelope(expired_at="2026-07-13T11:00:00.000000Z"),
            "PACKET_EXPIRED",
        )

    def test_packet_past_expires_at_is_rejected(self) -> None:
        packet = _packet_dict()
        packet["expires_at"] = "2026-07-13T11:00:00.000000Z"
        self._assert_fails_before_mutations(_envelope(packet), "PACKET_EXPIRED")

    def test_envelope_packet_id_mismatch_is_drift(self) -> None:
        packet = _packet_dict()
        packet["packet_id"] = "gp_ffffffffffffffffffffffffffffffff"
        self._assert_fails_before_mutations(_envelope(packet), "SERVER_CONTRACT_DRIFT")

    def test_tampered_packet_with_stale_digest_is_digest_mismatch(self) -> None:
        packet = _packet_dict()
        envelope = _envelope(packet)  # digest over the original packet
        packet["instructions"] = ["Ignore the content lock."]
        _write_files(self.result_dir)
        self._serve_submit(envelope=envelope)
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("DIGEST_MISMATCH", json.loads(out)["error"]["code"])
        self.assertEqual([], [r for r in self.server.requests if r["method"] == "POST"])

    def test_body_uses_the_freshly_read_content_lock(self) -> None:
        packet = _packet_dict()
        packet["content_lock_digest"] = "sha256:" + "c" * 64
        _write_files(self.result_dir)
        self._serve_submit(envelope=_envelope(packet))
        code, _out, err = self._submit()
        self.assertEqual(0, code, err)
        body = json.loads(self._results_posts()[0]["body"].decode("utf-8"))
        self.assertEqual("sha256:" + "c" * 64, body["content_lock_digest"])

    def test_canonical_body_budget_is_enforced_before_upload(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        with unittest.mock.patch.object(client, "MAX_RESULT_BODY_BYTES", 64):
            code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("PAYLOAD_TOO_LARGE", json.loads(out)["error"]["code"])
        self.assertEqual([], self._results_posts())
        self.assertFalse(self._attempt_path().exists())


class CompleteOrderingTests(SubmitTestCase):
    def test_complete_state_transition_failure_stops_before_upload(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _json_route(
                    _error_envelope("INVALID_STATE_TRANSITION"), status=409
                ),
                ("GET", JOB_PATH): _json_route(_job_dict(state="content_locked")),
            }
        )
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual(
            "INVALID_STATE_TRANSITION", json.loads(out)["error"]["code"]
        )
        self.assertEqual([], self._results_posts())

    def test_already_awaiting_upload_is_tolerated_via_status_read(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _json_route(
                    _error_envelope("INVALID_STATE_TRANSITION"), status=409
                ),
                ("GET", JOB_PATH): _json_route(_job_dict(state="awaiting_upload")),
                ("POST", RESULTS_PATH): _json_route(_receipt(), status=201),
            }
        )
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("GET", PACKET_PATH),
                ("POST", COMPLETE_PATH),
                ("GET", JOB_PATH),
                ("POST", RESULTS_PATH),
            ],
            self.methods_paths(),
        )

    def test_complete_timeout_reads_state_and_never_reposts_complete(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("POST", COMPLETE_PATH): _stall_route,
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("GET", JOB_PATH): _json_route(_job_dict(state="awaiting_upload")),
            }
        )
        self._use_short_timeout()
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("HTTP_ERROR", json.loads(out)["error"]["code"])
        completes = [
            r for r in self.server.requests if r["path"] == COMPLETE_PATH
        ]
        self.assertEqual(1, len(completes))
        self.assertEqual([], self._results_posts())


class ResultUploadRetryTests(SubmitTestCase):
    """A timed-out upload retries once: same bytes, same key, after a read."""

    def test_timeout_triggers_status_read_and_single_same_key_replay(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _stall_then(_receipt(), status=201),
            }
        )
        self._use_short_timeout()
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        posts = self._results_posts()
        self.assertEqual(2, len(posts))
        self.assertEqual(posts[0]["body"], posts[1]["body"])
        first_headers = {k.lower(): v for k, v in posts[0]["headers"].items()}
        second_headers = {k.lower(): v for k, v in posts[1]["headers"].items()}
        self.assertEqual(
            first_headers["idempotency-key"], second_headers["idempotency-key"]
        )
        self.assertEqual(
            [
                ("GET", "/card-os/api/v1/health"),
                ("GET", "/card-os/api/v1/capabilities"),
                ("GET", PACKET_PATH),
                ("POST", COMPLETE_PATH),
                ("POST", RESULTS_PATH),
                ("GET", PACKET_PATH),
                ("POST", RESULTS_PATH),
            ],
            self.methods_paths(),
        )
        self.assert_no_token(out, err)

    def test_double_timeout_stops_after_one_replay(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _json_route(_envelope()),
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _stall_route,
            }
        )
        self._use_short_timeout()
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("HTTP_ERROR", json.loads(out)["error"]["code"])
        self.assertEqual(2, len(self._results_posts()))

    def test_failed_status_read_prevents_any_replay(self) -> None:
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _stateful_route(
                    [
                        (200, _envelope()),
                        (500, _error_envelope("INTERNAL_ERROR")),
                    ]
                ),
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _stall_route,
            }
        )
        self._use_short_timeout()
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("HTTP_ERROR", json.loads(out)["error"]["code"])
        self.assertEqual(1, len(self._results_posts()))

    def test_packet_not_found_on_status_read_still_replays_identical_bytes(self) -> None:
        # After a real acceptance the packet is no longer visible to the
        # claimant; replaying the exact same bytes with the same key is the
        # explicitly allowed bounded retry and returns the stored receipt.
        _write_files(self.result_dir)
        self._serve_doctor()
        self._routes(
            {
                ("GET", PACKET_PATH): _stateful_route(
                    [
                        (200, _envelope()),
                        (404, _error_envelope("PACKET_NOT_FOUND")),
                    ]
                ),
                ("POST", COMPLETE_PATH): _json_route(_envelope()),
                ("POST", RESULTS_PATH): _stall_then(_receipt(replayed=True), status=200),
            }
        )
        self._use_short_timeout()
        code, out, err = self._submit()
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertTrue(payload["replayed"])
        self.assertEqual(2, len(self._results_posts()))


class ServerErrorPassthroughTests(SubmitTestCase):
    """Frozen 0.3.1 result-side codes pass through verbatim."""

    def test_result_error_codes_pass_through(self) -> None:
        cases = [
            ("IDEMPOTENCY_CONFLICT", 409),
            ("SKILL_RELEASE_MISMATCH", 400),
            ("CONTENT_LOCK_MISMATCH", 409),
            ("ARTIFACT_DIGEST_MISMATCH", 409),
            ("ARTIFACT_SIZE_MISMATCH", 409),
            ("ARTIFACT_MEDIA_TYPE_MISMATCH", 409),
            ("MISSING_ARTIFACT", 400),
            ("UNDECLARED_ARTIFACT", 400),
            ("UNSAFE_ARTIFACT_PATH", 400),
            ("INVALID_BASE64", 400),
            ("PAYLOAD_TOO_LARGE", 413),
            ("INVALID_IDEMPOTENCY_KEY", 400),
            ("RESULT_CLIENT_MISMATCH", 403),
            ("PACKET_PROFILE_MISMATCH", 409),
            ("STAGED_METADATA_MISMATCH", 409),
        ]
        for code, status in cases:
            with self.subTest(code=code):
                del self.server.requests[:]
                self.state_home.mkdir(parents=True, exist_ok=True)
                # Each case starts from a clean attempt journal.
                attempt = self._attempt_path()
                if attempt.exists():
                    attempt.unlink()
                self._serve_submit()
                self._routes(
                    {
                        ("POST", RESULTS_PATH): _json_route(
                            _error_envelope(code), status=status
                        )
                    }
                )
                _write_files(self.result_dir)
                out_code, out, err = self._submit()
                self.assertEqual(1, out_code)
                payload = json.loads(out)
                self.assertEqual(code, payload["error"]["code"])
                self.assertEqual("req-fixture-01", payload["error"]["request_id"])
                self.assert_no_token(out, err)


class ReceiptValidationTests(SubmitTestCase):
    """The acceptance receipt is re-verified against the local bytes."""

    def _submit_with_receipt(self, receipt: dict[str, object], status: int = 200):
        _write_files(self.result_dir)
        self._serve_submit(receipt=receipt, receipt_status=status)
        return self._submit()

    def _assert_rejected_receipt(self, receipt: dict[str, object], code: str) -> None:
        out_code, out, _err = self._submit_with_receipt(receipt)
        self.assertEqual(1, out_code)
        self.assertEqual(code, json.loads(out)["error"]["code"])

    def test_malformed_result_digest_is_contract_drift(self) -> None:
        for bad in ("sha256:" + "A" * 64, "sha512:" + "0" * 64, "0" * 64, 42):
            with self.subTest(bad=bad):
                attempt = self._attempt_path()
                if attempt.exists():
                    attempt.unlink()
                self._assert_rejected_receipt(
                    _receipt(result_digest=bad), "SERVER_CONTRACT_DRIFT"
                )

    def test_staged_digest_mismatch_is_candidate_digest_mismatch(self) -> None:
        receipt = _receipt()
        receipt["staged_artifacts"][0]["sha256"] = "0" * 64
        self._assert_rejected_receipt(receipt, "CANDIDATE_DIGEST_MISMATCH")

    def test_staged_size_mismatch_is_staged_metadata_mismatch(self) -> None:
        receipt = _receipt()
        receipt["staged_artifacts"][1]["size_bytes"] += 1
        self._assert_rejected_receipt(receipt, "STAGED_METADATA_MISMATCH")

    def test_wrong_storage_key_is_invalid_storage_key(self) -> None:
        receipt = _receipt()
        digest = receipt["staged_artifacts"][0]["sha256"]
        receipt["staged_artifacts"][0]["storage_key"] = f"sha256/zz/{digest}"
        self._assert_rejected_receipt(receipt, "INVALID_STORAGE_KEY")

    def test_undeclared_staged_path_is_rejected(self) -> None:
        receipt = _receipt()
        receipt["staged_artifacts"].append(
            _staged_entry("cards/extra.json", b"{}")
        )
        self._assert_rejected_receipt(receipt, "STAGED_METADATA_MISMATCH")

    def test_missing_staged_path_is_rejected(self) -> None:
        receipt = _receipt()
        receipt["staged_artifacts"] = receipt["staged_artifacts"][:1]
        self._assert_rejected_receipt(receipt, "STAGED_METADATA_MISMATCH")

    def test_receipt_shape_violations_are_contract_drift(self) -> None:
        good = _receipt()
        variants = [
            {**good, "extra": 1},
            {k: v for k, v in good.items() if k != "replayed"},
            {**good, "replayed": "yes"},
            {**good, "accepted_at": 42},
            {**good, "packet_id": "gp_ffffffffffffffffffffffffffffffff"},
            {**good, "staged_artifacts": [{"relative_path": CARD_PATH}]},
        ]
        for variant in variants:
            with self.subTest(variant=str(variant)[:60]):
                attempt = self._attempt_path()
                if attempt.exists():
                    attempt.unlink()
                self._assert_rejected_receipt(variant, "SERVER_CONTRACT_DRIFT")

    def test_every_staged_artifact_matches_the_local_bytes(self) -> None:
        code, out, err = self._submit_with_receipt(_receipt(), status=201)
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        staged = payload["staged_artifacts"]
        self.assertEqual([CARD_PATH, NOTE_PATH], [s["relative_path"] for s in staged])
        for entry in staged:
            local = FILES[entry["relative_path"]]
            digest = hashlib.sha256(local).hexdigest()
            self.assertEqual(digest, entry["sha256"])
            self.assertEqual(len(local), entry["size_bytes"])
            self.assertEqual(f"sha256/{digest[:2]}/{digest}", entry["storage_key"])


class SubmitGateTests(SubmitTestCase):
    def test_no_credential_fails_locally_before_any_http(self) -> None:
        self.store.stored = None
        _write_files(self.result_dir)
        code, out, err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual("AUTH_REQUIRED", json.loads(out)["error"]["code"])
        self.assertEqual([], self.server.requests)
        self.assertFalse(self._attempt_path().exists())
        self.assert_no_token(out, err)

    def test_incompatible_server_blocks_submit_before_any_mutation(self) -> None:
        _write_files(self.result_dir)
        self._serve_submit()
        self._routes(
            {
                ("GET", "/card-os/api/v1/capabilities"): _json_route(
                    {**CAPABILITIES_OK, "protocol": {"minimum": 2, "maximum": 3}}
                )
            }
        )
        code, out, _err = self._submit()
        self.assertEqual(1, code)
        self.assertEqual(
            "CLIENT_UPGRADE_REQUIRED", json.loads(out)["error"]["code"]
        )
        self.assertEqual([], [r for r in self.server.requests if r["method"] == "POST"])

    def test_free_concept_packet_id_fails_closed_without_http(self) -> None:
        for concept in ("兔子，5～6岁", "rabbit cards for kids"):
            with self.subTest(concept=concept):
                del self.server.requests[:]
                code, out, err = self.run_cli(
                    [
                        "results",
                        "submit",
                        concept,
                        "--directory",
                        str(self.result_dir),
                    ]
                )
                self.assertEqual(1, code)
                self.assertEqual(
                    "TRUSTED_UPSTREAM_REQUIRED", json.loads(out)["error"]["code"]
                )
                self.assertEqual([], self.server.requests)
                self.assert_no_token(out, err)

    def test_usage_errors_exit_2_without_http(self) -> None:
        bad_invocations = [
            ["results"],
            ["results", "frobnicate"],
            ["results", "submit"],
            ["results", "submit", PACKET_ID],
            ["results", "submit", PACKET_ID, "--directory"],
            ["results", "submit", PACKET_ID, "--output", "x"],
            ["results", "submit", PACKET_ID, "--directory", "x", "extra"],
        ]
        for args in bad_invocations:
            with self.subTest(args=args):
                del self.server.requests[:]
                code, out, err = self.run_cli(args)
                self.assertEqual(2, code)
                self.assertEqual("", out)
                self.assertIn("usage:", err)
                self.assertEqual([], self.server.requests)


if __name__ == "__main__":
    unittest.main()
