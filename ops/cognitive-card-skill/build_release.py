#!/usr/bin/env python3
"""Build and validate deterministic Cognitive Card OS Skill releases."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import zipfile
from pathlib import Path


SCHEMA = "cognitive-card-skill-release-v1"
ARCHIVE_NAME = "cognitive-card-os.zip"
ARCHIVE_ROOT = "cognitive-card-os"
PROTOCOL = {"minimum": 1, "maximum": 1}
MINIMUM_SERVER_VERSION = "0.3.1"
SOURCE_FILES = {
    "SKILL.md": 0o644,
    "agents/openai.yaml": 0o644,
    "scripts/card_os_client.py": 0o755,
    "references/protocol.md": 0o644,
    "references/errors.md": 0o644,
}
SOURCE_DIRECTORIES = {"agents", "references", "scripts"}
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")

MAX_ARCHIVE_MEMBERS = 32
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_BYTES = 28 * 1024 * 1024

_ZIP_MIN_EPOCH = 315_532_800
_ZIP_MAX_EPOCH = 4_354_819_199
_CREDENTIAL_COMPONENT = re.compile(
    r"(?:^\.env(?:\.|$)|credential|secret|token|api[-_]?key|id_rsa|\.pem$)",
    re.IGNORECASE,
)


class SkillReleaseError(RuntimeError):
    """A stable, fail-closed release build or validation error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}: {detail}")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _fail(code: str, detail: str = "") -> None:
    raise SkillReleaseError(code, detail)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _run_git(repository: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        _fail("GIT_COMMAND_FAILED", type(error).__name__)
    return completed.stdout


def _validate_build_inputs(
    repository: Path, expected_commit: str, version: str
) -> tuple[Path, str]:
    if not SEMVER.fullmatch(version):
        _fail("INVALID_VERSION")
    if not COMMIT.fullmatch(expected_commit):
        _fail("INVALID_SOURCE_COMMIT")
    repository = repository.resolve()
    if not repository.is_dir():
        _fail("INVALID_REPOSITORY")
    head = _run_git(repository, "rev-parse", "HEAD").decode("ascii").strip()
    if head != expected_commit:
        _fail("SOURCE_COMMIT_MISMATCH")
    dirty = _run_git(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    if dirty:
        _fail("SOURCE_TREE_DIRTY")
    return repository, head


def _validate_checkout_tree(repository: Path) -> None:
    root = repository / "skills" / ARCHIVE_ROOT
    if root.is_symlink() or not root.is_dir():
        _fail("UNSAFE_SOURCE_ENTRY")
    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        relative_directory = directory_path.relative_to(root).as_posix()
        if relative_directory != ".":
            actual_directories.add(relative_directory)
        for name in directory_names:
            path = directory_path / name
            if path.is_symlink():
                _fail("UNSAFE_SOURCE_ENTRY")
        for name in file_names:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            try:
                entry_mode = path.lstat().st_mode
            except OSError:
                _fail("UNSAFE_SOURCE_ENTRY")
            if not stat.S_ISREG(entry_mode):
                _fail("UNSAFE_SOURCE_ENTRY")
            actual_files.add(relative)
    if actual_files != set(SOURCE_FILES) or actual_directories != SOURCE_DIRECTORIES:
        _fail("SOURCE_TREE_DIRTY")


def _git_source_entries(repository: Path, commit: str) -> dict[str, bytes]:
    prefix = f"skills/{ARCHIVE_ROOT}/"
    listing = _run_git(
        repository,
        "ls-tree",
        "-r",
        "-z",
        commit,
        "--",
        f"skills/{ARCHIVE_ROOT}",
    )
    entries: dict[str, tuple[str, str]] = {}
    for raw_entry in listing.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode, kind, _object_id = metadata.decode("ascii").split(" ", 2)
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            _fail("UNSAFE_SOURCE_ENTRY")
        if not path.startswith(prefix):
            _fail("UNSAFE_SOURCE_ENTRY")
        relative = path[len(prefix) :]
        entries[relative] = (mode, kind)
    if set(entries) != set(SOURCE_FILES):
        _fail("SOURCE_TREE_CLOSURE_MISMATCH")

    contents: dict[str, bytes] = {}
    for relative in sorted(SOURCE_FILES):
        mode, kind = entries[relative]
        expected_git_mode = "100755" if SOURCE_FILES[relative] == 0o755 else "100644"
        if kind != "blob" or mode not in {"100644", "100755"}:
            _fail("UNSAFE_SOURCE_ENTRY")
        if mode != expected_git_mode:
            _fail("SOURCE_MODE_MISMATCH")
        contents[relative] = _run_git(
            repository, "show", f"{commit}:{prefix}{relative}"
        )
    return contents


def _commit_epoch(repository: Path, commit: str) -> int:
    raw = _run_git(repository, "log", "-1", "--format=%ct", commit)
    try:
        return int(raw.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError):
        _fail("INVALID_COMMIT_TIMESTAMP")


def _zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    if epoch <= _ZIP_MIN_EPOCH:
        return (1980, 1, 1, 0, 0, 0)
    if epoch >= _ZIP_MAX_EPOCH:
        return (2107, 12, 31, 23, 59, 58)
    converted = time.gmtime(epoch)
    second = converted.tm_sec - converted.tm_sec % 2
    return (
        converted.tm_year,
        converted.tm_mon,
        converted.tm_mday,
        converted.tm_hour,
        converted.tm_min,
        second,
    )


def _zip_info(name: str, mode: int, timestamp: tuple[int, int, int, int, int, int]) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=timestamp)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = mode << 16
    info.extra = b""
    info.comment = b""
    return info


def _release_metadata(
    *, version: str, commit: str, contents: dict[str, bytes]
) -> dict[str, object]:
    return {
        "files": {
            relative: {
                "mode": f"{SOURCE_FILES[relative]:04o}",
                "sha256": _sha256(contents[relative]),
                "size_bytes": len(contents[relative]),
            }
            for relative in sorted(SOURCE_FILES)
        },
        "minimum_server_version": MINIMUM_SERVER_VERSION,
        "protocol": PROTOCOL,
        "schema": SCHEMA,
        "source_commit": commit,
        "version": version,
    }


def _archive_entries(
    contents: dict[str, bytes], metadata_bytes: bytes
) -> dict[str, tuple[int, bytes]]:
    entries: dict[str, tuple[int, bytes]] = {
        f"{ARCHIVE_ROOT}/": (0o755, b""),
        f"{ARCHIVE_ROOT}/agents/": (0o755, b""),
        f"{ARCHIVE_ROOT}/references/": (0o755, b""),
        f"{ARCHIVE_ROOT}/scripts/": (0o755, b""),
        f"{ARCHIVE_ROOT}/release.json": (0o644, metadata_bytes),
    }
    for relative, content in contents.items():
        entries[f"{ARCHIVE_ROOT}/{relative}"] = (SOURCE_FILES[relative], content)
    return entries


def _write_archive(
    path: Path,
    contents: dict[str, bytes],
    metadata_bytes: bytes,
    timestamp: tuple[int, int, int, int, int, int],
) -> None:
    entries = _archive_entries(contents, metadata_bytes)
    with path.open("xb") as destination:
        os.fchmod(destination.fileno(), 0o644)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.comment = b""
            for name in sorted(entries):
                mode, content = entries[name]
                archive.writestr(_zip_info(name, mode, timestamp), content)
        destination.flush()
        os.fsync(destination.fileno())


def _write_file_fsynced(path: Path, content: bytes, mode: int = 0o644) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=False) as destination:
            destination.write(content)
            destination.flush()
            os.fsync(destination.fileno())
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _decode_member_name(raw_name: bytes, flags: int) -> str:
    if b"\x00" in raw_name:
        _fail("UNSAFE_ARCHIVE_PATH")
    encoding = "utf-8" if flags & 0x800 else "cp437"
    try:
        return raw_name.decode(encoding)
    except UnicodeDecodeError:
        _fail("UNSAFE_ARCHIVE_PATH")


def _raw_central_names(data: bytes) -> list[str]:
    eocd_position = data.rfind(b"PK\x05\x06", max(0, len(data) - 65_557))
    if eocd_position < 0 or eocd_position + 22 > len(data):
        _fail("INVALID_ARCHIVE")
    try:
        (
            _signature,
            disk,
            central_disk,
            entries_on_disk,
            entry_count,
            central_size,
            central_offset,
            comment_length,
        ) = struct.unpack_from("<4s4H2LH", data, eocd_position)
    except struct.error:
        _fail("INVALID_ARCHIVE")
    if disk or central_disk or entries_on_disk != entry_count:
        _fail("INVALID_ARCHIVE")
    if eocd_position + 22 + comment_length != len(data):
        _fail("INVALID_ARCHIVE")
    if central_offset + central_size != eocd_position:
        _fail("INVALID_ARCHIVE")
    position = central_offset
    names: list[str] = []
    for _ in range(entry_count):
        if position + 46 > eocd_position or data[position : position + 4] != b"PK\x01\x02":
            _fail("INVALID_ARCHIVE")
        flags = struct.unpack_from("<H", data, position + 8)[0]
        name_length, extra_length, member_comment_length = struct.unpack_from(
            "<HHH", data, position + 28
        )
        end = position + 46 + name_length + extra_length + member_comment_length
        if end > eocd_position:
            _fail("INVALID_ARCHIVE")
        raw_name = data[position + 46 : position + 46 + name_length]
        names.append(_decode_member_name(raw_name, flags))
        position = end
    if position != eocd_position:
        _fail("INVALID_ARCHIVE")
    return names


def _validate_member_path(name: str) -> str:
    if not name or "\x00" in name or "\\" in name:
        _fail("UNSAFE_ARCHIVE_PATH")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        _fail("UNSAFE_ARCHIVE_PATH")
    if unicodedata.normalize("NFC", name) != name:
        _fail("UNSAFE_ARCHIVE_PATH")
    components = name.rstrip("/").split("/")
    if any(component in {"", ".", ".."} for component in components):
        _fail("UNSAFE_ARCHIVE_PATH")
    normalized = posixpath.normpath(name.rstrip("/"))
    if normalized != name.rstrip("/"):
        _fail("UNSAFE_ARCHIVE_PATH")
    return normalized


def _classify_forbidden_name(name: str) -> None:
    components = name.rstrip("/").split("/")
    lowered = [component.lower() for component in components]
    if "__macosx" in lowered or any(
        component == ".ds_store" or component.startswith("._") for component in lowered
    ):
        _fail("MACOS_METADATA_FORBIDDEN")
    if any(_CREDENTIAL_COMPONENT.search(component) for component in components):
        _fail("CREDENTIAL_FILE_FORBIDDEN")


def _parse_release_metadata(content: bytes) -> dict[str, object]:
    try:
        decoded = content.decode("utf-8")
        metadata = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("INVALID_RELEASE_METADATA")
    if not isinstance(metadata, dict) or canonical_json(metadata) != content:
        _fail("INVALID_RELEASE_METADATA")
    expected_keys = {
        "files",
        "minimum_server_version",
        "protocol",
        "schema",
        "source_commit",
        "version",
    }
    if set(metadata) != expected_keys:
        _fail("INVALID_RELEASE_METADATA")
    if metadata.get("schema") != SCHEMA:
        _fail("INVALID_RELEASE_METADATA")
    version = metadata.get("version")
    commit = metadata.get("source_commit")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        _fail("INVALID_RELEASE_METADATA")
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        _fail("INVALID_RELEASE_METADATA")
    protocol = metadata.get("protocol")
    if not isinstance(protocol, dict) or set(protocol) != set(PROTOCOL):
        _fail("INVALID_RELEASE_METADATA")
    if any(
        type(protocol[bound]) is not int or protocol[bound] != PROTOCOL[bound]
        for bound in PROTOCOL
    ):
        _fail("INVALID_RELEASE_METADATA")
    if metadata.get("minimum_server_version") != MINIMUM_SERVER_VERSION:
        _fail("INVALID_RELEASE_METADATA")
    files = metadata.get("files")
    if not isinstance(files, dict) or set(files) != set(SOURCE_FILES):
        _fail("ARCHIVE_CLOSURE_MISMATCH")
    for relative, expected_mode in SOURCE_FILES.items():
        declaration = files.get(relative)
        if not isinstance(declaration, dict) or set(declaration) != {
            "mode",
            "sha256",
            "size_bytes",
        }:
            _fail("INVALID_RELEASE_METADATA")
        digest = declaration.get("sha256")
        size = declaration.get("size_bytes")
        mode = declaration.get("mode")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            _fail("INVALID_RELEASE_METADATA")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            _fail("INVALID_RELEASE_METADATA")
        if mode != f"{expected_mode:04o}":
            _fail("INVALID_RELEASE_METADATA")
    return metadata


def validate_archive(path: Path) -> dict[str, object]:
    path = Path(path)
    try:
        archive_size = path.stat().st_size
        if not path.is_file() or path.is_symlink():
            _fail("INVALID_ARCHIVE")
        if archive_size > MAX_ARCHIVE_BYTES:
            _fail("ARCHIVE_TOO_LARGE")
        archive_bytes = path.read_bytes()
        if len(archive_bytes) > MAX_ARCHIVE_BYTES:
            _fail("ARCHIVE_TOO_LARGE")
    except OSError:
        _fail("INVALID_ARCHIVE")

    raw_names = _raw_central_names(archive_bytes)
    if len(raw_names) > MAX_ARCHIVE_MEMBERS:
        _fail("ARCHIVE_MEMBER_LIMIT_EXCEEDED")
    normalized_names: set[str] = set()
    for name in raw_names:
        normalized = _validate_member_path(name)
        if normalized in normalized_names:
            _fail("DUPLICATE_ARCHIVE_PATH")
        normalized_names.add(normalized)
        _classify_forbidden_name(name)

    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
            if archive.comment:
                _fail("NONCANONICAL_ARCHIVE")
            infos = archive.infolist()
            if len(infos) != len(raw_names):
                _fail("INVALID_ARCHIVE")
            if [info.filename for info in infos] != raw_names:
                _fail("INVALID_ARCHIVE")
            if [info.filename for info in infos] != sorted(raw_names):
                _fail("NONCANONICAL_ARCHIVE")

            total_size = 0
            contents: dict[str, bytes] = {}
            modes: dict[str, int] = {}
            timestamps: set[tuple[int, int, int, int, int, int]] = set()
            for info in infos:
                if info.file_size > MAX_MEMBER_BYTES:
                    _fail("ARCHIVE_MEMBER_TOO_LARGE")
                total_size += info.file_size
                if total_size > MAX_TOTAL_BYTES:
                    _fail("ARCHIVE_TOTAL_TOO_LARGE")
                if info.compress_type != zipfile.ZIP_STORED:
                    _fail("NONCANONICAL_ARCHIVE")
                if info.create_system != 3 or info.extra or info.comment:
                    _fail("NONCANONICAL_ARCHIVE")
                type_bits = (info.external_attr >> 16) & stat.S_IFMT(0o177777)
                if type_bits not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    _fail("UNSAFE_ARCHIVE_ENTRY")
                if info.is_dir() and type_bits == stat.S_IFREG:
                    _fail("UNSAFE_ARCHIVE_ENTRY")
                if not info.is_dir() and type_bits == stat.S_IFDIR:
                    _fail("UNSAFE_ARCHIVE_ENTRY")
                timestamps.add(info.date_time)
                modes[info.filename] = info.external_attr >> 16
                try:
                    contents[info.filename] = archive.read(info)
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    _fail("INVALID_ARCHIVE")
    except zipfile.BadZipFile:
        _fail("INVALID_ARCHIVE")

    if len(timestamps) != 1:
        _fail("NONCANONICAL_ARCHIVE")
    timestamp = next(iter(timestamps))
    if not (1980 <= timestamp[0] <= 2107) or timestamp[5] % 2:
        _fail("NONCANONICAL_ARCHIVE")

    expected_names = set(
        _archive_entries({relative: b"" for relative in SOURCE_FILES}, b"")
    )
    if set(raw_names) != expected_names:
        _fail("ARCHIVE_CLOSURE_MISMATCH")
    metadata_name = f"{ARCHIVE_ROOT}/release.json"
    metadata = _parse_release_metadata(contents[metadata_name])
    files = metadata["files"]
    assert isinstance(files, dict)

    for name in sorted(expected_names):
        is_directory = name.endswith("/")
        if is_directory:
            expected_mode = 0o755
        elif name == metadata_name:
            expected_mode = 0o644
        else:
            relative = name[len(ARCHIVE_ROOT) + 1 :]
            expected_mode = SOURCE_FILES[relative]
        if modes[name] != expected_mode:
            _fail("ARCHIVE_MODE_MISMATCH")

    for relative in sorted(SOURCE_FILES):
        name = f"{ARCHIVE_ROOT}/{relative}"
        declaration = files[relative]
        assert isinstance(declaration, dict)
        content = contents[name]
        if declaration["size_bytes"] != len(content):
            _fail("ARCHIVE_DIGEST_MISMATCH")
        if declaration["sha256"] != _sha256(content):
            _fail("ARCHIVE_DIGEST_MISMATCH")

    return {
        "archive_path": str(path.resolve()),
        "archive_sha256": _sha256(archive_bytes),
        "archive_size_bytes": archive_size,
        "minimum_server_version": metadata["minimum_server_version"],
        "protocol": metadata["protocol"],
        "source_commit": metadata["source_commit"],
        "version": metadata["version"],
    }


def _identical_release_directory(staging: Path, destination: Path) -> bool:
    try:
        if destination.is_symlink() or not destination.is_dir():
            return False
        expected = {ARCHIVE_NAME, "sha256.txt"}
        actual = {path.name for path in destination.iterdir()}
        if actual != expected:
            return False
        for name in expected:
            left = staging / name
            right = destination / name
            if right.is_symlink() or not right.is_file():
                return False
            if left.read_bytes() != right.read_bytes():
                return False
        return True
    except OSError:
        return False


def build_release(
    *,
    repository: Path,
    expected_commit: str,
    output_root: Path,
    version: str = "0.1.0",
) -> dict[str, object]:
    repository, commit = _validate_build_inputs(
        Path(repository), expected_commit, version
    )
    contents = _git_source_entries(repository, commit)
    _validate_checkout_tree(repository)
    timestamp = _zip_datetime(_commit_epoch(repository, commit))
    metadata_bytes = canonical_json(
        _release_metadata(version=version, commit=commit, contents=contents)
    )

    output_root = Path(output_root)
    if output_root.is_symlink():
        _fail("UNSAFE_OUTPUT_ROOT")
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    destination = output_root / version
    staging = Path(tempfile.mkdtemp(prefix=f".{version}-", dir=output_root))
    staging.chmod(0o700)
    try:
        archive_path = staging / ARCHIVE_NAME
        _write_archive(archive_path, contents, metadata_bytes, timestamp)
        archive_bytes = archive_path.read_bytes()
        archive_digest = _sha256(archive_bytes)
        checksum = f"{archive_digest}  {ARCHIVE_NAME}\n".encode("ascii")
        _write_file_fsynced(staging / "sha256.txt", checksum)
        _fsync_directory(staging)
        validation = validate_archive(archive_path)
        if validation["archive_sha256"] != archive_digest:
            _fail("ARCHIVE_DIGEST_MISMATCH")

        if destination.exists() or destination.is_symlink():
            if not _identical_release_directory(staging, destination):
                _fail("VERSION_ALREADY_EXISTS")
            shutil.rmtree(staging)
        else:
            os.replace(staging, destination)
            _fsync_directory(output_root)
        result = {
            "archive_path": str((destination / ARCHIVE_NAME).resolve()),
            "archive_sha256": archive_digest,
            "archive_size_bytes": len(archive_bytes),
            "source_commit": commit,
            "version": version,
        }
        return result
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    validate = subparsers.add_parser("validate", help="validate an existing archive")
    validate.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--expected-commit")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--version", default="0.1.0")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = _parser()
    parsed = parser.parse_args(arguments)
    try:
        if parsed.command == "validate":
            result = validate_archive(parsed.archive)
        else:
            if not parsed.repository or not parsed.expected_commit or not parsed.output_root:
                parser.error(
                    "--repository, --expected-commit and --output-root are required"
                )
            result = build_release(
                repository=parsed.repository,
                expected_commit=parsed.expected_commit,
                output_root=parsed.output_root,
                version=parsed.version,
            )
    except SkillReleaseError as error:
        print(canonical_json({"error": error.code}).decode("utf-8"), end="", file=sys.stderr)
        return 1
    print(canonical_json(result).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
