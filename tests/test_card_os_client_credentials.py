"""Credential-backend tests for the thin Card OS client.

Covers the three storage backends (macOS Keychain through an in-process
ctypes binding, Linux ``secret-tool`` through an injectable runner, and the
explicitly gated 0600 file fallback), backend selection priority, the
``auth set/status/delete`` CLI, the ephemeral ``CARD_OS_TOKEN`` override, and
a token-leakage sweep over every failure path. The macOS backend is tested
against a fake Security.framework so the user's real login Keychain is never
touched; the Linux backend is tested against a fake runner so no real secret
service is required. All tokens in this file are obvious fakes.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "skills" / "cognitive-card-os" / "scripts" / "card_os_client.py"
FAKE_TOKEN = "dummy-fixture-token-not-a-real-secret"
FAKE_TOKEN_BYTES = FAKE_TOKEN.encode("utf-8")
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


class FakeSecurityFramework:
    """Records KeychainCredentialStore calls; mimics _SecurityFramework.

    The item model mirrors observed Security.framework semantics (learned
    from the 0.1.0 live acceptance defect): a modify call with a NULL data
    pointer is a no-op, while a zero-length non-NULL buffer truncates the
    item data.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.add_status = 0
        self.modify_status = 0
        # Explicit override for find_generic_password; None answers from the
        # item model instead.
        self.find_result: tuple[int, bytes | None, int | None] | None = None
        self._item: bytes | None = None
        self._next_ref = 1000

    def find_generic_password(self, service: bytes, account: bytes):
        self.calls.append(("find", service, account))
        if self.find_result is not None:
            return self.find_result
        if self._item is None:
            return (-25300, None, None)  # errSecItemNotFound
        self._next_ref += 1
        return (0, self._item, self._next_ref)

    def add_generic_password(self, service: bytes, account: bytes, data) -> int:
        self.calls.append(("add", service, account, bytes(data), data))
        if self.add_status != 0:
            return self.add_status
        if self._item is not None:
            return -25299  # errSecDuplicateItem
        self._item = bytes(data)
        return 0

    def modify_item_data(self, item_ref: int, data) -> int:
        self.calls.append(
            ("modify", item_ref, None if data is None else bytes(data), data)
        )
        if self.modify_status != 0:
            return self.modify_status
        if data is not None:
            # NULL pointer: no-op on real Security.framework. Any non-NULL
            # buffer replaces the data; a zero-length buffer truncates it.
            self._item = bytes(data)
        return 0

    def release_item(self, item_ref: int) -> None:
        self.calls.append(("release", item_ref))

    def buffers_of(self, verb: str) -> list[object]:
        return [call[-1] for call in self.calls if call[0] == verb]


class FakeSecretToolRunner:
    """Injectable runner for SecretToolCredentialStore."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.results: list[object] = []

    def push(self, returncode: int, stdout: bytes = b"") -> None:
        self.results.append((returncode, stdout))

    def push_error(self, exc: Exception) -> None:
        self.results.append(exc)

    def __call__(self, argv: list[str], stdin_data: bytes | None):
        self.calls.append((list(argv), stdin_data))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        returncode, stdout = result
        return client._SecretToolResult(returncode=returncode, stdout=stdout)


class FakeStore:
    """In-memory CredentialStore double for CLI and resolution tests."""

    backend_name = "fake-backend"

    def __init__(self, stored: bytes | None = None) -> None:
        self.stored = stored
        self.set_calls: list[bytes] = []
        self.get_calls = 0
        self.delete_calls = 0
        self.set_error: Exception | None = None
        self.get_error: Exception | None = None

    def set(self, token: bytes) -> None:
        if self.set_error is not None:
            raise self.set_error
        self.set_calls.append(bytes(token))
        self.stored = bytes(token)

    def get(self) -> bytes | None:
        self.get_calls += 1
        if self.get_error is not None:
            raise self.get_error
        return self.stored

    def delete(self) -> bool:
        self.delete_calls += 1
        had = self.stored is not None
        self.stored = None
        return had


class FakeStdin:
    """stdin double counting read() calls; .buffer mirrors real stdin."""

    def __init__(self, data: bytes) -> None:
        self.buffer = self
        self._data = data
        self.read_calls = 0

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        if size is None or size < 0:
            return self._data
        return self._data[:size]


class CliMixin:
    def run_cli(self, args: list[str], stdin_data: bytes | None = None):
        out, err = io.StringIO(), io.StringIO()
        fake_stdin = FakeStdin(stdin_data) if stdin_data is not None else None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if fake_stdin is not None:
                with unittest.mock.patch.object(sys, "stdin", fake_stdin):
                    code = client.main(args)
            else:
                code = client.main(args)
        return code, out.getvalue(), err.getvalue(), fake_stdin

    def assert_no_token(self, *chunks: str) -> None:
        for chunk in chunks:
            self.assertNotIn(FAKE_TOKEN, chunk)
            self.assertNotIn(STORED_TOKEN, chunk)


class SelectionTests(unittest.TestCase):
    def test_darwin_selects_keychain(self) -> None:
        store = client.select_credential_store(platform="darwin", allow_file_store=False)
        self.assertIsInstance(store, client.KeychainCredentialStore)
        self.assertEqual("macos-keychain", store.backend_name)

    def test_linux_with_secret_tool_selects_secret_tool(self) -> None:
        with unittest.mock.patch.object(
            client, "_secret_tool_available", return_value=True
        ):
            store = client.select_credential_store(
                platform="linux", allow_file_store=False
            )
        self.assertIsInstance(store, client.SecretToolCredentialStore)
        self.assertEqual("linux-secret-tool", store.backend_name)

    def test_linux_without_secret_tool_fails_closed_without_flag(self) -> None:
        with unittest.mock.patch.object(
            client, "_secret_tool_available", return_value=False
        ):
            with self.assertRaises(client.ClientError) as ctx:
                client.select_credential_store(platform="linux", allow_file_store=False)
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)

    def test_linux_without_secret_tool_with_flag_falls_back_to_file(self) -> None:
        with unittest.mock.patch.object(
            client, "_secret_tool_available", return_value=False
        ):
            store = client.select_credential_store(platform="linux", allow_file_store=True)
        self.assertIsInstance(store, client.FileCredentialStore)
        self.assertEqual("file", store.backend_name)

    def test_unknown_platform_fails_closed_without_flag(self) -> None:
        with self.assertRaises(client.ClientError) as ctx:
            client.select_credential_store(platform="freebsd", allow_file_store=False)
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)

    def test_unknown_platform_with_flag_uses_file_store(self) -> None:
        store = client.select_credential_store(platform="freebsd", allow_file_store=True)
        self.assertIsInstance(store, client.FileCredentialStore)

    def test_darwin_framework_failure_fails_closed_without_flag(self) -> None:
        with unittest.mock.patch.object(
            client._SecurityFramework,
            "load",
            side_effect=client.ClientError("CREDENTIAL_STORE_UNAVAILABLE", "boom"),
        ):
            with self.assertRaises(client.ClientError) as ctx:
                client.select_credential_store(platform="darwin", allow_file_store=False)
            self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)
            with_flag = client.select_credential_store(
                platform="darwin", allow_file_store=True
            )
        self.assertIsInstance(with_flag, client.FileCredentialStore)

    def test_selection_error_is_stable_and_secret_free(self) -> None:
        with self.assertRaises(client.ClientError) as ctx:
            client.select_credential_store(platform="plan9", allow_file_store=False)
        text = json.dumps(ctx.exception.to_dict())
        self.assertNotIn(FAKE_TOKEN, text)

    def test_stores_conform_to_the_credential_store_protocol(self) -> None:
        for cls in (
            client.KeychainCredentialStore,
            client.SecretToolCredentialStore,
            client.FileCredentialStore,
        ):
            for method in ("set", "get", "delete"):
                self.assertTrue(callable(getattr(cls, method, None)), (cls, method))


class StdinParsingTests(unittest.TestCase):
    def test_accepts_token_without_trailing_newline(self) -> None:
        self.assertEqual(FAKE_TOKEN_BYTES, client._parse_stdin_token(FAKE_TOKEN_BYTES))

    def test_strips_one_trailing_newline(self) -> None:
        self.assertEqual(
            FAKE_TOKEN_BYTES, client._parse_stdin_token(FAKE_TOKEN_BYTES + b"\n")
        )

    def test_rejects_empty_input(self) -> None:
        for data in (b"", b"\n"):
            with self.subTest(data=data):
                with self.assertRaises(client.ClientError) as ctx:
                    client._parse_stdin_token(data)
                self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)

    def test_rejects_interior_newlines(self) -> None:
        data = b"dummy-first-line\n" + b"dummy-second-line\n"
        with self.assertRaises(client.ClientError) as ctx:
            client._parse_stdin_token(data)
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)
        self.assertNotIn(data.decode("utf-8"), str(ctx.exception))

    def test_rejects_carriage_return_after_stripping_one_newline(self) -> None:
        with self.assertRaises(client.ClientError) as ctx:
            client._parse_stdin_token(FAKE_TOKEN_BYTES + b"\r\n")
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))

    def test_rejects_oversized_input(self) -> None:
        maximum = client.MAX_TOKEN_BYTES
        self.assertEqual(b"d" * maximum, client._parse_stdin_token(b"d" * maximum))
        with self.assertRaises(client.ClientError) as ctx:
            client._parse_stdin_token(b"d" * (maximum + 1))
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)

    def test_rejects_non_utf8_input(self) -> None:
        with self.assertRaises(client.ClientError) as ctx:
            client._parse_stdin_token(b"\xff\xfe" + FAKE_TOKEN_BYTES)
        self.assertEqual("REQUEST_VALIDATION_FAILED", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))


class KeychainStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.security = FakeSecurityFramework()
        self.store = client.KeychainCredentialStore(security=self.security)

    def _buffers_zeroed(self, verb: str) -> None:
        for buffer in self.security.buffers_of(verb):
            if buffer is not None:
                self.assertEqual(b"\x00" * len(buffer), bytes(buffer))

    def test_service_and_account_constants(self) -> None:
        self.assertEqual(b"cognitive-card-os", client._KEYCHAIN_SERVICE)
        self.assertEqual(client.BASE_URL.encode("utf-8"), client._KEYCHAIN_ACCOUNT)
        self.assertEqual(
            "https://www.yutou.space/card-os/", client._KEYCHAIN_ACCOUNT.decode("utf-8")
        )

    def test_only_the_frozen_function_set_is_bound(self) -> None:
        self.assertEqual(
            frozenset(
                {
                    "SecKeychainFindGenericPassword",
                    "SecKeychainAddGenericPassword",
                    "SecKeychainItemModifyAttributesAndData",
                    "SecKeychainItemFreeContent",
                    "CFRelease",
                }
            ),
            frozenset(client.KEYCHAIN_BOUND_FUNCTIONS),
        )

    def test_bound_symbols_actually_accessed_match_frozen_set(self) -> None:
        class RecordingModule:
            def __init__(self) -> None:
                self.accessed: set[str] = set()

            def __getattr__(self, name: str) -> unittest.mock.MagicMock:
                self.accessed.add(name)
                return unittest.mock.MagicMock(name=name)

        security = RecordingModule()
        core = RecordingModule()
        client._SecurityFramework(security, core)
        self.assertEqual({"CFRelease"}, core.accessed)
        self.assertEqual(
            set(client.KEYCHAIN_BOUND_FUNCTIONS),
            security.accessed | core.accessed,
        )

    def test_set_adds_generic_password_and_zeroes_buffer(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        adds = [call for call in self.security.calls if call[0] == "add"]
        self.assertEqual(1, len(adds))
        _, service, account, content, _buffer = adds[0]
        self.assertEqual(b"cognitive-card-os", service)
        self.assertEqual(client._KEYCHAIN_ACCOUNT, account)
        self.assertEqual(FAKE_TOKEN_BYTES, content)
        # The recorded content was captured during the call; afterwards the
        # mutable buffer handed to the framework must be zeroed.
        self._buffers_zeroed("add")

    def test_set_on_duplicate_item_modifies_in_place(self) -> None:
        self.security.add_status = client._ERR_SEC_DUPLICATE_ITEM
        self.security.find_result = (0, STORED_TOKEN_BYTES, 4242)
        self.store.set(FAKE_TOKEN_BYTES)
        verbs = [call[0] for call in self.security.calls]
        self.assertEqual(["add", "find", "modify", "release"], verbs)
        modify = [call for call in self.security.calls if call[0] == "modify"][0]
        self.assertEqual(4242, modify[1])
        self.assertEqual(FAKE_TOKEN_BYTES, modify[2])
        self.assertIn(("release", 4242), self.security.calls)
        self._buffers_zeroed("add")
        self._buffers_zeroed("modify")

    def test_set_osstatus_error_maps_without_secret_bytes(self) -> None:
        self.security.add_status = -25308  # errSecInteractionNotAllowed
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        exc = ctx.exception
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", exc.code)
        self.assertIn("-25308", str(exc))
        self.assertNotIn(FAKE_TOKEN, str(exc))
        self.assertNotIn(FAKE_TOKEN, json.dumps(exc.to_dict()))
        self._buffers_zeroed("add")

    def test_get_returns_password_bytes_and_releases_item(self) -> None:
        self.security.find_result = (0, STORED_TOKEN_BYTES, 777)
        self.assertEqual(STORED_TOKEN_BYTES, self.store.get())
        self.assertIn(("release", 777), self.security.calls)

    def test_get_item_not_found_returns_none(self) -> None:
        self.security.find_result = (client._ERR_SEC_ITEM_NOT_FOUND, None, None)
        self.assertIsNone(self.store.get())

    def test_get_empty_data_counts_as_absent(self) -> None:
        self.security.find_result = (0, b"", 99)
        self.assertIsNone(self.store.get())

    def test_get_osstatus_error_maps_without_secret_bytes(self) -> None:
        self.security.find_result = (-25293, None, None)  # errSecAuthFailed
        with self.assertRaises(client.ClientError) as ctx:
            self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))

    def test_delete_erases_existing_item_and_is_idempotent(self) -> None:
        self.security.find_result = (0, STORED_TOKEN_BYTES, 55)
        self.assertTrue(self.store.delete())
        modify = [call for call in self.security.calls if call[0] == "modify"]
        self.assertEqual(1, len(modify))
        self.assertEqual(55, modify[0][1])
        # Erased via a zero-length non-NULL buffer; a NULL pointer would be a
        # no-op on real Security.framework (the 0.1.0 live defect).
        self.assertEqual(b"", modify[0][2])
        self.assertIsNotNone(modify[0][3])
        self.assertIn(("release", 55), self.security.calls)
        # Second delete: item now absent.
        self.security.find_result = (client._ERR_SEC_ITEM_NOT_FOUND, None, None)
        self.assertFalse(self.store.delete())

    def test_delete_actually_removes_credential_data(self) -> None:
        # Regression for the 0.1.0 live defect: with the stateful fake the
        # erase must make get() report absence, exactly like the real backend.
        self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual(FAKE_TOKEN_BYTES, self.store.get())
        self.assertTrue(self.store.delete())
        self.assertIsNone(self.store.get())

    def test_delete_absent_item_returns_false_without_modify(self) -> None:
        self.security.find_result = (client._ERR_SEC_ITEM_NOT_FOUND, None, None)
        self.assertFalse(self.store.delete())
        self.assertEqual([], [call for call in self.security.calls if call[0] == "modify"])


class SecretToolStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = FakeSecretToolRunner()
        self.store = client.SecretToolCredentialStore(runner=self.runner)

    def _assert_metadata_argv(self, argv: list[str]) -> None:
        self.assertEqual("secret-tool", argv[0])
        joined = " ".join(argv)
        self.assertIn("cognitive-card-os", joined)
        self.assertIn(client.BASE_URL, joined)
        # The token must travel on stdin, never in argv.
        for arg in argv:
            self.assertNotIn(FAKE_TOKEN, arg)
            self.assertNotIn(STORED_TOKEN, arg)

    def test_set_sends_token_on_stdin_and_metadata_in_argv(self) -> None:
        self.runner.push(0)
        self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual(1, len(self.runner.calls))
        argv, stdin_data = self.runner.calls[0]
        self.assertIn("store", argv)
        self._assert_metadata_argv(argv)
        self.assertEqual(FAKE_TOKEN_BYTES, stdin_data)

    def test_set_failure_maps_without_leaking(self) -> None:
        self.runner.push(2, stdout=b"some stderr-adjacent noise")
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        exc = ctx.exception
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", exc.code)
        self.assertNotIn(FAKE_TOKEN, str(exc))
        self.assertNotIn("some stderr-adjacent noise", str(exc))

    def test_get_returns_stdout_bytes(self) -> None:
        self.runner.push(0, stdout=STORED_TOKEN_BYTES)
        self.assertEqual(STORED_TOKEN_BYTES, self.store.get())
        argv, stdin_data = self.runner.calls[0]
        self.assertIn("lookup", argv)
        self.assertIsNone(stdin_data)
        self._assert_metadata_argv(argv)

    def test_get_not_found_returns_none(self) -> None:
        self.runner.push(1)
        self.assertIsNone(self.store.get())

    def test_get_failure_never_logs_captured_output(self) -> None:
        marker = b"dummy-lookup-output-not-a-real-secret"
        self.runner.push(7, stdout=marker)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)
        self.assertNotIn(marker.decode("utf-8"), str(ctx.exception))

    def test_delete_is_idempotent(self) -> None:
        self.runner.push(0)
        self.assertTrue(self.store.delete())
        argv, _ = self.runner.calls[0]
        self.assertIn("clear", argv)
        self._assert_metadata_argv(argv)
        self.runner.push(1)
        self.assertFalse(self.store.delete())

    def test_missing_binary_maps_to_store_unavailable(self) -> None:
        self.runner.push_error(FileNotFoundError("secret-tool"))
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))

    def test_sanitized_environment_is_minimal(self) -> None:
        env = client._SANITIZED_ENV
        self.assertIsInstance(env, dict)
        self.assertLessEqual(len(env), 5)
        self.assertIn("PATH", env)
        for forbidden in ("CARD_OS_TOKEN", "OPENAI_API_KEY", "HOME", "DBUS_SESSION_BUS_ADDRESS"):
            self.assertNotIn(forbidden, env)


class FileStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.path = self.root / "cognitive-card-os" / "credentials.json"
        self.store = client.FileCredentialStore(self.path)

    def _lstat(self, path: Path) -> os.stat_result:
        return os.lstat(path)

    def test_set_get_delete_roundtrip(self) -> None:
        self.assertIsNone(self.store.get())
        self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual(FAKE_TOKEN_BYTES, self.store.get())
        self.assertTrue(self.store.delete())
        self.assertIsNone(self.store.get())
        # delete is idempotent.
        self.assertFalse(self.store.delete())

    def test_set_overwrites_existing_credential(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        self.store.set(STORED_TOKEN_BYTES)
        self.assertEqual(STORED_TOKEN_BYTES, self.store.get())

    def test_content_is_canonical_json_with_base_url_and_token(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        raw = self.path.read_bytes()
        expected = client.canonical_json(
            {"base_url": client.BASE_URL, "token": FAKE_TOKEN}
        )
        self.assertEqual(expected, raw)
        document = json.loads(raw.decode("utf-8"))
        self.assertEqual(client.BASE_URL, document["base_url"])
        self.assertEqual(FAKE_TOKEN, document["token"])

    def test_directory_and_file_modes_are_private(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        dir_stat = self._lstat(self.path.parent)
        file_stat = self._lstat(self.path)
        self.assertEqual(0o700, stat.S_IMODE(dir_stat.st_mode))
        self.assertEqual(0o600, stat.S_IMODE(file_stat.st_mode))
        self.assertTrue(stat.S_ISREG(file_stat.st_mode))
        # No private temp files are left behind.
        leftovers = [p.name for p in self.path.parent.iterdir()]
        self.assertEqual(["credentials.json"], leftovers)

    def test_unsafe_parent_mode_fails_closed(self) -> None:
        self.path.parent.mkdir(mode=0o700)
        os.chmod(self.path.parent, 0o755)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))
        self.assertFalse(self.path.exists())

    def test_symlink_parent_fails_closed(self) -> None:
        real_dir = self.root / "real"
        real_dir.mkdir(mode=0o700)
        os.symlink(real_dir, self.path.parent)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)

    def test_wrong_file_mode_fails_closed_on_read_and_rewrite(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        os.chmod(self.path, 0o644)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(STORED_TOKEN_BYTES)
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        # The readable-by-others file was not rewritten in place either.
        self.assertEqual(FAKE_TOKEN, json.loads(self.path.read_text())["token"])

    def test_symlink_file_is_never_followed(self) -> None:
        victim = self.root / "victim.json"
        victim.write_bytes(b"dummy-victim-content-not-a-secret")
        self.path.parent.mkdir(mode=0o700)
        os.symlink(victim, self.path)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        with self.assertRaises(client.ClientError) as ctx:
            self.store.set(FAKE_TOKEN_BYTES)
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        # The symlink target was neither read as a credential nor overwritten.
        self.assertEqual(b"dummy-victim-content-not-a-secret", victim.read_bytes())

    def test_wrong_owner_fails_closed(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        real_uid = self._lstat(self.path).st_uid
        with unittest.mock.patch("os.getuid", return_value=real_uid + 1):
            with self.assertRaises(client.ClientError) as ctx:
                self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)

    def test_malformed_content_fails_closed(self) -> None:
        self.store.set(FAKE_TOKEN_BYTES)
        os.chmod(self.path, 0o600)
        self.path.write_bytes(b'{"base_url": 42, "token": 7}')
        with self.assertRaises(client.ClientError) as ctx:
            self.store.get()
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))

    def test_default_path_honors_xdg_config_home(self) -> None:
        with unittest.mock.patch.dict(
            os.environ, {"XDG_CONFIG_HOME": str(self.root)}, clear=False
        ):
            store = client.FileCredentialStore()
        self.assertEqual(
            self.root / "cognitive-card-os" / "credentials.json", store.path
        )

    def test_default_path_falls_back_to_home_config(self) -> None:
        environ = {"HOME": str(self.root)}
        with unittest.mock.patch.dict(os.environ, environ, clear=True):
            store = client.FileCredentialStore()
        self.assertEqual(
            self.root / ".config" / "cognitive-card-os" / "credentials.json", store.path
        )


class EffectiveTokenTests(unittest.TestCase):
    def test_env_token_takes_precedence_over_store(self) -> None:
        store = FakeStore(stored=STORED_TOKEN_BYTES)
        environ = {"CARD_OS_TOKEN": FAKE_TOKEN}
        self.assertEqual(
            FAKE_TOKEN, client.resolve_effective_token(environ=environ, store=store)
        )
        # Short-circuit: the store is not even read when the env override wins.
        self.assertEqual(0, store.get_calls)

    def test_env_token_is_never_persisted(self) -> None:
        store = FakeStore()
        environ = {"CARD_OS_TOKEN": FAKE_TOKEN}
        client.resolve_effective_token(environ=environ, store=store)
        self.assertEqual([], store.set_calls)
        self.assertIsNone(store.stored)

    def test_empty_env_token_falls_through_to_store(self) -> None:
        store = FakeStore(stored=STORED_TOKEN_BYTES)
        environ = {"CARD_OS_TOKEN": ""}
        self.assertEqual(
            STORED_TOKEN, client.resolve_effective_token(environ=environ, store=store)
        )

    def test_store_token_used_when_env_absent(self) -> None:
        store = FakeStore(stored=STORED_TOKEN_BYTES)
        self.assertEqual(
            STORED_TOKEN, client.resolve_effective_token(environ={}, store=store)
        )

    def test_absent_everywhere_resolves_to_none(self) -> None:
        self.assertIsNone(
            client.resolve_effective_token(environ={}, store=FakeStore())
        )

    def test_reads_process_environ_by_default(self) -> None:
        with unittest.mock.patch.dict(
            os.environ, {"CARD_OS_TOKEN": FAKE_TOKEN}, clear=False
        ):
            self.assertEqual(
                FAKE_TOKEN,
                client.resolve_effective_token(store=FakeStore(STORED_TOKEN_BYTES)),
            )

    def test_unavailable_default_store_resolves_to_none(self) -> None:
        with unittest.mock.patch.object(
            client,
            "select_credential_store",
            side_effect=client.ClientError("CREDENTIAL_STORE_UNAVAILABLE", "none"),
        ):
            self.assertIsNone(client.resolve_effective_token(environ={}))

    def test_store_crash_is_wrapped_and_redacted(self) -> None:
        store = FakeStore()
        store.get_error = RuntimeError(FAKE_TOKEN)
        with self.assertRaises(client.ClientError) as ctx:
            client.resolve_effective_token(environ={}, store=store)
        exc = ctx.exception
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", exc.code)
        self.assertNotIn(FAKE_TOKEN, str(exc))
        self.assertNotIn(FAKE_TOKEN, repr(exc))
        self.assertNotIn(FAKE_TOKEN, json.dumps(exc.to_dict()))

    def test_env_token_redacted_from_store_errors(self) -> None:
        store = FakeStore(stored=STORED_TOKEN_BYTES)
        store.get_error = client.ClientError("CREDENTIAL_STORE_UNSAFE", "unsafe store")
        environ = {"CARD_OS_TOKEN": ""}
        with self.assertRaises(client.ClientError):
            client.resolve_effective_token(environ=environ, store=store)


class CliAuthTests(CliMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.store = FakeStore()
        self._saved_override = client._credential_store_override
        self.addCleanup(self._restore)
        client._credential_store_override = self.store

    def _restore(self) -> None:
        client._credential_store_override = self._saved_override

    def test_auth_set_stdin_stores_token_and_reports_backend(self) -> None:
        code, out, err, fake_stdin = self.run_cli(
            ["auth", "set", "--stdin"], stdin_data=FAKE_TOKEN_BYTES + b"\n"
        )
        self.assertEqual(0, code)
        self.assertEqual(1, fake_stdin.read_calls)  # stdin read exactly once
        self.assertEqual([FAKE_TOKEN_BYTES], self.store.set_calls)
        payload = json.loads(out)
        self.assertEqual("stored", payload["status"])
        self.assertEqual("fake-backend", payload["backend"])
        self.assertEqual(client.canonical_json(payload).decode("utf-8") + "\n", out)
        self.assert_no_token(out, err)

    def test_auth_set_accepts_allow_file_store_flag(self) -> None:
        for args in (
            ["auth", "set", "--stdin", "--allow-file-store"],
            ["auth", "set", "--allow-file-store", "--stdin"],
        ):
            with self.subTest(args=args):
                code, out, err, _ = self.run_cli(args, stdin_data=FAKE_TOKEN_BYTES)
                self.assertEqual(0, code)
                self.assert_no_token(out, err)

    def test_auth_set_rejects_invalid_input_without_storing(self) -> None:
        bad_inputs = [
            b"",
            b"\n",
            FAKE_TOKEN_BYTES + b"\nextra\n",
            FAKE_TOKEN_BYTES + b"\r\n",
            b"d" * (client.MAX_TOKEN_BYTES + 1),
        ]
        for data in bad_inputs:
            with self.subTest(data=data[:32]):
                self.store.set_calls.clear()
                code, out, err, fake_stdin = self.run_cli(
                    ["auth", "set", "--stdin"], stdin_data=data
                )
                self.assertEqual(1, code)
                self.assertEqual(1, fake_stdin.read_calls)
                payload = json.loads(out)
                self.assertEqual("REQUEST_VALIDATION_FAILED", payload["error"]["code"])
                self.assertEqual([], self.store.set_calls)
                stripped = data.decode("utf-8", errors="ignore").strip()
                if stripped:
                    self.assertNotIn(stripped, out)
                self.assert_no_token(out, err)

    def test_auth_set_without_stdin_flag_is_usage_error(self) -> None:
        code, out, err, _ = self.run_cli(["auth", "set"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("usage:", err)
        self.assertIn("--stdin", err)
        self.assertEqual([], self.store.set_calls)

    def test_auth_set_token_as_positional_arg_is_usage_error(self) -> None:
        # A token must never be accepted through argv.
        code, out, err, _ = self.run_cli(["auth", "set", "--stdin", FAKE_TOKEN])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("usage:", err)
        self.assertEqual([], self.store.set_calls)

    def test_auth_set_store_unavailable_fails_closed(self) -> None:
        client._credential_store_override = None
        with unittest.mock.patch.object(
            client,
            "select_credential_store",
            side_effect=client.ClientError(
                "CREDENTIAL_STORE_UNAVAILABLE", "no backend"
            ),
        ):
            code, out, err, _ = self.run_cli(
                ["auth", "set", "--stdin"], stdin_data=FAKE_TOKEN_BYTES
            )
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", payload["error"]["code"])
        self.assert_no_token(out, err)

    def test_auth_set_backend_write_failure_never_echoes_token(self) -> None:
        self.store.set_error = client.ClientError(
            "CREDENTIAL_STORE_UNAVAILABLE", "backend refused the write"
        )
        code, out, err, _ = self.run_cli(
            ["auth", "set", "--stdin"], stdin_data=FAKE_TOKEN_BYTES
        )
        self.assertEqual(1, code)
        payload = json.loads(out)
        self.assertEqual("CREDENTIAL_STORE_UNAVAILABLE", payload["error"]["code"])
        self.assert_no_token(out, err)

    def test_auth_status_reports_backend_and_presence_only(self) -> None:
        self.store.stored = STORED_TOKEN_BYTES
        code, out, err, _ = self.run_cli(["auth", "status"])
        self.assertEqual(0, code)
        payload = json.loads(out)
        self.assertEqual("ok", payload["status"])
        self.assertEqual("fake-backend", payload["backend"])
        self.assertEqual("present", payload["credential"])
        # Never the token, and never a prefix or fingerprint of it.
        self.assertNotIn(STORED_TOKEN[:12], out)
        self.assert_no_token(out, err)

    def test_auth_status_reports_absence(self) -> None:
        code, out, err, _ = self.run_cli(["auth", "status"])
        self.assertEqual(0, code)
        payload = json.loads(out)
        self.assertEqual("absent", payload["credential"])
        self.assertEqual("fake-backend", payload["backend"])

    def test_auth_delete_is_idempotent(self) -> None:
        self.store.stored = STORED_TOKEN_BYTES
        code, out, err, _ = self.run_cli(["auth", "delete"])
        self.assertEqual(0, code)
        self.assertTrue(json.loads(out)["deleted"])
        self.assertIsNone(self.store.stored)
        # Second delete succeeds even though nothing remained.
        code, out, err, _ = self.run_cli(["auth", "delete"])
        self.assertEqual(0, code)
        self.assertFalse(json.loads(out)["deleted"])
        self.assertEqual(2, self.store.delete_calls)
        self.assert_no_token(out, err)

    def test_auth_unknown_subcommand_is_usage_error(self) -> None:
        code, out, err, _ = self.run_cli(["auth", "frobnicate"])
        self.assertEqual(2, code)
        self.assertIn("usage:", err)


class FileStoreReadFallbackTests(CliMixin, unittest.TestCase):
    """The --allow-file-store opt-in must be readable after auth set.

    On a host without any platform backend (simulated here as linux without
    secret-tool) selection raises CREDENTIAL_STORE_UNAVAILABLE, and every
    read path then falls back to the gated 0600 file store: auth status and
    auth delete operate on it, resolve_effective_token reads it, and unsafe
    permissions stay fail-closed with CREDENTIAL_STORE_UNSAFE.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.config_home = Path(self._tmp.name) / "config"
        self._saved_override = client._credential_store_override
        self.addCleanup(self._restore)
        client._credential_store_override = None  # real selection path
        self._env_patcher = unittest.mock.patch.dict(
            os.environ,
            {"CARD_OS_TOKEN": "", "XDG_CONFIG_HOME": str(self.config_home)},
            clear=False,
        )
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)
        self._platform_patcher = unittest.mock.patch.object(sys, "platform", "linux")
        self._platform_patcher.start()
        self.addCleanup(self._platform_patcher.stop)
        self._secret_patcher = unittest.mock.patch.object(
            client, "_secret_tool_available", return_value=False
        )
        self._secret_patcher.start()
        self.addCleanup(self._secret_patcher.stop)

    def _restore(self) -> None:
        client._credential_store_override = self._saved_override

    @property
    def credential_path(self) -> Path:
        return self.config_home / "cognitive-card-os" / "credentials.json"

    def _auth_set_file_store(self):
        return self.run_cli(
            ["auth", "set", "--stdin", "--allow-file-store"],
            stdin_data=FAKE_TOKEN_BYTES + b"\n",
        )

    def test_set_status_delete_roundtrip_through_the_file_fallback(self) -> None:
        code, out, err, _ = self._auth_set_file_store()
        self.assertEqual(0, code, err)
        self.assertEqual("file", json.loads(out)["backend"])
        info = os.lstat(self.credential_path)
        self.assertEqual(0o600, stat.S_IMODE(info.st_mode))

        code, out, err, _ = self.run_cli(["auth", "status"])
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertEqual("file", payload["backend"])
        self.assertEqual("present", payload["credential"])
        self.assertNotIn(FAKE_TOKEN[:12], out)

        code, out, err, _ = self.run_cli(["auth", "delete"])
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertEqual("file", payload["backend"])
        self.assertTrue(payload["deleted"])
        self.assertFalse(self.credential_path.exists())

        code, out, err, _ = self.run_cli(["auth", "status"])
        self.assertEqual(0, code, err)
        self.assertEqual("absent", json.loads(out)["credential"])
        self.assert_no_token(out, err)

    def test_resolve_effective_token_reads_the_file_fallback(self) -> None:
        code, _out, err, _ = self._auth_set_file_store()
        self.assertEqual(0, code, err)
        self.assertEqual(FAKE_TOKEN, client.resolve_effective_token())

    def test_env_token_still_takes_precedence_over_the_file_fallback(self) -> None:
        code, _out, err, _ = self._auth_set_file_store()
        self.assertEqual(0, code, err)
        with unittest.mock.patch.dict(
            os.environ, {"CARD_OS_TOKEN": STORED_TOKEN}, clear=False
        ):
            self.assertEqual(STORED_TOKEN, client.resolve_effective_token())

    def test_unsafe_permissions_fail_closed_on_read(self) -> None:
        code, _out, err, _ = self._auth_set_file_store()
        self.assertEqual(0, code, err)
        os.chmod(self.credential_path, 0o644)
        code, out, err, _ = self.run_cli(["auth", "status"])
        self.assertEqual(1, code)
        self.assertEqual(
            "CREDENTIAL_STORE_UNSAFE", json.loads(out)["error"]["code"]
        )
        self.assert_no_token(out, err)
        with self.assertRaises(client.ClientError) as ctx:
            client.resolve_effective_token()
        self.assertEqual("CREDENTIAL_STORE_UNSAFE", ctx.exception.code)

    def test_selection_errors_other_than_unavailability_do_not_fall_back(self) -> None:
        # Only CREDENTIAL_STORE_UNAVAILABLE triggers the file fallback; a
        # genuine selection failure keeps propagating unchanged.
        with unittest.mock.patch.object(
            client,
            "select_credential_store",
            side_effect=client.ClientError(
                "CREDENTIAL_STORE_UNSAFE", "backend present but unsafe"
            ),
        ):
            code, out, err, _ = self.run_cli(["auth", "status"])
            self.assertEqual(1, code)
            self.assertEqual(
                "CREDENTIAL_STORE_UNSAFE", json.loads(out)["error"]["code"]
            )
            # resolve_effective_token keeps its historical contract: any
            # selection failure resolves to None (AUTH_REQUIRED downstream).
            self.assertIsNone(client.resolve_effective_token())
        self.assert_no_token(out, err)


class LeakageSweepTests(CliMixin, unittest.TestCase):
    """On every failure path the fake token appears in no output or error."""

    def setUp(self) -> None:
        self._saved_override = client._credential_store_override
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        client._credential_store_override = self._saved_override

    def test_sweep(self) -> None:
        failing_store = FakeStore(stored=STORED_TOKEN_BYTES)
        failing_store.set_error = client.ClientError(
            "CREDENTIAL_STORE_UNAVAILABLE", "write refused"
        )
        failing_store.get_error = client.ClientError(
            "CREDENTIAL_STORE_UNSAFE", "unsafe permissions"
        )
        client._credential_store_override = failing_store
        scenarios = [
            (["auth", "set", "--stdin"], FAKE_TOKEN_BYTES),
            (["auth", "status"], None),
        ]
        for args, stdin_data in scenarios:
            with self.subTest(args=args):
                code, out, err, _ = self.run_cli(args, stdin_data=stdin_data)
                self.assertEqual(1, code)
                self.assert_no_token(out, err)
        # Keychain and secret-tool failure mapping, swept again end to end.
        security = FakeSecurityFramework()
        security.add_status = -25291  # errSecNotAvailable
        keychain = client.KeychainCredentialStore(security=security)
        with self.assertRaises(client.ClientError) as ctx:
            keychain.set(FAKE_TOKEN_BYTES)
        self.assert_no_token(str(ctx.exception), json.dumps(ctx.exception.to_dict()))
        runner = FakeSecretToolRunner()
        runner.push_error(OSError("spawn failed"))
        secret_tool = client.SecretToolCredentialStore(runner=runner)
        with self.assertRaises(client.ClientError) as ctx:
            secret_tool.set(FAKE_TOKEN_BYTES)
        self.assert_no_token(str(ctx.exception), json.dumps(ctx.exception.to_dict()))


if __name__ == "__main__":
    unittest.main()
