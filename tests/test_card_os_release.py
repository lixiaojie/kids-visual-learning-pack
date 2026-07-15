from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import base64
import csv
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "cognitive-card-server"
BUILDER = OPS / "build_release.py"
INSTALLER = OPS / "install_release.sh"
LOCK = OPS / "runtime-requirements.lock"
WHEEL_AUDIT = OPS / "wheel_audit.py"

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
    "ops/wheel_audit.py",
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


def record_digest(content: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
    return "sha256=" + encoded.decode("ascii")


def write_test_wheel(
    path: Path,
    *,
    name: str,
    version: str,
    tags: tuple[str, ...] = ("py3-none-any",),
    metadata_name: str | None = None,
    metadata_version: str | None = None,
    extra_members: tuple[tuple[str, bytes, int], ...] = (),
    directory_entries: tuple[tuple[str, bytes, int], ...] = (),
    duplicate_member: str | None = None,
    corrupt_record_for: str | None = None,
    wheel_tags: tuple[str, ...] | None = None,
    module_content: bytes = b"MARKER = 'governed'\n",
    compression: int = zipfile.ZIP_STORED,
) -> None:
    distribution = name.replace("-", "_").replace(".", "_")
    dist_info = f"{distribution}-{version}.dist-info"
    module_path = f"{distribution}/__init__.py"
    metadata = (
        "Metadata-Version: 2.1\n"
        f"Name: {metadata_name or name}\n"
        f"Version: {metadata_version or version}\n\n"
    ).encode("utf-8")
    declared_tags = wheel_tags if wheel_tags is not None else tags
    wheel = (
        "Wheel-Version: 1.0\n"
        "Generator: card-os-tests\n"
        "Root-Is-Purelib: true\n"
        + "".join(f"Tag: {tag}\n" for tag in declared_tags)
        + "\n"
    ).encode("utf-8")
    entries: list[tuple[str, bytes, int]] = [
        (module_path, module_content, 0o100644),
        (f"{dist_info}/METADATA", metadata, 0o100644),
        (f"{dist_info}/WHEEL", wheel, 0o100644),
        *extra_members,
    ]
    record_path = f"{dist_info}/RECORD"
    record_rows = []
    for entry_name, content, _ in entries:
        digest = "sha256=invalid" if entry_name == corrupt_record_for else record_digest(content)
        record_rows.append((entry_name, digest, str(len(content))))
    record_rows.append((record_path, "", ""))
    record_buffer = io.StringIO(newline="")
    csv.writer(record_buffer, lineterminator="\n").writerows(record_rows)
    entries.append((record_path, record_buffer.getvalue().encode("utf-8"), 0o100644))

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as wheel_archive:
        for entry_name, content, mode in entries:
            info = zipfile.ZipInfo(entry_name)
            info.create_system = 3
            info.external_attr = mode << 16
            info.compress_type = compression
            wheel_archive.writestr(info, content)
        for entry_name, content, mode in directory_entries:
            info = zipfile.ZipInfo(entry_name)
            info.create_system = 3
            info.external_attr = mode << 16
            info.compress_type = compression
            wheel_archive.writestr(info, content)
        if duplicate_member is not None:
            duplicate = next(content for entry_name, content, _ in entries if entry_name == duplicate_member)
            info = zipfile.ZipInfo(duplicate_member)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = compression
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                wheel_archive.writestr(info, duplicate)


def load_builder_module():
    spec = importlib.util.spec_from_file_location("card_os_release_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load release builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_wheel_audit_module():
    spec = importlib.util.spec_from_file_location("card_os_wheel_audit", WHEEL_AUDIT)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load wheel audit")
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


def write_release_tree(root: Path, *, size_value: object | None = None) -> None:
    wheel_name = "cognitive_card_server-0.3.1-py3-none-any.whl"
    payload_names = [
        *PAYLOAD_ASSETS,
        wheel_name,
        *(f"runtime-wheels/{name}" for name in RUNTIME_WHEELS),
    ]
    payload_bytes: dict[str, bytes] = {}
    for name in payload_names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "runtime-requirements.lock":
            path.write_text(RUNTIME_LOCK, encoding="utf-8")
        elif name == "ops/wheel_audit.py":
            shutil.copyfile(WHEEL_AUDIT, path)
        elif name.endswith(".whl"):
            fields = path.name[:-4].split("-")
            write_test_wheel(
                path,
                name=fields[0].replace("_", "-"),
                version=fields[1],
                tags=("-".join(fields[-3:]),),
            )
        else:
            path.write_bytes(b"x")
        payload_bytes[name] = path.read_bytes()
    files = [
        {
            "path": name,
            "sha256": hashlib.sha256(payload_bytes[name]).hexdigest(),
            "size": size_value if index == 0 and size_value is not None else len(payload_bytes[name]),
        }
        for index, name in enumerate(sorted(payload_names))
    ]
    manifest = {
        "schema": "cognitive-card-server-release-v2",
        "application_commit": "1" * 40,
        "operations_commit": "2" * 40,
        "application_version": "0.3.1",
        "python_version": "3.12.9",
        "runtime_target": RUNTIME_TARGET,
        "built_at": "2026-07-15T00:00:00Z",
        "lock_sha256": hashlib.sha256(payload_bytes["runtime-requirements.lock"]).hexdigest(),
        "wheel_sha256": hashlib.sha256(
            payload_bytes["cognitive_card_server-0.3.1-py3-none-any.whl"]
        ).hexdigest(),
        "files": files,
    }
    (root / "release-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class WheelAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(WHEEL_AUDIT.is_file(), "missing governed wheel audit")

    def test_valid_pure_and_abi3_wheels_pass_bounded_target_audit(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            pure = base / "demo-1.0-py3-none-any.whl"
            abi3 = base / (
                "core_demo-2.0-cp311-abi3-"
                "manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
            )
            write_test_wheel(pure, name="demo", version="1.0")
            write_test_wheel(
                abi3,
                name="core-demo",
                version="2.0",
                tags=(
                    "cp311-abi3-manylinux_2_17_x86_64",
                    "cp311-abi3-manylinux2014_x86_64",
                ),
            )

            self.assertEqual(("demo", "1.0"), audit.audit_wheel(pure, "demo", "1.0"))
            self.assertEqual(
                ("core-demo", "2.0"),
                audit.audit_wheel(abi3, "core-demo", "2.0"),
            )

    def test_wheel_audit_rejects_corruption_identity_zip_and_record_violations(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            cases: dict[str, Path] = {}

            corrupt = base / "corrupt-1.0-py3-none-any.whl"
            corrupt.write_bytes(b"not-a-zip")
            cases["corrupt"] = corrupt

            mislabeled = base / "demo-1.0-py3-none-any.whl"
            write_test_wheel(mislabeled, name="demo", version="1.0", metadata_name="other")
            cases["mislabeled"] = mislabeled

            unsafe = base / "unsafe_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                unsafe,
                name="unsafe-demo",
                version="1.0",
                extra_members=(("../escape", b"escape", 0o100644),),
            )
            cases["unsafe"] = unsafe

            duplicate = base / "duplicate_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                duplicate,
                name="duplicate-demo",
                version="1.0",
                duplicate_member="duplicate_demo/__init__.py",
            )
            cases["duplicate"] = duplicate

            symlink = base / "symlink_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                symlink,
                name="symlink-demo",
                version="1.0",
                extra_members=(("symlink_demo/link", b"target", 0o120777),),
            )
            cases["symlink"] = symlink

            record = base / "record_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                record,
                name="record-demo",
                version="1.0",
                corrupt_record_for="record_demo/__init__.py",
            )
            cases["record"] = record

            tags = base / "tag_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                tags,
                name="tag-demo",
                version="1.0",
                wheel_tags=("py312-none-any",),
            )
            cases["tags"] = tags

            expected_names = {
                "corrupt": "corrupt",
                "mislabeled": "demo",
                "unsafe": "unsafe-demo",
                "duplicate": "duplicate-demo",
                "symlink": "symlink-demo",
                "record": "record-demo",
                "tags": "tag-demo",
            }
            for label, wheel in cases.items():
                with self.subTest(label=label), self.assertRaises(audit.WheelAuditError) as caught:
                    audit.audit_wheel(wheel, expected_names[label], "1.0")
                self.assertEqual("WHEEL_INVALID", str(caught.exception))

    def test_wheel_audit_rejects_future_manylinux_and_invalid_abi3_floor(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            future = base / "future-1.0-cp312-cp312-manylinux_2_29_x86_64.whl"
            old_abi = base / "old_abi-1.0-cp31-abi3-manylinux_2_17_x86_64.whl"
            write_test_wheel(
                future,
                name="future",
                version="1.0",
                tags=("cp312-cp312-manylinux_2_29_x86_64",),
            )
            write_test_wheel(
                old_abi,
                name="old-abi",
                version="1.0",
                tags=("cp31-abi3-manylinux_2_17_x86_64",),
            )
            for wheel, name in ((future, "future"), (old_abi, "old-abi")):
                with self.subTest(wheel=wheel.name), self.assertRaises(audit.WheelAuditError):
                    audit.audit_wheel(wheel, name, "1.0")

    def test_wheel_audit_rejects_noncanonical_posix_aliases_and_collisions(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for label, alias in (
                ("double-slash", "alias_demo//payload.py"),
                ("dot-component", "alias_demo/./payload.py"),
            ):
                wheel = base / label / "alias_demo-1.0-py3-none-any.whl"
                write_test_wheel(
                    wheel,
                    name="alias-demo",
                    version="1.0",
                    extra_members=(
                        ("alias_demo/payload.py", b"canonical", 0o100644),
                        (alias, b"alias", 0o100644),
                    ),
                )
                with self.subTest(label=label), self.assertRaises(audit.WheelAuditError):
                    audit.audit_wheel(wheel, "alias-demo", "1.0")

    def test_wheel_audit_accepts_safe_explicit_directories_outside_record(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / "directory_demo-1.0-py3-none-any.whl"
            directories = (
                ("directory_demo/", b"", 0o40755),
                ("directory_demo-1.0.dist-info/licenses/", b"", 0o40755),
            )
            write_test_wheel(
                wheel,
                name="directory-demo",
                version="1.0",
                directory_entries=directories,
            )

            with zipfile.ZipFile(wheel) as archive:
                record_path = "directory_demo-1.0.dist-info/RECORD"
                record_names = {
                    row[0]
                    for row in csv.reader(
                        io.StringIO(archive.read(record_path).decode("utf-8"), newline=""),
                        strict=True,
                    )
                }
            self.assertTrue(all(name not in record_names for name, _, _ in directories))
            self.assertEqual(
                ("directory-demo", "1.0"),
                audit.audit_wheel(wheel, "directory-demo", "1.0"),
            )

    def test_wheel_audit_rejects_unsafe_explicit_directories(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            cases = {
                "alias": (("directory_demo//", b"", 0o40755),),
                "nonempty": (("directory_demo/", b"payload", 0o40755),),
                "symlink": (("directory_demo/", b"", 0o120777),),
            }
            for label, directories in cases.items():
                wheel = base / label / "directory_demo-1.0-py3-none-any.whl"
                write_test_wheel(
                    wheel,
                    name="directory-demo",
                    version="1.0",
                    directory_entries=directories,
                )
                with self.subTest(label=label), self.assertRaises(audit.WheelAuditError):
                    audit.audit_wheel(wheel, "directory-demo", "1.0")

            recorded = base / "recorded" / "directory_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                recorded,
                name="directory-demo",
                version="1.0",
                extra_members=(("directory_demo/assets/", b"", 0o40755),),
            )
            with self.subTest(label="recorded"), self.assertRaises(audit.WheelAuditError):
                audit.audit_wheel(recorded, "directory-demo", "1.0")

            collision = base / "collision" / "directory_demo-1.0-py3-none-any.whl"
            write_test_wheel(
                collision,
                name="directory-demo",
                version="1.0",
                extra_members=(("directory_demo/assets", b"file", 0o100644),),
                directory_entries=(("directory_demo/assets/", b"", 0o40755),),
            )
            with self.subTest(label="file-directory-collision"), self.assertRaises(
                audit.WheelAuditError
            ):
                audit.audit_wheel(collision, "directory-demo", "1.0")

    def test_valid_abi_none_target_tag_matrix_is_accepted(self) -> None:
        audit = load_wheel_audit_module()
        valid_tags = (
            "py3-none-any",
            "py312-none-any",
            "cp312-none-any",
            "py3-none-manylinux_2_17_x86_64",
            "py312-none-manylinux2014_x86_64",
            "cp312-none-manylinux_2_28_x86_64",
        )
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for index, tag in enumerate(valid_tags):
                wheel = base / f"none_demo{index}-1.0-{tag}.whl"
                name = f"none-demo{index}"
                write_test_wheel(wheel, name=name, version="1.0", tags=(tag,))
                with self.subTest(tag=tag):
                    self.assertEqual((name, "1.0"), audit.audit_wheel(wheel, name, "1.0"))

    def test_wheel_resource_limits_accept_exact_boundary_and_reject_excess(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / "limit_demo-1.0-py3-none-any.whl"
            write_test_wheel(wheel, name="limit-demo", version="1.0")
            with zipfile.ZipFile(wheel) as archive:
                infos = archive.infolist()
                boundaries = {
                    "MAX_ARCHIVE_SIZE": wheel.stat().st_size,
                    "MAX_ENTRIES": len(infos),
                    "MAX_MEMBER_SIZE": max(info.file_size for info in infos),
                    "MAX_TOTAL_SIZE": sum(info.file_size for info in infos),
                }
            for constant, boundary in boundaries.items():
                with self.subTest(constant=constant, state="exact"), mock.patch.object(
                    audit, constant, boundary
                ):
                    self.assertEqual(
                        ("limit-demo", "1.0"),
                        audit.audit_wheel(wheel, "limit-demo", "1.0"),
                    )
                with self.subTest(constant=constant, state="excess"), mock.patch.object(
                    audit, constant, boundary - 1
                ), self.assertRaises(audit.WheelAuditError):
                    audit.audit_wheel(wheel, "limit-demo", "1.0")

    def test_highly_compressed_member_is_bounded_by_uncompressed_size(self) -> None:
        audit = load_wheel_audit_module()
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / "compressed_demo-1.0-py3-none-any.whl"
            payload = b"A" * (256 * 1024)
            write_test_wheel(
                wheel,
                name="compressed-demo",
                version="1.0",
                extra_members=(("compressed_demo/payload.bin", payload, 0o100644),),
                compression=zipfile.ZIP_DEFLATED,
            )
            self.assertLess(wheel.stat().st_size, len(payload) // 8)
            with mock.patch.object(audit, "MAX_MEMBER_SIZE", len(payload) - 1), self.assertRaises(
                audit.WheelAuditError
            ):
                audit.audit_wheel(wheel, "compressed-demo", "1.0")


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
        self.fake_wheels = self.base / "fake-wheels"
        self.fake_runtime_wheels = self.fake_wheels / "runtime"
        self.fake_application_wheel = (
            self.fake_wheels / "cognitive_card_server-0.3.1-py3-none-any.whl"
        )
        self.mutate_application_on_wheel = False
        self.runtime_mode = "valid"
        self.application_mode = "valid"
        self.governance.mkdir()
        self.application.mkdir()
        self.output.mkdir()
        self.fake_runtime_wheels.mkdir(parents=True)
        for filename in RUNTIME_WHEELS:
            fields = filename[:-4].split("-")
            write_test_wheel(
                self.fake_runtime_wheels / filename,
                name=fields[0].replace("_", "-"),
                version=fields[1],
                tags=("-".join(fields[-3:]),),
            )
        write_test_wheel(
            self.fake_application_wheel,
            name="cognitive-card-server",
            version="0.3.1",
        )

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
            "[project]\nname='cognitive-card-server'\nversion='0.3.1'\n",
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
                import shutil
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
                    source_wheels = pathlib.Path(os.environ["FAKE_RUNTIME_WHEELS"])
                    for source_wheel in source_wheels.iterdir():
                        shutil.copy2(source_wheel, destination / source_wheel.name)
                    mode = os.environ.get("FAKE_RUNTIME_MODE", "valid")
                    if mode == "missing":
                        (destination / "anyio-4.14.2-py3-none-any.whl").unlink()
                    elif mode == "wrong-version":
                        source = destination / "anyio-4.14.2-py3-none-any.whl"
                        source.rename(destination / "anyio-4.14.1-py3-none-any.whl")
                    elif mode == "duplicate":
                        shutil.copy2(
                            destination / "anyio-4.14.2-py3-none-any.whl",
                            destination / "anyio-4.14.2-1-py3-none-any.whl",
                        )
                    elif mode == "unexpected":
                        (destination / "unexpected-1.0-py3-none-any.whl").write_bytes(b"unexpected")
                    elif mode == "sdist":
                        (destination / "anyio-4.14.2.tar.gz").write_bytes(b"sdist")
                    elif mode == "unsafe-name":
                        (destination / "unsafe name.whl").write_bytes(b"unsafe")
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
                application_wheel = wheel_dir / "cognitive_card_server-0.3.1-py3-none-any.whl"
                if os.environ.get("FAKE_APPLICATION_MODE") == "corrupt":
                    application_wheel.write_bytes(b"corrupt-wheel")
                else:
                    shutil.copy2(os.environ["FAKE_APPLICATION_WHEEL"], application_wheel)
                """
            ),
            encoding="utf-8",
        )
        self.python.chmod(self.python.stat().st_mode | stat.S_IXUSR)

    def invoke(self, expected_commit: str | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["FAKE_WHEEL_LOG"] = os.fspath(self.log)
        environment["FAKE_APPLICATION_ROOT"] = os.fspath(self.application)
        environment["FAKE_RUNTIME_WHEELS"] = os.fspath(self.fake_runtime_wheels)
        environment["FAKE_APPLICATION_WHEEL"] = os.fspath(self.fake_application_wheel)
        environment["FAKE_APPLICATION_MODE"] = self.application_mode
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

    def test_builder_rejects_structurally_corrupt_application_wheel(self) -> None:
        fixture = BuilderFixture(self)
        fixture.application_mode = "corrupt"

        process = fixture.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertIn("WHEEL_INVALID", process.stderr)
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

        wheel_name = "cognitive_card_server-0.3.1-py3-none-any.whl"
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
        self.assertEqual("0.3.1", manifest["application_version"])
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

    def test_application_install_resolves_exact_audited_distribution_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            recorder = base / "python"
            command_log = base / "command.json"
            release = base / "release"
            release.mkdir()
            (release / "cognitive_card_server-0.3.1-py3-none-any.whl").write_bytes(b"wheel")
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
                os.fspath(release / "cognitive_card_server-0.3.1-py3-none-any.whl"),
                env=environment,
            )

            self.assertEqual(0, process.returncode, process.stderr)
            recorded = json.loads(command_log.read_text(encoding="utf-8"))
            self.assertEqual(
                [
                    "-m", "pip", "--isolated", "--disable-pip-version-check",
                    "install", "--no-input", "--no-index", "--no-deps", "--find-links",
                    os.fspath(release), "cognitive-card-server==0.3.1",
                ],
                recorded["arguments"],
            )
            self.assertEqual(os.devnull, recorded["pip_config_file"])
            self.assertIsNone(recorded["pip_index_url"])
            self.assertIsNone(recorded["pip_extra_index_url"])

    def test_real_pip_application_install_produces_canonical_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            release = base / "release"
            release.mkdir()
            wheel = release / "cognitive_card_server-0.3.1-py3-none-any.whl"
            write_test_wheel(wheel, name="cognitive-card-server", version="0.3.1")

            direct_venv = base / "direct-venv"
            created = run(sys.executable, "-m", "venv", os.fspath(direct_venv), cwd=ROOT)
            self.assertEqual(0, created.returncode, created.stderr)
            direct = run(
                os.fspath(direct_venv / "bin" / "python"),
                "-m", "pip", "--isolated", "--disable-pip-version-check",
                "install", "--no-input", "--no-index", "--no-deps", os.fspath(wheel),
                cwd=ROOT,
            )
            self.assertEqual(0, direct.returncode, direct.stderr)
            direct_freeze = run(
                os.fspath(direct_venv / "bin" / "python"),
                "-m", "pip", "freeze", "--all",
                cwd=ROOT,
            )
            self.assertEqual(0, direct_freeze.returncode, direct_freeze.stderr)
            self.assertIn("cognitive-card-server @ file://", direct_freeze.stdout)
            rejected = subprocess.run(
                ["bash", "-c", 'source "$1"; normalize_freeze', "normalizer", os.fspath(INSTALLER)],
                input=direct_freeze.stdout,
                text=True,
                capture_output=True,
                cwd=ROOT,
                check=False,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("INVALID_FREEZE", rejected.stderr)

            resolved_venv = base / "resolved-venv"
            created = run(sys.executable, "-m", "venv", os.fspath(resolved_venv), cwd=ROOT)
            self.assertEqual(0, created.returncode, created.stderr)
            installed = self.run_installer_function(
                'source "$1"; install_application_wheel "$2" "$3"',
                os.fspath(resolved_venv / "bin" / "python"),
                os.fspath(wheel),
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            resolved_freeze = run(
                os.fspath(resolved_venv / "bin" / "python"),
                "-m", "pip", "freeze", "--all",
                cwd=ROOT,
            )
            self.assertEqual(0, resolved_freeze.returncode, resolved_freeze.stderr)
            self.assertIn("cognitive-card-server==0.3.1\n", resolved_freeze.stdout)
            self.assertNotIn("cognitive-card-server @ ", resolved_freeze.stdout)
            normalized = subprocess.run(
                ["bash", "-c", 'source "$1"; normalize_freeze', "normalizer", os.fspath(INSTALLER)],
                input=resolved_freeze.stdout,
                text=True,
                capture_output=True,
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(0, normalized.returncode, normalized.stderr)
            self.assertIn("cognitive-card-server==0.3.1\n", normalized.stdout)

    def test_real_pip_cannot_use_hostile_config_or_find_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            governed = base / "governed"
            attacker = base / "attacker"
            governed.mkdir()
            attacker_wheel = attacker / "attacker_only-1.0-py3-none-any.whl"
            write_test_wheel(
                attacker_wheel,
                name="attacker-only",
                version="1.0",
                module_content=b"MARKER = 'attacker'\n",
            )
            lock = base / "runtime.lock"
            lock.write_text("attacker-only==1.0\n", encoding="utf-8")
            config = base / "pip.conf"
            config.write_text(
                f"[global]\nno-index = true\nfind-links = {attacker}\n",
                encoding="utf-8",
            )
            venv = base / "venv"
            created = run(sys.executable, "-m", "venv", os.fspath(venv), cwd=ROOT)
            self.assertEqual(0, created.returncode, created.stderr)
            environment = os.environ.copy()
            environment.update({
                "PIP_CONFIG_FILE": os.fspath(config),
                "PIP_FIND_LINKS": os.fspath(attacker),
                "PIP_INDEX_URL": "https://environment.invalid/simple",
                "PIP_EXTRA_INDEX_URL": "https://extra.invalid/simple",
            })
            installed = self.run_installer_function(
                'source "$1"; install_runtime_dependencies "$2" "$3" "$4"',
                os.fspath(venv / "bin" / "python"),
                os.fspath(lock),
                os.fspath(governed),
                env=environment,
            )
            self.assertNotEqual(0, installed.returncode, installed.stdout)
            imported = run(
                os.fspath(venv / "bin" / "python"),
                "-c",
                "import attacker_only",
                cwd=ROOT,
            )
            self.assertNotEqual(0, imported.returncode)

    def test_first_install_prepares_private_data_paths_and_cleans_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            data_root = base / "data"
            candidate_root = data_root / "candidates"
            database = data_root / "card-os.sqlite3"
            uid = os.getuid()
            gid = os.getgid()
            script = r'''
source "$1"
prepare_data_layout "$2" data candidates card-os.sqlite3 "$3" "$4" "$3" "$4"
'''
            process = self.run_installer_function(
                script,
                os.fspath(base),
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
            script = r'''
source "$1"
prepare_data_layout "$2" data candidates card-os.sqlite3 "$3" "$4" "$3" "$4"
'''
            process = self.run_installer_function(
                script,
                os.fspath(base),
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
            for label in ("wrong-owner", "wrong-mode", "link", "directory"):
                with self.subTest(label=label):
                    parent = base / label
                    data = parent / "data"
                    candidate = data / "candidates"
                    candidate.mkdir(parents=True)
                    data.chmod(0o700)
                    candidate.chmod(0o700)
                    database = data / "card-os.sqlite3"
                    expected_db_uid = uid
                    if label == "wrong-owner":
                        database.write_bytes(b"db")
                        database.chmod(0o600)
                        expected_db_uid = uid + 1
                    elif label == "wrong-mode":
                        database.write_bytes(b"db")
                        database.chmod(0o640)
                    elif label == "link":
                        target = parent / "target"
                        target.write_bytes(b"target")
                        target.chmod(0o600)
                        database.symlink_to(target)
                    else:
                        database.mkdir()
                    process = self.run_installer_function(
                        'source "$1"; prepare_data_layout "$2" data candidates card-os.sqlite3 "$3" "$4" "$5" "$4"',
                        os.fspath(parent),
                        str(uid),
                        str(gid),
                        str(expected_db_uid),
                    )
                    self.assertNotEqual(0, process.returncode)
                    self.assertIn("error=UNSAFE_DATABASE", process.stderr)
                    self.assertTrue(database.exists() or database.is_symlink())

    def test_data_and_candidate_roots_reject_links_and_non_directories(self) -> None:
        uid = os.getuid()
        gid = os.getgid()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            directory = base / "real-directory"
            directory.mkdir()
            link = base / "linked-directory"
            link.symlink_to(directory, target_is_directory=True)
            regular = base / "regular-file"
            regular.write_bytes(b"keep")
            candidate_target = base / "real-candidate"
            candidate_target.mkdir()
            candidate_link = directory / "linked-candidate"
            candidate_link.symlink_to(candidate_target, target_is_directory=True)
            candidate_regular = directory / "candidate-file"
            candidate_regular.write_bytes(b"keep")

            for path, error, data_name, candidate_name in (
                (link, "UNSAFE_DATA_ROOT", link.name, "candidates"),
                (regular, "UNSAFE_DATA_ROOT", regular.name, "candidates"),
                (candidate_link, "UNSAFE_CANDIDATE_ROOT", directory.name, candidate_link.name),
                (candidate_regular, "UNSAFE_CANDIDATE_ROOT", directory.name, candidate_regular.name),
            ):
                with self.subTest(path=path.name, error=error):
                    process = self.run_installer_function(
                        'source "$1"; prepare_data_layout "$2" "$3" "$4" card-os.sqlite3 "$5" "$6" "$5" "$6"',
                        os.fspath(base),
                        data_name,
                        candidate_name,
                        str(uid),
                        str(gid),
                    )
                    self.assertNotEqual(0, process.returncode)
                    self.assertIn(f"error={error}", process.stderr)
                    self.assertTrue(path.exists() or path.is_symlink())

    def test_data_layout_uses_only_trusted_parent_descriptor_operations(self) -> None:
        source = self.installer_source()
        self.assertIn("prepare_data_layout", source)
        for required in (
            "dir_fd=parent_fd",
            "dir_fd=data_fd",
            "os.mkdir(",
            "os.fchown(",
            "os.fchmod(",
            "follow_symlinks=False",
            "os.fork()",
            "os.setgid(",
            "os.setuid(",
            "os.O_EXCL",
        ):
            self.assertIn(required, source)
        self.assertNotIn("ensure_private_directory", source)
        self.assertNotIn("validate_database_file", source)
        self.assertNotIn("probe_data_root", source)
        self.assertNotRegex(source, r"install -d[^\n]+/var/lib/cognitive-card-server")

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
            'release_id=$(verify_release "$extracted")',
            'audit_release_wheels "$extracted"',
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
        for fragment in ordered:
            self.assertIn(fragment, main_source)
        positions = [main_source.index(fragment) for fragment in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("set -euo pipefail", source)
        self.assertIn("umask 022", source)
        self.assertIn('chmod 0755 "$RELEASE_DIR/.venv/bin/cognitive-card-api"', source)
        self.assertNotIn("nginx -", source)
        self.assertNotIn("/etc/nginx", source)

    def test_installer_audits_manifest_bound_wheels_with_governed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            release = base / "release"
            release.mkdir()
            write_release_tree(release)
            valid = self.run_installer_function(
                'source "$1"; verify_release "$2" >/dev/null; audit_release_wheels "$2"',
                os.fspath(release),
            )
            self.assertEqual(0, valid.returncode, valid.stderr)

            application = release / "cognitive_card_server-0.3.1-py3-none-any.whl"
            application.write_bytes(b"corrupt-wheel")
            manifest_path = release / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in manifest["files"]:
                if item["path"] == application.name:
                    item["sha256"] = hashlib.sha256(application.read_bytes()).hexdigest()
                    item["size"] = application.stat().st_size
            manifest["wheel_sha256"] = hashlib.sha256(application.read_bytes()).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            invalid = self.run_installer_function(
                'source "$1"; verify_release "$2" >/dev/null; audit_release_wheels "$2"',
                os.fspath(release),
            )
            self.assertNotEqual(0, invalid.returncode)
            self.assertIn("error=WHEEL_INVALID", invalid.stderr)

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
                        "cognitive_card_server-0.3.1-py3-none-any.whl",
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

    def test_failed_activation_restores_old_units_reloads_and_restores_service_states(self) -> None:
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
            unit_paths = (
                base / "cognitive-card-server.service",
                base / "cognitive-card-backup.service",
                base / "cognitive-card-backup.timer",
            )
            for index, path in enumerate(unit_paths, start=1):
                path.write_text(f"old-unit-{index}\n", encoding="utf-8")
            log = base / "systemctl.log"
            log.touch()
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
INSTALL_UNIT_BACKUP_DIR="$2/unit-backups"
backup_systemd_units "$INSTALL_UNIT_BACKUP_DIR"
printf 'new-api-unit\n' >"$API_UNIT_PATH"
printf 'new-backup-unit\n' >"$BACKUP_SERVICE_UNIT_PATH"
printf 'new-backup-timer\n' >"$BACKUP_TIMER_UNIT_PATH"
LOG_PATH="$7"
systemctl() { printf '%s\n' "$*" >>"$LOG_PATH"; }
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$5"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=1
INSTALL_UNITS_INSTALLED=1
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$6"
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
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(staging), os.fspath(new_release),
                os.fspath(current), os.fspath(old_release), os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            for index, path in enumerate(unit_paths, start=1):
                self.assertEqual(f"old-unit-{index}\n", path.read_text(encoding="utf-8"))
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("stop cognitive-card-server.service", commands)
            self.assertIn("stop cognitive-card-backup.timer", commands)
            self.assertIn("daemon-reload", commands)
            self.assertIn("enable cognitive-card-server.service", commands)
            self.assertIn("enable cognitive-card-backup.timer", commands)
            self.assertIn("start cognitive-card-server.service", commands)
            self.assertIn("start cognitive-card-backup.timer", commands)
            self.assertLess(
                commands.index("daemon-reload"),
                commands.index("enable cognitive-card-server.service"),
            )

    def test_unit_write_failure_restores_all_old_units_before_activation(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            source = base / "source" / "systemd"
            old_release = base / "releases" / ("1" * 40)
            new_release = base / "releases" / ("2" * 40)
            staging.mkdir()
            source.mkdir(parents=True)
            old_release.mkdir(parents=True)
            new_release.mkdir()
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(old_release)
            unit_names = (
                "cognitive-card-server.service",
                "cognitive-card-backup.service",
                "cognitive-card-backup.timer",
            )
            for index, name in enumerate(unit_names, start=1):
                (base / name).write_text(f"old-unit-{index}\n", encoding="utf-8")
                (source / name).write_text(f"new-unit-{index}\n", encoding="utf-8")
            log = base / "systemctl.log"
            log.touch()
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
LOG_PATH="$8"
systemctl() { printf '%s\n' "$*" >>"$LOG_PATH"; }
INSTALL_CALLS=0
install() {
    INSTALL_CALLS=$((INSTALL_CALLS + 1))
    if [[ "$INSTALL_CALLS" == 2 ]]; then return 1; fi
    command install "$@"
}
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$5"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$6"
INSTALL_OLD_API_ACTIVE=active
INSTALL_OLD_API_ENABLED=enabled
INSTALL_OLD_TIMER_ACTIVE=active
INSTALL_OLD_TIMER_ENABLED=enabled
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
trap install_cleanup EXIT
install_systemd_units "$7" "$INSTALL_UNIT_BACKUP_DIR"
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(staging), os.fspath(new_release),
                os.fspath(current), os.fspath(old_release), os.fspath(source),
                os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            for index, name in enumerate(unit_names, start=1):
                self.assertEqual(
                    f"old-unit-{index}\n", (base / name).read_text(encoding="utf-8")
                )
            self.assertEqual(["daemon-reload"], log.read_text(encoding="utf-8").splitlines())

    def test_daemon_reload_failure_restores_old_units_before_activation(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            source = base / "source" / "systemd"
            old_release = base / "releases" / ("1" * 40)
            new_release = base / "releases" / ("2" * 40)
            staging.mkdir()
            source.mkdir(parents=True)
            old_release.mkdir(parents=True)
            new_release.mkdir()
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            current = base / "current"
            current.symlink_to(old_release)
            unit_names = (
                "cognitive-card-server.service",
                "cognitive-card-backup.service",
                "cognitive-card-backup.timer",
            )
            for index, name in enumerate(unit_names, start=1):
                (base / name).write_text(f"old-unit-{index}\n", encoding="utf-8")
                (source / name).write_text(f"new-unit-{index}\n", encoding="utf-8")
            log = base / "systemctl.log"
            log.touch()
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
LOG_PATH="$8"
DAEMON_RELOADS=0
systemctl() {
    printf '%s\n' "$*" >>"$LOG_PATH"
    if [[ "$*" == daemon-reload ]]; then
        DAEMON_RELOADS=$((DAEMON_RELOADS + 1))
        [[ "$DAEMON_RELOADS" != 1 ]]
        return
    fi
}
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$5"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$6"
INSTALL_OLD_API_ACTIVE=active
INSTALL_OLD_API_ENABLED=enabled
INSTALL_OLD_TIMER_ACTIVE=active
INSTALL_OLD_TIMER_ENABLED=enabled
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
trap install_cleanup EXIT
install_systemd_units "$7" "$INSTALL_UNIT_BACKUP_DIR"
systemctl daemon-reload
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(staging), os.fspath(new_release),
                os.fspath(current), os.fspath(old_release), os.fspath(source),
                os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            for index, name in enumerate(unit_names, start=1):
                self.assertEqual(
                    f"old-unit-{index}\n", (base / name).read_text(encoding="utf-8")
                )
            self.assertEqual(
                ["daemon-reload", "daemon-reload"],
                log.read_text(encoding="utf-8").splitlines(),
            )

    def test_first_install_failure_removes_new_units_and_reloads_before_activation(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            staging = base / "staging"
            source = base / "source" / "systemd"
            new_release = base / "releases" / ("2" * 40)
            staging.mkdir()
            source.mkdir(parents=True)
            new_release.mkdir(parents=True)
            (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
            unit_names = (
                "cognitive-card-server.service",
                "cognitive-card-backup.service",
                "cognitive-card-backup.timer",
            )
            for index, name in enumerate(unit_names, start=1):
                (source / name).write_text(f"new-unit-{index}\n", encoding="utf-8")
            log = base / "systemctl.log"
            log.touch()
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
LOG_PATH="$6"
systemctl() { printf '%s\n' "$*" >>"$LOG_PATH"; }
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$2/current"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET=""
INSTALL_OLD_API_ACTIVE=inactive
INSTALL_OLD_API_ENABLED=disabled
INSTALL_OLD_TIMER_ACTIVE=inactive
INSTALL_OLD_TIMER_ENABLED=disabled
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
trap install_cleanup EXIT
install_systemd_units "$5" "$INSTALL_UNIT_BACKUP_DIR"
false
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(staging), os.fspath(new_release),
                os.fspath(source), os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertFalse((base / "current").exists())
            for name in unit_names:
                self.assertFalse((base / name).exists())
                self.assertFalse((base / name).is_symlink())
            self.assertEqual(["daemon-reload"], log.read_text(encoding="utf-8").splitlines())

    def test_first_and_third_unit_write_failures_restore_all_old_units(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        for failure_index in (1, 3):
            with self.subTest(failure_index=failure_index), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                staging = base / "staging"
                source = base / "source" / "systemd"
                old_release = base / "releases" / ("1" * 40)
                new_release = base / "releases" / ("2" * 40)
                staging.mkdir()
                source.mkdir(parents=True)
                old_release.mkdir(parents=True)
                new_release.mkdir()
                (new_release / ".install-owner").write_text("test-token\n", encoding="ascii")
                current = base / "current"
                current.symlink_to(old_release)
                unit_names = (
                    "cognitive-card-server.service",
                    "cognitive-card-backup.service",
                    "cognitive-card-backup.timer",
                )
                for index, name in enumerate(unit_names, start=1):
                    (base / name).write_text(f"old-unit-{index}\n", encoding="utf-8")
                    (source / name).write_text(f"new-unit-{index}\n", encoding="utf-8")
                script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
systemctl() { return 0; }
INSTALL_CALLS=0
FAILURE_INDEX="$8"
install() {
    INSTALL_CALLS=$((INSTALL_CALLS + 1))
    if [[ "$INSTALL_CALLS" == "$FAILURE_INDEX" ]]; then return 1; fi
    command install "$@"
}
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$5"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$6"
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
trap install_cleanup EXIT
install_systemd_units "$7" "$INSTALL_UNIT_BACKUP_DIR"
'''
                process = run(
                    "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                    os.fspath(base), os.fspath(staging), os.fspath(new_release),
                    os.fspath(current), os.fspath(old_release), os.fspath(source),
                    str(failure_index), cwd=ROOT,
                )
                self.assertNotEqual(0, process.returncode)
                self.assertFalse(staging.exists())
                self.assertFalse(new_release.exists())
                self.assertEqual(os.fspath(old_release), os.readlink(current))
                for index, name in enumerate(unit_names, start=1):
                    self.assertEqual(
                        f"old-unit-{index}\n", (base / name).read_text(encoding="utf-8")
                    )

    def test_unit_restore_preserves_regular_metadata_and_symlink(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            api = base / "cognitive-card-server.service"
            backup_service = base / "cognitive-card-backup.service"
            timer = base / "cognitive-card-backup.timer"
            target = base / "linked-backup.service"
            api.write_text("old-api\n", encoding="utf-8")
            api.chmod(0o600)
            target.write_text("linked\n", encoding="utf-8")
            backup_service.symlink_to(target.name)
            timer.write_text("old-timer\n", encoding="utf-8")
            timer.chmod(0o640)
            unit_paths = (api, backup_service, timer)
            original_metadata = [path.lstat() for path in unit_paths]
            for index, path in enumerate(unit_paths, start=1):
                (source / path.name).write_text(f"new-unit-{index}\n", encoding="utf-8")
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
systemctl() { return 0; }
INSTALL_UNIT_BACKUP_DIR="$2/unit-backups"
install_systemd_units "$3" "$INSTALL_UNIT_BACKUP_DIR"
restore_systemd_units "$INSTALL_UNIT_BACKUP_DIR"
'''
            process = run(
                "bash", "-c", script, "metadata", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(source), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            for path, before in zip(unit_paths, original_metadata, strict=True):
                after = path.lstat()
                self.assertEqual(stat.S_IMODE(before.st_mode), stat.S_IMODE(after.st_mode))
                self.assertEqual(before.st_uid, after.st_uid)
                self.assertEqual(before.st_gid, after.st_gid)
                self.assertEqual(stat.S_IFMT(before.st_mode), stat.S_IFMT(after.st_mode))
            self.assertTrue(backup_service.is_symlink())
            self.assertEqual(target.name, os.readlink(backup_service))

    def test_partial_unit_restore_failure_preserves_exact_backup_directory(self) -> None:
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
            unit_names = (
                "cognitive-card-server.service",
                "cognitive-card-backup.service",
                "cognitive-card-backup.timer",
            )
            for index, name in enumerate(unit_names, start=1):
                (base / name).write_text(f"old-unit-{index}\n", encoding="utf-8")
            script = r'''
source "$1"
API_UNIT_PATH="$2/cognitive-card-server.service"
BACKUP_SERVICE_UNIT_PATH="$2/cognitive-card-backup.service"
BACKUP_TIMER_UNIT_PATH="$2/cognitive-card-backup.timer"
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
backup_systemd_units "$INSTALL_UNIT_BACKUP_DIR"
printf 'new-api\n' >"$API_UNIT_PATH"
printf 'new-backup\n' >"$BACKUP_SERVICE_UNIT_PATH"
printf 'new-timer\n' >"$BACKUP_TIMER_UNIT_PATH"
cp() {
    if [[ "$1" == -a && "$3" == "$INSTALL_UNIT_BACKUP_DIR/cognitive-card-backup.service" ]]; then
        return 1
    fi
    command cp "$@"
}
systemctl() { return 0; }
INSTALL_TEMPORARY_DIR="$3"
INSTALL_RELEASE_DIR="$4"
INSTALL_RELEASE_CREATED=1
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_CURRENT_PATH="$5"
INSTALL_CURRENT_LINK=""
INSTALL_ACTIVATED=1
INSTALL_UNITS_INSTALLED=1
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET="$6"
INSTALL_OLD_API_ACTIVE=active
INSTALL_OLD_API_ENABLED=enabled
INSTALL_OLD_TIMER_ACTIVE=active
INSTALL_OLD_TIMER_ENABLED=enabled
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0
trap install_cleanup EXIT
false
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(base), os.fspath(staging), os.fspath(new_release),
                os.fspath(current), os.fspath(old_release), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("error=INSTALL_ROLLBACK_FAILED", process.stderr)
            self.assertIn(f"rollback_backup_dir={staging / 'systemd-backup'}", process.stderr)
            self.assertTrue(staging.is_dir())
            self.assertTrue(new_release.is_dir())
            backup_dir = staging / "systemd-backup"
            for name in unit_names:
                self.assertTrue((backup_dir / name).exists())
                self.assertTrue((backup_dir / f"{name}.state").exists())

    def test_cleanup_ignores_secondary_term_until_rollback_finishes(self) -> None:
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
            log = base / "systemctl.log"
            script = r'''
source "$1"
LOG_PATH="$6"
systemctl() {
    printf '%s\n' "$*" >>"$LOG_PATH"
    if [[ "$*" == "stop cognitive-card-server.service" ]]; then kill -TERM $$; fi
    return 0
}
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
trap 'exit 143' TERM
trap install_cleanup EXIT
false
'''
            process = run(
                "bash", "-c", script, "signal", os.fspath(INSTALLER),
                os.fspath(staging), os.fspath(new_release), os.fspath(current),
                os.fspath(old_release), os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertFalse(staging.exists())
            self.assertFalse(new_release.exists())
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("enable cognitive-card-server.service", commands)
            self.assertIn("start cognitive-card-server.service", commands)

    def test_success_finalization_reports_temp_cleanup_failure_and_leaves_no_silent_residue(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            release = base / "release"
            staging = base / "staging"
            release.mkdir()
            staging.mkdir()
            (release / ".install-owner").write_text("test-token\n", encoding="ascii")
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_TEMPORARY_DIR="$3"
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
INSTALL_RELEASE_CREATED=1
INSTALL_ACTIVATED=1
INSTALL_UNITS_INSTALLED=1
TEMP_PATH="$3"
rm() {
    if [[ "$1" == -rf && "$3" == "$TEMP_PATH" ]]; then return 1; fi
    command rm "$@"
}
finalize_successful_install "$2" "$3" && printf 'status=installed\n'
'''
            process = run(
                "bash", "-c", script, "finalize", os.fspath(INSTALLER),
                os.fspath(release), os.fspath(staging), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("error=TEMPORARY_CLEANUP_FAILED", process.stderr)
            self.assertNotIn("status=installed", process.stdout)
            self.assertTrue(staging.is_dir())

    def test_success_finalization_removes_unit_backups_before_reporting_installed(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "missing release installer")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            release = base / "release"
            staging = base / "staging"
            backup_dir = staging / "systemd-backup"
            release.mkdir()
            backup_dir.mkdir(parents=True)
            (backup_dir / "cognitive-card-server.service").write_text(
                "old-unit\n", encoding="utf-8"
            )
            (release / ".install-owner").write_text("test-token\n", encoding="ascii")
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
INSTALL_TEMPORARY_DIR="$3"
INSTALL_UNIT_BACKUP_DIR="$3/systemd-backup"
INSTALL_RELEASE_CREATED=1
INSTALL_ACTIVATED=1
INSTALL_UNITS_INSTALLED=1
finalize_successful_install "$2" "$3"
printf 'status=installed\n'
'''
            process = run(
                "bash", "-c", script, "finalize", os.fspath(INSTALLER),
                os.fspath(release), os.fspath(staging), cwd=ROOT,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual("status=installed\n", process.stdout)
            self.assertFalse(staging.exists())
            self.assertFalse((release / ".install-owner").exists())

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
            log = base / "systemctl.log"
            script = r'''
source "$1"
INSTALL_OWNERSHIP_TOKEN=test-token
LOG_PATH="$5"
systemctl() {
    printf '%s\n' "$*" >>"$LOG_PATH"
    if [[ "$1 $2" == "stop cognitive-card-server.service" ]]; then return 1; fi
    return 0
}
rollback_activation "$2" "$3" "$4" inactive disabled inactive disabled 1 0
'''
            process = run(
                "bash", "-c", script, "rollback", os.fspath(INSTALLER),
                os.fspath(current), os.fspath(new_release), os.fspath(old_release),
                os.fspath(log), cwd=ROOT,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("error=INSTALL_ROLLBACK_FAILED", process.stderr)
            self.assertTrue(new_release.is_dir())
            self.assertEqual(os.fspath(old_release), os.readlink(current))
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("stop cognitive-card-server.service", commands)
            self.assertNotIn("disable cognitive-card-server.service", commands)
            self.assertNotIn("disable cognitive-card-backup.timer", commands)
            self.assertNotIn("start cognitive-card-server.service", commands)
            self.assertNotIn("start cognitive-card-backup.timer", commands)

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
