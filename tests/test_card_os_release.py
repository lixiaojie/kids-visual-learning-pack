from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "cognitive-card-server"
BUILDER = OPS / "build_release.py"
INSTALLER = OPS / "install_release.sh"
LOCK = OPS / "runtime-requirements.lock"

RUNTIME_LOCK = """annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.14.2
click==8.4.2
fastapi==0.139.0
h11==0.16.0
idna==3.18
pillow==12.3.0
pydantic==2.13.4
pydantic_core==2.46.4
starlette==1.3.1
typing_extensions==4.16.0
typing-inspection==0.4.2
uvicorn==0.51.0
"""

PAYLOAD_ASSETS = (
    "runtime-requirements.lock",
    "ops/card_os_backup.py",
    "ops/card_os_acceptance.py",
    "ops/install_nginx_include.py",
    "env/card-os.env",
    "systemd/cognitive-card-server.service",
    "systemd/cognitive-card-backup.service",
    "systemd/cognitive-card-backup.timer",
    "nginx/card-os.conf",
)


def run(*arguments: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def git(cwd: Path, *arguments: str) -> str:
    process = run("git", *arguments, cwd=cwd)
    if process.returncode:
        raise AssertionError(process.stderr)
    return process.stdout.strip()


class BuilderFixture:
    def __init__(self, case: unittest.TestCase) -> None:
        temporary = tempfile.TemporaryDirectory()
        case.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.governance = self.base / "governance"
        self.application = self.base / "application"
        self.output = self.base / "output"
        self.log = self.base / "wheel.log"
        self.python = self.base / "fake-python"
        self.mutate_application_on_wheel = False
        self.governance.mkdir()
        self.application.mkdir()
        self.output.mkdir()

        for asset in PAYLOAD_ASSETS:
            source = OPS / asset.removeprefix("ops/")
            destination = (
                self.governance
                / "ops"
                / "cognitive-card-server"
                / asset.removeprefix("ops/")
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        builder_destination = self.governance / "ops" / "cognitive-card-server" / "build_release.py"
        case.assertTrue(BUILDER.is_file(), "missing release builder")
        shutil.copy2(BUILDER, builder_destination)
        self.builder = builder_destination

        self._init_git(self.governance)
        (self.application / "pyproject.toml").write_text(
            "[project]\nname='cognitive-card-server'\nversion='0.3.0'\n",
            encoding="utf-8",
        )
        self._init_git(self.application)
        self.application_commit = git(self.application, "rev-parse", "HEAD")
        self.operations_commit = git(self.governance, "rev-parse", "HEAD")
        self._write_fake_python()

    @staticmethod
    def _init_git(path: Path) -> None:
        git(path, "init", "-q")
        git(path, "config", "user.name", "Release Test")
        git(path, "config", "user.email", "release@example.test")
        git(path, "add", ".")
        git(path, "commit", "-qm", "fixture")

    def _write_fake_python(self) -> None:
        self.python.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import os
                import pathlib
                import sys

                if sys.argv[1:] == ["--version"]:
                    print("Python 3.12.9")
                    raise SystemExit(0)
                pathlib.Path(os.environ["FAKE_WHEEL_LOG"]).write_text(" ".join(sys.argv[1:]))
                if os.environ.get("FAKE_MUTATE_APPLICATION"):
                    (pathlib.Path(sys.argv[-1]) / "changed-during-build.txt").write_text("changed")
                wheel_dir = pathlib.Path(sys.argv[sys.argv.index("--wheel-dir") + 1])
                wheel_dir.mkdir(parents=True, exist_ok=True)
                (wheel_dir / "cognitive_card_server-0.3.0-py3-none-any.whl").write_bytes(b"fixture-wheel")
                """
            ),
            encoding="utf-8",
        )
        self.python.chmod(self.python.stat().st_mode | stat.S_IXUSR)

    def invoke(self, expected_commit: str | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["FAKE_WHEEL_LOG"] = os.fspath(self.log)
        if self.mutate_application_on_wheel:
            environment["FAKE_MUTATE_APPLICATION"] = "1"
        return run(
            sys.executable,
            os.fspath(self.builder),
            "--server-repo",
            os.fspath(self.application),
            "--expected-commit",
            expected_commit or self.application_commit,
            "--output-dir",
            os.fspath(self.output),
            "--python",
            os.fspath(self.python),
            cwd=self.governance,
            env=environment,
        )


class CardOsReleaseBuilderTests(unittest.TestCase):
    def test_runtime_lock_and_package_commands_are_exact(self) -> None:
        self.assertEqual(RUNTIME_LOCK, LOCK.read_text(encoding="utf-8"))
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 -m unittest tests.test_card_os_backup tests.test_card_os_acceptance "
            "tests.test_card_os_deployment_assets tests.test_card_os_release -v",
            package["scripts"]["test:card-os-deploy"],
        )
        self.assertEqual(
            "python3 ops/cognitive-card-server/build_release.py",
            package["scripts"]["build:card-os-release"],
        )

    def test_wrong_head_stops_before_wheel_build(self) -> None:
        fixture = BuilderFixture(self)
        process = fixture.invoke("0" * 40)

        self.assertNotEqual(0, process.returncode)
        self.assertIn("SOURCE_COMMIT_MISMATCH", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_dirty_application_stops_before_wheel_build(self) -> None:
        fixture = BuilderFixture(self)
        (fixture.application / "dirty.txt").write_text("dirty", encoding="utf-8")
        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("SOURCE_WORKTREE_DIRTY", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_tracked_governance_change_stops_before_wheel_build(self) -> None:
        fixture = BuilderFixture(self)
        governance_lock = (
            fixture.governance / "ops" / "cognitive-card-server" / "runtime-requirements.lock"
        )
        governance_lock.write_text(RUNTIME_LOCK + "unexpected==1.0\n", encoding="utf-8")
        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("OPERATIONS_WORKTREE_DIRTY", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_source_change_during_wheel_build_discards_release(self) -> None:
        fixture = BuilderFixture(self)
        fixture.mutate_application_on_wheel = True
        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("SOURCE_CHANGED_DURING_BUILD", process.stderr)
        self.assertTrue(fixture.log.exists())
        self.assertEqual([], list(fixture.output.iterdir()))

    def test_builds_closed_normalized_release_with_dual_git_provenance(self) -> None:
        fixture = BuilderFixture(self)
        process = fixture.invoke()

        self.assertEqual(0, process.returncode, process.stderr)
        summary = json.loads(process.stdout)
        archive = fixture.output / f"cognitive-card-server-{fixture.application_commit}.tar.gz"
        checksum = Path(f"{archive}.sha256")
        self.assertEqual(archive, Path(summary["archive"]))
        self.assertEqual(checksum, Path(summary["sha256_file"]))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertEqual(f"{digest}  {archive.name}\n", checksum.read_text(encoding="ascii"))
        wheel_command = shlex.split(fixture.log.read_text(encoding="utf-8"))
        self.assertEqual(["-m", "pip", "wheel", "--no-deps", "--wheel-dir"], wheel_command[:5])
        self.assertEqual(7, len(wheel_command))
        self.assertEqual("wheel", Path(wheel_command[5]).name)
        self.assertEqual(os.fspath(fixture.application), wheel_command[6])

        wheel_name = "cognitive_card_server-0.3.0-py3-none-any.whl"
        expected_names = sorted((*PAYLOAD_ASSETS, wheel_name, "release-manifest.json"))
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            self.assertEqual(expected_names, sorted(member.name for member in members))
            self.assertTrue(all(member.isfile() for member in members))
            self.assertTrue(all(not Path(member.name).is_absolute() for member in members))
            self.assertTrue(all(".." not in Path(member.name).parts for member in members))
            self.assertTrue(all(member.uid == member.gid == member.mtime == 0 for member in members))
            manifest = json.load(bundle.extractfile("release-manifest.json"))
            payload_bytes = {
                member.name: bundle.extractfile(member).read()
                for member in members
                if member.name != "release-manifest.json"
            }

        self.assertEqual("cognitive-card-server-release-v1", manifest["schema"])
        self.assertEqual(fixture.application_commit, manifest["application_commit"])
        self.assertEqual(fixture.operations_commit, manifest["operations_commit"])
        self.assertEqual("0.3.0", manifest["application_version"])
        self.assertEqual("3.12.9", manifest["python_version"])
        self.assertRegex(manifest["built_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(
            hashlib.sha256(payload_bytes["runtime-requirements.lock"]).hexdigest(),
            manifest["lock_sha256"],
        )
        self.assertEqual(hashlib.sha256(payload_bytes[wheel_name]).hexdigest(), manifest["wheel_sha256"])
        expected_files = [
            {
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
            for path, content in sorted(payload_bytes.items())
        ]
        self.assertEqual(expected_files, manifest["files"])
        self.assertEqual(set(manifest), {
            "schema", "application_commit", "operations_commit", "application_version",
            "python_version", "built_at", "lock_sha256", "wheel_sha256", "files",
        })


class CardOsReleaseInstallerTests(unittest.TestCase):
    def installer_source(self) -> str:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        return INSTALLER.read_text(encoding="utf-8")

    def test_installer_is_valid_bash_and_orders_irreversible_actions_last(self) -> None:
        process = run("bash", "-n", os.fspath(INSTALLER), cwd=ROOT)
        self.assertEqual(0, process.returncode, process.stderr)
        source = self.installer_source()
        main_source = source.split("main() {", maxsplit=1)[1]
        ordered = (
            'sha256sum --check "$SHA256_FILE"',
            "apt-get update",
            "apt-get install -y python3-venv sqlite3",
            "validate_archive",
            'mkdir --mode=0755 "$RELEASE_DIR"',
            'python3 -m venv "$RELEASE_DIR/.venv"',
            '"$pip_path" install --requirement "$RELEASE_DIR/runtime-requirements.lock"',
            '"$pip_path" install --no-deps "$WHEEL"',
            '"$pip_path" check',
            "installed_runtime=",
            "write_install_manifest",
            "systemctl daemon-reload",
            'mv -T "$CURRENT_LINK" /opt/cognitive-card-server/current',
            "systemctl enable --now cognitive-card-server.service",
            "systemctl enable --now cognitive-card-backup.timer",
        )
        positions = [main_source.index(fragment) for fragment in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("set -euo pipefail", source)
        self.assertNotIn("nginx -", source)
        self.assertNotIn("/etc/nginx", source)

    def test_archive_validator_rejects_traversal_and_links(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            cases = (
                ("traversal.tar.gz", "../escape", tarfile.REGTYPE, ""),
                ("absolute.tar.gz", "/escape", tarfile.REGTYPE, ""),
                ("symlink.tar.gz", "runtime-requirements.lock", tarfile.SYMTYPE, "/etc/passwd"),
                ("hardlink.tar.gz", "runtime-requirements.lock", tarfile.LNKTYPE, "/etc/passwd"),
                ("device.tar.gz", "runtime-requirements.lock", tarfile.CHRTYPE, ""),
            )
            for name, member_name, member_type, link_name in cases:
                archive = base / name
                with tarfile.open(archive, "w:gz") as bundle:
                    valid_names = [
                        *PAYLOAD_ASSETS,
                        "cognitive_card_server-0.3.0-py3-none-any.whl",
                        "release-manifest.json",
                    ]
                    for valid_name in valid_names:
                        info = tarfile.TarInfo(valid_name)
                        if valid_name == member_name:
                            info.type = member_type
                            info.linkname = link_name
                        if info.type == tarfile.REGTYPE:
                            info.size = 1
                        bundle.addfile(
                            info,
                            io.BytesIO(b"x") if info.type == tarfile.REGTYPE else None,
                        )
                    if member_name not in valid_names:
                        info = tarfile.TarInfo(member_name)
                        info.size = 1
                        bundle.addfile(info, io.BytesIO(b"x"))
                process = run(
                    "bash", "-c", 'source "$1"; validate_archive "$2"',
                    "validator", os.fspath(INSTALLER), os.fspath(archive), cwd=ROOT,
                )
                self.assertNotEqual(0, process.returncode, name)
                self.assertIn("UNSAFE_ARCHIVE", process.stderr)

    def test_freeze_normalization_is_strict_and_pep503_sorted(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        process = subprocess.run(
            ["bash", "-c", 'source "$1"; normalize_freeze', "normalizer", os.fspath(INSTALLER)],
            input="Typing_Extensions==4.16.0\nannotated.doc==0.0.4\n",
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("annotated-doc==0.0.4\ntyping-extensions==4.16.0\n", process.stdout)
        invalid = subprocess.run(
            ["bash", "-c", 'source "$1"; normalize_freeze', "normalizer", os.fspath(INSTALLER)],
            input="package @ file:///tmp/package\n",
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        self.assertNotEqual(0, invalid.returncode)
        self.assertIn("INVALID_FREEZE", invalid.stderr)

    def test_activation_rollback_restores_old_current_and_service_states(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            old_release = base / "releases" / ("1" * 40)
            new_release = base / "releases" / ("2" * 40)
            old_release.mkdir(parents=True)
            new_release.mkdir()
            current = base / "current"
            current.symlink_to(new_release)
            log = base / "systemctl.log"
            script = r'''
source "$1"
LOG_PATH="$4"
systemctl() { printf '%s\n' "$*" >>"$LOG_PATH"; }
rollback_activation "$2" "$3" "$5" active enabled active enabled 1 1
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(current), os.fspath(new_release), os.fspath(log),
                os.fspath(old_release), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            self.assertFalse(new_release.exists())
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("stop cognitive-card-server.service", commands)
            self.assertIn("stop cognitive-card-backup.timer", commands)
            self.assertIn("enable cognitive-card-server.service", commands)
            self.assertIn("enable cognitive-card-backup.timer", commands)
            self.assertIn("start cognitive-card-server.service", commands)
            self.assertIn("start cognitive-card-backup.timer", commands)

    def test_first_install_rollback_removes_current_and_leaves_services_inactive(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            new_release = base / "releases" / ("2" * 40)
            new_release.mkdir(parents=True)
            current = base / "current"
            current.symlink_to(new_release)
            log = base / "systemctl.log"
            script = r'''
source "$1"
LOG_PATH="$4"
systemctl() { printf '%s\n' "$*" >>"$LOG_PATH"; }
rollback_activation "$2" "$3" "" inactive disabled inactive disabled 1 0
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(current), os.fspath(new_release), os.fspath(log), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertFalse(current.exists())
            self.assertFalse(current.is_symlink())
            self.assertFalse(new_release.exists())
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("stop cognitive-card-server.service", commands)
            self.assertIn("disable cognitive-card-server.service", commands)
            self.assertIn("disable cognitive-card-backup.timer", commands)
            self.assertNotIn("start cognitive-card-server.service", commands)
            self.assertNotIn("start cognitive-card-backup.timer", commands)

    def test_failed_rollback_preserves_new_release_and_reports_stable_error(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            old_release = base / "releases" / ("1" * 40)
            new_release = base / "releases" / ("2" * 40)
            old_release.mkdir(parents=True)
            new_release.mkdir()
            current = base / "current"
            current.symlink_to(new_release)
            script = r'''
source "$1"
systemctl() {
    if [[ "$1 $2" == "stop cognitive-card-server.service" ]]; then return 1; fi
    return 0
}
rollback_activation "$2" "$3" "$4" inactive disabled inactive disabled 1 0
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(current), os.fspath(new_release), os.fspath(old_release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("error=INSTALL_ROLLBACK_FAILED", process.stderr)
            self.assertTrue(new_release.is_dir())
            self.assertEqual(os.fspath(old_release), os.readlink(current))

    def test_exit_cleanup_before_activation_removes_partial_release(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            release = base / "release"
            staging.mkdir()
            release.mkdir()
            script = r'''
source "$1"
INSTALL_TEMPORARY_DIR="$2"
INSTALL_RELEASE_DIR="$3"
INSTALL_RELEASE_CREATED=1
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
trap install_cleanup EXIT
false
'''
            process = run(
                "bash", "-c", script, "cleanup", os.fspath(INSTALLER),
                os.fspath(staging), os.fspath(release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(release.exists())

    def test_exit_cleanup_after_activation_rolls_back_current(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            old_release = base / "releases" / ("1" * 40)
            new_release = base / "releases" / ("2" * 40)
            staging.mkdir()
            old_release.mkdir(parents=True)
            new_release.mkdir()
            current = base / "current"
            current.symlink_to(new_release)
            script = r'''
source "$1"
systemctl() { return 0; }
INSTALL_TEMPORARY_DIR="$2"
INSTALL_RELEASE_DIR="$3"
INSTALL_RELEASE_CREATED=1
INSTALL_CURRENT_PATH="$4"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=1
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$5"
INSTALL_OLD_API_ACTIVE=active
INSTALL_OLD_API_ENABLED=enabled
INSTALL_OLD_TIMER_ACTIVE=active
INSTALL_OLD_TIMER_ENABLED=enabled
INSTALL_API_STARTED=1
INSTALL_TIMER_STARTED=1
trap install_cleanup EXIT
false
'''
            process = run(
                "bash", "-c", script, "cleanup", os.fspath(INSTALLER),
                os.fspath(staging), os.fspath(new_release), os.fspath(current),
                os.fspath(old_release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertEqual(os.fspath(old_release), os.readlink(current))


if __name__ == "__main__":
    unittest.main()
