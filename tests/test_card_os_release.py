from __future__ import annotations

import hashlib
import json
import os
import shutil
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
        self.governance.mkdir()
        self.application.mkdir()
        self.output.mkdir()

        for asset in PAYLOAD_ASSETS:
            source = OPS / asset.removeprefix("ops/")
            destination = self.governance / "ops" / "cognitive-card-server" / asset
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
        return run(
            os.fspath(self.python),
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
        self.assertEqual(
            f"-m pip wheel --no-deps --wheel-dir ",
            fixture.log.read_text(encoding="utf-8")[:36],
        )

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
        ordered = (
            'sha256sum --check "$SHA256_FILE"',
            "apt-get update",
            "apt-get install -y python3-venv sqlite3",
            "validate_archive",
            '[[ ! -e "$RELEASE_DIR" ]]',
            'python3 -m venv "$RELEASE_DIR/.venv"',
            'pip install --requirement "$RELEASE_DIR/runtime-requirements.lock"',
            'pip install --no-deps "$WHEEL"',
            "pip check",
            "installed-runtime.txt",
            "install-manifest.json",
            "systemctl daemon-reload",
            'mv -T "$CURRENT_LINK" /opt/cognitive-card-server/current',
            "systemctl enable --now cognitive-card-server.service",
            "systemctl enable --now cognitive-card-backup.timer",
        )
        positions = [source.index(fragment) for fragment in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("set -euo pipefail", source)
        self.assertNotIn("nginx -", source)
        self.assertNotIn("/etc/nginx", source)

    def test_archive_validator_rejects_traversal_and_links(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name, kind in (("traversal.tar.gz", "traversal"), ("link.tar.gz", "link")):
                archive = base / name
                with tarfile.open(archive, "w:gz") as bundle:
                    info = tarfile.TarInfo("../escape" if kind == "traversal" else "runtime-requirements.lock")
                    if kind == "link":
                        info.type = tarfile.SYMTYPE
                        info.linkname = "/etc/passwd"
                    else:
                        info.size = 1
                    import io
                    bundle.addfile(info, io.BytesIO(b"x") if kind == "traversal" else None)
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


if __name__ == "__main__":
    unittest.main()
