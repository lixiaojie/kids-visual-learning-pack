from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import grp
import pwd
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

RUNTIME_WHEELS = (
    "annotated_doc-0.0.4-py3-none-any.whl",
    "annotated_types-0.7.0-py3-none-any.whl",
    "anyio-4.14.2-py3-none-any.whl",
    "click-8.4.2-py3-none-any.whl",
    "fastapi-0.139.0-py3-none-any.whl",
    "h11-0.16.0-py3-none-any.whl",
    "idna-3.18-py3-none-any.whl",
    "pillow-12.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
    "pydantic-2.13.4-py3-none-any.whl",
    "pydantic_core-2.46.4-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    "starlette-1.3.1-py3-none-any.whl",
    "typing_extensions-4.16.0-py3-none-any.whl",
    "typing_inspection-0.4.2-py3-none-any.whl",
    "uvicorn-0.51.0-py3-none-any.whl",
)

RUNTIME_TARGET = {
    "abi": "cp312",
    "implementation": "cp",
    "only_binary": ":all:",
    "platforms": ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64"],
    "python_version": "312",
}


def load_builder_module():
    spec = importlib.util.spec_from_file_location("card_os_release_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load release builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def write_release_tree(root: Path, *, size_value: object = 1) -> None:
    wheel_name = "cognitive_card_server-0.3.0-py3-none-any.whl"
    payload_names = [
        *PAYLOAD_ASSETS,
        wheel_name,
        *(f"runtime-wheels/{name}" for name in RUNTIME_WHEELS),
    ]
    payload_bytes: dict[str, bytes] = {}
    for name in payload_names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        content = RUNTIME_LOCK.encode("utf-8") if name == "runtime-requirements.lock" else b"x"
        path.write_bytes(content)
        payload_bytes[name] = content
    files = [
        {
            "path": name,
            "sha256": hashlib.sha256(payload_bytes[name]).hexdigest(),
            "size": size_value if index == 0 else len(payload_bytes[name]),
        }
        for index, name in enumerate(sorted(payload_names))
    ]
    manifest = {
        "schema": "cognitive-card-server-release-v2",
        "application_commit": "1" * 40,
        "operations_commit": "2" * 40,
        "application_version": "0.3.0",
        "python_version": "3.12.9",
        "runtime_target": RUNTIME_TARGET,
        "built_at": "2026-07-15T00:00:00Z",
        "lock_sha256": hashlib.sha256(payload_bytes["runtime-requirements.lock"]).hexdigest(),
        "wheel_sha256": hashlib.sha256(b"x").hexdigest(),
        "files": files,
    }
    (root / "release-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


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
        self.runtime_mode = "valid"
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
                import json
                import os
                import pathlib
                import subprocess
                import sys

                if sys.argv[1:] == ["--version"]:
                    print("Python 3.12.9")
                    raise SystemExit(0)
                log_path = pathlib.Path(os.environ["FAKE_WHEEL_LOG"])
                with log_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({{
                        "arguments": sys.argv[1:],
                        "pip_config_file": os.environ.get("PIP_CONFIG_FILE"),
                        "pip_index_url": os.environ.get("PIP_INDEX_URL"),
                        "pip_extra_index_url": os.environ.get("PIP_EXTRA_INDEX_URL"),
                    }}) + "\\n")
                if "download" in sys.argv:
                    destination = pathlib.Path(sys.argv[sys.argv.index("--dest") + 1])
                    destination.mkdir(parents=True, exist_ok=True)
                    wheels = {list(RUNTIME_WHEELS)!r}
                    mode = os.environ.get("FAKE_RUNTIME_MODE", "valid")
                    if mode == "missing":
                        wheels.remove("anyio-4.14.2-py3-none-any.whl")
                    elif mode == "wrong-version":
                        wheels[wheels.index("anyio-4.14.2-py3-none-any.whl")] = (
                            "anyio-4.14.1-py3-none-any.whl"
                        )
                    elif mode == "duplicate":
                        wheels.append("anyio-4.14.2-1-py3-none-any.whl")
                    elif mode == "unexpected":
                        wheels.append("unexpected-1.0-py3-none-any.whl")
                    elif mode == "sdist":
                        wheels.append("anyio-4.14.2.tar.gz")
                    elif mode == "unsafe-name":
                        wheels.append("unsafe name.whl")
                    for name in wheels:
                        (destination / name).write_bytes(b"runtime-wheel")
                    raise SystemExit(0)
                source = pathlib.Path(sys.argv[-1])
                source_head = subprocess.run(
                    ["git", "-C", str(source), "rev-parse", "HEAD"],
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                source_status = subprocess.run(
                    ["git", "-C", str(source), "status", "--porcelain"],
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                application = pathlib.Path(os.environ["FAKE_APPLICATION_ROOT"])
                def object_inodes(repository):
                    return {{
                        (path.stat().st_dev, path.stat().st_ino)
                        for path in (repository / ".git" / "objects").rglob("*")
                        if path.is_file() and not path.is_symlink()
                    }}
                wheel_dir = pathlib.Path(sys.argv[sys.argv.index("--wheel-dir") + 1])
                backend_artifact = source / "build" / "backend-created.txt"
                with log_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({{
                    "application_build": True,
                    "source_head": source_head,
                    "source_status": source_status,
                    "backend_artifact": str(backend_artifact),
                    "shared_object_inodes": len(
                        object_inodes(source) & object_inodes(application)
                    ),
                    }}) + "\\n")
                backend_artifact.parent.mkdir(parents=True, exist_ok=True)
                backend_artifact.write_text("backend output")
                if os.environ.get("FAKE_MUTATE_APPLICATION"):
                    (application / "changed-during-build.txt").write_text("changed")
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
        environment["FAKE_APPLICATION_ROOT"] = os.fspath(self.application)
        environment["FAKE_RUNTIME_MODE"] = self.runtime_mode
        environment["PIP_CONFIG_FILE"] = "/tmp/attacker-pip.conf"
        environment["PIP_INDEX_URL"] = "https://environment.invalid/simple"
        environment["PIP_EXTRA_INDEX_URL"] = "https://extra-environment.invalid/simple"
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

    def commands(self) -> list[dict[str, object]]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def commit_application(self, message: str) -> None:
        git(self.application, "add", "-A")
        git(self.application, "commit", "-qm", message)
        self.application_commit = git(self.application, "rev-parse", "HEAD")


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

    def test_wheel_build_uses_clean_exact_commit_snapshot_inside_staging(self) -> None:
        fixture = BuilderFixture(self)
        process = fixture.invoke()

        self.assertEqual(0, process.returncode, process.stderr)
        commands = fixture.commands()
        wheel_invocation = next(command for command in commands if command.get("application_build"))
        arguments = next(
            command["arguments"] for command in commands
            if command.get("arguments", [None, None, None])[2:3] == ["wheel"]
        )
        self.assertEqual(["-m", "pip", "wheel", "--no-deps", "--wheel-dir"], arguments[:5])
        self.assertEqual(7, len(arguments))
        wheel_dir = Path(arguments[5])
        source = Path(arguments[6])
        self.assertNotEqual(fixture.application, source)
        self.assertNotIn(os.fspath(fixture.application), arguments)
        self.assertEqual(wheel_dir.parent, source.parent)
        self.assertEqual(fixture.application_commit, wheel_invocation["source_head"])
        self.assertEqual("", wheel_invocation["source_status"])
        self.assertEqual(0, wheel_invocation["shared_object_inodes"])
        self.assertEqual(
            source / "build" / "backend-created.txt",
            Path(wheel_invocation["backend_artifact"]),
        )
        self.assertFalse((fixture.application / "build").exists())
        self.assertFalse(source.exists())
        self.assertFalse(wheel_dir.exists())

    def test_runtime_wheelhouse_download_is_targeted_isolated_and_official(self) -> None:
        fixture = BuilderFixture(self)
        process = fixture.invoke()

        self.assertEqual(0, process.returncode, process.stderr)
        download = next(
            command for command in fixture.commands()
            if "download" in command.get("arguments", [])
        )
        arguments = download["arguments"]
        self.assertEqual(
            [
                "-m", "pip", "--isolated", "--disable-pip-version-check",
                "download", "--no-input", "--only-binary=:all:",
                "--index-url", "https://pypi.org/simple",
                "--platform", "manylinux_2_28_x86_64",
                "--platform", "manylinux_2_17_x86_64",
                "--implementation", "cp", "--python-version", "312",
                "--abi", "cp312", "--dest",
            ],
            arguments[:-3],
        )
        self.assertEqual("--requirement", arguments[-2])
        self.assertEqual("runtime-requirements.lock", Path(arguments[-1]).name)
        self.assertEqual(os.devnull, download["pip_config_file"])
        self.assertIsNone(download["pip_index_url"])
        self.assertIsNone(download["pip_extra_index_url"])
        self.assertNotIn("--extra-index-url", arguments)

    def test_runtime_wheelhouse_rejects_incomplete_or_unsafe_resolutions(self) -> None:
        for mode in ("missing", "wrong-version", "duplicate", "unexpected", "sdist", "unsafe-name"):
            with self.subTest(mode=mode):
                fixture = BuilderFixture(self)
                fixture.runtime_mode = mode
                process = fixture.invoke()

                self.assertNotEqual(0, process.returncode)
                self.assertIn("RUNTIME_WHEELHOUSE_INVALID", process.stderr)
                self.assertEqual([], list(fixture.output.iterdir()))

    def test_gitlink_is_rejected_before_wheel_execution(self) -> None:
        fixture = BuilderFixture(self)
        submodule = fixture.base / "submodule"
        submodule.mkdir()
        (submodule / "content.txt").write_text("submodule", encoding="utf-8")
        fixture._init_git(submodule)
        git(
            fixture.application,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            os.fspath(submodule),
            "vendor/module",
        )
        fixture.commit_application("add gitlink")

        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("COMMAND_FAILED", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_tracked_symlink_is_rejected_before_wheel_execution(self) -> None:
        fixture = BuilderFixture(self)
        (fixture.application / "escaping-link").symlink_to("../outside")
        fixture.commit_application("add symlink")

        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("COMMAND_FAILED", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_checkout_transformed_regular_file_is_rejected_before_wheel_execution(self) -> None:
        fixture = BuilderFixture(self)
        (fixture.application / ".gitattributes").write_text(
            "transformed.txt text eol=crlf\n",
            encoding="utf-8",
        )
        (fixture.application / "transformed.txt").write_bytes(b"exact blob bytes\n")
        fixture.commit_application("add checkout transformation")

        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("COMMAND_FAILED", process.stderr)
        self.assertFalse(fixture.log.exists())

    def test_staged_executable_mode_must_match_git_tree(self) -> None:
        builder = load_builder_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            git(source, "init", "-q")
            script = source / "entrypoint.sh"
            script.write_bytes(b"#!/bin/sh\n")
            object_id = git(source, "hash-object", "--no-filters", "--", script.name)

            for git_mode, staged_mode in (
                ("100755", 0o644),
                ("100644", 0o755),
                ("100644", 0o654),
            ):
                with self.subTest(git_mode=git_mode, staged_mode=oct(staged_mode)):
                    script.chmod(staged_mode)
                    with self.assertRaises(builder.ReleaseError) as caught:
                        builder.validate_staged_bytes(
                            source,
                            [(git_mode, "blob", object_id, script.name)],
                        )
                    self.assertEqual("COMMAND_FAILED", str(caught.exception))

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
        wheel_command = next(
            command["arguments"] for command in fixture.commands()
            if command.get("arguments", [None, None, None])[2:3] == ["wheel"]
        )
        self.assertEqual(["-m", "pip", "wheel", "--no-deps", "--wheel-dir"], wheel_command[:5])
        self.assertEqual(7, len(wheel_command))
        self.assertEqual("wheel", Path(wheel_command[5]).name)

        wheel_name = "cognitive_card_server-0.3.0-py3-none-any.whl"
        expected_names = sorted((
            *PAYLOAD_ASSETS,
            wheel_name,
            *(f"runtime-wheels/{name}" for name in RUNTIME_WHEELS),
            "release-manifest.json",
        ))
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

        self.assertEqual("cognitive-card-server-release-v2", manifest["schema"])
        self.assertEqual(fixture.application_commit, manifest["application_commit"])
        self.assertEqual(fixture.operations_commit, manifest["operations_commit"])
        self.assertEqual("0.3.0", manifest["application_version"])
        self.assertEqual("3.12.9", manifest["python_version"])
        self.assertEqual(RUNTIME_TARGET, manifest["runtime_target"])
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
            "python_version", "runtime_target", "built_at", "lock_sha256", "wheel_sha256", "files",
        })


class CardOsReleaseInstallerTests(unittest.TestCase):
    def installer_source(self) -> str:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        return INSTALLER.read_text(encoding="utf-8")

    def write_pip_recorder(self, path: Path) -> None:
        path.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                import pathlib
                import sys

                pathlib.Path(os.environ["COMMAND_LOG"]).write_text(
                    json.dumps({{
                        "arguments": sys.argv[1:],
                        "pip_config_file": os.environ.get("PIP_CONFIG_FILE"),
                        "pip_index_url": os.environ.get("PIP_INDEX_URL"),
                        "pip_extra_index_url": os.environ.get("PIP_EXTRA_INDEX_URL"),
                    }}),
                    encoding="utf-8",
                )
                """
            ),
            encoding="utf-8",
        )
        path.chmod(0o755)

    def run_installer_function(
        self,
        script: str,
        *arguments: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return run(
            "bash",
            "-c",
            script,
            "installer-function",
            os.fspath(INSTALLER),
            *arguments,
            cwd=ROOT,
            env=env,
        )

    def test_runtime_install_uses_only_isolated_release_wheelhouse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            recorder = base / "python"
            command_log = base / "command.json"
            lock = base / "runtime.lock"
            wheelhouse = base / "runtime-wheels"
            wheelhouse.mkdir()
            home = base / "home"
            (home / ".config" / "pip").mkdir(parents=True)
            (home / ".config" / "pip" / "pip.conf").write_text(
                "[global]\nindex-url=https://config.invalid/simple\n"
                "extra-index-url=https://extra.invalid/simple\n",
                encoding="utf-8",
            )
            lock.write_text("example==1.0\n", encoding="utf-8")
            self.write_pip_recorder(recorder)
            environment = os.environ.copy()
            environment.update({
                "COMMAND_LOG": os.fspath(command_log),
                "HOME": os.fspath(home),
                "PIP_CONFIG_FILE": os.fspath(home / ".config" / "pip" / "pip.conf"),
                "PIP_INDEX_URL": "https://environment.invalid/simple",
                "PIP_EXTRA_INDEX_URL": "https://extra-environment.invalid/simple",
            })

            process = self.run_installer_function(
                'source "$1"; install_runtime_dependencies "$2" "$3" "$4"',
                os.fspath(recorder),
                os.fspath(lock),
                os.fspath(wheelhouse),
                env=environment,
            )

            self.assertEqual(0, process.returncode, process.stderr)
            recorded = json.loads(command_log.read_text(encoding="utf-8"))
            self.assertEqual(
                [
                    "-m", "pip", "--isolated", "--disable-pip-version-check",
                    "install", "--no-input", "--no-index", "--find-links",
                    os.fspath(wheelhouse), "--requirement", os.fspath(lock),
                ],
                recorded["arguments"],
            )
            self.assertEqual(os.devnull, recorded["pip_config_file"])
            self.assertIsNone(recorded["pip_index_url"])
            self.assertIsNone(recorded["pip_extra_index_url"])
            self.assertNotIn("--extra-index-url", recorded["arguments"])
            self.assertNotIn("--index-url", recorded["arguments"])

    def test_local_wheel_install_is_isolated_no_index_and_no_deps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            recorder = base / "python"
            command_log = base / "command.json"
            wheel = base / "application.whl"
            wheel.write_bytes(b"wheel")
            self.write_pip_recorder(recorder)
            environment = os.environ.copy()
            environment.update({
                "COMMAND_LOG": os.fspath(command_log),
                "PIP_CONFIG_FILE": "/tmp/attacker-pip.conf",
                "PIP_INDEX_URL": "https://environment.invalid/simple",
                "PIP_EXTRA_INDEX_URL": "https://extra-environment.invalid/simple",
            })

            process = self.run_installer_function(
                'source "$1"; install_application_wheel "$2" "$3"',
                os.fspath(recorder),
                os.fspath(wheel),
                env=environment,
            )

            self.assertEqual(0, process.returncode, process.stderr)
            recorded = json.loads(command_log.read_text(encoding="utf-8"))
            self.assertEqual(
                [
                    "-m", "pip", "--isolated", "--disable-pip-version-check",
                    "install", "--no-input", "--no-index", "--no-deps", os.fspath(wheel),
                ],
                recorded["arguments"],
            )
            self.assertEqual(os.devnull, recorded["pip_config_file"])
            self.assertIsNone(recorded["pip_index_url"])
            self.assertIsNone(recorded["pip_extra_index_url"])

    def test_first_install_prepares_private_data_paths_and_cleans_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            data_root = base / "data"
            candidate_root = data_root / "candidates"
            database = data_root / "card-os.sqlite3"
            uid = os.getuid()
            gid = os.getgid()
            owner = pwd.getpwuid(uid).pw_name
            group = grp.getgrgid(gid).gr_name
            script = r'''
source "$1"
runuser() {
    [[ "$1" == -u && "$3" == -- ]] || return 97
    shift 3
    "$@"
}
ensure_private_directory "$2" "$5" "$6" "$7" "$8" UNSAFE_DATA_ROOT
ensure_private_directory "$3" "$5" "$6" "$7" "$8" UNSAFE_CANDIDATE_ROOT
validate_database_file "$4" "$7" "$8"
probe_data_root "$2" "$5" "$7" "$8"
'''
            process = self.run_installer_function(
                script,
                os.fspath(data_root),
                os.fspath(candidate_root),
                os.fspath(database),
                owner,
                group,
                str(uid),
                str(gid),
            )

            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual("", process.stdout)
            self.assertEqual(0o700, stat.S_IMODE(data_root.stat().st_mode))
            self.assertEqual(0o700, stat.S_IMODE(candidate_root.stat().st_mode))
            self.assertFalse(database.exists())
            self.assertEqual([], list(data_root.glob(".card-os-write-probe-*")))

    def test_safe_existing_database_and_data_are_not_modified_or_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            data_root = base / "data"
            candidate_root = data_root / "candidates"
            data_root.mkdir(mode=0o755)
            candidate_root.mkdir(mode=0o755)
            database = data_root / "card-os.sqlite3"
            database.write_bytes(b"existing-database")
            database.chmod(0o600)
            sentinel = candidate_root / "existing-packet.json"
            sentinel.write_bytes(b"existing-candidate")
            uid = os.getuid()
            gid = os.getgid()
            owner = pwd.getpwuid(uid).pw_name
            group = grp.getgrgid(gid).gr_name
            script = r'''
source "$1"
runuser() { shift 3; "$@"; }
ensure_private_directory "$2" "$5" "$6" "$7" "$8" UNSAFE_DATA_ROOT
ensure_private_directory "$3" "$5" "$6" "$7" "$8" UNSAFE_CANDIDATE_ROOT
validate_database_file "$4" "$7" "$8"
probe_data_root "$2" "$5" "$7" "$8"
'''
            process = self.run_installer_function(
                script,
                os.fspath(data_root),
                os.fspath(candidate_root),
                os.fspath(database),
                owner,
                group,
                str(uid),
                str(gid),
            )

            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual(b"existing-database", database.read_bytes())
            self.assertEqual(b"existing-candidate", sentinel.read_bytes())
            self.assertEqual(0o700, stat.S_IMODE(data_root.stat().st_mode))
            self.assertEqual(0o700, stat.S_IMODE(candidate_root.stat().st_mode))
            self.assertEqual([], list(data_root.glob(".card-os-write-probe-*")))

    def test_database_validation_rejects_unsafe_owner_mode_links_and_non_files(self) -> None:
        uid = os.getuid()
        gid = os.getgid()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            target.write_bytes(b"target")
            target.chmod(0o600)
            cases = []

            wrong_owner = base / "wrong-owner.sqlite3"
            wrong_owner.write_bytes(b"db")
            wrong_owner.chmod(0o600)
            cases.append((wrong_owner, uid + 1, gid))

            wrong_mode = base / "wrong-mode.sqlite3"
            wrong_mode.write_bytes(b"db")
            wrong_mode.chmod(0o640)
            cases.append((wrong_mode, uid, gid))

            link = base / "link.sqlite3"
            link.symlink_to(target)
            cases.append((link, uid, gid))

            directory = base / "directory.sqlite3"
            directory.mkdir()
            cases.append((directory, uid, gid))

            for path, expected_uid, expected_gid in cases:
                with self.subTest(path=path.name):
                    process = self.run_installer_function(
                        'source "$1"; validate_database_file "$2" "$3" "$4"',
                        os.fspath(path),
                        str(expected_uid),
                        str(expected_gid),
                    )
                    self.assertNotEqual(0, process.returncode)
                    self.assertIn("error=UNSAFE_DATABASE", process.stderr)
                    self.assertTrue(path.exists() or path.is_symlink())

    def test_data_and_candidate_roots_reject_links_and_non_directories(self) -> None:
        uid = os.getuid()
        gid = os.getgid()
        owner = pwd.getpwuid(uid).pw_name
        group = grp.getgrgid(gid).gr_name
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            directory = base / "real-directory"
            directory.mkdir()
            link = base / "linked-directory"
            link.symlink_to(directory, target_is_directory=True)
            regular = base / "regular-file"
            regular.write_bytes(b"keep")

            for path, error in (
                (link, "UNSAFE_DATA_ROOT"),
                (regular, "UNSAFE_DATA_ROOT"),
                (link, "UNSAFE_CANDIDATE_ROOT"),
                (regular, "UNSAFE_CANDIDATE_ROOT"),
            ):
                with self.subTest(path=path.name, error=error):
                    process = self.run_installer_function(
                        'source "$1"; ensure_private_directory "$2" "$3" "$4" "$5" "$6" "$7"',
                        os.fspath(path),
                        owner,
                        group,
                        str(uid),
                        str(gid),
                        error,
                    )
                    self.assertNotEqual(0, process.returncode)
                    self.assertIn(f"error={error}", process.stderr)
                    self.assertTrue(path.exists() or path.is_symlink())

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
            'publish_release_directory "$extracted" "$RELEASE_DIR"',
            'python3 -m venv "$RELEASE_DIR/.venv"',
            'install_runtime_dependencies "$python_path" "$RELEASE_DIR/runtime-requirements.lock" "$RELEASE_DIR/runtime-wheels"',
            'install_application_wheel "$python_path" "$WHEEL"',
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
        self.assertIn("umask 022", source)
        self.assertIn('chmod 0755 "$RELEASE_DIR/.venv/bin/cognitive-card-api"', source)
        self.assertNotIn("nginx -", source)
        self.assertNotIn("/etc/nginx", source)

    def test_installer_sets_safe_umask_for_service_runtime(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "release"
            script = r'''
umask 077
source "$1"
mkdir "$2"
python3 -m venv "$2/.venv"
printf '#!/bin/sh\n' >"$2/.venv/bin/cognitive-card-api"
chmod 0755 "$2/.venv/bin/cognitive-card-api"
python3 - "$2" <<'PY'
import pathlib
import stat
import sys
root = pathlib.Path(sys.argv[1])
directories = [root, *(path for path in root.rglob("*") if path.is_dir())]
if any(not (path.stat().st_mode & stat.S_IXOTH) for path in directories):
    raise SystemExit(1)
entrypoint = root / ".venv" / "bin" / "cognitive-card-api"
mode = entrypoint.stat().st_mode
if not (mode & stat.S_IROTH and mode & stat.S_IXOTH):
    raise SystemExit(1)
PY
'''
            process = run(
                "bash", "-c", script, "umask-test", os.fspath(INSTALLER),
                os.fspath(release), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)

    def test_manifest_rejects_non_integer_or_negative_sizes(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        for invalid_size in (1.0, True, -1, "1"):
            with self.subTest(size=invalid_size), tempfile.TemporaryDirectory() as temporary:
                release = Path(temporary) / "release"
                release.mkdir()
                write_release_tree(release, size_value=invalid_size)
                process = run(
                    "bash", "-c", 'source "$1"; verify_release "$2"',
                    "manifest-test", os.fspath(INSTALLER), os.fspath(release), cwd=ROOT,
                )
                self.assertNotEqual(0, process.returncode)
                self.assertIn("error=RELEASE_MANIFEST_INVALID", process.stderr)

    def test_release_validator_accepts_only_complete_closed_runtime_wheelhouse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "valid"
            release.mkdir()
            write_release_tree(release)
            valid = run(
                "bash", "-c", 'source "$1"; verify_release "$2"',
                "release-validator", os.fspath(INSTALLER), os.fspath(release), cwd=ROOT,
            )
            self.assertEqual(0, valid.returncode, valid.stderr)

        for mutation in ("missing", "unexpected", "sdist"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                release = Path(temporary) / "release"
                release.mkdir()
                write_release_tree(release)
                if mutation == "missing":
                    (release / "runtime-wheels" / RUNTIME_WHEELS[0]).unlink()
                elif mutation == "unexpected":
                    (release / "runtime-wheels" / "unexpected-1.0-py3-none-any.whl").write_bytes(b"x")
                else:
                    (release / "runtime-wheels" / "anyio-4.14.2.tar.gz").write_bytes(b"x")
                invalid = run(
                    "bash", "-c", 'source "$1"; verify_release "$2"',
                    "release-validator", os.fspath(INSTALLER), os.fspath(release), cwd=ROOT,
                )
                self.assertNotEqual(0, invalid.returncode)
                self.assertIn("error=RELEASE_MANIFEST_INVALID", invalid.stderr)

    def test_install_trap_precedes_first_fallible_temp_operation(self) -> None:
        source = self.installer_source().split("main() {", maxsplit=1)[1]
        self.assertLess(source.index("trap install_cleanup EXIT"), source.index('mkdir "$extracted"'))

    def test_cleanup_never_deletes_unmarked_release(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "preexisting-release"
            release.mkdir()
            script = r'''
source "$1"
INSTALL_TEMPORARY_DIR=""
INSTALL_RELEASE_DIR="$2"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=not-present
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
trap install_cleanup EXIT
false
'''
            process = run(
                "bash", "-c", script, "marker-test", os.fspath(INSTALLER),
                os.fspath(release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertTrue(release.is_dir())

    def test_atomic_release_publication_includes_invocation_marker(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            release = base / "release"
            staging.mkdir()
            (staging / "payload").write_text("payload", encoding="utf-8")
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=unique-token
printf '%s\n' "$INSTALL_OWNERSHIP_TOKEN" >"$2/.install-owner"
publish_release_directory "$2" "$3"
'''
            process = run(
                "bash", "-c", script, "marker-test", os.fspath(INSTALLER),
                os.fspath(staging), os.fspath(release), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertFalse(staging.exists())
            self.assertEqual("unique-token\n", (release / ".install-owner").read_text())

    def test_signal_immediately_after_publication_cleans_only_marked_release(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            release = base / "release"
            staging.mkdir()
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=unique-token
INSTALL_RELEASE_DIR="$3"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
printf '%s\n' "$INSTALL_OWNERSHIP_TOKEN" >"$2/.install-owner"
trap install_cleanup EXIT
trap 'exit 143' TERM
publish_release_directory "$2" "$3"
kill -TERM $$
'''
            process = run(
                "bash", "-c", script, "signal-test", os.fspath(INSTALLER),
                os.fspath(staging), os.fspath(release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(release.exists())

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
                        *(f"runtime-wheels/{name}" for name in RUNTIME_WHEELS),
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
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(new_release)
            log = base / "systemctl.log"
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
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
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(new_release)
            log = base / "systemctl.log"
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
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
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(new_release)
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
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
            (release / ".install-owner").write_text("test-token\n", encoding="ascii")
            script = r'''
source "$1"
INSTALL_TEMPORARY_DIR="$2"
INSTALL_RELEASE_DIR="$3"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
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
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(new_release)
            script = r'''
source "$1"
systemctl() { return 0; }
INSTALL_TEMPORARY_DIR="$2"
INSTALL_RELEASE_DIR="$3"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
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
