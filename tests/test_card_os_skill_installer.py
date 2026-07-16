from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
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

    def run(
        self,
        *arguments: str,
        extra_env: dict[str, str] | None = None,
        unset_env: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
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
        return subprocess.run(
            ["bash", str(INSTALLER), *arguments],
            env=environment,
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

    def test_digest_and_unsafe_zip_fail_before_active_mutation(self) -> None:
        self.fixture.write_manifest(archive_sha256="2" * 64)
        self.assert_error(self.fixture.run("--channel", "stable"), "DIGEST_MISMATCH")
        self.assertFalse((self.fixture.install_root / "skills" / "cognitive-card-os").exists())
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

    def test_upgrade_rollback_uses_pointer_and_swaps_identities(self) -> None:
        self.assertEqual(0, self.fixture.run("--channel", "stable").returncode)
        old_digest = self.fixture.archive_digest
        upgraded = InstallerFixture(self.base / "upgrade", "0.2.0", b"upgrade")
        upgraded.install_root = self.fixture.install_root
        self.assertEqual(0, upgraded.run("--version", "0.2.0").returncode)
        history = self.fixture.install_root / "skill-releases" / "cognitive-card-os"
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
    def tree_digest(path: Path) -> str:
        return digest(canonical(CardOsSkillInstallerTests.snapshot(path)))


if __name__ == "__main__":
    unittest.main()
