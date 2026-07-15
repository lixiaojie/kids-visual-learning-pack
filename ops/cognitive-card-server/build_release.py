#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


APPLICATION_VERSION = "0.3.1"
MANIFEST_SCHEMA = "cognitive-card-server-release-v2"
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
WHEEL_PATTERN = re.compile(r"^cognitive_card_server-0\.3\.1-[A-Za-z0-9_.-]+\.whl$")
RUNTIME_TARGET = {
    "abi": "cp312",
    "implementation": "cp",
    "only_binary": ":all:",
    "platforms": ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64"],
    "python_version": "312",
}

PAYLOAD_ASSETS = (
    ("runtime-requirements.lock", "runtime-requirements.lock"),
    ("card_os_backup.py", "ops/card_os_backup.py"),
    ("card_os_acceptance.py", "ops/card_os_acceptance.py"),
    ("install_nginx_include.py", "ops/install_nginx_include.py"),
    ("wheel_audit.py", "ops/wheel_audit.py"),
    ("env/card-os.env", "env/card-os.env"),
    ("systemd/cognitive-card-server.service", "systemd/cognitive-card-server.service"),
    ("systemd/cognitive-card-backup.service", "systemd/cognitive-card-backup.service"),
    ("systemd/cognitive-card-backup.timer", "systemd/cognitive-card-backup.timer"),
    ("nginx/card-os.conf", "nginx/card-os.conf"),
)
EXECUTABLE_PAYLOADS = {
    "ops/card_os_backup.py",
    "ops/card_os_acceptance.py",
    "ops/install_nginx_include.py",
    "ops/wheel_audit.py",
}


class ReleaseError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_checked(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> str:
    try:
        process = subprocess.run(
            arguments,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReleaseError("COMMAND_FAILED") from error
    if process.returncode:
        raise ReleaseError("COMMAND_FAILED")
    return process.stdout.strip()


def isolated_pip_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PIP_CONFIG_FILE"] = os.devnull
    environment.pop("PIP_INDEX_URL", None)
    environment.pop("PIP_EXTRA_INDEX_URL", None)
    return environment


def run_checked_bytes(arguments: list[str], *, cwd: Path | None = None) -> bytes:
    try:
        process = subprocess.run(
            arguments,
            cwd=cwd,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReleaseError("COMMAND_FAILED") from error
    if process.returncode:
        raise ReleaseError("COMMAND_FAILED")
    return process.stdout


def git(repository: Path, *arguments: str) -> str:
    return run_checked(["git", "-C", os.fspath(repository), *arguments])


def git_tree_entries(repository: Path, commit: str) -> list[tuple[str, str, str, str]]:
    output = run_checked_bytes(
        [
            "git",
            "-C",
            os.fspath(repository),
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            commit,
        ]
    )
    entries: list[tuple[str, str, str, str]] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        header, separator, path_bytes = record.partition(b"\t")
        fields = header.split(b" ")
        if not separator or len(fields) != 3 or not path_bytes:
            raise ReleaseError("COMMAND_FAILED")
        try:
            mode = fields[0].decode("ascii")
            object_type = fields[1].decode("ascii")
            object_id = fields[2].decode("ascii").lower()
        except UnicodeDecodeError as error:
            raise ReleaseError("COMMAND_FAILED") from error
        if COMMIT_PATTERN.fullmatch(object_id) is None:
            raise ReleaseError("COMMAND_FAILED")
        entries.append((mode, object_type, object_id, os.fsdecode(path_bytes)))
    return entries


def validate_regular_tree(entries: list[tuple[str, str, str, str]]) -> None:
    if any(
        mode not in {"100644", "100755"} or object_type != "blob"
        for mode, object_type, _, _ in entries
    ):
        raise ReleaseError("COMMAND_FAILED")


def validate_staged_bytes(
    source_dir: Path, entries: list[tuple[str, str, str, str]]
) -> None:
    for mode, _, object_id, path in entries:
        staged = source_dir / path
        try:
            metadata = staged.lstat()
        except OSError as error:
            raise ReleaseError("COMMAND_FAILED") from error
        if not stat.S_ISREG(metadata.st_mode):
            raise ReleaseError("COMMAND_FAILED")
        executable_bits = metadata.st_mode & (
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        if (
            mode == "100755" and not executable_bits & stat.S_IXUSR
        ) or (
            mode == "100644" and executable_bits
        ):
            raise ReleaseError("COMMAND_FAILED")
        if git(source_dir, "hash-object", "--no-filters", "--", path).lower() != object_id:
            raise ReleaseError("COMMAND_FAILED")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def python_version(python: Path) -> str:
    output = run_checked([os.fspath(python), "--version"])
    match = re.fullmatch(r"Python (\d+\.\d+\.\d+)", output)
    if match is None:
        raise ReleaseError("PYTHON_VERSION_INVALID")
    return match.group(1)


def load_wheel_audit():
    path = Path(__file__).resolve().with_name("wheel_audit.py")
    spec = importlib.util.spec_from_file_location("card_os_governed_wheel_audit", path)
    if spec is None or spec.loader is None:
        raise ReleaseError("WHEEL_INVALID")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (OSError, ImportError) as error:
        raise ReleaseError("WHEEL_INVALID") from error
    return module


def validate_runtime_wheelhouse(wheelhouse: Path, lock_path: Path) -> list[Path]:
    audit = load_wheel_audit()
    try:
        return audit.audit_wheelhouse(wheelhouse, lock_path)
    except audit.WheelAuditError as error:
        raise ReleaseError("RUNTIME_WHEELHOUSE_INVALID") from error


def operations_repository(ops_dir: Path) -> Path:
    repository = git(ops_dir, "rev-parse", "--show-toplevel")
    if not repository:
        raise ReleaseError("OPERATIONS_REPOSITORY_INVALID")
    return Path(repository)


def copy_payload(ops_dir: Path, release_dir: Path) -> list[Path]:
    copied: list[Path] = []
    for source_name, archive_name in PAYLOAD_ASSETS:
        source = ops_dir / source_name
        if not source.is_file():
            raise ReleaseError("PAYLOAD_MISSING")
        destination = release_dir / archive_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied.append(destination)
    return copied


def normalized_tar(archive: Path, release_dir: Path, names: list[str]) -> None:
    with archive.open("xb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as gzip_stream:
            with tarfile.open(fileobj=gzip_stream, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for name in sorted(names):
                    source = release_dir / name
                    info = tarfile.TarInfo(name)
                    info.size = source.stat().st_size
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    info.mode = 0o755 if name in EXECUTABLE_PAYLOADS else 0o644
                    with source.open("rb") as payload:
                        bundle.addfile(info, payload)


def build_release(
    *, server_repo: Path, expected_commit: str, output_dir: Path, python: Path
) -> dict[str, str]:
    expected_commit = expected_commit.lower()
    if COMMIT_PATTERN.fullmatch(expected_commit) is None:
        raise ReleaseError("EXPECTED_COMMIT_INVALID")

    head = git(server_repo, "rev-parse", "HEAD").lower()
    if head != expected_commit:
        raise ReleaseError("SOURCE_COMMIT_MISMATCH")
    if git(server_repo, "status", "--porcelain"):
        raise ReleaseError("SOURCE_WORKTREE_DIRTY")
    tree_entries = git_tree_entries(server_repo, expected_commit)
    validate_regular_tree(tree_entries)

    ops_dir = Path(__file__).resolve().parent
    governance_repo = operations_repository(ops_dir)
    if git(governance_repo, "status", "--porcelain", "--untracked-files=no"):
        raise ReleaseError("OPERATIONS_WORKTREE_DIRTY")
    operations_commit = git(governance_repo, "rev-parse", "HEAD").lower()
    if COMMIT_PATTERN.fullmatch(operations_commit) is None:
        raise ReleaseError("OPERATIONS_COMMIT_INVALID")

    interpreter_version = python_version(python)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"cognitive-card-server-{expected_commit}.tar.gz"
    checksum_file = Path(f"{archive}.sha256")
    if archive.exists() or checksum_file.exists():
        raise ReleaseError("OUTPUT_EXISTS")

    with tempfile.TemporaryDirectory(prefix="card-os-release-") as temporary:
        staging = Path(temporary)
        source_dir = staging / "source"
        run_checked(
            [
                "git",
                "clone",
                "--no-checkout",
                "--no-local",
                "--quiet",
                "--",
                os.fspath(server_repo),
                os.fspath(source_dir),
            ]
        )
        run_checked(
            [
                "git",
                "-C",
                os.fspath(source_dir),
                "checkout",
                "--quiet",
                "--detach",
                expected_commit,
            ]
        )
        if (
            git(source_dir, "rev-parse", "HEAD").lower() != expected_commit
            or git(source_dir, "status", "--porcelain")
        ):
            raise ReleaseError("COMMAND_FAILED")
        validate_staged_bytes(source_dir, tree_entries)
        lock_source = ops_dir / "runtime-requirements.lock"
        runtime_wheel_dir = staging / "runtime-wheels"
        runtime_wheel_dir.mkdir()
        run_checked(
            [
                os.fspath(python),
                "-m",
                "pip",
                "--isolated",
                "--disable-pip-version-check",
                "download",
                "--no-input",
                "--only-binary=:all:",
                "--index-url",
                "https://pypi.org/simple",
                "--platform",
                "manylinux_2_28_x86_64",
                "--platform",
                "manylinux_2_17_x86_64",
                "--implementation",
                "cp",
                "--python-version",
                "312",
                "--abi",
                "cp312",
                "--dest",
                os.fspath(runtime_wheel_dir),
                "--requirement",
                os.fspath(lock_source),
            ],
            env=isolated_pip_environment(),
        )
        runtime_wheels = validate_runtime_wheelhouse(runtime_wheel_dir, lock_source)
        wheel_dir = staging / "wheel"
        wheel_dir.mkdir()
        # The pinned backend still executes as the invoking user. This staging
        # boundary protects the live tree from ordinary build outputs; it is
        # not an operating-system sandbox for hostile build code.
        run_checked(
            [
                os.fspath(python),
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                os.fspath(wheel_dir),
                os.fspath(source_dir),
            ],
            env=isolated_pip_environment(),
        )
        wheels = [path for path in wheel_dir.iterdir() if path.is_file()]
        if len(wheels) != 1 or WHEEL_PATTERN.fullmatch(wheels[0].name) is None:
            raise ReleaseError("APPLICATION_WHEEL_INVALID")
        audit = load_wheel_audit()
        try:
            audit.audit_wheel(wheels[0], "cognitive-card-server", APPLICATION_VERSION)
        except audit.WheelAuditError as error:
            raise ReleaseError("WHEEL_INVALID") from error

        release_dir = staging / "release"
        release_dir.mkdir()
        payloads = copy_payload(ops_dir, release_dir)
        wheel = release_dir / wheels[0].name
        shutil.copyfile(wheels[0], wheel)
        payloads.append(wheel)
        release_wheelhouse = release_dir / "runtime-wheels"
        release_wheelhouse.mkdir()
        for runtime_wheel in runtime_wheels:
            destination = release_wheelhouse / runtime_wheel.name
            shutil.copyfile(runtime_wheel, destination)
            payloads.append(destination)

        if (
            git(server_repo, "rev-parse", "HEAD").lower() != expected_commit
            or git(server_repo, "status", "--porcelain")
        ):
            raise ReleaseError("SOURCE_CHANGED_DURING_BUILD")
        if (
            git(governance_repo, "rev-parse", "HEAD").lower() != operations_commit
            or git(governance_repo, "status", "--porcelain", "--untracked-files=no")
        ):
            raise ReleaseError("OPERATIONS_CHANGED_DURING_BUILD")

        files = [
            {
                "path": path.relative_to(release_dir).as_posix(),
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }
            for path in payloads
        ]
        files.sort(key=lambda item: item["path"])
        lock_path = release_dir / "runtime-requirements.lock"
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "application_commit": expected_commit,
            "operations_commit": operations_commit,
            "application_version": APPLICATION_VERSION,
            "python_version": interpreter_version,
            "runtime_target": RUNTIME_TARGET,
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lock_sha256": sha256(lock_path),
            "wheel_sha256": sha256(wheel),
            "files": files,
        }
        manifest_path = release_dir / "release-manifest.json"
        manifest_path.write_bytes(canonical_json(manifest))
        names = [item["path"] for item in files]
        names.append("release-manifest.json")
        normalized_tar(archive, release_dir, names)

    archive_digest = sha256(archive)
    try:
        with checksum_file.open("x", encoding="ascii", newline="\n") as stream:
            stream.write(f"{archive_digest}  {archive.name}\n")
    except BaseException:
        archive.unlink(missing_ok=True)
        raise
    return {
        "application_commit": expected_commit,
        "operations_commit": operations_commit,
        "archive": os.fspath(archive),
        "sha256_file": os.fspath(checksum_file),
        "archive_sha256": archive_digest,
    }


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description="Build an immutable Card OS release.")
    argument_parser.add_argument("--server-repo", required=True, type=Path)
    argument_parser.add_argument("--expected-commit", required=True)
    argument_parser.add_argument("--output-dir", required=True, type=Path)
    argument_parser.add_argument("--python", required=True, type=Path)
    return argument_parser


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    try:
        summary = build_release(
            server_repo=options.server_repo,
            expected_commit=options.expected_commit,
            output_dir=options.output_dir,
            python=options.python,
        )
    except (ReleaseError, OSError) as error:
        code = str(error) if isinstance(error, ReleaseError) else "FILESYSTEM_ERROR"
        print(f"error={code}", file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
