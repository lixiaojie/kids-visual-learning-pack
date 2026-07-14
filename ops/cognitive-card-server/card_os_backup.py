#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Sequence


SCHEMA = "card-os-backup-v1"
DATABASE_NAME = "card-os.sqlite3"
MANIFEST_NAME = "manifest.json"
BATCH_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")
RELEASE_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class BackupResult:
    backup_dir: Path
    manifest_path: Path


class BackupError(RuntimeError):
    pass


def _resolve_regular_file(path: Path, error: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
        mode = resolved.stat().st_mode
    except (OSError, RuntimeError) as exc:
        raise BackupError(error) from exc
    if not stat.S_ISREG(mode):
        raise BackupError(error)
    return resolved


def _resolve_directory(path: Path, error: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
        mode = resolved.stat().st_mode
    except (OSError, RuntimeError) as exc:
        raise BackupError(error) from exc
    if not stat.S_ISDIR(mode):
        raise BackupError(error)
    return resolved


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_only_sqlite(database: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)


def _require_sqlite_integrity(database: Path) -> None:
    connection: sqlite3.Connection | None = None
    try:
        connection = _read_only_sqlite(database)
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.Error as exc:
        raise BackupError("SQLITE_INTEGRITY_CHECK_FAILED") from exc
    finally:
        if connection is not None:
            connection.close()
    if rows != [("ok",)]:
        raise BackupError("SQLITE_INTEGRITY_CHECK_FAILED")


def _copy_database(source_path: Path, destination_path: Path) -> dict[str, object]:
    source: sqlite3.Connection | None = None
    destination: sqlite3.Connection | None = None
    try:
        source = _read_only_sqlite(source_path)
        destination = sqlite3.connect(destination_path)
        source.backup(destination)
    except sqlite3.Error as exc:
        raise BackupError("SQLITE_BACKUP_FAILED") from exc
    finally:
        if destination is not None:
            destination.close()
        if source is not None:
            source.close()
    destination_path.chmod(0o600)
    _require_sqlite_integrity(destination_path)
    return {
        "path": DATABASE_NAME,
        "sha256": _sha256(destination_path),
        "size": destination_path.stat().st_size,
    }


def _candidate_entries(root: Path) -> list[tuple[str, Path]]:
    entries: list[tuple[str, Path]] = []

    def walk(directory: Path, prefix: PurePosixPath) -> None:
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise BackupError("UNSAFE_CANDIDATE_ENTRY") from exc
        for child in children:
            relative = prefix / child.name
            try:
                if child.is_symlink():
                    raise BackupError("UNSAFE_CANDIDATE_ENTRY")
                if child.is_dir(follow_symlinks=False):
                    walk(Path(child.path), relative)
                elif child.is_file(follow_symlinks=False):
                    entries.append((relative.as_posix(), Path(child.path)))
                else:
                    raise BackupError("UNSAFE_CANDIDATE_ENTRY")
            except OSError as exc:
                raise BackupError("UNSAFE_CANDIDATE_ENTRY") from exc

    walk(root, PurePosixPath())
    return sorted(entries, key=lambda entry: entry[0])


def _copy_candidates(source_root: Path, destination_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    destination_root.mkdir(mode=0o700)
    for relative, source_path in _candidate_entries(source_root):
        destination_path = destination_root.joinpath(*PurePosixPath(relative).parts)
        destination_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            shutil.copyfile(source_path, destination_path, follow_symlinks=False)
            source_mode = source_path.lstat().st_mode
        except OSError as exc:
            raise BackupError("UNSAFE_CANDIDATE_ENTRY") from exc
        if not stat.S_ISREG(source_mode):
            raise BackupError("UNSAFE_CANDIDATE_ENTRY")
        destination_path.chmod(0o600)
        records.append(
            {
                "path": relative,
                "sha256": _sha256(destination_path),
                "size": destination_path.stat().st_size,
            }
        )
    return records


def _validated_manifest(backup_dir: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest_path = backup_dir / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BackupError("INVALID_MANIFEST") from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "candidates",
        "created_at",
        "database",
        "release_id",
        "schema",
    }:
        raise BackupError("INVALID_MANIFEST")
    if manifest.get("schema") != SCHEMA:
        raise BackupError("INVALID_MANIFEST")
    release_id = manifest.get("release_id")
    if not isinstance(release_id, str) or RELEASE_PATTERN.fullmatch(release_id) is None:
        raise BackupError("INVALID_MANIFEST")
    created_at = manifest.get("created_at")
    if not isinstance(created_at, str):
        raise BackupError("INVALID_MANIFEST")
    try:
        datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise BackupError("INVALID_MANIFEST") from exc

    database = manifest.get("database")
    if not isinstance(database, dict) or set(database) != {"path", "sha256", "size"}:
        raise BackupError("INVALID_MANIFEST")
    _validate_file_record(database, expected_path=DATABASE_NAME)

    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict) for candidate in candidates
    ):
        raise BackupError("INVALID_MANIFEST")
    typed_candidates = list(candidates)
    paths: list[str] = []
    for candidate in typed_candidates:
        if set(candidate) != {"path", "sha256", "size"}:
            raise BackupError("INVALID_MANIFEST")
        _validate_file_record(candidate)
        path = candidate["path"]
        if not isinstance(path, str) or not _safe_relative_path(path):
            raise BackupError("INVALID_MANIFEST")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise BackupError("INVALID_MANIFEST")
    return manifest, typed_candidates


def _validate_file_record(record: dict[str, object], expected_path: str | None = None) -> None:
    path = record.get("path")
    digest = record.get("sha256")
    size = record.get("size")
    if expected_path is not None and path != expected_path:
        raise BackupError("INVALID_MANIFEST")
    if not isinstance(digest, str) or DIGEST_PATTERN.fullmatch(digest) is None:
        raise BackupError("INVALID_MANIFEST")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise BackupError("INVALID_MANIFEST")


def _safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _actual_files(root: Path) -> set[str]:
    files: set[str] = set()

    def walk(directory: Path, prefix: PurePosixPath) -> None:
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise BackupError("BACKUP_VERIFICATION_FAILED") from exc
        for child in children:
            relative = prefix / child.name
            try:
                if child.is_symlink():
                    raise BackupError("BACKUP_VERIFICATION_FAILED")
                if child.is_dir(follow_symlinks=False):
                    walk(Path(child.path), relative)
                elif child.is_file(follow_symlinks=False):
                    files.add(relative.as_posix())
                else:
                    raise BackupError("BACKUP_VERIFICATION_FAILED")
            except OSError as exc:
                raise BackupError("BACKUP_VERIFICATION_FAILED") from exc

    walk(root, PurePosixPath())
    return files


def verify_backup(backup_dir: Path) -> dict[str, object]:
    resolved = _resolve_directory(backup_dir, "INVALID_BACKUP_DIRECTORY")
    manifest, candidates = _validated_manifest(resolved)
    database = manifest["database"]
    assert isinstance(database, dict)

    declared = {MANIFEST_NAME, DATABASE_NAME}
    declared.update(f"candidates/{candidate['path']}" for candidate in candidates)
    if _actual_files(resolved) != declared:
        raise BackupError("UNDECLARED_BACKUP_FILE")

    records = [(database, resolved / DATABASE_NAME)]
    records.extend(
        (
            candidate,
            resolved / "candidates" / Path(str(candidate["path"])),
        )
        for candidate in candidates
    )
    for record, path in records:
        try:
            size = path.stat().st_size
            digest = _sha256(path)
        except OSError as exc:
            raise BackupError("BACKUP_DIGEST_MISMATCH") from exc
        if size != record["size"] or digest != record["sha256"]:
            raise BackupError("BACKUP_DIGEST_MISMATCH")

    _require_sqlite_integrity(resolved / DATABASE_NAME)
    return {
        "status": "ok",
        "release_id": manifest["release_id"],
        "file_count": 1 + len(candidates),
    }


def _remove_expired_backups(backup_root: Path, now: datetime, retention_days: int) -> None:
    cutoff = now - timedelta(days=retention_days)
    for entry in sorted(os.scandir(backup_root), key=lambda item: item.name):
        if BATCH_PATTERN.fullmatch(entry.name) is None:
            continue
        if not entry.is_dir(follow_symlinks=False):
            continue
        timestamp = datetime.strptime(entry.name[:16], "%Y%m%dT%H%M%SZ").replace(
            tzinfo=timezone.utc
        )
        if timestamp >= cutoff:
            continue
        path = Path(entry.path)
        try:
            verify_backup(path)
        except (BackupError, OSError):
            continue
        shutil.rmtree(path)


def create_backup(
    database: Path,
    candidate_root: Path,
    backup_root: Path,
    current_release: Path,
    now: datetime,
    retention_days: int = 14,
) -> BackupResult:
    database = _resolve_regular_file(database, "INVALID_DATABASE")
    candidate_root = _resolve_directory(candidate_root, "INVALID_CANDIDATE_ROOT")
    backup_root = _resolve_directory(backup_root, "INVALID_BACKUP_ROOT")
    current_release = _resolve_directory(current_release, "INVALID_CURRENT_RELEASE")
    release_id = current_release.name
    if RELEASE_PATTERN.fullmatch(release_id) is None:
        raise BackupError("INVALID_RELEASE_ID")
    if now.tzinfo is None or now.utcoffset() is None:
        raise BackupError("INVALID_TIMESTAMP")
    if not isinstance(retention_days, int) or isinstance(retention_days, bool) or retention_days < 0:
        raise BackupError("INVALID_RETENTION_DAYS")

    utc_now = now.astimezone(timezone.utc)
    batch_id = utc_now.strftime("%Y%m%dT%H%M%SZ") + f"-{release_id[:12]}"
    final_path = backup_root / batch_id
    staging_path = backup_root / f".{batch_id}.staging"
    if os.path.lexists(staging_path) or os.path.lexists(final_path):
        raise BackupError("BACKUP_PATH_EXISTS")

    staging_created = False
    try:
        staging_path.mkdir(mode=0o700)
        staging_created = True
        staging_path.chmod(0o700)
        database_record = _copy_database(database, staging_path / DATABASE_NAME)
        candidates = _copy_candidates(candidate_root, staging_path / "candidates")
        manifest = {
            "schema": SCHEMA,
            "created_at": utc_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "release_id": release_id,
            "database": database_record,
            "candidates": candidates,
        }
        manifest_path = staging_path / MANIFEST_NAME
        manifest_path.write_bytes(_canonical_json(manifest))
        manifest_path.chmod(0o600)
        verify_backup(staging_path)
        staging_path.rename(final_path)
        staging_created = False
    except BaseException:
        if staging_created:
            shutil.rmtree(staging_path, ignore_errors=True)
        raise

    _remove_expired_backups(backup_root, utc_now, retention_days)
    return BackupResult(
        backup_dir=final_path,
        manifest_path=final_path / MANIFEST_NAME,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and verify Card OS backups")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--database", type=Path, required=True)
    create.add_argument("--candidate-root", type=Path, required=True)
    create.add_argument("--backup-root", type=Path, required=True)
    create.add_argument("--current-release", type=Path, required=True)
    create.add_argument("--retention-days", type=int, default=14)
    verify = commands.add_parser("verify")
    verify.add_argument("--backup-dir", type=Path, required=True)
    return parser


def _print_json(payload: object) -> None:
    sys.stdout.buffer.write(_canonical_json(payload))


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "create":
        result = create_backup(
            database=arguments.database,
            candidate_root=arguments.candidate_root,
            backup_root=arguments.backup_root,
            current_release=arguments.current_release,
            now=datetime.now(timezone.utc),
            retention_days=arguments.retention_days,
        )
        manifest_sha256 = _sha256(result.manifest_path)
        verification = verify_backup(result.backup_dir)
        _print_json(
            {
                "status": "ok",
                "backup_dir": os.fspath(result.backup_dir),
                "manifest_sha256": manifest_sha256,
                "release_id": verification["release_id"],
            }
        )
    else:
        _print_json(verify_backup(arguments.backup_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
