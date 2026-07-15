#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import os
import re
import stat
import sys
import zipfile
from email import policy
from email.parser import BytesParser
from itertools import product
from pathlib import Path, PurePosixPath


APPLICATION_NAME = "cognitive-card-server"
APPLICATION_VERSION = "0.3.0"
MAX_ARCHIVE_SIZE = 128 * 1024 * 1024
MAX_ENTRIES = 4096
MAX_MEMBER_SIZE = 64 * 1024 * 1024
MAX_TOTAL_SIZE = 256 * 1024 * 1024
MAX_METADATA_SIZE = 1024 * 1024
SAFE_WHEEL_NAME = re.compile(r"^[A-Za-z0-9_.+-]+\.whl$")
SAFE_TAG = re.compile(r"^[a-z0-9_]+$")


class WheelAuditError(RuntimeError):
    pass


def invalid() -> None:
    raise WheelAuditError("WHEEL_INVALID")


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def wheel_distribution(name: str) -> str:
    return normalize_name(name).replace("-", "_")


def safe_member_name(name: str) -> bool:
    if not name or len(name) > 512 or "\\" in name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def expand_tag(tag: str) -> set[tuple[str, str, str]]:
    fields = tag.split("-")
    if len(fields) != 3:
        invalid()
    components = [field.split(".") for field in fields]
    if any(
        not values or any(SAFE_TAG.fullmatch(value) is None for value in values)
        for values in components
    ):
        invalid()
    return set(product(*components))


def compatible_tag(tag: tuple[str, str, str]) -> bool:
    python_tag, abi_tag, platform_tag = tag
    if platform_tag == "any":
        platform_ok = True
    elif platform_tag == "manylinux2014_x86_64":
        platform_ok = True
    else:
        match = re.fullmatch(r"manylinux_2_(\d+)_x86_64", platform_tag)
        platform_ok = match is not None and 5 <= int(match.group(1)) <= 28
    if not platform_ok:
        return False

    if python_tag in {"py3", "py312"}:
        return abi_tag == "none" and platform_tag == "any"
    if python_tag == "cp312":
        return abi_tag in {"cp312", "abi3"} and platform_tag != "any"
    abi3 = re.fullmatch(r"cp3(\d+)", python_tag)
    return (
        abi_tag == "abi3"
        and abi3 is not None
        and 2 <= int(abi3.group(1)) <= 12
        and platform_tag != "any"
    )


def declared_identity(path: Path) -> tuple[list[str], str, str]:
    filename = path.name
    if SAFE_WHEEL_NAME.fullmatch(filename) is None:
        invalid()
    fields = filename[:-4].split("-")
    if len(fields) not in {5, 6}:
        invalid()
    distribution, version = fields[0], fields[1]
    return fields, normalize_name(distribution), version


def parse_filename(
    path: Path, expected_name: str, expected_version: str
) -> tuple[str, str, set[tuple[str, str, str]], str]:
    fields, normalized_distribution, version = declared_identity(path)
    distribution = fields[0]
    if (
        distribution != wheel_distribution(expected_name)
        or version != expected_version
        or (len(fields) == 6 and re.fullmatch(r"\d[0-9A-Za-z_]*", fields[2]) is None)
    ):
        invalid()
    tags = expand_tag("-".join(fields[-3:]))
    if not tags or not any(compatible_tag(tag) for tag in tags):
        invalid()
    return normalized_distribution, version, tags, f"{distribution}-{version}.dist-info"


def parse_message(content: bytes):
    if len(content) > MAX_METADATA_SIZE:
        invalid()
    try:
        message = BytesParser(policy=policy.default).parsebytes(content)
    except (TypeError, ValueError):
        invalid()
    if message.defects:
        invalid()
    return message


def audit_record(record_path: str, content: bytes, members: dict[str, bytes]) -> None:
    if len(content) > MAX_METADATA_SIZE:
        invalid()
    try:
        rows = list(csv.reader(io.StringIO(content.decode("utf-8"), newline=""), strict=True))
    except (UnicodeError, csv.Error):
        invalid()
    recorded: dict[str, tuple[str, str]] = {}
    for row in rows:
        if len(row) != 3 or not safe_member_name(row[0]) or row[0] in recorded:
            invalid()
        recorded[row[0]] = (row[1], row[2])
    if set(recorded) != set(members):
        invalid()
    for name, payload in members.items():
        digest, size = recorded[name]
        if name == record_path:
            if digest or size:
                invalid()
            continue
        expected_digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
        if digest != f"sha256={expected_digest}" or size != str(len(payload)):
            invalid()


def audit_wheel(path: Path, expected_name: str, expected_version: str) -> tuple[str, str]:
    path = Path(path)
    try:
        metadata = path.lstat()
    except OSError:
        invalid()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or metadata.st_size <= 0
        or metadata.st_size > MAX_ARCHIVE_SIZE
    ):
        invalid()
    normalized_name, version, filename_tags, dist_info = parse_filename(
        path, expected_name, expected_version
    )
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_ENTRIES:
                invalid()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                invalid()
            total_size = 0
            members: dict[str, bytes] = {}
            for info in infos:
                if (
                    not safe_member_name(info.filename)
                    or info.is_dir()
                    or info.flag_bits & 1
                    or info.file_size > MAX_MEMBER_SIZE
                ):
                    invalid()
                mode = (info.external_attr >> 16) & 0xFFFF
                file_type = stat.S_IFMT(mode)
                if file_type not in {0, stat.S_IFREG}:
                    invalid()
                total_size += info.file_size
                if total_size > MAX_TOTAL_SIZE:
                    invalid()
                members[info.filename] = archive.read(info)
    except (OSError, EOFError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile):
        invalid()

    dist_info_roots = {
        part
        for name in members
        for part in PurePosixPath(name).parts
        if part.endswith(".dist-info")
    }
    if dist_info_roots != {dist_info}:
        invalid()
    metadata_path = f"{dist_info}/METADATA"
    wheel_path = f"{dist_info}/WHEEL"
    record_path = f"{dist_info}/RECORD"
    if any(name not in members for name in (metadata_path, wheel_path, record_path)):
        invalid()

    metadata_message = parse_message(members[metadata_path])
    names = metadata_message.get_all("Name", [])
    versions = metadata_message.get_all("Version", [])
    if (
        len(names) != 1
        or len(versions) != 1
        or normalize_name(str(names[0])) != normalize_name(expected_name)
        or str(versions[0]) != expected_version
    ):
        invalid()

    wheel_message = parse_message(members[wheel_path])
    wheel_versions = wheel_message.get_all("Wheel-Version", [])
    declared = wheel_message.get_all("Tag", [])
    if len(wheel_versions) != 1 or str(wheel_versions[0]) != "1.0" or not declared:
        invalid()
    declared_tags: set[tuple[str, str, str]] = set()
    for tag in declared:
        declared_tags.update(expand_tag(str(tag)))
    if declared_tags != filename_tags or not any(compatible_tag(tag) for tag in declared_tags):
        invalid()

    audit_record(record_path, members[record_path], members)
    return normalized_name, version


def parse_lock(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        invalid()
    for line in lines:
        if not line or line != line.strip() or line.count("==") != 1:
            invalid()
        name, version = line.split("==", 1)
        normalized = normalize_name(name)
        if (
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", version) is None
            or normalized in result
        ):
            invalid()
        result[normalized] = version
    if not result:
        invalid()
    return result


def audit_wheelhouse(wheelhouse: Path, lock_path: Path) -> list[Path]:
    locked = parse_lock(lock_path)
    try:
        root_metadata = wheelhouse.lstat()
        entries = sorted(wheelhouse.iterdir(), key=lambda item: item.name)
    except OSError:
        invalid()
    if not stat.S_ISDIR(root_metadata.st_mode) or wheelhouse.is_symlink():
        invalid()
    resolved: dict[str, tuple[str, Path]] = {}
    for path in entries:
        _, identity, version = declared_identity(path)
        expected_version = locked.get(identity)
        if expected_version is None or identity in resolved:
            invalid()
        audit_wheel(path, identity, expected_version)
        resolved[identity] = (expected_version, path)
    if set(resolved) != set(locked):
        invalid()
    return [resolved[name][1] for name in sorted(resolved)]


def audit_release(release_root: Path) -> None:
    audit_wheelhouse(
        release_root / "runtime-wheels", release_root / "runtime-requirements.lock"
    )
    application_wheels = sorted(release_root.glob("cognitive_card_server-0.3.0-*.whl"))
    if len(application_wheels) != 1:
        invalid()
    audit_wheel(application_wheels[0], APPLICATION_NAME, APPLICATION_VERSION)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Audit governed Card OS wheels.")
    subparsers = result.add_subparsers(dest="command", required=True)
    release = subparsers.add_parser("release")
    release.add_argument("--release-root", required=True, type=Path)
    return result


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    try:
        audit_release(options.release_root)
    except WheelAuditError as error:
        print(f"error={error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
