"""Transport and capability-negotiation tests for the thin Card OS client.

Uses a loopback fixture HTTP server reached only through an explicitly
injected ``TransportConfig``; the production CLI never exposes a base-url
flag. All tokens in this file are obvious fakes.
"""

from __future__ import annotations

import contextlib
import http.server
import importlib.util
import io
import json
import sys
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "skills" / "cognitive-card-os" / "scripts" / "card_os_client.py"
FAKE_TOKEN = "dummy-fixture-token-not-a-real-secret"

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


# Frozen 0.3.1 client-visible server-code contract snapshot (app commit
# c2a898cba5b8a8948c06688d8c2a387353d7cbbe), copied from the SKILL-02 plan.
FROZEN_SERVER_CODES = frozenset(
    {
        # auth/protocol
        "AUTH_REQUIRED", "AUTH_INVALID", "AUTH_EXPIRED", "AUTH_SCOPE_REQUIRED",
        "AUTH_REVOKED", "CLIENT_UPGRADE_REQUIRED", "SERVER_UPGRADE_REQUIRED",
        "INVALID_SKILL_RELEASE",
        # request/http
        "REQUEST_VALIDATION_FAILED", "REQUEST_TOO_LARGE", "PAYLOAD_TOO_LARGE",
        "UNSUPPORTED_MEDIA_TYPE", "UNSUPPORTED_CONTENT_ENCODING",
        "ROUTE_NOT_FOUND", "METHOD_NOT_ALLOWED", "HTTP_ERROR", "INTERNAL_ERROR",
        # packet/state
        "JOB_NOT_FOUND", "PACKET_NOT_FOUND", "PACKET_ALREADY_CLAIMED",
        "PACKET_EXPIRED", "LEASE_EXPIRED", "LEASE_OWNER_MISMATCH",
        "INVALID_STATE_TRANSITION", "INVALID_CLIENT_ID", "CLIENT_REVOKED",
        "INVALID_PACKET_LIMIT", "INVALID_LEASE_DURATION",
        # result/artifact
        "INVALID_IDEMPOTENCY_KEY", "IDEMPOTENCY_CONFLICT",
        "SKILL_RELEASE_MISMATCH", "INVALID_BASE64", "MISSING_ARTIFACT",
        "UNDECLARED_ARTIFACT", "UNSAFE_ARTIFACT_PATH",
        "ARTIFACT_MEDIA_TYPE_MISMATCH", "ARTIFACT_SIZE_MISMATCH",
        "ARTIFACT_TOO_LARGE", "ARTIFACT_DIGEST_MISMATCH",
        "UNSUPPORTED_ARTIFACT_MEDIA_TYPE", "INVALID_ARTIFACT_MEDIA",
        "UNSAFE_ARTIFACT_COMPRESSION", "CONTENT_LOCK_MISMATCH",
        "PACKET_PROFILE_MISMATCH", "RESULT_CLIENT_MISMATCH",
        "STAGED_METADATA_MISMATCH",
        # server-integrity
        "CANDIDATE_DIGEST_MISMATCH", "CANDIDATE_STORE_CLOSED",
        "CANDIDATE_STORE_REQUIRED", "INVALID_STORAGE_KEY",
        "UNSAFE_CANDIDATE_STORE", "FORBIDDEN_CREDENTIAL_FIELD",
        "FORBIDDEN_CREDENTIAL_VALUE", "NON_CANONICAL_JSON",
        "DATABASE_CONSTRAINT_VIOLATION", "INVALID_UTC_CLOCK",
        "INVALID_UTC_TIMESTAMP",
    }
)

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
        with self.server.lock:
            self.server.requests.append(
                {
                    "method": self.command,
                    "path": self.path,
                    "headers": {k: v for k, v in self.headers.items()},
                }
            )
        route = self.server.routes.get((self.command, self.path))
        try:
            if route is None:
                self._respond(
                    404,
                    b'{"error":{"code":"ROUTE_NOT_FOUND","message":"no such route",'
                    b'"request_id":"req-fixture"}}',
                )
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
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def _json_route(document: dict[str, object], status: int = 200):
    body = json.dumps(document).encode("utf-8")

    def route(handler: _FixtureHandler) -> None:
        handler._respond(status, body)

    return route


class TransportTestCase(unittest.TestCase):
    """Base class wiring the fixture server and config injection seam."""

    def setUp(self) -> None:
        self.server = _FixtureServer()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self._saved_config = client._config
        self.addCleanup(self._restore)
        self._use_config()

    def _restore(self) -> None:
        client._config = self._saved_config
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _use_config(self, **overrides: object) -> None:
        values: dict[str, object] = {
            "base_url": f"http://127.0.0.1:{self.server.port}/card-os/",
            "timeout_seconds": 2.0,
            "allow_plain_http_loopback": True,
        }
        values.update(overrides)
        client._config = client.TransportConfig(**values)

    def _routes(self, routes: dict[tuple[str, str], object]) -> None:
        self.server.routes.update(routes)


class BaseUrlTests(TransportTestCase):
    def test_fixed_production_base_url(self) -> None:
        self.assertEqual("https://www.yutou.space/card-os/", client.BASE_URL)
        self.assertEqual("https://www.yutou.space/card-os/", client.TransportConfig().base_url)

    def test_plain_http_refused_without_loopback_opt_in(self) -> None:
        client._config = client.TransportConfig(
            base_url=f"http://127.0.0.1:{self.server.port}/card-os/"
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health")
        self.assertEqual("TLS_REQUIRED", ctx.exception.code)

    def test_non_loopback_plain_http_refused_even_with_opt_in(self) -> None:
        client._config = client.TransportConfig(
            base_url="http://203.0.113.10/card-os/",
            allow_plain_http_loopback=True,
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health")
        self.assertEqual("TLS_REQUIRED", ctx.exception.code)

    def test_non_http_scheme_refused(self) -> None:
        client._config = client.TransportConfig(base_url="ftp://www.yutou.space/card-os/")
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health")
        self.assertEqual("TLS_REQUIRED", ctx.exception.code)


class HeaderTests(TransportTestCase):
    def test_protected_headers_exact_when_token_supplied(self) -> None:
        self._routes({("GET", "/card-os/api/v1/health"): _json_route(HEALTH_OK)})
        status, document = client.request_json(
            "GET", "/card-os/api/v1/health", token=FAKE_TOKEN
        )
        self.assertEqual(200, status)
        self.assertEqual("ok", document["status"])
        self.assertEqual(1, len(self.server.requests))
        # Header names are case-insensitive (RFC 9110); urllib capitalizes
        # them its own way, so compare case-insensitively and values exactly.
        headers = {k.lower(): v for k, v in self.server.requests[0]["headers"].items()}
        self.assertEqual(f"Bearer {FAKE_TOKEN}", headers["authorization"])
        self.assertEqual("1", headers["x-card-os-protocol"])
        self.assertEqual("0.1.0", headers["x-card-os-skill-release"])

    def test_no_authorization_header_without_token(self) -> None:
        self._routes({("GET", "/card-os/api/v1/health"): _json_route(HEALTH_OK)})
        client.request_json("GET", "/card-os/api/v1/health")
        headers = {k.lower() for k in self.server.requests[0]["headers"]}
        self.assertNotIn("authorization", headers)


class RedirectTests(TransportTestCase):
    def test_redirects_refused_and_never_followed(self) -> None:
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                del self.server.requests[:]

                def route(handler: _FixtureHandler, status: int = status) -> None:
                    handler._respond(
                        status,
                        b"",
                        extra_headers={"Location": "/card-os/api/v1/capabilities"},
                    )

                self._routes({("GET", "/card-os/api/v1/health"): route})
                with self.assertRaises(client.ClientError) as ctx:
                    client.request_json(
                        "GET", "/card-os/api/v1/health", token=FAKE_TOKEN
                    )
                self.assertEqual("REDIRECT_REFUSED", ctx.exception.code)
                # The fixture must have seen exactly one request: the bearer
                # was never replayed against the redirect target.
                self.assertEqual(1, len(self.server.requests))


class ResponseBoundTests(TransportTestCase):
    def test_oversized_response_refused(self) -> None:
        marker = "x" * 4096
        self._routes(
            {("GET", "/card-os/api/v1/health"): _json_route({"status": "ok", "pad": marker})}
        )
        self._use_config(max_response_bytes=256)
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self.assertEqual("HTTP_ERROR", ctx.exception.code)
        self.assertNotIn(marker, str(ctx.exception))
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))


class CanonicalJsonTests(TransportTestCase):
    def test_canonical_json_exact_bytes(self) -> None:
        value = {"b": [2, {"é": 1}], "a": "芋"}
        self.assertEqual(
            '{"a":"芋","b":[2,{"é":1}]}'.encode("utf-8"),
            client.canonical_json(value),
        )

    def test_canonical_json_rejects_nan_and_infinity(self) -> None:
        for bad in (float("nan"), float("inf"), float("-inf"), {"x": float("nan")}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    client.canonical_json(bad)


class TimeoutTests(TransportTestCase):
    def test_stalling_server_maps_to_stable_code(self) -> None:
        def stall(handler: _FixtureHandler) -> None:
            time.sleep(5)

        self._routes({("GET", "/card-os/api/v1/health"): stall})
        self._use_config(timeout_seconds=0.3)
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self.assertEqual("HTTP_ERROR", ctx.exception.code)
        text = str(ctx.exception)
        self.assertNotIn("Traceback", text)
        self.assertNotIn(FAKE_TOKEN, text)

    def test_connection_refused_maps_to_stable_code(self) -> None:
        # Closed loopback port: exercises the URLError branch of the transport.
        client._config = client.TransportConfig(
            base_url="http://127.0.0.1:1/card-os/",
            timeout_seconds=1.0,
            allow_plain_http_loopback=True,
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self.assertEqual("HTTP_ERROR", ctx.exception.code)
        text = str(ctx.exception)
        self.assertNotIn("Traceback", text)
        self.assertNotIn(FAKE_TOKEN, text)


class ErrorParsingTests(TransportTestCase):
    def test_frozen_server_code_set(self) -> None:
        self.assertEqual(FROZEN_SERVER_CODES, frozenset(client.SERVER_ERROR_CODES))

    def test_known_server_code_preserved_verbatim(self) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(
                    {
                        "error": {
                            "code": "AUTH_REQUIRED",
                            "message": "a scoped token is required",
                            "request_id": "req-abc-123",
                        }
                    },
                    status=403,
                )
            }
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        exc = ctx.exception
        self.assertEqual("AUTH_REQUIRED", exc.code)
        self.assertEqual("AUTH_REQUIRED", exc.server_code)
        self.assertEqual(403, exc.status)
        self.assertEqual("req-abc-123", exc.request_id)

    def test_unknown_safe_server_code_maps_to_drift_but_is_preserved(self) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(
                    {"error": {"code": "BRAND_NEW_2040", "message": "future code"}},
                    status=500,
                )
            }
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health")
        exc = ctx.exception
        self.assertEqual("SERVER_CONTRACT_DRIFT", exc.code)
        self.assertEqual("BRAND_NEW_2040", exc.server_code)
        self.assertIn("BRAND_NEW_2040", json.dumps(exc.to_dict()))

    def test_non_json_error_body_maps_to_stable_code_without_leak(self) -> None:
        marker = "INTERNAL-STACK-DETAIL-" + "z" * 500

        def route(handler: _FixtureHandler) -> None:
            handler._respond(
                500, f"<html>{marker}</html>".encode(), content_type="text/html"
            )

        self._routes({("GET", "/card-os/api/v1/health"): route})
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        exc = ctx.exception
        self.assertEqual("HTTP_ERROR", exc.code)
        self.assertEqual(500, exc.status)
        self.assertNotIn(marker, str(exc))
        self.assertNotIn(FAKE_TOKEN, str(exc))

    def test_malformed_error_envelope_maps_to_drift(self) -> None:
        malformed = [
            {},
            {"error": "AUTH_REQUIRED"},
            {"error": {"code": 123}},
            {"error": {"code": "not a safe code!!"}},
            ["not", "a", "dict"],
        ]
        for document in malformed:
            with self.subTest(document=document):
                del self.server.requests[:]
                self._routes(
                    {("GET", "/card-os/api/v1/health"): _json_route(document, status=400)}
                )
                with self.assertRaises(client.ClientError) as ctx:
                    client.request_json("GET", "/card-os/api/v1/health")
                self.assertEqual("SERVER_CONTRACT_DRIFT", ctx.exception.code)
                self.assertIsNone(ctx.exception.server_code)
                if isinstance(document, dict) and isinstance(document.get("error"), dict):
                    self.assertNotIn("not a safe code!!", str(ctx.exception))

    def test_success_body_must_be_a_json_object(self) -> None:
        self._routes(
            {("GET", "/card-os/api/v1/health"): _json_route(["not", "a", "dict"])}
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health")
        self.assertEqual("SERVER_CONTRACT_DRIFT", ctx.exception.code)


class TokenLeakageTests(TransportTestCase):
    def _assert_no_token(self, exc: BaseException) -> None:
        self.assertNotIn(FAKE_TOKEN, str(exc))
        self.assertNotIn(FAKE_TOKEN, repr(exc))
        if isinstance(exc, client.ClientError):
            self.assertNotIn(FAKE_TOKEN, json.dumps(exc.to_dict()))

    def test_no_token_leak_on_redirect(self) -> None:
        def route(handler: _FixtureHandler) -> None:
            handler._respond(302, b"", extra_headers={"Location": "/elsewhere"})

        self._routes({("GET", "/card-os/api/v1/health"): route})
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self._assert_no_token(ctx.exception)

    def test_no_token_leak_on_tls_refusal(self) -> None:
        client._config = client.TransportConfig(base_url="http://127.0.0.1:1/card-os/")
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self._assert_no_token(ctx.exception)

    def test_no_token_leak_on_timeout(self) -> None:
        def stall(handler: _FixtureHandler) -> None:
            time.sleep(5)

        self._routes({("GET", "/card-os/api/v1/health"): stall})
        self._use_config(timeout_seconds=0.3)
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self._assert_no_token(ctx.exception)

    def test_no_token_leak_on_http_error(self) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(
                    {"error": {"code": "INTERNAL_ERROR", "message": "boom",
                               "request_id": "req-1"}},
                    status=500,
                )
            }
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.request_json("GET", "/card-os/api/v1/health", token=FAKE_TOKEN)
        self._assert_no_token(ctx.exception)


class DoctorTests(TransportTestCase):
    def _serve(self, health: dict[str, object] | None = None,
               capabilities: dict[str, object] | None = None) -> None:
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

    def test_happy_path_returns_status_and_compatible_versions(self) -> None:
        self._serve()
        result = client.doctor()
        self.assertEqual("ok", result["status"])
        self.assertEqual("0.3.1", result["server_version"])
        self.assertEqual("0.1.0", result["skill_release"])
        self.assertEqual(1, result["protocol"]["client"])
        self.assertEqual(1, result["protocol"]["server_minimum"])
        self.assertEqual(1, result["protocol"]["server_maximum"])
        self.assertEqual("0.1.0", result["minimum_skill_release"])
        self.assertIn("cognitive-card-generation-packet-v1", result["packet_schemas"])
        self.assertIn("cognitive-card-generation-result-v1", result["result_schemas"])
        self.assertFalse(result["features"]["free_form_job_creation"])
        # Both discovery reads are unauthenticated GETs.
        self.assertEqual(2, len(self.server.requests))
        paths = sorted(r["path"] for r in self.server.requests)
        self.assertEqual(
            ["/card-os/api/v1/capabilities", "/card-os/api/v1/health"], paths
        )
        for record in self.server.requests:
            self.assertEqual("GET", record["method"])
            self.assertNotIn(
                "authorization", {k.lower() for k in record["headers"]}
            )

    def test_server_protocol_above_client_requires_client_upgrade(self) -> None:
        self._serve(
            capabilities={**CAPABILITIES_OK, "protocol": {"minimum": 2, "maximum": 3}}
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.doctor()
        self.assertEqual("CLIENT_UPGRADE_REQUIRED", ctx.exception.code)

    def test_server_protocol_below_client_requires_server_upgrade(self) -> None:
        self._serve(
            capabilities={**CAPABILITIES_OK, "protocol": {"minimum": 0, "maximum": 0}}
        )
        with self.assertRaises(client.ClientError) as ctx:
            client.doctor()
        self.assertEqual("SERVER_UPGRADE_REQUIRED", ctx.exception.code)

    def test_server_version_below_minimum_requires_server_upgrade(self) -> None:
        self._serve(capabilities={**CAPABILITIES_OK, "server_version": "0.3.0"})
        with self.assertRaises(client.ClientError) as ctx:
            client.doctor()
        self.assertEqual("SERVER_UPGRADE_REQUIRED", ctx.exception.code)

    def test_server_version_compared_numerically_not_lexically(self) -> None:
        # "0.10.0" < "0.3.1" lexically but is newer numerically.
        self._serve(capabilities={**CAPABILITIES_OK, "server_version": "0.10.0"})
        result = client.doctor()
        self.assertEqual("ok", result["status"])
        self.assertEqual("0.10.0", result["server_version"])

    def test_minimum_skill_release_above_client_requires_client_upgrade(self) -> None:
        self._serve(capabilities={**CAPABILITIES_OK, "minimum_skill_release": "0.2.0"})
        with self.assertRaises(client.ClientError) as ctx:
            client.doctor()
        self.assertEqual("CLIENT_UPGRADE_REQUIRED", ctx.exception.code)

    def test_malformed_protocol_values_are_contract_drift(self) -> None:
        bad_protocols = [
            {"minimum": -1, "maximum": 1},
            {"minimum": "1", "maximum": 1},
            {"minimum": 1.0, "maximum": 1},
            {"minimum": True, "maximum": 1},
            {"minimum": 2, "maximum": 1},
            {"minimum": 1},
            {"maximum": 1},
            "1",
        ]
        for protocol in bad_protocols:
            with self.subTest(protocol=protocol):
                self._serve(capabilities={**CAPABILITIES_OK, "protocol": protocol})
                with self.assertRaises(client.ClientError) as ctx:
                    client.doctor()
                self.assertEqual("SERVER_CONTRACT_DRIFT", ctx.exception.code)

    def test_wrong_capabilities_schema_is_contract_drift(self) -> None:
        bad_documents = [
            {**CAPABILITIES_OK, "schema": "cognitive-card-capabilities-v2"},
            {**CAPABILITIES_OK, "server_version": "0.3"},  # not full semver
            {**CAPABILITIES_OK, "minimum_skill_release": 1},
            {**CAPABILITIES_OK, "packet_schemas": "cognitive-card-generation-packet-v1"},
            {**CAPABILITIES_OK, "features": {"review": "no"}},
            {k: v for k, v in CAPABILITIES_OK.items() if k != "protocol"},
        ]
        for document in bad_documents:
            with self.subTest(document=document):
                self._serve(capabilities=document)
                with self.assertRaises(client.ClientError) as ctx:
                    client.doctor()
                self.assertEqual("SERVER_CONTRACT_DRIFT", ctx.exception.code)

    def test_unhealthy_server_is_contract_drift(self) -> None:
        self._serve(health={"status": "degraded", "server_version": "0.3.1"})
        with self.assertRaises(client.ClientError) as ctx:
            client.doctor()
        self.assertEqual("SERVER_CONTRACT_DRIFT", ctx.exception.code)


class CliTests(TransportTestCase):
    def test_doctor_cli_success_writes_canonical_json(self) -> None:
        self._routes(
            {
                ("GET", "/card-os/api/v1/health"): _json_route(HEALTH_OK),
                ("GET", "/card-os/api/v1/capabilities"): _json_route(CAPABILITIES_OK),
            }
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = client.main(["doctor"])
        self.assertEqual(0, exit_code)
        payload = json.loads(out.getvalue())
        self.assertEqual("ok", payload["status"])
        # stdout must be canonical: sorted keys, tight separators, no NaN.
        self.assertEqual(
            client.canonical_json(payload).decode("utf-8") + "\n", out.getvalue()
        )

    def test_doctor_cli_failure_writes_stable_error_and_nonzero_exit(self) -> None:
        # No routes: the fixture answers 404 with a ROUTE_NOT_FOUND envelope.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = client.main(["doctor"])
        self.assertNotEqual(0, exit_code)
        payload = json.loads(out.getvalue())
        self.assertEqual("ROUTE_NOT_FOUND", payload["error"]["code"])

    def test_unknown_command_exits_nonzero_without_json_crash(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            exit_code = client.main(["frobnicate"])
        self.assertEqual(2, exit_code)
        self.assertIn("usage:", err.getvalue())

    def test_client_not_released_is_gone_from_source(self) -> None:
        self.assertNotIn("CLIENT_NOT_RELEASED", CLIENT_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
