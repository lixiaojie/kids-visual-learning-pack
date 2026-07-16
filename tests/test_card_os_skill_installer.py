from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import tempfile
import time
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "ops" / "cognitive-card-skill" / "install.sh"
REGISTRY = "https://www.yutou.space/card-os/skill/v1/"
MANIFEST_URL = REGISTRY + "manifest.json"
SOURCE_FILES = {
    "SKILL.md": (0o644, b"---\nname: cognitive-card-os\ndescription: fixture\n---\nfixture\n"),
    "agents/openai.yaml": (0o644, b"interface:\n  display_name: Fixture\n"),
    "scripts/card_os_client.py": (0o755, b"#!/usr/bin/env python3\nprint('fixture')\n"),
    "references/protocol.md": (0o644, b"# Protocol\n"),
    "references/errors.md": (0o644, b"# Errors\n"),
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_release(path: Path, version: str, marker: bytes = b"") -> tuple[Path, str]:
    sources = dict(SOURCE_FILES)
    mode, skill = sources["SKILL.md"]
    sources["SKILL.md"] = (mode, skill + marker)
    release = {
        "files": {
            name: {"mode": f"{mode:04o}", "sha256": digest(content), "size_bytes": len(content)}
            for name, (mode, content) in sorted(sources.items())
        },
        "minimum_server_version": "0.3.1",
        "protocol": {"minimum": 1, "maximum": 1},
        "schema": "cognitive-card-skill-release-v1",
        "source_commit": "1" * 40,
        "version": version,
    }
    entries: dict[str, tuple[int, bytes]] = {
        "cognitive-card-os/": (0o755, b""),
        "cognitive-card-os/agents/": (0o755, b""),
        "cognitive-card-os/references/": (0o755, b""),
        "cognitive-card-os/scripts/": (0o755, b""),
        "cognitive-card-os/release.json": (0o644, canonical(release)),
    }
    entries.update({f"cognitive-card-os/{name}": value for name, value in sources.items()})
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, (mode, content) in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 2, 3, 4, 6))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = mode << 16
            archive.writestr(info, content)
    return path, digest(path.read_bytes())


def central_entries(data: bytes) -> dict[str, tuple[int, int]]:
    """Return central-header and local-header offsets keyed by decoded member name."""
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise AssertionError("fixture ZIP has no EOCD")
    entries = struct.unpack_from("<H", data, eocd + 10)[0]
    position = struct.unpack_from("<I", data, eocd + 16)[0]
    result: dict[str, tuple[int, int]] = {}
    for _ in range(entries):
        if data[position : position + 4] != b"PK\x01\x02":
            raise AssertionError("fixture ZIP has invalid central directory")
        flags = struct.unpack_from("<H", data, position + 8)[0]
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", data, position + 28)
        raw_name = data[position + 46 : position + 46 + name_size]
        name = raw_name.decode("utf-8" if flags & 0x800 else "cp437")
        local_offset = struct.unpack_from("<I", data, position + 42)[0]
        result[name] = (position, local_offset)
        position += 46 + name_size + extra_size + comment_size
    return result


def mutate_zip_headers(
    data: bytes,
    member: str,
    *,
    central_name: bytes | None = None,
    local_name: bytes | None = None,
    external_attr: int | None = None,
    uncompressed_size: int | None = None,
) -> bytes:
    changed = bytearray(data)
    central, local = central_entries(data)[member]
    name_size = struct.unpack_from("<H", data, central + 28)[0]
    if central_name is not None:
        if len(central_name) != name_size:
            raise AssertionError("central replacement must preserve raw name length")
        changed[central + 46 : central + 46 + name_size] = central_name
    if local_name is not None:
        local_size = struct.unpack_from("<H", data, local + 26)[0]
        if len(local_name) != local_size:
            raise AssertionError("local replacement must preserve raw name length")
        changed[local + 30 : local + 30 + local_size] = local_name
    if external_attr is not None:
        struct.pack_into("<I", changed, central + 38, external_attr)
    if uncompressed_size is not None:
        struct.pack_into("<I", changed, central + 24, uncompressed_size)
    return bytes(changed)


class InstallerFixture:
    def __init__(self, base: Path, version: str = "0.1.0", marker: bytes = b"") -> None:
        self.base = base
        self.version = version
        self.install_root = base / "codex"
        self.remote = base / "remote"
        self.remote.mkdir(parents=True)
        self.archive, self.archive_digest = make_release(
            self.remote / f"{version}.zip", version, marker
        )
        self.archive_url = REGISTRY + f"releases/{version}/cognitive-card-os.zip"
        self.checksum_url = REGISTRY + f"releases/{version}/sha256.txt"
        self.checksum_path = self.remote / f"sha256-{version}.txt"
        self.checksum_path.write_text(f"{self.archive_digest}  cognitive-card-os.zip\n", encoding="ascii")
        self.extra_mapping: dict[str, str] = {}
        self.manifest_path = self.remote / f"manifest-{version}.json"
        self.fake_bin = base / "bin"
        self.fake_bin.mkdir()
        self.log = base / "curl.jsonl"
        self._write_fake_curl()
        self.write_manifest()

    def _write_fake_curl(self) -> None:
        fake = self.fake_bin / "curl"
        fake.write_text(
            """#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
args = sys.argv[1:]
with open(os.environ['FAKE_CURL_LOG'], 'a', encoding='utf-8') as out:
    out.write(json.dumps(args, separators=(',', ':')) + '\\n')
if not args or args[0] != '-q':
    raise SystemExit(90)
url = args[-1]
if os.environ.get('FAKE_CURL_REDIRECT') == url:
    raise SystemExit(47)
try:
    destination = args[args.index('--output') + 1]
    source = json.loads(os.environ['FAKE_CURL_MAP'])[url]
except (ValueError, KeyError):
    raise SystemExit(22)
shutil.copyfile(source, destination)
""",
            encoding="utf-8",
        )
        fake.chmod(0o755)

    def write_manifest(self, **changes: object) -> None:
        installer_digest = digest(INSTALLER.read_bytes()) if INSTALLER.exists() else "0" * 64
        manifest = {
            "archive_sha256": self.archive_digest,
            "archive_size_bytes": self.archive.stat().st_size,
            "archive_url": self.archive_url,
            "channel": "stable",
            "installer": {
                "sha256": installer_digest,
                "url": REGISTRY + f"installers/{installer_digest}/install.sh",
            },
            "minimum_server_version": "0.3.1",
            "protocol": {"minimum": 1, "maximum": 1},
            "published_at": "2026-07-16T00:00:00Z",
            "schema": "cognitive-card-skill-registry-v1",
            "source_commit": "1" * 40,
            "version": self.version,
        }
        manifest.update(changes)
        self.manifest_path.write_bytes(canonical(manifest))

    def replace_archive(self, data: bytes) -> None:
        self.archive.write_bytes(data)
        self.archive_digest = digest(data)
        self.checksum_path.write_text(
            f"{self.archive_digest}  cognitive-card-os.zip\n", encoding="ascii"
        )
        self.write_manifest()

    def reset_archive(self) -> bytes:
        self.archive, self.archive_digest = make_release(
            self.archive, self.version
        )
        self.checksum_path.write_text(
            f"{self.archive_digest}  cognitive-card-os.zip\n", encoding="ascii"
        )
        self.write_manifest()
        return self.archive.read_bytes()

    def environment(
        self,
        *,
        extra_env: dict[str, str] | None = None,
        unset_env: tuple[str, ...] = (),
    ) -> dict[str, str]:
        mapping = {
            MANIFEST_URL: str(self.manifest_path),
            self.archive_url: str(self.archive),
            self.checksum_url: str(self.checksum_path),
        }
        mapping.update(self.extra_mapping)
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{self.fake_bin}{os.pathsep}{environment['PATH']}",
                "FAKE_CURL_LOG": str(self.log),
                "FAKE_CURL_MAP": json.dumps(mapping),
                "HOME": str(self.base / "home"),
                "CODEX_HOME": str(self.install_root),
            }
        )
        if extra_env:
            environment.update(extra_env)
        for name in unset_env:
            environment.pop(name, None)
        return environment

    def run(
        self,
        *arguments: str,
        extra_env: dict[str, str] | None = None,
        unset_env: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALLER), *arguments],
            env=self.environment(extra_env=extra_env, unset_env=unset_env),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def popen(
        self, *arguments: str, extra_env: dict[str, str] | None = None
    ) -> subprocess.Popen[str]:
        return subprocess.Popen(
            ["bash", str(INSTALLER), *arguments],
            env=self.environment(extra_env=extra_env),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


class CardOsSkillInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.fixture = InstallerFixture(self.base)

    def assert_error(self, result: subprocess.CompletedProcess[str], code: str) -> None:
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(code, result.stderr)

    def test_cli_surface_and_real_flags(self) -> None:
        self.assertTrue(INSTALLER.is_file(), f"missing installer: {INSTALLER}")
        help_result = self.fixture.run("--help")
        self.assertEqual(0, help_result.returncode)
        for flag in ("--channel", "--version", "--check", "--rollback", "--install-root"):
            self.assertIn(flag, help_result.stdout)
        self.assert_error(self.fixture.run("--channel", "beta"), "INVALID_ARGUMENT")

    def test_fixed_urls_curl_q_and_malicious_curlrc_are_ignored(self) -> None:
        curlrc = self.base / ".curlrc"
        curlrc.write_text("--insecure\n--location\n", encoding="utf-8")
        result = self.fixture.run(
            "--channel", "stable", "--install-root", str(self.fixture.install_root),
            extra_env={"CURL_HOME": str(self.base)},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        calls = [json.loads(line) for line in self.fixture.log.read_text().splitlines()]
        self.assertEqual([MANIFEST_URL, self.fixture.archive_url], [call[-1] for call in calls])
        for call in calls:
            self.assertEqual("-q", call[0])
            self.assertIn("--proto", call)
            self.assertIn("=https", call)
            self.assertIn("--tlsv1.2", call)
            self.assertEqual("0", call[call.index("--max-redirs") + 1])
            for flag in ("--location", "--fail", "--silent", "--show-error", "--max-filesize", "--output"):
                self.assertIn(flag, call)
            self.assertNotIn("--insecure", call)

    def test_redirect_and_manifest_url_attacks_fail_closed(self) -> None:
        redirected = self.fixture.run(
            "--channel", "stable", extra_env={"FAKE_CURL_REDIRECT": MANIFEST_URL}
        )
        self.assert_error(redirected, "REDIRECT_REFUSED")
        attacks = [
            ("http://www.yutou.space/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip", "TLS_REQUIRED"),
            ("https://evil.invalid/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip", "REDIRECT_REFUSED"),
            ("https://user@www.yutou.space/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip", "REDIRECT_REFUSED"),
            (self.fixture.archive_url + "?x=1", "REDIRECT_REFUSED"),
            (self.fixture.archive_url + "#x", "REDIRECT_REFUSED"),
            (REGISTRY + "../secret", "REDIRECT_REFUSED"),
        ]
        for url, code in attacks:
            with self.subTest(url=url):
                self.fixture.write_manifest(archive_url=url)
                self.assert_error(self.fixture.run("--channel", "stable"), code)

    def test_manifest_schema_types_compatibility_and_installer_digest(self) -> None:
        mutations = [
            ({"schema": "wrong"}, "INVALID_MANIFEST"),
            ({"archive_size_bytes": True}, "INVALID_MANIFEST"),
            ({"version": "v1"}, "INVALID_MANIFEST"),
            ({"protocol": {"minimum": 2, "maximum": 2}}, "INCOMPATIBLE_PROTOCOL"),
            ({"minimum_server_version": "0.3.2"}, "INVALID_MANIFEST"),
            ({"installer": {"sha256": "0" * 64, "url": REGISTRY + "installers/" + "0" * 64 + "/install.sh"}}, "INSTALLER_DIGEST_MISMATCH"),
        ]
        for changes, code in mutations:
            with self.subTest(changes=changes):
                self.fixture.write_manifest(**changes)
                self.assert_error(self.fixture.run("--channel", "stable"), code)
        self.fixture.write_manifest()
        with self.fixture.manifest_path.open("ab") as manifest:
            manifest.write(b" \n")
        self.assert_error(self.fixture.run("--channel", "stable"), "INVALID_MANIFEST")

    def test_published_at_requires_real_canonical_utc_datetime(self) -> None:
        invalid = (
            "2026-99-99T99:99:99Z",
            "2025-02-29T00:00:00Z",
            "2026-01-01T24:00:00Z",
            "2026-01-01T00:00:60Z",
            "2026-01-01T00:00:00+00:00",
        )
        for timestamp in invalid:
            with self.subTest(timestamp=timestamp):
                self.fixture.write_manifest(published_at=timestamp)
                self.assert_error(
                    self.fixture.run("--channel", "stable"), "INVALID_MANIFEST"
                )

    def test_digest_and_unsafe_zip_fail_before_active_mutation(self) -> None:
        self.fixture.write_manifest(archive_sha256="2" * 64)
        self.assert_error(self.fixture.run("--channel", "stable"), "DIGEST_MISMATCH")
        self.assertFalse((self.fixture.install_root / "skills" / "cognitive-card-os").exists())

    def test_zip_central_directory_and_unsafe_member_regressions(self) -> None:
        member = "cognitive-card-os/SKILL.md"

        def duplicate(data: bytes) -> bytes:
            self.fixture.archive.write_bytes(data)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(self.fixture.archive, "a") as archive:
                    archive.writestr(member, b"duplicate")
            return self.fixture.archive.read_bytes()

        def append_member(data: bytes, name: str) -> bytes:
            self.fixture.archive.write_bytes(data)
            with zipfile.ZipFile(self.fixture.archive, "a") as archive:
                archive.writestr(name, b"unexpected")
            return self.fixture.archive.read_bytes()

        raw_name = member.encode("ascii")
        attacks = {
            "duplicate normalized name": duplicate,
            "symlink mode": lambda data: mutate_zip_headers(
                data, member, external_attr=(stat.S_IFLNK | 0o777) << 16
            ),
            "device mode": lambda data: mutate_zip_headers(
                data, member, external_attr=(stat.S_IFCHR | 0o600) << 16
            ),
            "macOS metadata": lambda data: append_member(
                data, "__MACOSX/._SKILL.md"
            ),
            "undeclared closure": lambda data: append_member(
                data, "cognitive-card-os/README.md"
            ),
            "central local name mismatch": lambda data: mutate_zip_headers(
                data,
                member,
                local_name=raw_name[:-1] + (b"x" if raw_name[-1:] != b"x" else b"y"),
            ),
            "central raw NUL": lambda data: mutate_zip_headers(
                data, member, central_name=b"\x00" + raw_name[1:]
            ),
            "member size limit": lambda data: mutate_zip_headers(
                data, member, uncompressed_size=8 * 1024 * 1024 + 1
            ),
            "total size limit": lambda data: mutate_zip_headers(
                mutate_zip_headers(
                    mutate_zip_headers(
                        data,
                        "cognitive-card-os/SKILL.md",
                        uncompressed_size=7 * 1024 * 1024,
                    ),
                    "cognitive-card-os/agents/openai.yaml",
                    uncompressed_size=7 * 1024 * 1024,
                ),
                "cognitive-card-os/references/protocol.md",
                uncompressed_size=7 * 1024 * 1024,
            ),
        }
        for name, mutate in attacks.items():
            with self.subTest(attack=name):
                data = self.fixture.reset_archive()
                self.fixture.replace_archive(mutate(data))
                before = self.snapshot(self.fixture.install_root)
                result = self.fixture.run("--channel", "stable")
                self.assert_error(result, "UNSAFE_ARCHIVE")
                self.assertEqual(before, self.snapshot(self.fixture.install_root))
        self.fixture.write_manifest()
        with zipfile.ZipFile(self.fixture.archive, "a") as archive:
            archive.writestr("../escape", b"bad")
        self.fixture.archive_digest = digest(self.fixture.archive.read_bytes())
        self.fixture.write_manifest()
        self.assert_error(self.fixture.run("--channel", "stable"), "UNSAFE_ARCHIVE")
        self.assertFalse((self.fixture.install_root / "skills" / "cognitive-card-os").exists())

    def test_first_install_cache_state_and_idempotency(self) -> None:
        result = self.fixture.run("--channel", "stable")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("restart Codex", result.stdout)
        active = self.fixture.install_root / "skills" / "cognitive-card-os"
        self.assertTrue(active.is_dir())
        self.assertFalse(active.is_symlink())
        key = f"0.1.0-{self.fixture.archive_digest}"
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        cache = history / key
        self.assertEqual(self.fixture.archive.read_bytes(), (cache / "cognitive-card-os.zip").read_bytes())
        self.assertTrue((cache / "skill" / "cognitive-card-os" / "release.json").is_file())
        state_bytes = (history / "state.json").read_bytes()
        state = json.loads(state_bytes)
        self.assertEqual(canonical(state), state_bytes)
        self.assertEqual(0o600, stat.S_IMODE((history / "state.json").stat().st_mode))
        self.assertEqual({"schema", "active", "previous"}, set(state))
        self.assertIsNone(state["previous"])
        self.assertEqual({"version": "0.1.0", "archive_sha256": self.fixture.archive_digest}, state["active"])
        before = self.snapshot(self.fixture.install_root)
        again = self.fixture.run("--channel", "stable")
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual(before, self.snapshot(self.fixture.install_root))

    def test_isolated_installs_have_identical_active_bytes_and_modes(self) -> None:
        install_a = self.base / "isolated-a"
        install_b = self.base / "isolated-b"
        first = self.fixture.run(
            "--channel", "stable", "--install-root", str(install_a)
        )
        second = self.fixture.run(
            "--channel", "stable", "--install-root", str(install_b)
        )
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)

        active_a = install_a / "skills" / "cognitive-card-os"
        active_b = install_b / "skills" / "cognitive-card-os"
        snapshot_a = self.exact_snapshot(active_a)
        snapshot_b = self.exact_snapshot(active_b)
        self.assertTrue(snapshot_a)
        self.assertEqual(snapshot_a, snapshot_b)

    def test_default_codex_home_and_explicit_root(self) -> None:
        explicit = self.base / "explicit"
        result = self.fixture.run("--channel", "stable", "--install-root", str(explicit))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((explicit / "skills" / "cognitive-card-os").is_dir())
        self.assertFalse((self.fixture.install_root / "skills" / "cognitive-card-os").exists())
        home_fixture = InstallerFixture(self.base / "home-fallback")
        fallback = home_fixture.run("--channel", "stable", unset_env=("CODEX_HOME",))
        self.assertEqual(0, fallback.returncode, fallback.stderr)
        self.assertTrue((home_fixture.base / "home" / ".codex" / "skills" / "cognitive-card-os").is_dir())

    def test_unmanaged_active_is_refused_without_mutation(self) -> None:
        active = self.fixture.install_root / "skills" / "cognitive-card-os"
        active.mkdir(parents=True)
        (active / "owned.txt").write_bytes(b"user-owned")
        before = self.snapshot(self.fixture.install_root)
        result = self.fixture.run("--channel", "stable")
        self.assert_error(result, "UNMANAGED_ACTIVE_SKILL")
        self.assertEqual(before, self.snapshot(self.fixture.install_root))

    def test_state_bound_drift_is_refused_without_any_install_root_mutation(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        active_skill = self.fixture.install_root / "skills" / "cognitive-card-os" / "SKILL.md"
        active_skill.write_bytes(active_skill.read_bytes() + b"drift")
        before = self.snapshot(self.fixture.install_root)
        upgraded = InstallerFixture(self.base / "drift-upgrade", "0.2.0", b"upgrade")
        upgraded.install_root = self.fixture.install_root
        result = upgraded.run("--channel", "stable")
        self.assert_error(result, "UNMANAGED_ACTIVE_SKILL")
        self.assertEqual(before, self.snapshot(self.fixture.install_root))

    def test_upgrade_rollback_uses_pointer_and_swaps_identities(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        old_digest = self.fixture.archive_digest
        upgraded = InstallerFixture(self.base / "upgrade", "0.2.0", b"upgrade")
        upgraded.install_root = self.fixture.install_root

        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        active = self.fixture.install_root / "skills" / "cognitive-card-os"
        before_active = self.snapshot(active)
        before_state = (history / "state.json").read_bytes()
        failed = upgraded.run(
            "--version",
            "0.2.0",
            extra_env={"CARD_OS_INSTALL_ERROR": "after_new_active"},
        )
        self.assert_error(failed, "INJECTED_INSTALL_FAILURE")
        self.assertEqual(before_active, self.snapshot(active))
        self.assertEqual(before_state, (history / "state.json").read_bytes())

        self.assertEqual(0, upgraded.run("--version", "0.2.0").returncode)
        state = json.loads((history / "state.json").read_bytes())
        self.assertEqual("0.2.0", state["active"]["version"])
        self.assertEqual({"version": "0.1.0", "archive_sha256": old_digest}, state["previous"])
        rolled = upgraded.run("--rollback")
        self.assertEqual(0, rolled.returncode, rolled.stderr)
        state = json.loads((history / "state.json").read_bytes())
        self.assertEqual("0.1.0", state["active"]["version"])
        self.assertEqual("0.2.0", state["previous"]["version"])

    def test_exact_version_can_use_verified_immutable_release(self) -> None:
        historical = InstallerFixture(self.base / "historical", "0.1.0", b"old")
        stable = InstallerFixture(self.base / "stable", "0.2.0", b"stable")
        stable.extra_mapping.update(
            {
                historical.archive_url: str(historical.archive),
                historical.checksum_url: str(historical.checksum_path),
            }
        )
        result = stable.run("--version", "0.1.0")
        self.assertEqual(0, result.returncode, result.stderr)
        history = stable.install_root / "skill-releases" / "cognitive-card-os"
        state = json.loads((history / "state.json").read_bytes())
        self.assertEqual("0.1.0", state["active"]["version"])
        self.assertEqual(historical.archive_digest, state["active"]["archive_sha256"])

    def test_check_is_write_free_and_invalid_rollback_preserves_active(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        before = self.snapshot(self.fixture.install_root)
        checked = self.fixture.run("--check")
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertEqual(before, self.snapshot(self.fixture.install_root))
        rolled = self.fixture.run("--rollback")
        self.assert_error(rolled, "ROLLBACK_UNAVAILABLE")
        self.assertEqual(before, self.snapshot(self.fixture.install_root))

    def test_crash_transitions_recover_old_or_committed_state(self) -> None:
        for fault in ("after_extract", "after_journal", "after_old_moved", "after_new_active", "after_state"):
            with self.subTest(fault=fault):
                case = self.base / fault
                first = InstallerFixture(case / "first", "0.1.0")
                self.assertEqual(0, first.run("--channel", "stable").returncode)
                old_active = self.tree_digest(first.install_root / "skills" / "cognitive-card-os")
                second = InstallerFixture(case / "second", "0.2.0", b"new")
                second.install_root = first.install_root
                crashed = second.run("--channel", "stable", extra_env={"CARD_OS_INSTALL_FAULT": fault})
                self.assertNotEqual(0, crashed.returncode)
                recovered = second.run("--channel", "stable")
                self.assertEqual(0, recovered.returncode, recovered.stderr)
                state = json.loads((first.install_root / "skill-releases" / "cognitive-card-os" / "state.json").read_bytes())
                self.assertEqual("0.2.0", state["active"]["version"])
                self.assertNotEqual(old_active, self.tree_digest(first.install_root / "skills" / "cognitive-card-os"))
                self.assertFalse((first.install_root / "skill-releases" / "cognitive-card-os" / "transaction.json").exists())

    def test_ordinary_activation_failures_restore_old_state_immediately(self) -> None:
        for point in ("after_journal", "after_old_moved", "after_new_active"):
            with self.subTest(point=point):
                case = self.base / f"ordinary-{point}"
                first = InstallerFixture(case / "first", "0.1.0")
                self.assertEqual(0, first.run("--channel", "stable").returncode)
                before = self.snapshot(first.install_root)
                second = InstallerFixture(case / "second", "0.2.0", b"new")
                second.install_root = first.install_root
                failed = second.run("--channel", "stable", extra_env={"CARD_OS_INSTALL_ERROR": point})
                self.assert_error(failed, "INJECTED_INSTALL_FAILURE")
                after = self.snapshot(first.install_root)
                # The newly verified immutable cache may remain, but active and state are restored.
                active = "skills/cognitive-card-os/"
                for path, value in before.items():
                    if path.startswith(active) or path.endswith("state.json"):
                        self.assertEqual(value, after.get(path), path)
                history = first.install_root / "skill-releases" / "cognitive-card-os"
                self.assertFalse((history / "transaction.json").exists())
                self.assertFalse((first.install_root / "skills" / ".cognitive-card-os.backup").exists())
                self.assertFalse((first.install_root / "skills" / ".cognitive-card-os.new").exists())

    def test_after_state_ordinary_failure_rolls_back_immediately(self) -> None:
        first = InstallerFixture(self.base / "ordinary-after-state-first", "0.1.0")
        self.assertEqual(0, first.run("--channel", "stable").returncode)
        history = first.install_root / "skill-releases" / "cognitive-card-os"
        before_active = self.snapshot(first.install_root / "skills" / "cognitive-card-os")
        before_state = (history / "state.json").read_bytes()
        second = InstallerFixture(
            self.base / "ordinary-after-state-second", "0.2.0", b"new"
        )
        second.install_root = first.install_root
        failed = second.run(
            "--channel", "stable", extra_env={"CARD_OS_INSTALL_ERROR": "after_state"}
        )
        self.assert_error(failed, "INJECTED_INSTALL_FAILURE")
        self.assertEqual(
            before_active,
            self.snapshot(first.install_root / "skills" / "cognitive-card-os"),
        )
        self.assertEqual(before_state, (history / "state.json").read_bytes())
        self.assertFalse((history / "transaction.json").exists())
        self.assertFalse((first.install_root / "skills" / ".cognitive-card-os.backup").exists())
        self.assertFalse((first.install_root / "skills" / ".cognitive-card-os.new").exists())

    def test_skills_parent_fsync_trace_proves_activation_and_recovery_order(self) -> None:
        trace_env = {"CARD_OS_INSTALL_TEST_TRACE": "1"}
        first = InstallerFixture(self.base / "trace-first", "0.1.0")
        initial = first.run("--channel", "stable", extra_env=trace_env)
        self.assertEqual(0, initial.returncode, initial.stderr)
        self.assertEqual(
            ["replace:new->active"], self.transition_trace(initial.stderr)
        )

        second = InstallerFixture(self.base / "trace-second", "0.2.0", b"new")
        second.install_root = first.install_root
        upgraded = second.run("--channel", "stable", extra_env=trace_env)
        self.assertEqual(0, upgraded.returncode, upgraded.stderr)
        self.assertEqual(
            [
                "replace:active->backup",
                "replace:new->active",
                "replace:backup->cleanup-trash",
                "delete:cleanup-trash",
            ],
            self.transition_trace(upgraded.stderr),
        )

        rollback_case = InstallerFixture(self.base / "trace-rollback", "0.3.0", b"next")
        rollback_case.install_root = first.install_root
        crashed = rollback_case.run(
            "--channel",
            "stable",
            extra_env={**trace_env, "CARD_OS_INSTALL_FAULT": "after_old_moved"},
        )
        self.assertNotEqual(0, crashed.returncode)
        self.assertEqual(
            ["replace:active->backup"], self.transition_trace(crashed.stderr)
        )
        recovered = rollback_case.run("--channel", "stable", extra_env=trace_env)
        self.assertEqual(0, recovered.returncode, recovered.stderr)
        self.assertEqual(
            [
                "replace:new->recovery-trash",
                "replace:backup->active",
                "delete:recovery-trash",
                "replace:active->backup",
                "replace:new->active",
                "replace:backup->cleanup-trash",
                "delete:cleanup-trash",
            ],
            self.transition_trace(recovered.stderr),
        )

        active_delete_case = InstallerFixture(
            self.base / "trace-active-delete", "0.3.1", b"active-delete"
        )
        active_delete_case.install_root = first.install_root
        active_delete_crash = active_delete_case.run(
            "--channel",
            "stable",
            extra_env={**trace_env, "CARD_OS_INSTALL_FAULT": "after_new_active"},
        )
        self.assertNotEqual(0, active_delete_crash.returncode)
        self.assertEqual(
            ["replace:active->backup", "replace:new->active"],
            self.transition_trace(active_delete_crash.stderr),
        )
        active_delete_recovery = active_delete_case.run(
            "--channel", "stable", extra_env=trace_env
        )
        self.assertEqual(
            0, active_delete_recovery.returncode, active_delete_recovery.stderr
        )
        self.assertEqual(
            [
                "replace:active->recovery-trash",
                "replace:backup->active",
                "delete:recovery-trash",
                "replace:active->backup",
                "replace:new->active",
                "replace:backup->cleanup-trash",
                "delete:cleanup-trash",
            ],
            self.transition_trace(active_delete_recovery.stderr),
        )

        committed_case = InstallerFixture(
            self.base / "trace-committed", "0.4.0", b"committed"
        )
        committed_case.install_root = first.install_root
        committed_crash = committed_case.run(
            "--channel",
            "stable",
            extra_env={**trace_env, "CARD_OS_INSTALL_FAULT": "after_state"},
        )
        self.assertNotEqual(0, committed_crash.returncode)
        self.assertEqual(
            ["replace:active->backup", "replace:new->active"],
            self.transition_trace(committed_crash.stderr),
        )
        committed_recovery = committed_case.run(
            "--channel", "stable", extra_env=trace_env
        )
        self.assertEqual(0, committed_recovery.returncode, committed_recovery.stderr)
        self.assertEqual(
            ["replace:backup->cleanup-trash", "delete:cleanup-trash"],
            self.transition_trace(committed_recovery.stderr),
        )

    def test_committed_backup_cleanup_is_reentrant_in_success_and_recovery_paths(self) -> None:
        for path_kind in ("normal-success", "committed-recovery"):
            with self.subTest(path_kind=path_kind):
                case = self.base / f"commit-cleanup-{path_kind}"
                first = InstallerFixture(case / "first", "0.1.0")
                self.assertEqual(0, first.run("--channel", "stable").returncode)
                second = InstallerFixture(case / "second", "0.2.0", b"new")
                second.install_root = first.install_root
                history = first.install_root / "skill-releases" / "cognitive-card-os"
                skills = first.install_root / "skills"

                if path_kind == "committed-recovery":
                    committed = second.run(
                        "--channel",
                        "stable",
                        extra_env={"CARD_OS_INSTALL_FAULT": "after_state"},
                    )
                    self.assertNotEqual(0, committed.returncode)

                interrupted = second.run(
                    "--channel",
                    "stable",
                    extra_env={"CARD_OS_INSTALL_FAULT": "commit_during_cleanup"},
                )
                self.assertNotEqual(0, interrupted.returncode)
                journal = json.loads((history / "transaction.json").read_bytes())
                self.assertEqual("commit_cleanup", journal["phase"])
                cleanup_trash = skills / ".cognitive-card-os.cleanup-trash"
                self.assertTrue(cleanup_trash.is_dir())
                self.assertFalse((skills / ".cognitive-card-os.backup").exists())
                old_cache = (
                    history
                    / f"0.1.0-{first.archive_digest}"
                    / "skill"
                    / "cognitive-card-os"
                )
                self.assertNotEqual(
                    self.snapshot(old_cache), self.snapshot(cleanup_trash)
                )
                state = json.loads((history / "state.json").read_bytes())
                self.assertEqual("0.2.0", state["active"]["version"])

                recovered = second.run("--channel", "stable")
                self.assertEqual(0, recovered.returncode, recovered.stderr)
                self.assertFalse((history / "transaction.json").exists())
                self.assertFalse(cleanup_trash.exists())
                self.assertFalse((skills / ".cognitive-card-os.backup").exists())
                state = json.loads((history / "state.json").read_bytes())
                self.assertEqual("0.2.0", state["active"]["version"])

    def test_rollback_recovery_is_reentrant_across_nested_interruptions(self) -> None:
        fault_expectations = {
            "recovery_after_active_trashed": {
                "phase": "rollback_trash_pending",
                "active": False,
                "backup": True,
                "trash_complete": True,
            },
            "recovery_after_backup_restored": {
                "phase": "rollback_active_trashed",
                "active": True,
                "backup": False,
                "trash_complete": True,
            },
            "recovery_during_trash_cleanup": {
                "phase": "rollback_cleanup",
                "active": True,
                "backup": False,
                "trash_complete": False,
            },
        }
        for recovery_fault, expected in fault_expectations.items():
            with self.subTest(recovery_fault=recovery_fault):
                case = self.base / recovery_fault
                first = InstallerFixture(case / "first", "0.1.0")
                self.assertEqual(0, first.run("--channel", "stable").returncode)
                active = first.install_root / "skills" / "cognitive-card-os"
                old_active = self.snapshot(active)
                history = first.install_root / "skill-releases" / "cognitive-card-os"
                old_state = (history / "state.json").read_bytes()

                second = InstallerFixture(case / "second", "0.2.0", b"new")
                second.install_root = first.install_root
                interrupted_upgrade = second.run(
                    "--channel",
                    "stable",
                    extra_env={"CARD_OS_INSTALL_FAULT": "after_new_active"},
                )
                self.assertNotEqual(0, interrupted_upgrade.returncode)
                journal_path = history / "transaction.json"
                journal = json.loads(journal_path.read_bytes())
                self.assertEqual("old_moved", journal["phase"])

                interrupted_recovery = second.run(
                    "--rollback",
                    extra_env={"CARD_OS_INSTALL_FAULT": recovery_fault},
                )
                self.assertNotEqual(0, interrupted_recovery.returncode)
                journal = json.loads(journal_path.read_bytes())
                self.assertEqual(expected["phase"], journal["phase"])
                backup = first.install_root / "skills" / ".cognitive-card-os.backup"
                trash = first.install_root / "skills" / ".cognitive-card-os.recovery-trash"
                self.assertEqual(expected["active"], active.is_dir())
                self.assertEqual(expected["backup"], backup.is_dir())
                self.assertTrue(trash.is_dir())
                new_cache = history / f"0.2.0-{second.archive_digest}" / "skill" / "cognitive-card-os"
                self.assertEqual(
                    expected["trash_complete"],
                    self.snapshot(trash) == self.snapshot(new_cache),
                )

                recovered = second.run("--rollback")
                self.assert_error(recovered, "ROLLBACK_UNAVAILABLE")
                self.assertEqual(old_active, self.snapshot(active))
                self.assertEqual(old_state, (history / "state.json").read_bytes())
                self.assertFalse(journal_path.exists())
                self.assertFalse(backup.exists())
                self.assertFalse(trash.exists())

    def test_recovery_trash_is_journal_bound_and_unexpected_states_fail_closed(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        skills = self.fixture.install_root / "skills"
        active = skills / "cognitive-card-os"
        trash = skills / ".cognitive-card-os.recovery-trash"
        shutil.copytree(active, trash)
        before = self.snapshot(self.fixture.install_root)
        unexpected = self.fixture.run("--channel", "stable")
        self.assert_error(unexpected, "INVALID_JOURNAL")
        self.assertEqual(before, self.snapshot(self.fixture.install_root))
        shutil.rmtree(trash)

        upgraded = InstallerFixture(self.base / "trash-binding-upgrade", "0.2.0", b"new")
        upgraded.install_root = self.fixture.install_root
        crashed = upgraded.run(
            "--channel", "stable", extra_env={"CARD_OS_INSTALL_FAULT": "after_new_active"}
        )
        self.assertNotEqual(0, crashed.returncode)
        trashed = upgraded.run(
            "--rollback",
            extra_env={"CARD_OS_INSTALL_FAULT": "recovery_after_active_trashed"},
        )
        self.assertNotEqual(0, trashed.returncode)
        (trash / "SKILL.md").write_bytes(b"unexpected identity")
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        backup = skills / ".cognitive-card-os.backup"
        before_active = self.snapshot(active)
        before_backup = self.snapshot(backup)
        before_trash = self.snapshot(trash)
        before_state = (history / "state.json").read_bytes()
        before_journal = (history / "transaction.json").read_bytes()
        refused = upgraded.run("--rollback")
        self.assert_error(refused, "INVALID_JOURNAL")
        self.assertEqual(before_active, self.snapshot(active))
        self.assertEqual(before_backup, self.snapshot(backup))
        self.assertEqual(before_trash, self.snapshot(trash))
        self.assertEqual(before_state, (history / "state.json").read_bytes())
        self.assertEqual(before_journal, (history / "transaction.json").read_bytes())

    def test_first_install_durability_chain_and_published_cache_crash_recovery(self) -> None:
        traced = InstallerFixture(self.base / "durability-trace", "0.1.0")
        result = traced.run(
            "--channel", "stable", extra_env={"CARD_OS_INSTALL_TEST_DURABILITY_TRACE": "1"}
        )
        self.assertEqual(0, result.returncode, result.stderr)
        events = self.durability_trace(result.stderr)
        required = [
            "setup:root",
            "setup:skills",
            "setup:releases",
            "setup:history",
            "lock:container",
            "cache:contents",
            "cache:published",
            "active:new",
            "active:published",
            "state:published",
        ]
        cursor = 0
        for event in events:
            if cursor < len(required) and event == required[cursor]:
                cursor += 1
        self.assertEqual(len(required), cursor, events)

        crashed = InstallerFixture(self.base / "durability-crash", "0.1.0")
        interrupted = crashed.run(
            "--channel",
            "stable",
            extra_env={"CARD_OS_INSTALL_DURABILITY_FAULT": "cache:published"},
        )
        self.assertNotEqual(0, interrupted.returncode)
        key = f"0.1.0-{crashed.archive_digest}"
        cache = crashed.install_root / "skill-releases" / "cognitive-card-os" / key
        self.assertTrue((cache / "cognitive-card-os.zip").is_file())
        self.assertTrue((cache / "skill" / "cognitive-card-os" / "release.json").is_file())
        recovered = crashed.run("--channel", "stable")
        self.assertEqual(0, recovered.returncode, recovered.stderr)
        self.assertNotIn("INVALID_CACHE", recovered.stderr)

    def test_pre_journal_active_new_crash_is_reclaimed_before_next_operation(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        active = self.fixture.install_root / "skills" / "cognitive-card-os"
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        state_before = (history / "state.json").read_bytes()
        active_before = self.snapshot(active)
        old_key = f"0.1.0-{self.fixture.archive_digest}"
        old_cache_before = self.snapshot(history / old_key)

        upgraded = InstallerFixture(
            self.base / "pre-journal-upgrade", "0.2.0", b"pre-journal"
        )
        upgraded.install_root = self.fixture.install_root
        interrupted = upgraded.run(
            "--channel",
            "stable",
            extra_env={"CARD_OS_INSTALL_DURABILITY_FAULT": "active:new"},
        )
        self.assertNotEqual(0, interrupted.returncode)
        orphan = self.fixture.install_root / "skills" / ".cognitive-card-os.new"
        backup = self.fixture.install_root / "skills" / ".cognitive-card-os.backup"
        self.assertTrue(orphan.is_dir())
        self.assertFalse((history / "transaction.json").exists())
        self.assertFalse(backup.exists())

        checked = self.fixture.run(
            "--channel",
            "stable",
            extra_env={"CARD_OS_INSTALL_TEST_TRACE": "1"},
        )
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertEqual(
            ["replace:new->cleanup-trash", "delete:cleanup-trash"],
            self.transition_trace(checked.stderr),
        )
        self.assertFalse(orphan.exists())
        self.assertEqual(active_before, self.snapshot(active))
        self.assertEqual(state_before, (history / "state.json").read_bytes())
        self.assertEqual(old_cache_before, self.snapshot(history / old_key))

        completed = upgraded.run("--channel", "stable")
        self.assertEqual(0, completed.returncode, completed.stderr)
        state = json.loads((history / "state.json").read_bytes())
        self.assertEqual("0.2.0", state["active"]["version"])
        self.assertEqual("0.1.0", state["previous"]["version"])

    def test_pre_journal_staging_cleanup_is_reentrant_after_partial_delete(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        skills = self.fixture.install_root / "skills"
        active = skills / "cognitive-card-os"
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        active_before = self.snapshot(active)
        state_before = (history / "state.json").read_bytes()
        upgraded = InstallerFixture(
            self.base / "pre-journal-nested", "0.2.0", b"pre-journal-nested"
        )
        upgraded.install_root = self.fixture.install_root

        staged = upgraded.run(
            "--channel",
            "stable",
            extra_env={"CARD_OS_INSTALL_DURABILITY_FAULT": "active:new"},
        )
        self.assertNotEqual(0, staged.returncode)
        interrupted = self.fixture.run(
            "--channel",
            "stable",
            extra_env={"CARD_OS_INSTALL_FAULT": "prejournal_during_cleanup"},
        )
        self.assertNotEqual(0, interrupted.returncode)
        cleanup_record = history / "cleanup.json"
        cleanup_trash = skills / ".cognitive-card-os.cleanup-trash"
        self.assertTrue(cleanup_record.is_file())
        self.assertTrue(cleanup_trash.is_dir())
        self.assertFalse((skills / ".cognitive-card-os.new").exists())
        staged_cache = (
            history
            / f"0.2.0-{upgraded.archive_digest}"
            / "skill"
            / "cognitive-card-os"
        )
        self.assertNotEqual(self.snapshot(staged_cache), self.snapshot(cleanup_trash))

        recovered = self.fixture.run("--channel", "stable")
        self.assertEqual(0, recovered.returncode, recovered.stderr)
        self.assertEqual(active_before, self.snapshot(active))
        self.assertEqual(state_before, (history / "state.json").read_bytes())
        self.assertFalse(cleanup_record.exists())
        self.assertFalse(cleanup_trash.exists())

    def test_check_rejects_every_unexpected_transaction_topology_without_writes(self) -> None:
        transient_names = (
            ".cognitive-card-os.new",
            ".cognitive-card-os.backup",
            ".cognitive-card-os.recovery-trash",
            ".cognitive-card-os.cleanup-trash",
        )
        for name in transient_names:
            with self.subTest(name=name):
                case = self.base / f"check-topology-{name.removeprefix('.')}"
                fixture = InstallerFixture(case, "0.1.0")
                self.assertEqual(0, fixture.run("--channel", "stable").returncode)
                skills = fixture.install_root / "skills"
                shutil.copytree(skills / "cognitive-card-os", skills / name)
                before = self.snapshot(fixture.install_root)
                checked = fixture.run("--check")
                self.assert_error(checked, "INVALID_JOURNAL")
                self.assertEqual(before, self.snapshot(fixture.install_root))

        record_case = InstallerFixture(self.base / "check-topology-record", "0.1.0")
        self.assertEqual(0, record_case.run("--channel", "stable").returncode)
        history = record_case.install_root / "skill-releases" / "cognitive-card-os"
        (history / "cleanup.json").write_bytes(b"{}\n")
        (history / "cleanup.json").chmod(0o600)
        before = self.snapshot(record_case.install_root)
        checked = record_case.run("--check")
        self.assert_error(checked, "INVALID_JOURNAL")
        self.assertEqual(before, self.snapshot(record_case.install_root))

    def test_no_journal_unexpected_new_backup_combinations_fail_closed(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        skills = self.fixture.install_root / "skills"
        active = skills / "cognitive-card-os"
        new_active = skills / ".cognitive-card-os.new"
        backup = skills / ".cognitive-card-os.backup"

        cases = ("backup-only", "new-and-backup", "invalid-new")
        for case in cases:
            with self.subTest(case=case):
                if new_active.exists():
                    shutil.rmtree(new_active)
                if backup.exists():
                    shutil.rmtree(backup)
                if case in {"new-and-backup", "invalid-new"}:
                    shutil.copytree(active, new_active)
                if case in {"backup-only", "new-and-backup"}:
                    shutil.copytree(active, backup)
                if case == "invalid-new":
                    (new_active / "SKILL.md").write_bytes(b"not-a-cache-tree")
                before = self.snapshot(self.fixture.install_root)
                result = self.fixture.run("--channel", "stable")
                self.assert_error(result, "INVALID_JOURNAL")
                self.assertEqual(before, self.snapshot(self.fixture.install_root))

    def test_lock_rejects_true_holder_and_recovers_reused_live_pid(self) -> None:
        first = InstallerFixture(self.base / "lock-first", "0.1.0")
        self.assertEqual(0, first.run("--channel", "stable").returncode)
        upgraded = InstallerFixture(self.base / "lock-upgrade", "0.2.0", b"upgrade")
        upgraded.install_root = first.install_root
        ready = self.base / "lock-ready"
        token = "ccos_v1." + "b" * 32 + ".owner_secret"
        holder = upgraded.popen(
            "--channel",
            "stable",
            extra_env={
                "CARD_OS_INSTALL_TEST_LOCK_READY": str(ready),
                "CARD_OS_INSTALL_TEST_HOLD_LOCK_SECONDS": "5",
                "CARD_OS_TOKEN": token,
            },
        )
        self.addCleanup(lambda: holder.poll() is None and holder.kill())
        deadline = time.monotonic() + 4
        while not ready.exists() and holder.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        if not ready.exists():
            holder_out, holder_err = holder.communicate(timeout=1)
            self.fail(holder_out + holder_err)
        locked = upgraded.run("--channel", "stable")
        self.assert_error(locked, "INSTALL_LOCKED")
        owner_path = (
            first.install_root / "skill-releases" / "cognitive-card-os" / ".lock" / "owner.json"
        )
        owner_bytes = owner_path.read_bytes()
        owner = json.loads(owner_bytes)
        self.assertEqual(canonical(owner), owner_bytes)
        self.assertEqual({"schema", "pid", "identity"}, set(owner))
        self.assertRegex(owner["identity"], r"^[0-9a-f]{64}$")
        self.assertNotIn(str(first.install_root), owner_bytes.decode("ascii"))
        self.assertNotIn(token, owner_bytes.decode("ascii"))
        holder_out, holder_err = holder.communicate(timeout=10)
        self.assertEqual(0, holder.returncode, holder_out + holder_err)

        crashed = InstallerFixture(self.base / "lock-crash", "0.3.0", b"crash")
        crashed.install_root = first.install_root
        interrupted = crashed.run(
            "--channel", "stable", extra_env={"CARD_OS_INSTALL_FAULT": "after_old_moved"}
        )
        self.assertNotEqual(0, interrupted.returncode)
        history = first.install_root / "skill-releases" / "cognitive-card-os"
        self.assertTrue((history / "transaction.json").is_file())
        unrelated = subprocess.Popen(["sleep", "10"])
        self.addCleanup(self.stop_process, unrelated)
        stale_owner = {
            "schema": "cognitive-card-skill-install-lock-owner-v1",
            "pid": unrelated.pid,
            "identity": "0" * 64,
        }
        owner_path.write_bytes(canonical(stale_owner))
        owner_path.chmod(0o600)
        recovered = crashed.run("--channel", "stable")
        self.assertEqual(0, recovered.returncode, recovered.stderr)
        self.assertFalse((history / "transaction.json").exists())
        state = json.loads((history / "state.json").read_bytes())
        self.assertEqual("0.3.0", state["active"]["version"])
        self.stop_process(unrelated)

    def test_tampered_previous_cache_makes_rollback_write_free(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        old_digest = self.fixture.archive_digest
        upgraded = InstallerFixture(self.base / "tampered-upgrade", "0.2.0", b"upgrade")
        upgraded.install_root = self.fixture.install_root
        self.assertEqual(0, upgraded.run("--channel", "stable").returncode)
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
        old_zip = history / f"0.1.0-{old_digest}" / "cognitive-card-os.zip"
        old_zip.write_bytes(old_zip.read_bytes() + b"tamper")
        before_active = self.snapshot(self.fixture.install_root / "skills" / "cognitive-card-os")
        before_state = (history / "state.json").read_bytes()
        result = upgraded.run("--rollback")
        self.assert_error(result, "INVALID_CACHE")
        self.assertEqual(before_active, self.snapshot(self.fixture.install_root / "skills" / "cognitive-card-os"))
        self.assertEqual(before_state, (history / "state.json").read_bytes())

    def test_token_shapes_never_appear_in_output_or_curl_argv(self) -> None:
        token = "ccos_v1." + "a" * 32 + ".SECRET_value"
        result = self.fixture.run("--channel", "stable", extra_env={"CARD_OS_TOKEN": token})
        combined = result.stdout + result.stderr
        self.assertNotIn(token, combined)
        self.assertNotIn(token, self.fixture.log.read_text() if self.fixture.log.exists() else "")

    @staticmethod
    def snapshot(path: Path) -> dict[str, tuple[int, str]]:
        if not path.exists():
            return {}
        result: dict[str, tuple[int, str]] = {}
        for item in sorted(path.rglob("*")):
            relative = item.relative_to(path).as_posix()
            mode = stat.S_IMODE(item.lstat().st_mode)
            if item.is_file() and not item.is_symlink():
                value = digest(item.read_bytes())
            elif item.is_dir() and not item.is_symlink():
                value = "dir"
            else:
                value = "link"
            result[relative] = (mode, value)
        return result

    @staticmethod
    def exact_snapshot(path: Path) -> dict[str, tuple[int, bytes | None]]:
        result: dict[str, tuple[int, bytes | None]] = {}
        for item in [path, *sorted(path.rglob("*"))]:
            relative = "." if item == path else item.relative_to(path).as_posix()
            mode = stat.S_IMODE(item.lstat().st_mode)
            result[relative] = (
                mode,
                item.read_bytes() if item.is_file() and not item.is_symlink() else None,
            )
        return result

    @staticmethod
    def tree_digest(path: Path) -> str:
        return digest(canonical(CardOsSkillInstallerTests.snapshot(path)))

    @staticmethod
    def transition_trace(stderr: str) -> list[str]:
        prefix = "CARD_OS_INSTALL_TEST_TRACE:"
        return [line[len(prefix) :] for line in stderr.splitlines() if line.startswith(prefix)]

    @staticmethod
    def durability_trace(stderr: str) -> list[str]:
        prefix = "CARD_OS_INSTALL_TEST_DURABILITY_TRACE:"
        return [line[len(prefix) :] for line in stderr.splitlines() if line.startswith(prefix)]

    @staticmethod
    def stop_process(process: subprocess.Popen[object]) -> None:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
