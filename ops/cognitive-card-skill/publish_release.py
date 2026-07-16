#!/usr/bin/env python3
"""Publish and verify the immutable Cognitive Card OS Skill registry."""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


REGISTRY_SCHEMA = "cognitive-card-skill-registry-v1"
REGISTRY_URL = "https://www.yutou.space/card-os/skill/v1/"
ARCHIVE_NAME = "cognitive-card-os.zip"
PRODUCTION_UID = 0
PRODUCTION_GID = 0
PUBLIC_DIRECTORY_MODE = 0o755
PUBLIC_FILE_MODE = 0o644
PRIVATE_MODE = 0o700
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
RFC3339_UTC = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z"
)
MAX_INSTALLER_BYTES = 4 * 1024 * 1024


class RegistryError(RuntimeError):
    """A stable, fail-closed registry publication error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _fail(code: str) -> None:
    raise RegistryError(code)


def _fault(_point: str) -> None:
    """Test-only transition hook; production behavior is deliberately inert."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _load_builder():
    path = Path(__file__).with_name("build_release.py")
    spec = importlib.util.spec_from_file_location("card_os_governed_release_builder", path)
    if spec is None or spec.loader is None:
        _fail("RELEASE_VALIDATOR_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        _fail("RELEASE_VALIDATOR_UNAVAILABLE")
    return module


BUILDER = _load_builder()


def _format_published_at(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _fail("INVALID_PUBLISHED_AT")
    try:
        normalized = value.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        _fail("INVALID_PUBLISHED_AT")
    if normalized.microsecond:
        _fail("INVALID_PUBLISHED_AT")
    return (
        f"{normalized.year:04d}-{normalized.month:02d}-{normalized.day:02d}"
        f"T{normalized.hour:02d}:{normalized.minute:02d}:{normalized.second:02d}Z"
    )


def _parse_published_at(value: object) -> datetime:
    if not isinstance(value, str) or not RFC3339_UTC.fullmatch(value):
        _fail("INVALID_MANIFEST")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        _fail("INVALID_MANIFEST")
    if _format_published_at(parsed) != value:
        _fail("INVALID_MANIFEST")
    return parsed


def _check_process_owner() -> None:
    if os.geteuid() != PRODUCTION_UID or os.getegid() != PRODUCTION_GID:
        _fail("ROOT_REQUIRED")


def _lstat(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except OSError:
        _fail("REGISTRY_IO_ERROR")


def _check_owner_mode(
    path: Path, *, mode: int, directory: bool = False, regular: bool = False
) -> None:
    status = _lstat(path)
    if status.st_uid != PRODUCTION_UID or status.st_gid != PRODUCTION_GID:
        _fail("INVALID_REGISTRY_OWNER")
    if stat.S_IMODE(status.st_mode) != mode:
        _fail("INVALID_REGISTRY_MODE")
    if directory and not stat.S_ISDIR(status.st_mode):
        _fail("INVALID_REGISTRY_ENTRY")
    if regular and not stat.S_ISREG(status.st_mode):
        _fail("INVALID_REGISTRY_ENTRY")


@contextmanager
def _restrictive_umask() -> Iterator[None]:
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_file(path: Path, content: bytes, mode: int = PUBLIC_FILE_MODE) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.fchmod(descriptor, mode)
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                _fail("REGISTRY_IO_ERROR")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _safe_remove(path: Path) -> None:
    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except OSError:
        pass


def _prepare_registry_path(root: Path) -> Path:
    _check_process_owner()
    requested = Path(root).absolute()
    if requested.is_symlink():
        _fail("UNSAFE_REGISTRY_SYMLINK")
    try:
        # Canonicalize platform aliases such as macOS /var -> /private/var,
        # while never resolving the governed registry root itself.
        root = requested.parent.resolve(strict=False) / requested.name
    except (OSError, RuntimeError):
        _fail("UNSAFE_REGISTRY_SYMLINK")
    with _restrictive_umask():
        try:
            root.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            _fail("REGISTRY_IO_ERROR")
    current = Path(root.anchor)
    for part in root.parent.parts[1:]:
        current /= part
        if current.is_symlink():
            _fail("UNSAFE_REGISTRY_SYMLINK")
    return root


def _ensure_registry(root: Path) -> Path:
    """Initialize only an absent/empty registry; fully verify any populated one."""
    _check_process_owner()
    root = Path(root).absolute()
    created_root = False
    try:
        if root.is_symlink():
            _fail("UNSAFE_REGISTRY_SYMLINK")
        if not root.exists():
            with _restrictive_umask():
                root.mkdir(mode=PUBLIC_DIRECTORY_MODE)
            os.chmod(root, PUBLIC_DIRECTORY_MODE)
            created_root = True
        _check_owner_mode(root, mode=PUBLIC_DIRECTORY_MODE, directory=True)
        entries = list(root.iterdir())
        if entries:
            verify_registry(registry_root=root)
            return root
        with _restrictive_umask():
            for name in ("installers", "manifests", "releases"):
                child = root / name
                child.mkdir(mode=PUBLIC_DIRECTORY_MODE)
                os.chmod(child, PUBLIC_DIRECTORY_MODE)
        _fsync_directory(root)
    except RegistryError:
        raise
    except FileExistsError:
        # A non-cooperating creator raced initialization. It owns the entry;
        # validate it on the next call instead of completing or replacing it.
        _fail("REGISTRY_INITIALIZATION_CONFLICT")
    except OSError:
        if created_root:
            _fail("REGISTRY_IO_ERROR")
        _fail("REGISTRY_IO_ERROR")
    return root


@contextmanager
def _registry_lock(root: Path) -> Iterator[None]:
    lock_path = root.parent / f".{root.name}.publisher.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError:
        _fail("UNSAFE_PUBLISHER_LOCK")
    try:
        status = os.fstat(descriptor)
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_uid != PRODUCTION_UID
            or status.st_gid != PRODUCTION_GID
        ):
            _fail("UNSAFE_PUBLISHER_LOCK")
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


@contextmanager
def _staging_directory(root: Path) -> Iterator[Path]:
    with _restrictive_umask():
        staging = Path(
            tempfile.mkdtemp(prefix=f".{root.name}.publish-", dir=root.parent)
        )
    os.chmod(staging, PRIVATE_MODE)
    try:
        yield staging
    finally:
        _safe_remove(staging)


def _read_regular(path: Path, *, maximum: int | None = None) -> bytes:
    try:
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode):
            _fail("INVALID_REGISTRY_ENTRY")
        if maximum is not None and status.st_size > maximum:
            _fail("REGISTRY_FILE_TOO_LARGE")
        content = path.read_bytes()
    except RegistryError:
        raise
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    if maximum is not None and len(content) > maximum:
        _fail("REGISTRY_FILE_TOO_LARGE")
    return content


def _validate_immutable_directory(
    destination: Path, expected: dict[str, bytes]
) -> None:
    if destination.is_symlink() or not destination.is_dir():
        _fail("IMMUTABLE_CONFLICT")
    try:
        actual_names = {entry.name for entry in destination.iterdir()}
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    if actual_names != set(expected):
        _fail("IMMUTABLE_CONFLICT")
    try:
        for name, content in expected.items():
            path = destination / name
            if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
                _fail("IMMUTABLE_CONFLICT")
            _check_owner_mode(path, mode=PUBLIC_FILE_MODE, regular=True)
    except RegistryError:
        raise
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    _check_owner_mode(destination, mode=PUBLIC_DIRECTORY_MODE, directory=True)


def _publish_immutable_directory(
    *, root: Path, staged: Path, destination: Path, expected: dict[str, bytes]
) -> bool:
    if destination.exists() or destination.is_symlink():
        _validate_immutable_directory(destination, expected)
        return False
    os.chmod(staged, PUBLIC_DIRECTORY_MODE)
    for name in expected:
        os.chmod(staged / name, PUBLIC_FILE_MODE)
    _fsync_directory(staged)
    try:
        # mkdir is the atomic no-overwrite reservation. Unlike rename(2), it
        # cannot replace a raced empty destination directory. The already
        # fsynced private staging files are then linked into our reservation.
        os.mkdir(destination, PRIVATE_MODE)
    except FileExistsError:
        _validate_immutable_directory(destination, expected)
        return False
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    linked: list[str] = []
    try:
        for name in expected:
            os.link(staged / name, destination / name, follow_symlinks=False)
            linked.append(name)
        os.chmod(destination, PUBLIC_DIRECTORY_MODE)
        _fsync_directory(destination)
        _validate_immutable_directory(destination, expected)
    except Exception:
        # Remove only links whose inode still matches our private staged file,
        # then remove the directory only if it is empty. Never delete a raced
        # foreign entry while unwinding an incomplete publication.
        for name in linked:
            published = destination / name
            staged_file = staged / name
            try:
                if published.lstat().st_ino == staged_file.lstat().st_ino:
                    published.unlink()
            except OSError:
                pass
        try:
            destination.rmdir()
        except OSError:
            pass
        raise
    _fsync_directory(destination.parent)
    return True


def _publish_immutable_file(*, root: Path, content: bytes, destination: Path) -> bool:
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_file():
            _fail("IMMUTABLE_CONFLICT")
        try:
            existing = destination.read_bytes()
        except OSError:
            _fail("REGISTRY_IO_ERROR")
        if existing != content:
            _fail("IMMUTABLE_CONFLICT")
        _check_owner_mode(destination, mode=PUBLIC_FILE_MODE, regular=True)
        return False
    with _staging_directory(root) as staging:
        staged = staging / destination.name
        _write_file(staged, content)
        try:
            os.link(staged, destination, follow_symlinks=False)
        except FileExistsError:
            _fail("IMMUTABLE_CONFLICT")
        except OSError:
            _fail("REGISTRY_IO_ERROR")
        _fsync_directory(destination.parent)
    return True


def _scan_symlinks(root: Path) -> None:
    if root.is_symlink():
        _fail("UNSAFE_REGISTRY_SYMLINK")
    try:
        for directory, directory_names, file_names in os.walk(root, followlinks=False):
            directory_path = Path(directory)
            for name in [*directory_names, *file_names]:
                path = directory_path / name
                if not path.is_symlink():
                    continue
                if path == root / "installer-current":
                    continue
                _fail("UNSAFE_REGISTRY_SYMLINK")
    except RegistryError:
        raise
    except OSError:
        _fail("REGISTRY_IO_ERROR")


def _validate_installer_snapshot(root: Path, digest: str) -> dict[str, object]:
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        _fail("INVALID_INSTALLER_DIGEST")
    directory = root / "installers" / digest
    if directory.is_symlink() or not directory.is_dir():
        _fail("INSTALLER_NOT_FOUND")
    _check_owner_mode(directory, mode=PUBLIC_DIRECTORY_MODE, directory=True)
    try:
        if {entry.name for entry in directory.iterdir()} != {
            "install.sh",
            "install.sh.sha256",
        }:
            _fail("INVALID_INSTALLER_SNAPSHOT")
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    installer = directory / "install.sh"
    checksum = directory / "install.sh.sha256"
    _check_owner_mode(installer, mode=PUBLIC_FILE_MODE, regular=True)
    _check_owner_mode(checksum, mode=PUBLIC_FILE_MODE, regular=True)
    content = _read_regular(installer, maximum=MAX_INSTALLER_BYTES)
    if not content or _sha256(content) != digest:
        _fail("INSTALLER_DIGEST_MISMATCH")
    expected_checksum = f"{digest}  install.sh\n".encode("ascii")
    if _read_regular(checksum, maximum=256) != expected_checksum:
        _fail("INSTALLER_DIGEST_MISMATCH")
    return {
        "installer_path": f"installers/{digest}/install.sh",
        "installer_sha256": digest,
    }


def _validate_installer_pointer(root: Path) -> str | None:
    pointer = root / "installer-current"
    if not pointer.exists() and not pointer.is_symlink():
        return None
    if not pointer.is_symlink():
        _fail("INVALID_INSTALLER_POINTER")
    status = _lstat(pointer)
    if status.st_uid != PRODUCTION_UID or status.st_gid != PRODUCTION_GID:
        _fail("INVALID_REGISTRY_OWNER")
    try:
        target = os.readlink(pointer)
    except OSError:
        _fail("INVALID_INSTALLER_POINTER")
    match = re.fullmatch(r"installers/([0-9a-f]{64})", target)
    if match is None or Path(target).is_absolute():
        _fail("INVALID_INSTALLER_POINTER")
    digest = match.group(1)
    target_path = root / "installers" / digest
    try:
        if target_path.resolve(strict=True).parent != (root / "installers").resolve(
            strict=True
        ):
            _fail("INVALID_INSTALLER_POINTER")
    except (OSError, RuntimeError):
        _fail("INVALID_INSTALLER_POINTER")
    _validate_installer_snapshot(root, digest)
    return digest


def _validate_release_directory(root: Path, version: str) -> dict[str, object]:
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        _fail("INVALID_RELEASE_VERSION")
    directory = root / "releases" / version
    if directory.is_symlink() or not directory.is_dir():
        _fail("RELEASE_NOT_FOUND")
    _check_owner_mode(directory, mode=PUBLIC_DIRECTORY_MODE, directory=True)
    try:
        if {entry.name for entry in directory.iterdir()} != {
            ARCHIVE_NAME,
            "sha256.txt",
        }:
            _fail("INVALID_RELEASE_SNAPSHOT")
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    archive = directory / ARCHIVE_NAME
    checksum = directory / "sha256.txt"
    _check_owner_mode(archive, mode=PUBLIC_FILE_MODE, regular=True)
    _check_owner_mode(checksum, mode=PUBLIC_FILE_MODE, regular=True)
    try:
        metadata = BUILDER.validate_archive(archive)
    except BUILDER.SkillReleaseError:
        _fail("INVALID_RELEASE_ARCHIVE")
    if metadata.get("version") != version:
        _fail("INVALID_RELEASE_ARCHIVE")
    digest = metadata.get("archive_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        _fail("INVALID_RELEASE_ARCHIVE")
    expected_checksum = f"{digest}  {ARCHIVE_NAME}\n".encode("ascii")
    if _read_regular(checksum, maximum=256) != expected_checksum:
        _fail("RELEASE_DIGEST_MISMATCH")
    return metadata


def _parse_manifest(content: bytes) -> dict[str, object]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("INVALID_MANIFEST")
    if not isinstance(payload, dict) or canonical_json(payload) != content:
        _fail("INVALID_MANIFEST")
    expected_keys = {
        "archive_sha256",
        "archive_size_bytes",
        "archive_url",
        "channel",
        "installer",
        "minimum_server_version",
        "protocol",
        "published_at",
        "schema",
        "source_commit",
        "version",
    }
    if set(payload) != expected_keys:
        _fail("INVALID_MANIFEST")
    version = payload.get("version")
    source_commit = payload.get("source_commit")
    archive_digest = payload.get("archive_sha256")
    published_at = payload.get("published_at")
    if payload.get("schema") != REGISTRY_SCHEMA or payload.get("channel") != "stable":
        _fail("INVALID_MANIFEST")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        _fail("INVALID_MANIFEST")
    if not isinstance(source_commit, str) or not COMMIT.fullmatch(source_commit):
        _fail("INVALID_MANIFEST")
    if not isinstance(archive_digest, str) or not SHA256.fullmatch(archive_digest):
        _fail("INVALID_MANIFEST")
    _parse_published_at(published_at)
    size = payload.get("archive_size_bytes")
    if type(size) is not int or size <= 0:
        _fail("INVALID_MANIFEST")
    protocol = payload.get("protocol")
    if (
        not isinstance(protocol, dict)
        or set(protocol) != {"minimum", "maximum"}
        or type(protocol.get("minimum")) is not int
        or type(protocol.get("maximum")) is not int
        or protocol["minimum"] > protocol["maximum"]
    ):
        _fail("INVALID_MANIFEST")
    installer = payload.get("installer")
    if not isinstance(installer, dict) or set(installer) != {"sha256", "url"}:
        _fail("INVALID_MANIFEST")
    installer_digest = installer.get("sha256")
    if not isinstance(installer_digest, str) or not SHA256.fullmatch(installer_digest):
        _fail("INVALID_MANIFEST")
    if payload.get("archive_url") != (
        f"{REGISTRY_URL}releases/{version}/{ARCHIVE_NAME}"
    ):
        _fail("INVALID_MANIFEST")
    if installer.get("url") != (
        f"{REGISTRY_URL}installers/{installer_digest}/install.sh"
    ):
        _fail("INVALID_MANIFEST")
    minimum_server = payload.get("minimum_server_version")
    if not isinstance(minimum_server, str) or not SEMVER.fullmatch(minimum_server):
        _fail("INVALID_MANIFEST")
    return payload


def _validate_manifest_references(root: Path, content: bytes) -> dict[str, object]:
    payload = _parse_manifest(content)
    version = payload["version"]
    assert isinstance(version, str)
    release = _validate_release_directory(root, version)
    checks = (
        ("archive_sha256", "archive_sha256"),
        ("archive_size_bytes", "archive_size_bytes"),
        ("source_commit", "source_commit"),
        ("protocol", "protocol"),
        ("minimum_server_version", "minimum_server_version"),
    )
    for manifest_key, release_key in checks:
        if payload[manifest_key] != release[release_key]:
            _fail("MANIFEST_RELEASE_MISMATCH")
    installer = payload["installer"]
    assert isinstance(installer, dict)
    digest = installer["sha256"]
    assert isinstance(digest, str)
    _validate_installer_snapshot(root, digest)
    return payload


def _manifest_from_release(
    *, release: dict[str, object], installer_digest: str, published_at: datetime
) -> dict[str, object]:
    version = release["version"]
    assert isinstance(version, str)
    return {
        "archive_sha256": release["archive_sha256"],
        "archive_size_bytes": release["archive_size_bytes"],
        "archive_url": f"{REGISTRY_URL}releases/{version}/{ARCHIVE_NAME}",
        "channel": "stable",
        "installer": {
            "sha256": installer_digest,
            "url": f"{REGISTRY_URL}installers/{installer_digest}/install.sh",
        },
        "minimum_server_version": release["minimum_server_version"],
        "protocol": release["protocol"],
        "published_at": _format_published_at(published_at),
        "schema": REGISTRY_SCHEMA,
        "source_commit": release["source_commit"],
        "version": version,
    }


def _replace_manifest(root: Path, content: bytes) -> None:
    target = root / "manifest.json"
    try:
        old_content = (
            target.read_bytes() if target.is_file() and not target.is_symlink() else None
        )
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    if target.is_symlink() or (target.exists() and not target.is_file()):
        _fail("INVALID_MANIFEST")
    with _staging_directory(root) as staging:
        replacement = staging / "manifest.json"
        _write_file(replacement, content)
        _fault("manifest_before_switch")
        try:
            os.replace(replacement, target)
            _fsync_directory(root)
            _fault("manifest_after_switch")
            if target.read_bytes() != content:
                _fail("MANIFEST_SWITCH_FAILED")
            _check_owner_mode(target, mode=PUBLIC_FILE_MODE, regular=True)
            _validate_manifest_references(root, content)
        except Exception:
            rollback = staging / "manifest.rollback"
            try:
                if old_content is None:
                    if target.exists() or target.is_symlink():
                        target.unlink()
                        _fsync_directory(root)
                else:
                    _write_file(rollback, old_content)
                    os.replace(rollback, target)
                    _fsync_directory(root)
            except OSError:
                _fail("MANIFEST_ROLLBACK_FAILED")
            raise


def _activate_manifest_content(root: Path, content: bytes) -> dict[str, object]:
    payload = _validate_manifest_references(root, content)
    digest = _sha256(content)
    snapshot = root / "manifests" / f"{digest}.json"
    _fault("manifest_snapshot_before_publish")
    _publish_immutable_file(root=root, content=content, destination=snapshot)
    _fault("manifest_snapshot_after_publish")
    _replace_manifest(root, content)
    return {
        "manifest_path": f"manifests/{digest}.json",
        "manifest_sha256": digest,
        "status": "active",
        "version": payload["version"],
    }


def _replace_installer_pointer(root: Path, digest: str) -> None:
    _validate_installer_snapshot(root, digest)
    pointer = root / "installer-current"
    try:
        old_target = os.readlink(pointer) if pointer.is_symlink() else None
    except OSError:
        _fail("INVALID_INSTALLER_POINTER")
    if pointer.exists() and not pointer.is_symlink():
        _fail("INVALID_INSTALLER_POINTER")
    with _staging_directory(root) as staging:
        replacement = staging / "installer-current"
        replacement.symlink_to(f"installers/{digest}")
        _fault("installer_before_switch")
        try:
            os.replace(replacement, pointer)
            _fsync_directory(root)
            _fault("installer_after_switch")
            if _validate_installer_pointer(root) != digest:
                _fail("INSTALLER_SWITCH_FAILED")
            _validate_installer_snapshot(root, digest)
        except Exception:
            try:
                if old_target is None:
                    if pointer.exists() or pointer.is_symlink():
                        pointer.unlink()
                        _fsync_directory(root)
                else:
                    rollback = staging / "installer-current.rollback"
                    rollback.symlink_to(old_target)
                    os.replace(rollback, pointer)
                    _fsync_directory(root)
                    _validate_installer_pointer(root)
            except OSError:
                _fail("INSTALLER_ROLLBACK_FAILED")
            raise


def _activate_installer_locked(root: Path, digest: str) -> dict[str, object]:
    _replace_installer_pointer(root, digest)
    return {
        "installer_path": f"installers/{digest}/install.sh",
        "installer_sha256": digest,
        "status": "active",
    }


def publish_installer(
    *, registry_root: Path, installer: Path, activate: bool
) -> dict[str, object]:
    root = _prepare_registry_path(Path(registry_root))
    with _registry_lock(root), _restrictive_umask():
        root = _ensure_registry(root)
        _scan_symlinks(root)
        verify_registry(registry_root=root)
        source = Path(installer)
        if source.is_symlink() or not source.is_file():
            _fail("INVALID_INSTALLER")
        content = _read_regular(source, maximum=MAX_INSTALLER_BYTES)
        if not content:
            _fail("INVALID_INSTALLER")
        digest = _sha256(content)
        checksum = f"{digest}  install.sh\n".encode("ascii")
        destination = root / "installers" / digest
        with _staging_directory(root) as staging:
            immutable = staging / digest
            immutable.mkdir(mode=PRIVATE_MODE)
            _write_file(immutable / "install.sh", content)
            _write_file(immutable / "install.sh.sha256", checksum)
            _fault("installer_snapshot_before_publish")
            created = _publish_immutable_directory(
                root=root,
                staged=immutable,
                destination=destination,
                expected={"install.sh": content, "install.sh.sha256": checksum},
            )
            _fault("installer_snapshot_after_publish")
        _validate_installer_snapshot(root, digest)
        verify_registry(registry_root=root)
        if activate:
            return _activate_installer_locked(root, digest)
        return {
            "installer_path": f"installers/{digest}/install.sh",
            "installer_sha256": digest,
            "status": "published",
        }


def activate_installer(
    *, registry_root: Path, installer_digest: str
) -> dict[str, object]:
    root = _prepare_registry_path(Path(registry_root))
    with _registry_lock(root), _restrictive_umask():
        root = _ensure_registry(root)
        _scan_symlinks(root)
        verify_registry(registry_root=root)
        _validate_installer_snapshot(root, installer_digest)
        return _activate_installer_locked(root, installer_digest)


def publish_release(
    *,
    registry_root: Path,
    archive: Path,
    installer_digest: str,
    published_at: datetime,
    activate_stable: bool,
) -> dict[str, object]:
    root = _prepare_registry_path(Path(registry_root))
    with _registry_lock(root), _restrictive_umask():
        root = _ensure_registry(root)
        _scan_symlinks(root)
        verify_registry(registry_root=root)
        _validate_installer_snapshot(root, installer_digest)
        try:
            release = BUILDER.validate_archive(Path(archive))
        except BUILDER.SkillReleaseError:
            _fail("INVALID_RELEASE_ARCHIVE")
        version = release["version"]
        digest = release["archive_sha256"]
        assert isinstance(version, str) and isinstance(digest, str)
        archive_content = _read_regular(Path(archive), maximum=BUILDER.MAX_ARCHIVE_BYTES)
        if _sha256(archive_content) != digest:
            _fail("RELEASE_DIGEST_MISMATCH")
        # Both fixture and stable publication must exercise the exact same
        # publisher-owned channel candidate.  Construct and parse it before
        # creating the immutable release so invalid publication metadata can
        # never leave release bytes behind.
        manifest = _manifest_from_release(
            release=release,
            installer_digest=installer_digest,
            published_at=published_at,
        )
        manifest_content = canonical_json(manifest)
        if _parse_manifest(manifest_content) != manifest:
            _fail("INVALID_MANIFEST")
        manifest_candidate_digest = _sha256(manifest_content)
        checksum = f"{digest}  {ARCHIVE_NAME}\n".encode("ascii")
        destination = root / "releases" / version
        with _staging_directory(root) as staging:
            immutable = staging / version
            immutable.mkdir(mode=PRIVATE_MODE)
            _write_file(immutable / ARCHIVE_NAME, archive_content)
            _write_file(immutable / "sha256.txt", checksum)
            _fault("release_before_publish")
            created = _publish_immutable_directory(
                root=root,
                staged=immutable,
                destination=destination,
                expected={ARCHIVE_NAME: archive_content, "sha256.txt": checksum},
            )
            _fault("release_after_publish")
        published_release = _validate_release_directory(root, version)
        comparable_keys = {
            "archive_sha256",
            "archive_size_bytes",
            "minimum_server_version",
            "protocol",
            "source_commit",
            "version",
        }
        if any(published_release[key] != release[key] for key in comparable_keys):
            _fail("RELEASE_METADATA_MISMATCH")
        verify_registry(registry_root=root)
        base = {
            "archive_path": f"releases/{version}/{ARCHIVE_NAME}",
            "archive_sha256": digest,
            "manifest_candidate_sha256": manifest_candidate_digest,
            "status": "published",
            "version": version,
        }
        if not activate_stable:
            return base
        activated = _activate_manifest_content(root, manifest_content)
        return {**base, **activated}


def _next_rollback_published_at(root: Path) -> datetime:
    candidate = _parse_published_at(_format_published_at(_utc_now()))
    latest: datetime | None = None
    try:
        snapshots = list((root / "manifests").iterdir())
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    for snapshot in snapshots:
        payload = _parse_manifest(_read_regular(snapshot, maximum=256 * 1024))
        observed = _parse_published_at(payload["published_at"])
        if latest is None or observed > latest:
            latest = observed
    if latest is not None and candidate <= latest:
        try:
            candidate = latest + timedelta(seconds=1)
        except OverflowError:
            _fail("MANIFEST_TIMESTAMP_EXHAUSTED")
    # Force canonical formatting now so an unrepresentable edge cannot reach
    # immutable publication after other validation work.
    _format_published_at(candidate)
    return candidate


def activate_manifest(*, registry_root: Path, snapshot: Path) -> dict[str, object]:
    root = _prepare_registry_path(Path(registry_root))
    with _registry_lock(root), _restrictive_umask():
        root = _ensure_registry(root)
        _scan_symlinks(root)
        verify_registry(registry_root=root)
        snapshot_path = Path(snapshot)
        try:
            if snapshot_path.resolve(strict=True).parent != (
                root / "manifests"
            ).resolve(strict=True):
                _fail("INVALID_MANIFEST_SNAPSHOT")
        except (OSError, RuntimeError):
            _fail("INVALID_MANIFEST_SNAPSHOT")
        if snapshot_path.is_symlink() or not snapshot_path.is_file():
            _fail("INVALID_MANIFEST_SNAPSHOT")
        original = _read_regular(snapshot_path, maximum=256 * 1024)
        if snapshot_path.name != f"{_sha256(original)}.json":
            _fail("INVALID_MANIFEST_SNAPSHOT")
        target = _validate_manifest_references(root, original)
        version = target["version"]
        assert isinstance(version, str)
        release = _validate_release_directory(root, version)
        installer = target["installer"]
        assert isinstance(installer, dict)
        installer_digest = installer["sha256"]
        assert isinstance(installer_digest, str)
        rollback = _manifest_from_release(
            release=release,
            installer_digest=installer_digest,
            published_at=_next_rollback_published_at(root),
        )
        return _activate_manifest_content(root, canonical_json(rollback))


def verify_registry(*, registry_root: Path) -> dict[str, object]:
    _check_process_owner()
    root = Path(registry_root).absolute()
    if root.is_symlink() or not root.is_dir():
        _fail("UNSAFE_REGISTRY_SYMLINK" if root.is_symlink() else "REGISTRY_NOT_FOUND")
    _scan_symlinks(root)
    _check_owner_mode(root, mode=PUBLIC_DIRECTORY_MODE, directory=True)
    required_directories = {"installers", "manifests", "releases"}
    allowed_root = required_directories | {"installer-current", "manifest.json"}
    try:
        root_entries = {entry.name for entry in root.iterdir()}
    except OSError:
        _fail("REGISTRY_IO_ERROR")
    if not required_directories.issubset(root_entries) or not root_entries.issubset(
        allowed_root
    ):
        _fail("INVALID_REGISTRY_ENTRY")
    for name in required_directories:
        _check_owner_mode(root / name, mode=PUBLIC_DIRECTORY_MODE, directory=True)

    installer_count = 0
    for entry in (root / "installers").iterdir():
        if not SHA256.fullmatch(entry.name):
            _fail("INVALID_REGISTRY_ENTRY")
        _validate_installer_snapshot(root, entry.name)
        installer_count += 1

    release_count = 0
    for entry in (root / "releases").iterdir():
        if not SEMVER.fullmatch(entry.name):
            _fail("INVALID_REGISTRY_ENTRY")
        _validate_release_directory(root, entry.name)
        release_count += 1

    snapshot_count = 0
    snapshot_contents: set[bytes] = set()
    for entry in (root / "manifests").iterdir():
        if entry.is_symlink() or not entry.is_file() or not re.fullmatch(
            r"[0-9a-f]{64}\.json", entry.name
        ):
            _fail("INVALID_REGISTRY_ENTRY")
        _check_owner_mode(entry, mode=PUBLIC_FILE_MODE, regular=True)
        content = _read_regular(entry, maximum=256 * 1024)
        if entry.name != f"{_sha256(content)}.json":
            _fail("MANIFEST_DIGEST_MISMATCH")
        _validate_manifest_references(root, content)
        snapshot_contents.add(content)
        snapshot_count += 1

    active_installer = _validate_installer_pointer(root)
    stable = root / "manifest.json"
    stable_version = None
    if stable.exists() or stable.is_symlink():
        if stable.is_symlink() or not stable.is_file():
            _fail("INVALID_MANIFEST")
        _check_owner_mode(stable, mode=PUBLIC_FILE_MODE, regular=True)
        stable_content = _read_regular(stable, maximum=256 * 1024)
        stable_payload = _validate_manifest_references(root, stable_content)
        if stable_content not in snapshot_contents:
            _fail("MANIFEST_SNAPSHOT_MISSING")
        stable_version = stable_payload["version"]

    return {
        "active_installer_sha256": active_installer,
        "installer_count": installer_count,
        "manifest_snapshot_count": snapshot_count,
        "release_count": release_count,
        "stable_version": stable_version,
        "valid": True,
    }
