#!/usr/bin/env python3
"""Cognitive Card OS thin client (skill release 0.1.1).

Standard-library-only client for the Card OS API 0.3.1 contract. This slice
implements the fail-closed transport (fixed HTTPS base URL, zero redirects,
bounded responses, stable error codes), unauthenticated capability
negotiation (``doctor``), the non-disclosing credential backends
(``auth set/status/delete``), the packet/job commands
(``packets list/claim/get/complete``, ``jobs status/events``) with closed
packet-envelope validation, server-0.3.1 digest recomputation and
timeout-triggered status reads, and result submission
(``results submit``) with local directory closure, a credential scan, a
private submit-attempt journal, the frozen idempotency-key formula, bounded
same-key replay and acceptance-receipt verification.

Security invariants enforced here:

- the base URL is fixed to the production HTTPS origin; plain HTTP is only
  possible through an explicitly injected loopback-only test config;
- redirects are never followed, so a bearer token can never be replayed
  against a redirect target;
- responses are size-bounded and error bodies are parsed defensively;
- the token never appears in argv, exceptions, output, or logs;
- credential storage priority is macOS Keychain, then Linux ``secret-tool``,
  then the 0600 file fallback only with an explicit ``--allow-file-store``;
  with no usable backend and no flag, configuration fails closed;
- ``CARD_OS_TOKEN`` is ephemeral: it wins at request time, is never
  persisted automatically and is redacted from every error.
"""

from __future__ import annotations

import base64
import ctypes
import dataclasses
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

BASE_URL = "https://www.yutou.space/card-os/"
API_ROOT = "/card-os/api/v1"
PROTOCOL_VERSION = 1
SKILL_RELEASE = "0.1.1"
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


# ---------------------------------------------------------------------------
# Credential storage
#
# Three non-disclosing backends behind the CredentialStore protocol:
# macOS Keychain (in-process Security.framework through ctypes), Linux
# Secret Service (secret-tool with the token on stdin only) and an explicit
# 0600 file fallback. Backend failures never include secret bytes; only
# stable codes, integer OSStatus/exit statuses and fixed actions are
# reported.
# ---------------------------------------------------------------------------

MAX_TOKEN_BYTES = 4096
MAX_CREDENTIAL_FILE_BYTES = 64 * 1024
SECRET_TOOL_TIMEOUT_SECONDS = 15.0

_KEYCHAIN_SERVICE = b"cognitive-card-os"
_KEYCHAIN_ACCOUNT = BASE_URL.encode("utf-8")
_ERR_SEC_DUPLICATE_ITEM = -25299
_ERR_SEC_ITEM_NOT_FOUND = -25300

# The complete set of Security.framework/CoreFoundation entry points this
# client binds. Nothing else is ever looked up.
KEYCHAIN_BOUND_FUNCTIONS = frozenset(
    {
        "SecKeychainFindGenericPassword",
        "SecKeychainAddGenericPassword",
        "SecKeychainItemModifyAttributesAndData",
        "SecKeychainItemFreeContent",
        "CFRelease",
    }
)

_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)

# Minimal environment for the secret-tool subprocess: metadata travels in
# argv, the token on stdin, and no inherited variable can leak either.
_SANITIZED_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}


class CredentialStore(Protocol):
    """Non-disclosing credential backend."""

    backend_name: str

    def set(self, token: bytes) -> None: ...
    def get(self) -> bytes | None: ...
    def delete(self) -> bool: ...


class _SecurityFramework:
    """In-process ctypes binding over Security.framework.

    Only the functions in KEYCHAIN_BOUND_FUNCTIONS are bound. Tests
    substitute a fake with the same method surface, so the suite never
    touches the user's real login Keychain. Method arguments carry service /
    account metadata or ctypes buffers only, never Python copies of the
    secret beyond the buffers the store zeroes after each call.
    """

    def __init__(self, security, core_foundation) -> None:  # noqa: ANN001
        self._security = security
        self._core_foundation = core_foundation
        security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
        security.SecKeychainAddGenericPassword.restype = ctypes.c_int32
        security.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
        security.SecKeychainItemFreeContent.restype = ctypes.c_int32
        core_foundation.CFRelease.restype = None

    @classmethod
    def load(cls) -> "_SecurityFramework":
        try:
            security = ctypes.CDLL(
                "/System/Library/Frameworks/Security.framework/Security"
            )
            core_foundation = ctypes.CDLL(
                "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
            )
        except OSError:
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                "Security.framework could not be loaded",
                action="re-run auth set --stdin --allow-file-store to use the file store",
            ) from None
        return cls(security, core_foundation)

    def find_generic_password(
        self, service: bytes, account: bytes
    ) -> tuple[int, bytes | None, int | None]:
        """(OSStatus, password bytes, item ref); frees the password buffer."""
        length = ctypes.c_uint32(0)
        data = ctypes.c_void_p()
        item = ctypes.c_void_p()
        status = self._security.SecKeychainFindGenericPassword(
            None,
            len(service),
            service,
            len(account),
            account,
            ctypes.byref(length),
            ctypes.byref(data),
            ctypes.byref(item),
        )
        if status != 0:
            return status, None, None
        payload = ctypes.string_at(data, length.value) if data else b""
        self._security.SecKeychainItemFreeContent(None, data)
        return 0, payload, item.value

    def add_generic_password(self, service: bytes, account: bytes, token_buffer) -> int:  # noqa: ANN001
        return self._security.SecKeychainAddGenericPassword(
            None,
            len(service),
            service,
            len(account),
            account,
            len(token_buffer),
            token_buffer,
            None,
        )

    def modify_item_data(self, item_ref: int, token_buffer) -> int:  # noqa: ANN001
        length = 0 if token_buffer is None else len(token_buffer)
        return self._security.SecKeychainItemModifyAttributesAndData(
            ctypes.c_void_p(item_ref), None, length, token_buffer
        )

    def release_item(self, item_ref: int) -> None:
        self._core_foundation.CFRelease(ctypes.c_void_p(item_ref))


def _keychain_error(operation: str, status: int) -> ClientError:
    # Only the integer OSStatus is reported; never secret bytes.
    return ClientError(
        "CREDENTIAL_STORE_UNAVAILABLE",
        f"keychain {operation} failed with OSStatus {status}",
        action="unlock the login keychain or re-run auth set",
    )


class KeychainCredentialStore:
    """macOS Keychain backend: service cognitive-card-os, account base URL."""

    backend_name = "macos-keychain"

    def __init__(self, security: _SecurityFramework | None = None) -> None:
        self._security = security if security is not None else _SecurityFramework.load()

    def set(self, token: bytes) -> None:
        token = bytes(token)
        buffer = ctypes.create_string_buffer(token, len(token))
        try:
            status = self._security.add_generic_password(
                _KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT, buffer
            )
            if status == _ERR_SEC_DUPLICATE_ITEM:
                find_status, _data, item_ref = self._security.find_generic_password(
                    _KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT
                )
                if find_status != 0 or item_ref is None:
                    raise _keychain_error("lookup before update", find_status)
                try:
                    modify_status = self._security.modify_item_data(item_ref, buffer)
                finally:
                    self._security.release_item(item_ref)
                if modify_status != 0:
                    raise _keychain_error("update", modify_status)
            elif status != 0:
                raise _keychain_error("add", status)
        finally:
            # The mutable token buffer is zeroed after every call path.
            ctypes.memset(buffer, 0, len(buffer))

    def get(self) -> bytes | None:
        status, data, item_ref = self._security.find_generic_password(
            _KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT
        )
        if status == _ERR_SEC_ITEM_NOT_FOUND:
            return None
        if status != 0:
            raise _keychain_error("lookup", status)
        if item_ref is not None:
            self._security.release_item(item_ref)
        # Zero-length data is the erased state written by delete().
        return data or None

    def delete(self) -> bool:
        status, _data, item_ref = self._security.find_generic_password(
            _KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT
        )
        if status == _ERR_SEC_ITEM_NOT_FOUND:
            return False
        if status != 0:
            raise _keychain_error("lookup before delete", status)
        if item_ref is None:
            return False
        try:
            # The frozen binding set has no SecKeychainItemDelete, so deletion
            # is an in-place erase to zero-length data; get() treats that as
            # absent. The buffer must be non-NULL: on real Security.framework
            # a NULL pointer makes the modify a no-op (the 0.1.0 live
            # acceptance defect), while a zero-length buffer truncates.
            empty = ctypes.create_string_buffer(0)
            modify_status = self._security.modify_item_data(item_ref, empty)
        finally:
            self._security.release_item(item_ref)
        if modify_status != 0:
            raise _keychain_error("delete", modify_status)
        return True


@dataclasses.dataclass(frozen=True)
class _SecretToolResult:
    returncode: int
    stdout: bytes


def _secret_tool_available() -> bool:
    return shutil.which("secret-tool") is not None


def _run_secret_tool(argv: list[str], stdin_data: bytes | None) -> _SecretToolResult:
    completed = subprocess.run(
        argv,
        input=stdin_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_SANITIZED_ENV,
        timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        check=False,
    )
    # Captured output is returned to the caller only on success and is never
    # logged or embedded in errors.
    return _SecretToolResult(completed.returncode, completed.stdout)


class SecretToolCredentialStore:
    """Linux Secret Service backend through the secret-tool CLI."""

    backend_name = "linux-secret-tool"

    def __init__(self, runner=None) -> None:  # noqa: ANN001
        self._runner = runner if runner is not None else _run_secret_tool

    @staticmethod
    def _argv(verb: str) -> list[str]:
        # Metadata only; the token itself travels on stdin for `store`.
        argv = ["secret-tool", verb]
        if verb == "store":
            argv.append("--label=Cognitive Card OS client credential")
        argv += ["service", "cognitive-card-os", "base-url", BASE_URL]
        return argv

    def _run(self, argv: list[str], stdin_data: bytes | None) -> _SecretToolResult:
        try:
            return self._runner(argv, stdin_data)
        except (OSError, subprocess.SubprocessError):
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                "secret-tool could not be executed",
                action="install secret-tool or re-run auth set --stdin --allow-file-store",
            ) from None

    def set(self, token: bytes) -> None:
        result = self._run(self._argv("store"), bytes(token))
        if result.returncode != 0:
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                f"secret-tool store exited with status {result.returncode}",
                action="check the Secret Service daemon and re-run auth set",
            )

    def get(self) -> bytes | None:
        result = self._run(self._argv("lookup"), None)
        if result.returncode == 1:
            return None
        if result.returncode != 0:
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                f"secret-tool lookup exited with status {result.returncode}",
                action="check the Secret Service daemon and re-run auth set",
            )
        return bytes(result.stdout) or None

    def delete(self) -> bool:
        result = self._run(self._argv("clear"), None)
        if result.returncode == 1:
            return False
        if result.returncode != 0:
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                f"secret-tool clear exited with status {result.returncode}",
                action="check the Secret Service daemon and re-run auth delete",
            )
        return True


def _file_store_path(environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    config_home = env.get("XDG_CONFIG_HOME")
    if not config_home:
        home = env.get("HOME") or str(Path.home())
        config_home = os.path.join(home, ".config")
    return Path(config_home) / "cognitive-card-os" / "credentials.json"


def _unsafe_store(message: str) -> ClientError:
    return ClientError(
        "CREDENTIAL_STORE_UNSAFE",
        message,
        action="fix ownership and permissions or remove the file and re-run auth set",
    )


class FileCredentialStore:
    """0600 JSON file fallback.

    Writes require the explicit --allow-file-store opt-in; reads also reach
    this store whenever no platform backend exists on the host, so a
    credential stored through the opt-in is never write-only.
    """

    backend_name = "file"

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else _file_store_path()

    @property
    def path(self) -> Path:
        return self._path

    def _verify_directory(self) -> bool:
        """True when the parent directory exists and passes all checks."""
        try:
            info = os.lstat(self._path.parent)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(info.st_mode):  # lstat: symlinks are not dirs
            raise _unsafe_store("credential directory is not a real directory")
        if info.st_uid != os.getuid():
            raise _unsafe_store("credential directory is owned by another user")
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise _unsafe_store("credential directory must have mode 0700")
        return True

    def _verify_file(self, info: os.stat_result) -> None:
        if not stat.S_ISREG(info.st_mode):  # lstat: symlinks are not regular
            raise _unsafe_store("credential file is not a regular file")
        if info.st_uid != os.getuid():
            raise _unsafe_store("credential file is owned by another user")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise _unsafe_store("credential file must have mode 0600")
        if info.st_size > MAX_CREDENTIAL_FILE_BYTES:
            raise _unsafe_store("credential file exceeds the maximum accepted size")

    def _write_private_temp(self, payload: bytes) -> Path:
        parent = self._path.parent
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
        for _ in range(16):
            candidate = parent / (".credentials-" + secrets.token_hex(8) + ".tmp")
            try:
                descriptor = os.open(candidate, flags, 0o600)
                break
            except FileExistsError:
                continue
        else:
            raise ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE",
                "could not allocate a private temp file for the credential store",
                action="remove stale temp files and re-run auth set",
            )
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
        except BaseException:
            os.close(descriptor)
            candidate.unlink(missing_ok=True)
            raise
        os.close(descriptor)
        return candidate

    def set(self, token: bytes) -> None:
        payload = canonical_json(
            {"base_url": BASE_URL, "token": bytes(token).decode("utf-8")}
        )
        os.makedirs(self._path.parent, mode=0o700, exist_ok=True)
        self._verify_directory()
        try:
            self._verify_file(os.lstat(self._path))
        except FileNotFoundError:
            pass
        candidate = self._write_private_temp(payload)
        os.replace(candidate, self._path)
        dir_descriptor = os.open(self._path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_descriptor)
        finally:
            os.close(dir_descriptor)

    def get(self) -> bytes | None:
        if not self._verify_directory():
            return None
        try:
            info = os.lstat(self._path)
        except FileNotFoundError:
            return None
        self._verify_file(info)
        descriptor = os.open(self._path, os.O_RDONLY | _O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as handle:
            raw = handle.read(MAX_CREDENTIAL_FILE_BYTES + 1)
        if len(raw) > MAX_CREDENTIAL_FILE_BYTES:
            raise _unsafe_store("credential file exceeds the maximum accepted size")
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise _unsafe_store("credential file is not valid JSON") from None
        if not isinstance(document, dict):
            raise _unsafe_store("credential file is not a JSON object")
        base_url = document.get("base_url")
        stored = document.get("token")
        if not isinstance(base_url, str) or not isinstance(stored, str) or not stored:
            raise _unsafe_store("credential file has a malformed shape")
        return stored.encode("utf-8")

    def delete(self) -> bool:
        if not self._verify_directory():
            return False
        try:
            info = os.lstat(self._path)
        except FileNotFoundError:
            return False
        self._verify_file(info)
        os.unlink(self._path)
        return True


def select_credential_store(
    *, platform: str, allow_file_store: bool
) -> CredentialStore:
    """macOS Keychain, then Linux secret-tool, then the gated file store."""
    if platform == "darwin":
        try:
            return KeychainCredentialStore()
        except ClientError:
            if not allow_file_store:
                raise
            return FileCredentialStore()
    if platform.startswith("linux"):
        if _secret_tool_available():
            return SecretToolCredentialStore()
        if allow_file_store:
            return FileCredentialStore()
        raise ClientError(
            "CREDENTIAL_STORE_UNAVAILABLE",
            "secret-tool is not available on this host",
            action="install secret-tool or re-run auth set --stdin --allow-file-store",
        )
    if allow_file_store:
        return FileCredentialStore()
    raise ClientError(
        "CREDENTIAL_STORE_UNAVAILABLE",
        "no OS credential backend exists on this platform",
        action="re-run auth set --stdin --allow-file-store to use the 0600 file store",
    )


def _select_read_store() -> CredentialStore:
    """Selection for read/delete paths: platform backend, else the file store.

    The --allow-file-store opt-in happens once at auth set time, so a host
    without any platform backend must still read, report and delete the
    credential it wrote: when selection reports CREDENTIAL_STORE_UNAVAILABLE
    the read paths fall back to the gated 0600 file store. The file store's
    owner/mode/link gates keep this fail-closed; any other selection error
    propagates unchanged.
    """
    try:
        return select_credential_store(platform=sys.platform, allow_file_store=False)
    except ClientError as exc:
        if exc.code != "CREDENTIAL_STORE_UNAVAILABLE":
            raise
        return FileCredentialStore()


def resolve_effective_token(
    *,
    environ: dict[str, str] | None = None,
    store: CredentialStore | None = None,
) -> str | None:
    """The one helper request-time callers use: CARD_OS_TOKEN, then store.

    The environment override is ephemeral: it is read here, takes precedence
    over any stored credential, is never persisted and is never copied into
    errors. When no platform backend exists, the store read falls back to
    the gated 0600 file store (see _select_read_store).
    """
    environment = os.environ if environ is None else environ
    override = environment.get("CARD_OS_TOKEN")
    if override:
        return override
    if store is None:
        try:
            store = _select_read_store()
        except ClientError:
            return None
    try:
        stored = store.get()
    except ClientError:
        raise
    except Exception:
        # Never propagate the original exception text: it could embed bytes
        # the backend handled.
        raise ClientError(
            "CREDENTIAL_STORE_UNAVAILABLE",
            "credential store read failed",
            action="re-run auth set to repair the stored credential",
        ) from None
    if stored is None:
        return None
    try:
        return stored.decode("utf-8")
    except UnicodeDecodeError:
        raise ClientError(
            "CREDENTIAL_STORE_UNSAFE",
            "stored credential is not valid UTF-8",
            action="re-run auth set to repair the stored credential",
        ) from None


def _parse_stdin_token(data: bytes) -> bytes:
    """One stripped line, 1..MAX_TOKEN_BYTES of UTF-8, no other newlines."""
    if data.endswith(b"\n"):
        data = data[:-1]
    if not data:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "no token was provided on stdin",
            action="pipe exactly one token line into auth set --stdin",
        )
    if b"\n" in data or b"\r" in data:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "token input must be a single line",
            action="pipe exactly one token line into auth set --stdin",
        )
    if len(data) > MAX_TOKEN_BYTES:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "token input exceeds the maximum accepted length",
            action="use a scoped Card OS token, not a file or multi-line blob",
        )
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "token input must be valid UTF-8",
            action="pipe exactly one token line into auth set --stdin",
        ) from None
    return data


# Injection seam for tests, mirroring _config: replaces backend selection so
# the suite never touches a real Keychain or secret service. The production
# CLI has no flag that can influence this value.
_credential_store_override: CredentialStore | None = None


def _auth_store(allow_file_store: bool) -> CredentialStore:
    if _credential_store_override is not None:
        return _credential_store_override
    return select_credential_store(
        platform=sys.platform, allow_file_store=allow_file_store
    )


def _auth_read_store() -> CredentialStore:
    """Store for status/delete: the opt-in already happened at auth set time."""
    if _credential_store_override is not None:
        return _credential_store_override
    return _select_read_store()


def _cmd_auth_set(*, allow_file_store: bool) -> dict[str, object]:
    # Exactly one read; bounded so an endless stream cannot exhaust memory.
    raw = sys.stdin.buffer.read(MAX_TOKEN_BYTES + 2)
    if len(raw) > MAX_TOKEN_BYTES + 1:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "token input exceeds the maximum accepted length",
            action="use a scoped Card OS token, not a file or multi-line blob",
        )
    parsed = _parse_stdin_token(raw)
    store = _auth_store(allow_file_store)
    store.set(parsed)
    return {"backend": store.backend_name, "status": "stored"}


def _cmd_auth_status() -> dict[str, object]:
    store = _auth_read_store()
    present = store.get() is not None
    return {
        "backend": store.backend_name,
        "credential": "present" if present else "absent",
        "status": "ok",
    }


def _cmd_auth_delete() -> dict[str, object]:
    store = _auth_read_store()
    deleted = store.delete()
    return {"backend": store.backend_name, "deleted": deleted, "status": "ok"}


# ---------------------------------------------------------------------------
# Packet and job commands
#
# Centralized route building, closed-envelope validation and stable state
# handling for the six packet/job commands. Every packet envelope is checked
# against the closed GenerationPacket schema and its packet_digest is
# recomputed exactly as server 0.3.1 before anything is saved or mutated.
# Claim/complete are doctor-gated and never blindly replayed: a transport
# failure after the POST triggers a status read instead.
# ---------------------------------------------------------------------------

PACKET_SCHEMA = "cognitive-card-generation-packet-v1"

_PACKET_STRING_KEYS = (
    "packet_id", "job_id", "execution_profile", "stage", "content_lock_digest",
    "registry_commit", "template_fingerprint", "age_profile",
    "language_projection", "issued_at", "expires_at", "schema",
)
_PACKET_LIST_KEYS = ("instructions", "forbidden_changes", "input_artifacts")
_PACKET_KEYS = frozenset(
    _PACKET_STRING_KEYS + _PACKET_LIST_KEYS + ("required_outputs",)
)
_REQUIRED_OUTPUT_KEYS = frozenset({"relative_path", "media_type", "max_bytes"})
_ENVELOPE_KEYS = frozenset(
    {"packet", "packet_digest", "claimed_by", "lease_expires_at",
     "created_at", "expired_at"}
)
_JOB_KEYS = frozenset(
    {"job_id", "execution_profile", "state", "content_lock_digest",
     "registry_commit", "template_fingerprint", "age_profile",
     "created_at", "updated_at"}
)
_JOB_STRING_KEYS = _JOB_KEYS
_EVENT_KEYS = frozenset(
    {"event_id", "job_id", "event_type", "actor", "reason", "details",
     "occurred_at"}
)
_EVENT_STRING_KEYS = ("job_id", "event_type", "actor", "reason", "occurred_at")

# Process-local doctor cache for the mutation gate; never persisted.
_doctor_cache: dict[str, object] | None = None


def recompute_packet_digest(packet: dict[str, object]) -> str:
    """Server 0.3.1 packet digest: sha256 over the canonical packet JSON."""
    return "sha256:" + hashlib.sha256(canonical_json(packet)).hexdigest()


def _id_segment(value: str, *, kind: str) -> str:
    """Validate an id as exactly one path segment and percent-encode it.

    The server contract accepts any single segment; the client only rejects
    what can never be a server-issued id. Empty values, control characters
    and path separators are malformed; whitespace or non-ASCII means the
    caller pasted a free-form concept, which this skill can never turn into
    a job.
    """
    if (
        not value
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)
        or "/" in value
        or "\\" in value
    ):
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            f"{kind} id is empty or contains characters that are forbidden in a path segment",
            action=f"pass the exact server-issued {kind} id",
        )
    if any(ch.isspace() or ord(ch) > 0x7E for ch in value):
        raise ClientError(
            "TRUSTED_UPSTREAM_REQUIRED",
            "free-form concepts cannot be turned into jobs by this client; "
            "a locked server packet is required",
            action="run packets list and use the id of a visible locked packet",
        )
    return urllib.parse.quote(value, safe="")


def _packet_route(packet_id: str, suffix: str = "") -> str:
    return f"{API_ROOT}/packets/{_id_segment(packet_id, kind='packet')}{suffix}"


def _job_route(job_id: str, suffix: str = "") -> str:
    return f"{API_ROOT}/jobs/{_id_segment(job_id, kind='job')}{suffix}"


def _validate_packet(packet: object) -> dict[str, object]:
    if not isinstance(packet, dict) or set(packet) != _PACKET_KEYS:
        raise _drift("packet document does not match the closed packet schema")
    for key in _PACKET_STRING_KEYS:
        if not isinstance(packet[key], str):
            raise _drift(f"packet field {key} is not a string")
    if packet["schema"] != PACKET_SCHEMA:
        raise _drift("packet document has an unexpected schema")
    for key in _PACKET_LIST_KEYS:
        items = packet[key]
        if not isinstance(items, list) or any(not isinstance(i, str) for i in items):
            raise _drift(f"packet field {key} is not a list of strings")
    required_outputs = packet["required_outputs"]
    if not isinstance(required_outputs, list):
        raise _drift("packet required_outputs is not a list")
    for output in required_outputs:
        if not isinstance(output, dict) or set(output) != _REQUIRED_OUTPUT_KEYS:
            raise _drift("packet required_outputs entry has an unexpected shape")
        if not isinstance(output["relative_path"], str) or not isinstance(
            output["media_type"], str
        ):
            raise _drift("packet required_outputs entry has malformed fields")
        if type(output["max_bytes"]) is not int or output["max_bytes"] < 1:
            raise _drift("packet required_outputs entry has a malformed max_bytes")
    return packet


def _validate_packet_envelope(document: object) -> dict[str, object]:
    """Closed envelope schema + digest recompute + claim/lease/expiry types."""
    if not isinstance(document, dict) or set(document) != _ENVELOPE_KEYS:
        raise _drift("packet envelope has an unexpected shape")
    packet = _validate_packet(document["packet"])
    digest = document["packet_digest"]
    if not isinstance(digest, str):
        raise _drift("packet envelope has a malformed packet_digest")
    if digest != recompute_packet_digest(packet):
        raise ClientError(
            "DIGEST_MISMATCH",
            "packet_digest does not match the recomputed packet digest",
            action="do not use this packet; report the server integrity failure",
        )
    # Claim/lease/expiry metadata is not covered by the digest; validate its
    # types separately.
    claimed_by = document["claimed_by"]
    lease_expires_at = document["lease_expires_at"]
    created_at = document["created_at"]
    expired_at = document["expired_at"]
    if claimed_by is not None and not isinstance(claimed_by, str):
        raise _drift("packet envelope has a malformed claimed_by")
    if lease_expires_at is not None and not isinstance(lease_expires_at, str):
        raise _drift("packet envelope has a malformed lease_expires_at")
    if not isinstance(created_at, str):
        raise _drift("packet envelope has a malformed created_at")
    if expired_at is not None and not isinstance(expired_at, str):
        raise _drift("packet envelope has a malformed expired_at")
    return document


def _validate_job(document: object) -> dict[str, object]:
    if not isinstance(document, dict) or set(document) != _JOB_KEYS:
        raise _drift("job document has an unexpected shape")
    for key in _JOB_STRING_KEYS:
        if not isinstance(document[key], str):
            raise _drift(f"job field {key} is not a string")
    return document


def _validate_events(document: object) -> list[object]:
    if not isinstance(document, dict) or not isinstance(document.get("events"), list):
        raise _drift("job events document has an unexpected shape")
    events = document["events"]
    for event in events:
        if not isinstance(event, dict) or set(event) != _EVENT_KEYS:
            raise _drift("job event has an unexpected shape")
        if type(event["event_id"]) is not int:
            raise _drift("job event has a malformed event_id")
        if not isinstance(event["details"], dict):
            raise _drift("job event has malformed details")
        for key in _EVENT_STRING_KEYS:
            if not isinstance(event[key], str):
                raise _drift(f"job event field {key} is not a string")
    return events


def _cli_token() -> str:
    """Resolve the request credential; fail locally before any HTTP."""
    effective = resolve_effective_token(store=_credential_store_override)
    if effective is None:
        raise ClientError(
            "AUTH_REQUIRED",
            "no client credential is configured",
            action="run auth set --stdin to store a scoped token "
            "(or set CARD_OS_TOKEN for a single run)",
        )
    return effective


def _require_compatible_server() -> None:
    """Doctor gate for protected mutations, cached within the process."""
    global _doctor_cache
    if _doctor_cache is None:
        _doctor_cache = doctor()


def _mutation_state_read(packet_id: str, action: str, *, token: str) -> ClientError:
    """Build the failure for an ambiguous mutation: read state, never replay."""
    observation: str | None = None
    try:
        _, document = request_json("GET", _packet_route(packet_id), token=token)
        envelope = _validate_packet_envelope(document)
        if action == "complete":
            job_id = str(envelope["packet"]["job_id"])
            _, job_document = request_json("GET", _job_route(job_id), token=token)
            job = _validate_job(job_document)
            observation = f"job state is {_bounded_text(job['state']) or 'unknown'}"
        else:
            claimed_by = _bounded_text(envelope["claimed_by"]) or "none"
            lease = _bounded_text(envelope["lease_expires_at"]) or "none"
            observation = f"claimed_by={claimed_by} lease_expires_at={lease}"
    except ClientError:
        observation = None
    if observation is None:
        return ClientError(
            "HTTP_ERROR",
            f"packet {action} did not complete and the server state could not "
            "be read afterwards",
            action="check packets list / jobs status before any retry; "
            "a mutation is never blindly replayed",
        )
    return ClientError(
        "HTTP_ERROR",
        f"packet {action} did not complete; observed server state afterwards: "
        f"{observation}",
        action="refresh state with packets list / jobs status; "
        "re-run only if the transition did not happen",
    )


def _post_packet_mutation(
    path: str, packet_id: str, action: str, *, token: str
) -> dict[str, object]:
    try:
        _, document = request_json("POST", path, token=token, body=canonical_json({}))
    except ClientError as exc:
        if exc.code == "HTTP_ERROR" and exc.status is None:
            # The request may or may not have reached the server: reconcile
            # with a status read instead of replaying the POST.
            raise _mutation_state_read(packet_id, action, token=token) from None
        raise
    return _validate_packet_envelope(document)


def _packet_summary(envelope: dict[str, object]) -> dict[str, object]:
    packet = envelope["packet"]
    return {
        "packet_id": packet["packet_id"],
        "job_id": packet["job_id"],
        "stage": packet["stage"],
        "execution_profile": packet["execution_profile"],
        "age_profile": packet["age_profile"],
        "expires_at": packet["expires_at"],
        "packet_digest": envelope["packet_digest"],
    }


def _cmd_packets_list(*, token: str | None = None) -> dict[str, object]:
    if token is None:
        token = _cli_token()
    _, document = request_json("GET", f"{API_ROOT}/packets/available", token=token)
    raw_packets = document.get("packets")
    if not isinstance(raw_packets, list):
        raise _drift("packets document has a malformed packets list")
    envelopes = [_validate_packet_envelope(item) for item in raw_packets]
    if not envelopes:
        raise ClientError(
            "TRUSTED_UPSTREAM_REQUIRED",
            "no locked generation packet is visible to this credential",
            action="this client cannot create free-form jobs; "
            "a locked packet must be issued upstream first",
        )
    return {
        "status": "ok",
        "packets": [_packet_summary(envelope) for envelope in envelopes],
    }


def _cmd_packets_claim(
    packet_id: str, *, token: str | None = None
) -> dict[str, object]:
    path = _packet_route(packet_id, "/claim")  # validates the id first
    if token is None:
        token = _cli_token()
    _require_compatible_server()
    envelope = _post_packet_mutation(path, packet_id, "claim", token=token)
    packet = envelope["packet"]
    return {
        "status": "claimed",
        "packet_id": packet["packet_id"],
        "job_id": packet["job_id"],
        "lease_expires_at": envelope["lease_expires_at"],
        "packet_digest": envelope["packet_digest"],
    }


def _write_new_private_file(path: Path, payload: bytes) -> None:
    """O_EXCL|O_NOFOLLOW create at mode 0600; never overwrite, never follow."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "output file already exists; refusing to overwrite it",
            action="choose a new --output path or remove the existing file",
        ) from None
    except OSError:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "output path is not writable (missing directory or not a regular file target)",
            action="choose a writable --output path in an existing directory",
        ) from None
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        path.unlink(missing_ok=True)
        raise
    os.close(descriptor)


def _cmd_packets_get(
    packet_id: str, output: str, *, token: str | None = None
) -> dict[str, object]:
    path = _packet_route(packet_id)  # validates the id first
    if token is None:
        token = _cli_token()
    _, document = request_json("GET", path, token=token)
    envelope = _validate_packet_envelope(document)
    packet = envelope["packet"]
    # The saved bytes are exactly the canonical packet JSON the digest covers.
    _write_new_private_file(Path(output), canonical_json(packet))
    return {
        "status": "saved",
        "packet_id": packet["packet_id"],
        "job_id": packet["job_id"],
        "packet_digest": envelope["packet_digest"],
        "output": output,
    }


def _cmd_packets_complete(
    packet_id: str, *, token: str | None = None
) -> dict[str, object]:
    path = _packet_route(packet_id, "/complete")  # validates the id first
    if token is None:
        token = _cli_token()
    _require_compatible_server()
    envelope = _post_packet_mutation(path, packet_id, "complete", token=token)
    packet = envelope["packet"]
    return {
        "status": "completed",
        "packet_id": packet["packet_id"],
        "job_id": packet["job_id"],
        "packet_digest": envelope["packet_digest"],
        "note": "state transition recorded only; result upload and review "
        "are separate later steps",
    }


def _cmd_jobs_status(job_id: str, *, token: str | None = None) -> dict[str, object]:
    path = _job_route(job_id)  # validates the id first
    if token is None:
        token = _cli_token()
    _, document = request_json("GET", path, token=token)
    return {"status": "ok", "job": _validate_job(document)}


def _cmd_jobs_events(job_id: str, *, token: str | None = None) -> dict[str, object]:
    path = _job_route(job_id, "/events")  # validates the id first
    if token is None:
        token = _cli_token()
    _, document = request_json("GET", path, token=token)
    return {
        "status": "ok",
        "job_id": job_id,
        "events": _validate_events(document),
    }


# ---------------------------------------------------------------------------
# Result validation and upload
#
# ``results submit`` closes the local generation loop: the directory is
# walked without following links, every declared required output must appear
# exactly once, media types come only from the digest-covered packet
# declarations, all decoded/encoded budgets are enforced, and every decoded
# payload plus all metadata strings and the final canonical body are scanned
# for the raw token and any complete credential shape. One canonical request
# body is built around the generated_at fixed by the private
# cognitive-card-submit-attempt-v1 journal, its frozen idempotency key is
# computed once, complete runs before the upload, and only the exact same
# bytes with the same key may be replayed (once, after a status read). The
# acceptance receipt is re-verified against the local bytes; a staged
# candidate is never a publication.
# ---------------------------------------------------------------------------

RESULT_SCHEMA = "cognitive-card-generation-result-v1"
ATTEMPT_SCHEMA = "cognitive-card-submit-attempt-v1"
CLIENT_SURFACE = "codex-cli"

# Server 0.3.1 budgets (c2a898c): http/config.py
# DEFAULT_MAX_DECODED_PAYLOAD_BYTES and http/schemas.py
# MAX_ENCODED_PAYLOAD_CHARACTERS.
MAX_DECODED_ARTIFACT_BYTES = 20 * 1024 * 1024
MAX_RESULT_BODY_BYTES = 28 * 1024 * 1024
MAX_ATTEMPT_FILE_BYTES = 64 * 1024

# http/schemas.py RequiredOutputRequest caps max_bytes at 20 MiB per file.
_MAX_DECLARED_FILE_BYTES = 20 * 1024 * 1024

# subscriber/media.py ALLOWED_ARTIFACT_MEDIA_TYPES at c2a898c.
ALLOWED_ARTIFACT_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "text/markdown",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
)

_RESULT_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_ATTEMPT_KEY_RE = re.compile(r"ccos-v1-[0-9a-f]{64}")
_GENERATED_AT_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z"
)

# Safe shape source: a prefix plus character classes, never a complete
# credential. Matches any full ccos_v1.<32 hex>.<url-safe> credential.
_CREDENTIAL_SHAPE_RE = re.compile(rb"ccos_v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+")

_RECEIPT_KEYS = frozenset(
    {"packet_id", "result_digest", "staged_artifacts", "accepted_at", "replayed"}
)
_STAGED_KEYS = frozenset({"relative_path", "storage_key", "sha256", "size_bytes"})
_ATTEMPT_KEYS = frozenset(
    {"schema", "packet_id", "generated_at", "body_sha256", "idempotency_key",
     "content_lock_digest", "artifacts"}
)
_ATTEMPT_ARTIFACT_KEYS = frozenset(
    {"relative_path", "media_type", "sha256", "size_bytes"}
)


def result_idempotency_key(packet_id: str, canonical_body: bytes) -> str:
    """Frozen formula: ccos-v1- + sha256(packet_id + "\\n" + body) hex."""
    return "ccos-v1-" + hashlib.sha256(
        packet_id.encode("utf-8") + b"\n" + canonical_body
    ).hexdigest()


def _credential_in_result(category: str) -> ClientError:
    # Only the code and the path category are reported; matched bytes,
    # fingerprints and surrounding context never leave the scan.
    return ClientError(
        "CREDENTIAL_IN_RESULT",
        f"credential-shaped content detected in the {category}; "
        "the result was not uploaded",
        action="remove every credential from the generated files and "
        "regenerate them; never upload tokens",
    )


def _scan_for_credentials(data: bytes, token: bytes, category: str) -> None:
    """Reject the exact raw token or any complete credential shape."""
    if token and token in data:
        raise _credential_in_result(category)
    if _CREDENTIAL_SHAPE_RE.search(data) is not None:
        raise _credential_in_result(category)


def _scan_value_for_credentials(value: object, token: bytes, category: str) -> None:
    """Recursively scan every string in a JSON-shaped value."""
    if isinstance(value, str):
        _scan_for_credentials(value.encode("utf-8"), token, category)
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan_value_for_credentials(key, token, category)
            _scan_value_for_credentials(item, token, category)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _scan_value_for_credentials(item, token, category)


def _unsafe_path(message: str) -> ClientError:
    # Path material is never echoed: an on-disk name could itself carry
    # credential-shaped bytes that must not reach the output.
    return ClientError(
        "UNSAFE_ARTIFACT_PATH",
        message,
        action="fix the result directory so every file is a regular file "
        "with a safe relative POSIX path",
    )


def _require_safe_declared_path(relative_path: str) -> None:
    """Server 0.3.1 _require_safe_artifact_path rule, plus control chars."""
    if (
        not relative_path
        or relative_path.startswith("/")
        or "\\" in relative_path
        or "\0" in relative_path
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in relative_path)
    ):
        raise _unsafe_path("the packet declares an unsafe required output path")
    if any(segment in ("", ".", "..") for segment in relative_path.split("/")):
        raise _unsafe_path("the packet declares an unsafe required output path")


def _require_safe_disk_name(relative_path: str) -> None:
    if "\\" in relative_path or any(
        ord(ch) < 0x20 or ord(ch) == 0x7F for ch in relative_path
    ):
        raise _unsafe_path(
            "result directory contains a file name that is unsafe to upload"
        )


def _check_normalization_collisions(relative_paths: list[str]) -> None:
    """Reject two distinct paths that collide after Unicode normalization."""
    seen: dict[str, str] = {}
    for relative_path in relative_paths:
        normalized = unicodedata.normalize("NFC", relative_path)
        if normalized in seen and seen[normalized] != relative_path:
            raise _unsafe_path(
                "result directory contains paths that collide after "
                "Unicode normalization"
            )
        seen[normalized] = relative_path


def _walk_result_files(root: Path) -> dict[str, os.stat_result]:
    """Walk without following links; return regular files by POSIX rel path."""
    try:
        root_info = os.lstat(root)
    except OSError:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "result directory does not exist",
            action="pass --directory pointing at the generated result files",
        ) from None
    if not stat.S_ISDIR(root_info.st_mode):  # lstat: a symlink is not a dir
        if stat.S_ISLNK(root_info.st_mode):
            raise _unsafe_path("result directory must not be a symbolic link")
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "result path is not a directory",
            action="pass --directory pointing at the generated result files",
        )
    found: dict[str, os.stat_result] = {}
    stack: list[tuple[str, Path]] = [("", root)]
    while stack:
        prefix, current = stack.pop()
        try:
            with os.scandir(current) as entries:
                batch = list(entries)
        except OSError:
            raise ClientError(
                "REQUEST_VALIDATION_FAILED",
                "result directory could not be read",
                action="fix permissions on the result directory and re-run",
            ) from None
        for entry in batch:
            relative = entry.name if not prefix else prefix + "/" + entry.name
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                stack.append((relative, Path(entry.path)))
                continue
            if not stat.S_ISREG(info.st_mode):
                # Symlinks, devices, FIFOs and sockets are never followed
                # and never read.
                raise _unsafe_path(
                    "result directory contains a non-regular or linked entry"
                )
            _require_safe_disk_name(relative)
            found[relative] = info
    _check_normalization_collisions(sorted(found))
    return found


def _read_artifact_bytes(path: Path, expected_size: int) -> bytes:
    """Read exactly expected_size bytes without following links."""
    try:
        descriptor = os.open(path, os.O_RDONLY | _O_NOFOLLOW)
    except OSError:
        raise _unsafe_path(
            "result file could not be opened without following links"
        ) from None
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise _unsafe_path("result entry is not a regular file")
        payload = handle.read(expected_size + 1)
    if len(payload) != expected_size:
        raise ClientError(
            "ARTIFACT_SIZE_MISMATCH",
            "a result file changed size while it was being read",
            action="regenerate the result files and re-run results submit",
        )
    return payload


def _matches_declared_signature(media_type: str, payload: bytes) -> bool:
    """Stdlib image signature checks mirroring the server media policy."""
    if media_type == "image/png":
        return payload.startswith(b"\x89PNG\r\n\x1a\n")
    if media_type == "image/jpeg":
        return payload.startswith(b"\xff\xd8\xff")
    if media_type == "image/webp":
        return (
            len(payload) >= 12
            and payload[:4] == b"RIFF"
            and payload[8:12] == b"WEBP"
        )
    return True


def validate_result_directory(
    packet: dict[str, object], directory: Path
) -> tuple[dict[str, object], bytes]:
    """Close the result directory against the packet's required_outputs.

    Returns (descriptor, decoded): the descriptor carries the sorted
    artifact entries (relative_path, media_type, sha256, size_bytes,
    payload_base64) plus empty source_records/operator_notes, and decoded is
    the concatenation of all decoded artifact bytes in sorted path order.
    """
    required_outputs = packet["required_outputs"]  # closed packet schema
    if not isinstance(required_outputs, list) or not required_outputs:
        raise _drift("packet declares no required outputs")
    declarations: dict[str, dict[str, object]] = {}
    for output in required_outputs:
        relative_path = output["relative_path"]
        _require_safe_declared_path(relative_path)
        if output["max_bytes"] > _MAX_DECLARED_FILE_BYTES:
            raise _drift("packet declares a max_bytes above the server schema limit")
        if relative_path in declarations:
            raise ClientError(
                "UNDECLARED_ARTIFACT",
                "the packet declares the same required output path twice",
                action="do not use this packet; report the server integrity failure",
            )
        declarations[relative_path] = output
    root = Path(directory)
    found = _walk_result_files(root)
    if set(declarations) - set(found):
        raise ClientError(
            "MISSING_ARTIFACT",
            "a declared required output is missing from the result directory",
            action="generate every required output declared by the packet",
        )
    if set(found) - set(declarations):
        raise ClientError(
            "UNDECLARED_ARTIFACT",
            "the result directory contains files the packet did not declare",
            action="remove every file that is not a declared required output",
        )
    artifacts: list[dict[str, object]] = []
    decoded_parts: list[bytes] = []
    decoded_total = 0
    for relative_path in sorted(declarations):
        declaration = declarations[relative_path]
        info = found[relative_path]
        if info.st_size > declaration["max_bytes"]:
            raise ClientError(
                "ARTIFACT_TOO_LARGE",
                "a result file exceeds its declared max_bytes",
                action="shrink the file below the declared max_bytes",
            )
        decoded_total += info.st_size
        if decoded_total > MAX_DECODED_ARTIFACT_BYTES:
            raise ClientError(
                "PAYLOAD_TOO_LARGE",
                "decoded artifacts exceed the 20 MiB total budget",
                action="reduce the total size of the generated files",
            )
        payload = _read_artifact_bytes(root / relative_path, info.st_size)
        media_type = declaration["media_type"]
        if media_type not in ALLOWED_ARTIFACT_MEDIA_TYPES:
            raise ClientError(
                "UNSUPPORTED_ARTIFACT_MEDIA_TYPE",
                "the packet declares a media type the server never accepts",
                action="do not use this packet; report the server integrity failure",
            )
        if not _matches_declared_signature(media_type, payload):
            raise ClientError(
                "INVALID_ARTIFACT_MEDIA",
                "a result file does not match its declared media type signature",
                action="regenerate the file in the declared media type",
            )
        artifacts.append(
            {
                "relative_path": relative_path,
                "media_type": media_type,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "payload_base64": base64.b64encode(payload).decode("ascii"),
            }
        )
        decoded_parts.append(payload)
    descriptor = {
        "artifacts": artifacts,
        "source_records": [],
        "operator_notes": "",
    }
    return descriptor, b"".join(decoded_parts)


def _utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _parse_rfc3339(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _attempts_directory() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    if not state_home:
        home = os.environ.get("HOME") or str(Path.home())
        state_home = os.path.join(home, ".local", "state")
    return Path(state_home) / "cognitive-card-os" / "attempts"


def _attempt_file_path(packet_id: str) -> Path:
    _id_segment(packet_id, kind="packet")  # one safe path segment, or fail
    if packet_id in (".", ".."):
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "packet id cannot be used as a state file name",
            action="pass the exact server-issued packet id",
        )
    file_name = packet_id + ".json"
    if Path(file_name).name != file_name:
        raise ClientError(
            "REQUEST_VALIDATION_FAILED",
            "packet id cannot be used as a state file name",
            action="pass the exact server-issued packet id",
        )
    return _attempts_directory() / file_name


def _attempt_error(message: str) -> ClientError:
    # Attempt-state errors never echo stored content.
    return ClientError(
        "ATTEMPT_BODY_CHANGED",
        message,
        action="stop and reconcile: the recorded submit attempt no longer "
        "matches the current result; inspect jobs status before changing "
        "anything, and never edit the attempt state by hand",
    )


def _verify_attempt_directory(directory: Path) -> None:
    info = os.lstat(directory)
    if not stat.S_ISDIR(info.st_mode):  # lstat: a symlink is not a dir
        raise _attempt_error("attempt state directory is not a real directory")
    if info.st_uid != os.getuid():
        raise _attempt_error("attempt state directory is owned by another user")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise _attempt_error("attempt state directory must have mode 0700")


def _validate_attempt_journal(
    journal: object, packet_id: str
) -> dict[str, object]:
    if not isinstance(journal, dict) or set(journal) != _ATTEMPT_KEYS:
        raise _attempt_error("attempt state has an unexpected shape")
    if journal["schema"] != ATTEMPT_SCHEMA:
        raise _attempt_error("attempt state has an unexpected schema")
    if journal["packet_id"] != packet_id:
        raise _attempt_error("attempt state belongs to a different packet")
    generated_at = journal["generated_at"]
    if (
        not isinstance(generated_at, str)
        or _GENERATED_AT_RE.fullmatch(generated_at) is None
        or _parse_rfc3339(generated_at) is None
    ):
        raise _attempt_error("attempt state has a malformed generated_at")
    body_sha256 = journal["body_sha256"]
    if not isinstance(body_sha256, str) or _HEX64_RE.fullmatch(body_sha256) is None:
        raise _attempt_error("attempt state has a malformed body digest")
    key = journal["idempotency_key"]
    if not isinstance(key, str) or _ATTEMPT_KEY_RE.fullmatch(key) is None:
        raise _attempt_error("attempt state has a malformed idempotency key")
    content_lock_digest = journal["content_lock_digest"]
    if (
        not isinstance(content_lock_digest, str)
        or _RESULT_DIGEST_RE.fullmatch(content_lock_digest) is None
    ):
        raise _attempt_error("attempt state has a malformed content lock digest")
    artifacts = journal["artifacts"]
    if not isinstance(artifacts, list):
        raise _attempt_error("attempt state has malformed artifacts")
    previous: str | None = None
    for entry in artifacts:
        if not isinstance(entry, dict) or set(entry) != _ATTEMPT_ARTIFACT_KEYS:
            raise _attempt_error("attempt state has a malformed artifact entry")
        relative_path = entry["relative_path"]
        media_type = entry["media_type"]
        sha256 = entry["sha256"]
        size_bytes = entry["size_bytes"]
        if not isinstance(relative_path, str) or not relative_path:
            raise _attempt_error("attempt state has a malformed artifact entry")
        if media_type not in ALLOWED_ARTIFACT_MEDIA_TYPES:
            raise _attempt_error("attempt state has a malformed artifact entry")
        if not isinstance(sha256, str) or _HEX64_RE.fullmatch(sha256) is None:
            raise _attempt_error("attempt state has a malformed artifact entry")
        if type(size_bytes) is not int or size_bytes < 0:
            raise _attempt_error("attempt state has a malformed artifact entry")
        if previous is not None and relative_path <= previous:
            raise _attempt_error("attempt state artifacts are not strictly sorted")
        previous = relative_path
    return journal


def _read_attempt(path: Path, packet_id: str) -> dict[str, object] | None:
    """Verified attempt journal, or None when no attempt was ever recorded."""
    try:
        _verify_attempt_directory(path.parent)
    except FileNotFoundError:
        return None
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):  # lstat: a symlink is not regular
        raise _attempt_error("attempt state is not a regular file")
    if info.st_uid != os.getuid():
        raise _attempt_error("attempt state is owned by another user")
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise _attempt_error("attempt state must have mode 0600")
    if info.st_size > MAX_ATTEMPT_FILE_BYTES:
        raise _attempt_error("attempt state exceeds the maximum accepted size")
    descriptor = os.open(path, os.O_RDONLY | _O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as handle:
        raw = handle.read(MAX_ATTEMPT_FILE_BYTES + 1)
    if len(raw) > MAX_ATTEMPT_FILE_BYTES:
        raise _attempt_error("attempt state exceeds the maximum accepted size")
    try:
        journal = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _attempt_error("attempt state is not valid JSON") from None
    return _validate_attempt_journal(journal, packet_id)


def _write_attempt(path: Path, journal: dict[str, object]) -> None:
    """Create the attempt journal atomically; never overwrite an existing one."""
    parent = path.parent
    os.makedirs(parent, mode=0o700, exist_ok=True)
    _verify_attempt_directory(parent)
    payload = canonical_json(journal)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
    for _ in range(16):
        candidate = parent / (".attempt-" + secrets.token_hex(8) + ".tmp")
        try:
            descriptor = os.open(candidate, flags, 0o600)
            break
        except FileExistsError:
            continue
    else:
        raise _attempt_error("could not allocate a private temp file for attempt state")
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        candidate.unlink(missing_ok=True)
        raise
    os.close(descriptor)
    try:
        # Atomic create-exclusive: an existing journal always wins.
        os.link(candidate, path)
    except FileExistsError:
        candidate.unlink(missing_ok=True)
        raise
    candidate.unlink(missing_ok=True)
    dir_descriptor = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(dir_descriptor)
    finally:
        os.close(dir_descriptor)


def _build_checked_body(body_factory: Callable[[str], bytes], generated_at: str) -> bytes:
    body = body_factory(generated_at)
    if len(body) > MAX_RESULT_BODY_BYTES:
        raise ClientError(
            "PAYLOAD_TOO_LARGE",
            "the canonical result body exceeds the 28 MiB budget",
            action="reduce the total artifact size; the server never accepts "
            "a larger body",
        )
    return body


def load_or_create_attempt(
    packet_id: str,
    artifacts: tuple[dict[str, object], ...],
    body_factory: Callable[[str], bytes],
) -> tuple[bytes, str]:
    """Return (canonical_body, idempotency_key) pinned by the attempt journal.

    The first submit records generated_at, the body digest, the key, the
    content lock digest and the sorted artifact metadata in a private 0600
    journal BEFORE any complete or upload. Every later submit with the same
    packet must rebuild byte-identical body and key from the recorded
    generated_at; any change stops locally with ATTEMPT_BODY_CHANGED instead
    of silently starting a second logical submit.
    """
    path = _attempt_file_path(packet_id)
    journal = _read_attempt(path, packet_id)
    if journal is None:
        generated_at = _utc_now_rfc3339()
        body = _build_checked_body(body_factory, generated_at)
        key = result_idempotency_key(packet_id, body)
        # The content lock digest is recorded so a cross-invocation replay
        # can rebuild the byte-identical body after the accepted packet
        # becomes invisible to this claimant. It is packet metadata, never
        # payload bytes.
        content_lock_digest = json.loads(body.decode("utf-8"))[
            "content_lock_digest"
        ]
        fresh = {
            "schema": ATTEMPT_SCHEMA,
            "packet_id": packet_id,
            "generated_at": generated_at,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "idempotency_key": key,
            "content_lock_digest": content_lock_digest,
            "artifacts": [dict(entry) for entry in artifacts],
        }
        try:
            _write_attempt(path, fresh)
        except FileExistsError:
            # Lost a creation race: verify the winning journal instead.
            journal = _read_attempt(path, packet_id)
        else:
            return body, key
    current = [dict(entry) for entry in artifacts]
    if journal["artifacts"] != current:
        raise _attempt_error(
            "the result artifacts changed since the first submit attempt"
        )
    body = _build_checked_body(body_factory, str(journal["generated_at"]))
    if hashlib.sha256(body).hexdigest() != journal["body_sha256"]:
        raise _attempt_error(
            "the rebuilt result body no longer matches the recorded attempt"
        )
    key = result_idempotency_key(packet_id, body)
    if key != journal["idempotency_key"]:
        raise _attempt_error(
            "the rebuilt idempotency key no longer matches the recorded attempt"
        )
    return body, key


def _require_current_claim(envelope: dict[str, object]) -> None:
    """Local claimant/lease/expiry recheck before any result mutation."""
    if envelope["expired_at"] is not None:
        raise ClientError(
            "PACKET_EXPIRED",
            "the packet has been expired by the server",
            action="run packets list to find a reissued locked packet",
        )
    packet = envelope["packet"]
    now = datetime.now(timezone.utc)
    expires_at = _parse_rfc3339(packet["expires_at"])
    if expires_at is None:
        raise _drift("packet has a malformed expires_at")
    if expires_at <= now:
        raise ClientError(
            "PACKET_EXPIRED",
            "the packet has passed its expires_at",
            action="run packets list to find a reissued locked packet",
        )
    if envelope["claimed_by"] is None:
        raise ClientError(
            "LEASE_OWNER_MISMATCH",
            "the packet is not currently claimed",
            action="run packets claim again before submitting a result",
        )
    lease = envelope["lease_expires_at"]
    if lease is None:
        raise ClientError(
            "LEASE_EXPIRED",
            "the packet has no active lease",
            action="run packets claim again before submitting a result",
        )
    lease_at = _parse_rfc3339(lease)
    if lease_at is None:
        raise _drift("packet envelope has a malformed lease_expires_at")
    if lease_at <= now:
        raise ClientError(
            "LEASE_EXPIRED",
            "the packet lease has expired",
            action="run packets claim again to renew the lease",
        )


def _validate_result_receipt(
    document: object,
    packet_id: str,
    artifacts: tuple[dict[str, object], ...],
) -> dict[str, object]:
    """Re-verify the acceptance receipt against the local artifact bytes.

    result_digest is an opaque server-generated identifier: only its exact
    sha256:<64 lowercase hex> shape is validated here, never any relation to
    the canonical request body. Every staged artifact must match the local
    relative path, SHA-256, size and content-addressed storage key.
    """
    if not isinstance(document, dict) or set(document) != _RECEIPT_KEYS:
        raise _drift("result receipt has an unexpected shape")
    if not isinstance(document["packet_id"], str) or document["packet_id"] != packet_id:
        raise _drift("result receipt is for a different packet")
    result_digest = document["result_digest"]
    if not isinstance(result_digest, str) or _RESULT_DIGEST_RE.fullmatch(result_digest) is None:
        raise _drift("result receipt has a malformed result_digest")
    if not isinstance(document["accepted_at"], str):
        raise _drift("result receipt has a malformed accepted_at")
    if type(document["replayed"]) is not bool:
        raise _drift("result receipt has a malformed replayed flag")
    staged = document["staged_artifacts"]
    if not isinstance(staged, list):
        raise _drift("result receipt has malformed staged artifacts")
    expected = {entry["relative_path"]: entry for entry in artifacts}
    seen: set[str] = set()
    for entry in staged:
        if not isinstance(entry, dict) or set(entry) != _STAGED_KEYS:
            raise _drift("staged artifact has an unexpected shape")
        relative_path = entry["relative_path"]
        if (
            not isinstance(relative_path, str)
            or relative_path not in expected
            or relative_path in seen
        ):
            raise ClientError(
                "STAGED_METADATA_MISMATCH",
                "staged artifacts do not match the uploaded artifact set",
                action="stop and report the server integrity failure",
            )
        seen.add(relative_path)
        local = expected[relative_path]
        sha256 = entry["sha256"]
        if not isinstance(sha256, str) or _HEX64_RE.fullmatch(sha256) is None:
            raise _drift("staged artifact has a malformed sha256")
        if sha256 != local["sha256"]:
            raise ClientError(
                "CANDIDATE_DIGEST_MISMATCH",
                "a staged artifact digest does not match the local bytes",
                action="stop and report the server integrity failure",
            )
        if type(entry["size_bytes"]) is not int or entry["size_bytes"] != local["size_bytes"]:
            raise ClientError(
                "STAGED_METADATA_MISMATCH",
                "a staged artifact size does not match the local bytes",
                action="stop and report the server integrity failure",
            )
        if entry["storage_key"] != f"sha256/{sha256[:2]}/{sha256}":
            raise ClientError(
                "INVALID_STORAGE_KEY",
                "a staged artifact storage key is not the content-addressed key",
                action="stop and report the server integrity failure",
            )
    if seen != set(expected):
        raise ClientError(
            "STAGED_METADATA_MISMATCH",
            "staged artifacts do not match the uploaded artifact set",
            action="stop and report the server integrity failure",
        )
    return document


def _post_result(
    packet_id: str, body: bytes, key: str, *, token: str
) -> dict[str, object]:
    """POST the immutable result body with its frozen idempotency key.

    A timeout leaves the upload ambiguous: the only legal retry is the exact
    same byte string with the same Idempotency-Key, at most once, and only
    after a status read. If the packet is no longer visible the result may
    already be accepted, and the same-key replay is still the only safe probe.
    """
    path = _packet_route(packet_id, "/results")
    try:
        status, document = request_json(
            "POST", path, token=token, body=body, idempotency_key=key
        )
    except ClientError as exc:
        if exc.code != "HTTP_ERROR" or exc.status is not None:
            raise
        try:
            _, envelope_document = request_json(
                "GET", _packet_route(packet_id), token=token
            )
            _validate_packet_envelope(envelope_document)
        except ClientError as read_error:
            if read_error.code != "PACKET_NOT_FOUND":
                raise ClientError(
                    "HTTP_ERROR",
                    "result upload did not complete and the server state "
                    "could not be read afterwards",
                    action="run packets list / jobs status before any retry; "
                    "only the exact same submit may be replayed",
                ) from None
        status, document = request_json(
            "POST", path, token=token, body=body, idempotency_key=key
        )
    if status not in (200, 201):
        raise _drift(f"result upload returned an unexpected HTTP status {status}")
    return document


def _replay_attempt_result(
    packet_id: str,
    directory: Path,
    *,
    token: str,
    original_error: ClientError,
) -> dict[str, object]:
    """Replay a recorded submit after the accepted packet became invisible.

    Server 0.3.1 hides an accepted packet from its claimant, so the
    pre-flight GET fails with PACKET_NOT_FOUND. A valid attempt journal
    proves this client already built exactly one immutable body for this
    packet: re-verify the directory against the journal, rebuild the
    byte-identical body and key, and replay them. The server's idempotency
    layer answers before any state check, so the replay returns the stored
    receipt with replayed=true; a never-submitted packet keeps failing
    closed with the original PACKET_NOT_FOUND, and any local mismatch stops
    with ATTEMPT_BODY_CHANGED before any upload.
    """
    journal = _read_attempt(_attempt_file_path(packet_id), packet_id)
    if journal is None:
        raise original_error
    root = Path(directory)
    found = _walk_result_files(root)
    recorded = journal["artifacts"]
    if {str(entry["relative_path"]) for entry in recorded} != set(found):
        raise _attempt_error(
            "the result directory no longer matches the recorded attempt"
        )
    token_bytes = token.encode("utf-8")
    artifacts: list[dict[str, object]] = []
    decoded_parts: list[bytes] = []
    for entry in recorded:  # journal artifact order is strictly sorted
        relative_path = str(entry["relative_path"])
        try:
            _require_safe_declared_path(relative_path)
        except ClientError:
            raise _attempt_error(
                "attempt state records an unsafe artifact path"
            ) from None
        media_type = str(entry["media_type"])
        info = found[relative_path]
        if info.st_size != entry["size_bytes"]:
            raise _attempt_error(
                "a result file size no longer matches the recorded attempt"
            )
        payload = _read_artifact_bytes(root / relative_path, info.st_size)
        sha256 = hashlib.sha256(payload).hexdigest()
        if sha256 != entry["sha256"]:
            raise _attempt_error(
                "a result file digest no longer matches the recorded attempt"
            )
        _scan_for_credentials(
            relative_path.encode("utf-8"), token_bytes, "artifact relative path"
        )
        _scan_for_credentials(
            media_type.encode("utf-8"), token_bytes, "artifact media metadata"
        )
        artifacts.append(
            {
                "relative_path": relative_path,
                "media_type": media_type,
                "sha256": sha256,
                "size_bytes": len(payload),
                "payload_base64": base64.b64encode(payload).decode("ascii"),
            }
        )
        decoded_parts.append(payload)
    _scan_for_credentials(b"".join(decoded_parts), token_bytes, "artifact payload")

    def body_factory(generated_at: str) -> bytes:
        return canonical_json(
            {
                "schema": RESULT_SCHEMA,
                "content_lock_digest": journal["content_lock_digest"],
                "skill_release": SKILL_RELEASE,
                "client_surface": CLIENT_SURFACE,
                "generated_at": generated_at,
                "artifacts": artifacts,
                "source_records": [],
                "operator_notes": "",
            }
        )

    body = _build_checked_body(body_factory, str(journal["generated_at"]))
    if hashlib.sha256(body).hexdigest() != journal["body_sha256"]:
        raise _attempt_error(
            "the rebuilt result body no longer matches the recorded attempt"
        )
    key = result_idempotency_key(packet_id, body)
    if key != journal["idempotency_key"]:
        raise _attempt_error(
            "the rebuilt idempotency key no longer matches the recorded attempt"
        )
    _scan_for_credentials(body, token_bytes, "request body")
    artifacts_meta = tuple(
        {
            "relative_path": artifact["relative_path"],
            "media_type": artifact["media_type"],
            "sha256": artifact["sha256"],
            "size_bytes": artifact["size_bytes"],
        }
        for artifact in artifacts
    )
    receipt = _validate_result_receipt(
        _post_result(packet_id, body, key, token=token), packet_id, artifacts_meta
    )
    if receipt["replayed"] is not True:
        # The recorded key was already accepted once; answering the exact
        # replay as a new result is server contract drift.
        raise _drift("a journaled replay was accepted as a new result")
    return {
        "status": "candidate_staged",
        "packet_id": packet_id,
        "result_digest": receipt["result_digest"],
        "replayed": receipt["replayed"],
        "accepted_at": receipt["accepted_at"],
        "staged_artifacts": receipt["staged_artifacts"],
        "note": "candidates are staged for server verification; review and "
        "release are separate later steps",
    }


def submit_result(packet_id: str, directory: Path) -> dict[str, object]:
    """Validate a generated result directory and upload it idempotently."""
    path = _packet_route(packet_id)  # validates the id first
    token = _cli_token()
    _require_compatible_server()
    try:
        _, envelope_document = request_json("GET", path, token=token)
    except ClientError as exc:
        if exc.code != "PACKET_NOT_FOUND":
            raise
        # The packet may already be accepted and therefore invisible: the
        # attempt journal drives the exact replay, or the original error
        # propagates when no attempt was ever recorded.
        return _replay_attempt_result(
            packet_id, Path(directory), token=token, original_error=exc
        )
    # The packet envelope digest is recomputed again before result construction.
    envelope = _validate_packet_envelope(envelope_document)
    packet = envelope["packet"]
    if packet["packet_id"] != packet_id:
        raise _drift("server returned a packet for a different packet id")
    _require_current_claim(envelope)
    validated, decoded = validate_result_directory(packet, Path(directory))
    token_bytes = token.encode("utf-8")
    # Credential scan before anything is persisted, encoded further or
    # uploaded: relative paths, media metadata, source_records,
    # operator_notes, every decoded artifact byte string, and (below) the
    # final canonical request body.
    for artifact in validated["artifacts"]:
        _scan_for_credentials(
            str(artifact["relative_path"]).encode("utf-8"),
            token_bytes,
            "artifact relative path",
        )
        _scan_for_credentials(
            str(artifact["media_type"]).encode("utf-8"),
            token_bytes,
            "artifact media metadata",
        )
    _scan_value_for_credentials(
        validated["source_records"], token_bytes, "result metadata"
    )
    _scan_value_for_credentials(
        validated["operator_notes"], token_bytes, "result metadata"
    )
    _scan_for_credentials(decoded, token_bytes, "artifact payload")
    artifacts_meta = tuple(
        {
            "relative_path": artifact["relative_path"],
            "media_type": artifact["media_type"],
            "sha256": artifact["sha256"],
            "size_bytes": artifact["size_bytes"],
        }
        for artifact in validated["artifacts"]
    )

    def body_factory(generated_at: str) -> bytes:
        return canonical_json(
            {
                "schema": RESULT_SCHEMA,
                "content_lock_digest": packet["content_lock_digest"],
                "skill_release": SKILL_RELEASE,
                "client_surface": CLIENT_SURFACE,
                "generated_at": generated_at,
                "artifacts": validated["artifacts"],
                "source_records": validated["source_records"],
                "operator_notes": validated["operator_notes"],
            }
        )

    body, key = load_or_create_attempt(
        str(packet["packet_id"]), artifacts_meta, body_factory
    )
    _scan_for_credentials(body, token_bytes, "request body")
    # complete before submit; an already-completed packet is confirmed via a
    # job status read instead of failing the upload.
    try:
        _post_packet_mutation(
            _packet_route(packet_id, "/complete"), packet_id, "complete", token=token
        )
    except ClientError as exc:
        if exc.code != "INVALID_STATE_TRANSITION":
            raise
        _, job_document = request_json(
            "GET", _job_route(str(packet["job_id"])), token=token
        )
        job = _validate_job(job_document)
        if job["state"] not in ("awaiting_upload", "server_verifying"):
            raise exc
    receipt = _validate_result_receipt(
        _post_result(packet_id, body, key, token=token), packet_id, artifacts_meta
    )
    return {
        "status": "candidate_staged",
        "packet_id": packet_id,
        "result_digest": receipt["result_digest"],
        "replayed": receipt["replayed"],
        "accepted_at": receipt["accepted_at"],
        "staged_artifacts": receipt["staged_artifacts"],
        "note": "candidates are staged for server verification; review and "
        "release are separate later steps",
    }


_PACKETS_USAGE = (
    "usage: card_os_client.py packets list\n"
    "       card_os_client.py packets claim PACKET_ID\n"
    "       card_os_client.py packets get PACKET_ID --output FILE\n"
    "       card_os_client.py packets complete PACKET_ID\n"
)

_JOBS_USAGE = (
    "usage: card_os_client.py jobs status JOB_ID\n"
    "       card_os_client.py jobs events JOB_ID\n"
)

_RESULTS_USAGE = (
    "usage: card_os_client.py results submit PACKET_ID --directory DIR\n"
)


def _packets_main(rest: list[str]) -> int:
    try:
        if rest == ["list"]:
            _emit(_cmd_packets_list())
            return 0
        if len(rest) == 2 and rest[0] == "claim":
            _emit(_cmd_packets_claim(rest[1]))
            return 0
        if len(rest) == 2 and rest[0] == "complete":
            _emit(_cmd_packets_complete(rest[1]))
            return 0
        if len(rest) == 4 and rest[0] == "get" and rest[2] == "--output":
            _emit(_cmd_packets_get(rest[1], rest[3]))
            return 0
        sys.stderr.write(_PACKETS_USAGE)
        return 2
    except ClientError as exc:
        _emit({"error": exc.to_dict()})
        return 1


def _jobs_main(rest: list[str]) -> int:
    try:
        if len(rest) == 2 and rest[0] == "status":
            _emit(_cmd_jobs_status(rest[1]))
            return 0
        if len(rest) == 2 and rest[0] == "events":
            _emit(_cmd_jobs_events(rest[1]))
            return 0
        sys.stderr.write(_JOBS_USAGE)
        return 2
    except ClientError as exc:
        _emit({"error": exc.to_dict()})
        return 1


def _results_main(rest: list[str]) -> int:
    try:
        if len(rest) == 4 and rest[0] == "submit" and rest[2] == "--directory":
            _emit(submit_result(rest[1], Path(rest[3])))
            return 0
        sys.stderr.write(_RESULTS_USAGE)
        return 2
    except ClientError as exc:
        _emit({"error": exc.to_dict()})
        return 1


_AUTH_USAGE = (
    "usage: card_os_client.py auth set --stdin [--allow-file-store]\n"
    "       card_os_client.py auth status\n"
    "       card_os_client.py auth delete\n"
)


def _auth_main(rest: list[str]) -> int:
    try:
        if rest == ["status"]:
            _emit(_cmd_auth_status())
            return 0
        if rest == ["delete"]:
            _emit(_cmd_auth_delete())
            return 0
        if rest and rest[0] == "set":
            flags = rest[1:]
            if "--stdin" not in flags or any(
                flag not in ("--stdin", "--allow-file-store") for flag in flags
            ):
                sys.stderr.write(_AUTH_USAGE)
                return 2
            _emit(_cmd_auth_set(allow_file_store="--allow-file-store" in flags))
            return 0
        sys.stderr.write(_AUTH_USAGE)
        return 2
    except ClientError as exc:
        _emit({"error": exc.to_dict()})
        return 1


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
    if args[:1] == ["auth"]:
        return _auth_main(args[1:])
    if args[:1] == ["packets"]:
        return _packets_main(args[1:])
    if args[:1] == ["jobs"]:
        return _jobs_main(args[1:])
    if args[:1] == ["results"]:
        return _results_main(args[1:])
    sys.stderr.write(
        "usage: card_os_client.py doctor\n"
        + _AUTH_USAGE
        + _PACKETS_USAGE
        + _JOBS_USAGE
        + _RESULTS_USAGE
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
