#!/usr/bin/env python3
"""Cognitive Card OS thin client (skill release 0.1.0).

Standard-library-only client for the Card OS API 0.3.1 contract. This slice
implements the fail-closed transport (fixed HTTPS base URL, zero redirects,
bounded responses, stable error codes) and unauthenticated capability
negotiation (``doctor``). Credential backends and packet/result/job commands
are added by later tasks.

Security invariants enforced here:

- the base URL is fixed to the production HTTPS origin; plain HTTP is only
  possible through an explicitly injected loopback-only test config;
- redirects are never followed, so a bearer token can never be replayed
  against a redirect target;
- responses are size-bounded and error bodies are parsed defensively;
- the token never appears in exceptions, output, or logs.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.yutou.space/card-os/"
API_ROOT = "/card-os/api/v1"
PROTOCOL_VERSION = 1
SKILL_RELEASE = "0.1.0"
MINIMUM_SERVER_VERSION = (0, 3, 1)
CAPABILITIES_SCHEMA = "cognitive-card-capabilities-v1"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_SAFE_CODE_RE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_SAFE_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_SEMVER_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")

# Frozen 0.3.1 client-visible server-code contract snapshot (app commit
# c2a898cba5b8a8948c06688d8c2a387353d7cbbe). Known codes are passed through
# verbatim; anything else syntactically safe maps to SERVER_CONTRACT_DRIFT.
SERVER_ERROR_CODES = frozenset(
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


class ClientError(RuntimeError):
    """Stable, non-secret client failure.

    ``code`` is always one of the frozen local production codes or a frozen
    0.3.1 server code preserved verbatim. ``server_code`` preserves the
    original server code when ``code`` is ``SERVER_CONTRACT_DRIFT``. No field
    ever carries credentials, request objects, or raw response bytes.
    """

    def __init__(
        self,
        code: str,
        message: str = "",
        *,
        action: str | None = None,
        status: int | None = None,
        server_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.action = action
        self.status = status
        self.server_code = server_code
        self.request_id = request_id

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code, "message": str(self)}
        if self.action is not None:
            result["action"] = self.action
        if self.status is not None:
            result["status"] = self.status
        if self.server_code is not None:
            result["server_code"] = self.server_code
        if self.request_id is not None:
            result["request_id"] = self.request_id
        return result


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuses every redirect so Authorization is never sent onward."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


@dataclasses.dataclass(frozen=True)
class TransportConfig:
    """Connection settings. ``allow_plain_http_loopback`` exists only so
    tests can inject a 127.0.0.1 fixture; the loopback host check is
    re-verified at request time, so the flag alone can never weaken TLS."""

    base_url: str = BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_response_bytes: int = MAX_RESPONSE_BYTES
    allow_plain_http_loopback: bool = False


# Injection seam for tests: replaced with a loopback TransportConfig. The
# production CLI has no flag that can influence this value.
_config = TransportConfig()


def canonical_json(value: object) -> bytes:
    """UTF-8 canonical JSON: sorted keys, tight separators, no NaN."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _endpoint(config: TransportConfig, path: str) -> str:
    if not path.startswith(API_ROOT + "/"):
        raise ValueError("path outside the /card-os/api/v1 namespace")
    parts = urllib.parse.urlsplit(config.base_url)
    host = (parts.hostname or "").lower()
    if parts.scheme == "https":
        pass
    elif (
        parts.scheme == "http"
        and config.allow_plain_http_loopback
        and host in _LOOPBACK_HOSTS
    ):
        pass
    else:
        raise ClientError(
            "TLS_REQUIRED",
            "refusing non-HTTPS base URL",
            action="use the fixed production HTTPS endpoint",
        )
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _read_bounded(stream, limit: int) -> bytes:  # noqa: ANN001
    payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise ClientError(
            "HTTP_ERROR",
            "response body exceeds the maximum accepted size",
            action="stop and report the oversized response; do not retry blindly",
        )
    return payload


def _bounded_text(value: object, limit: int = 300) -> str | None:
    """Return a printable, length-bounded summary of a server string field."""
    if not isinstance(value, str):
        return None
    text = "".join(ch for ch in value if ch.isprintable())[:limit]
    return text or None


def _parse_error_payload(status: int, payload: bytes) -> ClientError:
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ClientError(
            "HTTP_ERROR",
            f"server returned HTTP {status} with a non-JSON error body",
            action="retry once; if it persists report the server status",
            status=status,
        )
    if not isinstance(document, dict) or not isinstance(document.get("error"), dict):
        return ClientError(
            "SERVER_CONTRACT_DRIFT",
            f"server returned HTTP {status} without an error envelope",
            action="stop and report the server contract drift",
            status=status,
        )
    error = document["error"]
    code = error.get("code")
    message = _bounded_text(error.get("message"))
    raw_request_id = error.get("request_id")
    request_id = (
        raw_request_id
        if isinstance(raw_request_id, str) and _SAFE_REQUEST_ID_RE.fullmatch(raw_request_id)
        else None
    )
    if isinstance(code, str) and code in SERVER_ERROR_CODES:
        return ClientError(
            code,
            message or f"server returned {code}",
            status=status,
            server_code=code,
            request_id=request_id,
        )
    if isinstance(code, str) and _SAFE_CODE_RE.fullmatch(code):
        return ClientError(
            "SERVER_CONTRACT_DRIFT",
            f"server returned an unknown error code outside the frozen 0.3.1 contract",
            action="stop and report the server contract drift",
            status=status,
            server_code=code,
            request_id=request_id,
        )
    return ClientError(
        "SERVER_CONTRACT_DRIFT",
        f"server returned HTTP {status} with a malformed error code",
        action="stop and report the server contract drift",
        status=status,
        request_id=request_id,
    )


def _parse_success_payload(payload: bytes) -> dict[str, object]:
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ClientError(
            "SERVER_CONTRACT_DRIFT",
            "server returned a non-JSON success body",
            action="stop and report the server contract drift",
        ) from None
    if not isinstance(document, dict):
        raise ClientError(
            "SERVER_CONTRACT_DRIFT",
            "server returned a non-object JSON success body",
            action="stop and report the server contract drift",
        )
    return document


def request_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: bytes | None = None,
    idempotency_key: str | None = None,
) -> tuple[int, dict[str, object]]:
    """One bounded JSON request against the fixed Card OS API namespace."""
    config = _config
    url = _endpoint(config, path)
    headers = {
        "Accept": "application/json",
        "User-Agent": f"cognitive-card-os-client/{SKILL_RELEASE}",
        "X-Card-OS-Protocol": str(PROTOCOL_VERSION),
        "X-Card-OS-Skill-Release": SKILL_RELEASE,
    }
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        with opener.open(request, timeout=config.timeout_seconds) as response:
            status = response.status
            payload = _read_bounded(response, config.max_response_bytes)
    except urllib.error.HTTPError as exc:
        try:
            if 300 <= exc.code < 400:
                raise ClientError(
                    "REDIRECT_REFUSED",
                    f"server answered with redirect status {exc.code}; redirects are never followed",
                    action="use the fixed production endpoint; do not follow redirects",
                    status=exc.code,
                ) from None
            raise _parse_error_payload(
                exc.code, _read_bounded(exc, config.max_response_bytes)
            ) from None
        finally:
            exc.close()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # Never echo the exception: it may embed connection details. The
        # request object, headers and token are never included anywhere.
        del exc
        raise ClientError(
            "HTTP_ERROR",
            "request failed or timed out before a complete HTTP response",
            action="check network connectivity and retry",
        ) from None
    return status, _parse_success_payload(payload)


def _parse_semver(value: object) -> tuple[int, int, int] | None:
    """Numeric SemVer tuple; never string ordering. None when malformed."""
    if not isinstance(value, str):
        return None
    match = _SEMVER_RE.fullmatch(value)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _format_semver(version: tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


def _unsigned_decimal(value: object) -> int | None:
    # type(...) is int excludes bool, which is an int subclass.
    if type(value) is int and value >= 0:
        return value
    return None


def _drift(message: str) -> ClientError:
    return ClientError(
        "SERVER_CONTRACT_DRIFT",
        message,
        action="stop and report the server contract drift",
    )


def _check_health(document: dict[str, object]) -> None:
    if document.get("status") != "ok":
        raise _drift("health endpoint did not report status ok")
    if _parse_semver(document.get("server_version")) is None:
        raise _drift("health endpoint returned a malformed server version")


def _check_capabilities(document: dict[str, object]) -> dict[str, object]:
    if document.get("schema") != CAPABILITIES_SCHEMA:
        raise _drift("capabilities document has an unexpected schema")
    server_version = _parse_semver(document.get("server_version"))
    if server_version is None:
        raise _drift("capabilities document has a malformed server version")
    protocol = document.get("protocol")
    if not isinstance(protocol, dict):
        raise _drift("capabilities document has a malformed protocol range")
    minimum = _unsigned_decimal(protocol.get("minimum"))
    maximum = _unsigned_decimal(protocol.get("maximum"))
    if minimum is None or maximum is None or minimum > maximum:
        raise _drift("capabilities document has a malformed protocol range")
    minimum_skill = _parse_semver(document.get("minimum_skill_release"))
    if minimum_skill is None:
        raise _drift("capabilities document has a malformed minimum skill release")
    packet_schemas = document.get("packet_schemas")
    result_schemas = document.get("result_schemas")
    for name, value in (("packet_schemas", packet_schemas), ("result_schemas", result_schemas)):
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item for item in value)
        ):
            raise _drift(f"capabilities document has malformed {name}")
    features = document.get("features")
    if not isinstance(features, dict) or any(
        not isinstance(key, str) or type(item) is not bool
        for key, item in features.items()
    ):
        raise _drift("capabilities document has malformed features")
    return {
        "server_version": server_version,
        "protocol_minimum": minimum,
        "protocol_maximum": maximum,
        "minimum_skill_release": minimum_skill,
        "packet_schemas": packet_schemas,
        "result_schemas": result_schemas,
        "features": features,
    }


def doctor() -> dict[str, object]:
    """Unauthenticated compatibility check against health and capabilities."""
    _, health = request_json("GET", f"{API_ROOT}/health")
    _check_health(health)
    _, capabilities_document = request_json("GET", f"{API_ROOT}/capabilities")
    capabilities = _check_capabilities(capabilities_document)

    if PROTOCOL_VERSION < capabilities["protocol_minimum"]:
        raise ClientError(
            "CLIENT_UPGRADE_REQUIRED",
            "server requires a newer protocol than this skill speaks",
            action="install the current stable skill release",
        )
    if PROTOCOL_VERSION > capabilities["protocol_maximum"]:
        raise ClientError(
            "SERVER_UPGRADE_REQUIRED",
            "server speaks only older protocol versions",
            action="stop claiming packets until the server is upgraded",
        )
    if capabilities["server_version"] < MINIMUM_SERVER_VERSION:
        raise ClientError(
            "SERVER_UPGRADE_REQUIRED",
            f"server version {_format_semver(capabilities['server_version'])} is below "
            f"the required {_format_semver(MINIMUM_SERVER_VERSION)}",
            action="stop claiming packets until the server is upgraded",
        )
    if capabilities["minimum_skill_release"] > _parse_semver(SKILL_RELEASE):
        raise ClientError(
            "CLIENT_UPGRADE_REQUIRED",
            "server requires a newer skill release",
            action="install the current stable skill release",
        )
    return {
        "status": "ok",
        "server_version": _format_semver(capabilities["server_version"]),
        "skill_release": SKILL_RELEASE,
        "protocol": {
            "client": PROTOCOL_VERSION,
            "server_minimum": capabilities["protocol_minimum"],
            "server_maximum": capabilities["protocol_maximum"],
        },
        "minimum_skill_release": _format_semver(capabilities["minimum_skill_release"]),
        "packet_schemas": capabilities["packet_schemas"],
        "result_schemas": capabilities["result_schemas"],
        "features": capabilities["features"],
    }


def _emit(document: dict[str, object]) -> None:
    sys.stdout.write(canonical_json(document).decode("utf-8") + "\n")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["doctor"]:
        try:
            _emit(doctor())
        except ClientError as exc:
            _emit({"error": exc.to_dict()})
            return 1
        return 0
    sys.stderr.write("usage: card_os_client.py doctor\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
