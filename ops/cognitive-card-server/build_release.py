#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


APPLICATION_VERSION = "0.3.0"
MANIFEST_SCHEMA = "cognitive-card-server-release-v1"
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
WHEEL_PATTERN = re.compile(r"^cognitive_card_server-0\.3\.0-[A-Za-z0-9_.-]+\.whl$")

PAYLOAD_ASSETS = (
    ("runtime-requirements.lock", "runtime-requirements.lock"),
    ("card_os_backup.py", "ops/card_os_backup.py"),
    ("card_os_acceptance.py", "ops/card_os_acceptance.py"),
    ("install_nginx_include.py", "ops/install_nginx_include.py"),
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
}


class ReleaseError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_checked(arguments: list[str], *, cwd: Path | None = None) -> str:
    try:
        process = subprocess.run(
            arguments,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReleaseError("COMMAND_FAILED") from error
    if process.returncode:
        raise ReleaseError("COMMAND_FAILED")
    return process.stdout.strip()


def git(repository: Path, *arguments: str) -> str:
    return run_checked(["git", "-C", os.fspath(repository), *arguments])


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def python_version(python: Path) -> str:
    output = run_checked([os.fspath(python), "--version"])
    match = re.fullmatch(r"Python (\d+\.\d+\.\d+)", output)
    if match is None:
        raise ReleaseError("PYTHON_VERSION_INVALID")
    return match.group(1)


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
        wheel_dir = staging / "wheel"
        wheel_dir.mkdir()
        run_checked(
            [
                os.fspath(python),
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                os.fspath(wheel_dir),
                os.fspath(server_repo),
            ]
        )
        wheels = [path for path in wheel_dir.iterdir() if path.is_file()]
        if len(wheels) != 1 or WHEEL_PATTERN.fullmatch(wheels[0].name) is None:
            raise ReleaseError("APPLICATION_WHEEL_INVALID")

        release_dir = staging / "release"
        release_dir.mkdir()
        payloads = copy_payload(ops_dir, release_dir)
        wheel = release_dir / wheels[0].name
        shutil.copyfile(wheels[0], wheel)
        payloads.append(wheel)

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
