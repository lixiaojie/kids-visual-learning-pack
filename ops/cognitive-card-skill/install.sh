#!/usr/bin/env bash
set -eu
umask 077

REGISTRY_ROOT='https://www.yutou.space/card-os/skill/v1/'
MANIFEST_URL="${REGISTRY_ROOT}manifest.json"
INSTALL_ROOT="${CODEX_HOME:-${HOME}/.codex}"
ACTION=''
REQUESTED_VERSION=''

usage() {
  printf '%s\n' 'Usage: install.sh --channel stable | --version SEMVER | --check | --rollback [--install-root PATH]'
}

fail() {
  printf '{"error":{"code":"%s"}}\n' "$1" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --channel)
      [ "$#" -ge 2 ] || fail INVALID_ARGUMENT
      [ -z "$ACTION" ] || fail INVALID_ARGUMENT
      [ "$2" = stable ] || fail INVALID_ARGUMENT
      ACTION=install
      shift 2
      ;;
    --version)
      [ "$#" -ge 2 ] || fail INVALID_ARGUMENT
      [ -z "$ACTION" ] || fail INVALID_ARGUMENT
      ACTION=install
      REQUESTED_VERSION=$2
      shift 2
      ;;
    --check)
      [ -z "$ACTION" ] || fail INVALID_ARGUMENT
      ACTION=check
      shift
      ;;
    --rollback)
      [ -z "$ACTION" ] || fail INVALID_ARGUMENT
      ACTION=rollback
      shift
      ;;
    --install-root)
      [ "$#" -ge 2 ] || fail INVALID_ARGUMENT
      INSTALL_ROOT=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *) fail INVALID_ARGUMENT ;;
  esac
done
[ -n "$ACTION" ] || fail INVALID_ARGUMENT
[ -n "$INSTALL_ROOT" ] || fail INVALID_ARGUMENT

PYTHON_BIN=${PYTHON_BIN:-python3}
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' \
  >/dev/null 2>&1 || fail PYTHON_3_11_REQUIRED

TMP_BASE=${TMPDIR:-/tmp}
WORK_DIR=$(mktemp -d "${TMP_BASE%/}/cognitive-card-skill.XXXXXXXX") || fail TEMPORARY_DIRECTORY_FAILED
chmod 700 "$WORK_DIR"
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT HUP INT TERM

download() {
  destination=$1
  limit=$2
  url=$3
  set +e
  curl -q --proto '=https' --tlsv1.2 --location --max-redirs 0 \
    --fail --silent --show-error --max-filesize "$limit" --output "$destination" "$url"
  status=$?
  set -e
  [ "$status" -eq 0 ] || {
    [ "$status" -eq 47 ] && fail REDIRECT_REFUSED
    fail DOWNLOAD_FAILED
  }
  [ -f "$destination" ] && [ ! -L "$destination" ] || fail DOWNLOAD_FAILED
}

run_helper() {
  "$PYTHON_BIN" - "$@" <<'PY'
from __future__ import annotations

import hashlib
import io
import json
import os
import fcntl
import posixpath
import re
import secrets
import shutil
import stat
import struct
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REGISTRY = "https://www.yutou.space/card-os/skill/v1/"
MANIFEST_SCHEMA = "cognitive-card-skill-registry-v1"
RELEASE_SCHEMA = "cognitive-card-skill-release-v1"
STATE_SCHEMA = "cognitive-card-skill-install-state-v1"
JOURNAL_SCHEMA = "cognitive-card-skill-install-transaction-v1"
LOCK_OWNER_SCHEMA = "cognitive-card-skill-install-lock-owner-v1"
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
RFC3339 = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
SOURCE = {
    "SKILL.md": 0o644,
    "agents/openai.yaml": 0o644,
    "scripts/card_os_client.py": 0o755,
    "references/protocol.md": 0o644,
    "references/errors.md": 0o644,
}
DIRS = {"", "agents", "references", "scripts"}
MAX_MANIFEST = 256 * 1024
MAX_ARCHIVE = 28 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_TOTAL = 20 * 1024 * 1024
MAX_MEMBERS = 32
TOKEN = re.compile(rb"ccos_v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+")
FORBIDDEN_NAME = re.compile(r"(?:^\.env(?:\.|$)|credential|secret|token|api[-_]?key|id_rsa|\.pem$)", re.I)


class InstallError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def fail(code: str) -> None:
    raise InstallError(code)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_limited(path: Path, maximum: int, code: str) -> bytes:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
            fail(code)
        data = path.read_bytes()
    except OSError:
        fail(code)
    if len(data) > maximum:
        fail(code)
    return data


def json_canonical(data: bytes, code: str) -> dict[str, object]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(code)
    if not isinstance(value, dict) or canonical(value) != data:
        fail(code)
    return value


def safe_url(value: object, expected: str | None = None) -> str:
    if not isinstance(value, str):
        fail("INVALID_MANIFEST")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https":
        fail("TLS_REQUIRED")
    if parsed.username is not None or parsed.password is not None:
        fail("REDIRECT_REFUSED")
    if parsed.hostname != "www.yutou.space" or parsed.port not in (None, 443):
        fail("REDIRECT_REFUSED")
    if parsed.query or parsed.fragment or not parsed.path.startswith("/card-os/skill/v1/"):
        fail("REDIRECT_REFUSED")
    if any(part in {"", ".", ".."} for part in parsed.path[len("/card-os/skill/v1/"):].split("/")):
        fail("REDIRECT_REFUSED")
    if expected is not None and value != expected:
        fail("REDIRECT_REFUSED")
    return value


def parse_manifest(path: Path, installer_path: Path, requested: str) -> dict[str, object]:
    data = read_limited(path, MAX_MANIFEST, "INVALID_MANIFEST")
    value = json_canonical(data, "INVALID_MANIFEST")
    expected_keys = {
        "archive_sha256", "archive_size_bytes", "archive_url", "channel", "installer",
        "minimum_server_version", "protocol", "published_at", "schema", "source_commit", "version",
    }
    if set(value) != expected_keys or value.get("schema") != MANIFEST_SCHEMA or value.get("channel") != "stable":
        fail("INVALID_MANIFEST")
    version = value.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        fail("INVALID_MANIFEST")
    if requested and not SEMVER.fullmatch(requested):
        fail("INVALID_ARGUMENT")
    digest = value.get("archive_sha256")
    size = value.get("archive_size_bytes")
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        fail("INVALID_MANIFEST")
    if type(size) is not int or not (0 < size <= MAX_ARCHIVE):
        fail("INVALID_MANIFEST")
    if not isinstance(value.get("source_commit"), str) or not COMMIT.fullmatch(value["source_commit"]):
        fail("INVALID_MANIFEST")
    protocol = value.get("protocol")
    if not isinstance(protocol, dict) or set(protocol) != {"minimum", "maximum"}:
        fail("INVALID_MANIFEST")
    if any(type(protocol.get(key)) is not int for key in ("minimum", "maximum")):
        fail("INVALID_MANIFEST")
    if not (protocol["minimum"] <= 1 <= protocol["maximum"]):
        fail("INCOMPATIBLE_PROTOCOL")
    if value.get("minimum_server_version") != "0.3.1":
        fail("INVALID_MANIFEST")
    published_at = value.get("published_at")
    if not isinstance(published_at, str) or not RFC3339.fullmatch(published_at):
        fail("INVALID_MANIFEST")
    try:
        parsed_published_at = datetime.strptime(
            published_at, "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        fail("INVALID_MANIFEST")
    if parsed_published_at.strftime("%Y-%m-%dT%H:%M:%SZ") != published_at:
        fail("INVALID_MANIFEST")
    archive_expected = REGISTRY + f"releases/{version}/cognitive-card-os.zip"
    safe_url(value.get("archive_url"), archive_expected)
    installer = value.get("installer")
    if not isinstance(installer, dict) or set(installer) != {"sha256", "url"}:
        fail("INVALID_MANIFEST")
    installer_digest = installer.get("sha256")
    if not isinstance(installer_digest, str) or not SHA.fullmatch(installer_digest):
        fail("INVALID_MANIFEST")
    safe_url(installer.get("url"), REGISTRY + f"installers/{installer_digest}/install.sh")
    script = read_limited(installer_path, 4 * 1024 * 1024, "INSTALLER_DIGEST_MISMATCH")
    if sha(script) != installer_digest:
        fail("INSTALLER_DIGEST_MISMATCH")
    return value


def safe_member(name: str) -> str:
    if not name or "\x00" in name or "\\" in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        fail("UNSAFE_ARCHIVE")
    if unicodedata.normalize("NFC", name) != name:
        fail("UNSAFE_ARCHIVE")
    raw = name.rstrip("/")
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts) or posixpath.normpath(raw) != raw:
        fail("UNSAFE_ARCHIVE")
    lowered = [part.lower() for part in parts]
    if "__macosx" in lowered or any(part == ".ds_store" or part.startswith("._") for part in lowered):
        fail("UNSAFE_ARCHIVE")
    if any(FORBIDDEN_NAME.search(part) for part in parts):
        fail("UNSAFE_ARCHIVE")
    return raw


def raw_central_names(data: bytes) -> list[str]:
    eocd = data.rfind(b"PK\x05\x06", max(0, len(data) - 65_557))
    if eocd < 0 or eocd + 22 > len(data): fail("UNSAFE_ARCHIVE")
    try:
        _, disk, central_disk, disk_entries, entries, central_size, central_offset, comment_size = struct.unpack_from("<4s4H2LH", data, eocd)
    except struct.error:
        fail("UNSAFE_ARCHIVE")
    if disk or central_disk or disk_entries != entries or central_offset + central_size != eocd or eocd + 22 + comment_size != len(data):
        fail("UNSAFE_ARCHIVE")
    position = central_offset
    names: list[str] = []
    for _ in range(entries):
        if position + 46 > eocd or data[position:position + 4] != b"PK\x01\x02": fail("UNSAFE_ARCHIVE")
        flags = struct.unpack_from("<H", data, position + 8)[0]
        name_size, extra_size, member_comment_size = struct.unpack_from("<HHH", data, position + 28)
        end = position + 46 + name_size + extra_size + member_comment_size
        if end > eocd: fail("UNSAFE_ARCHIVE")
        raw = data[position + 46:position + 46 + name_size]
        if b"\x00" in raw: fail("UNSAFE_ARCHIVE")
        try: names.append(raw.decode("utf-8" if flags & 0x800 else "cp437"))
        except UnicodeDecodeError: fail("UNSAFE_ARCHIVE")
        position = end
    if position != eocd: fail("UNSAFE_ARCHIVE")
    return names


def validate_release_metadata(data: bytes) -> dict[str, object]:
    value = json_canonical(data, "UNSAFE_ARCHIVE")
    if set(value) != {"files", "minimum_server_version", "protocol", "schema", "source_commit", "version"}:
        fail("UNSAFE_ARCHIVE")
    if value.get("schema") != RELEASE_SCHEMA or value.get("minimum_server_version") != "0.3.1":
        fail("UNSAFE_ARCHIVE")
    if not isinstance(value.get("version"), str) or not SEMVER.fullmatch(value["version"]):
        fail("UNSAFE_ARCHIVE")
    if not isinstance(value.get("source_commit"), str) or not COMMIT.fullmatch(value["source_commit"]):
        fail("UNSAFE_ARCHIVE")
    if value.get("protocol") != {"minimum": 1, "maximum": 1}:
        fail("UNSAFE_ARCHIVE")
    files = value.get("files")
    if not isinstance(files, dict) or set(files) != set(SOURCE):
        fail("UNSAFE_ARCHIVE")
    for name, mode in SOURCE.items():
        declaration = files.get(name)
        if not isinstance(declaration, dict) or set(declaration) != {"mode", "sha256", "size_bytes"}:
            fail("UNSAFE_ARCHIVE")
        if declaration.get("mode") != f"{mode:04o}":
            fail("UNSAFE_ARCHIVE")
        if not isinstance(declaration.get("sha256"), str) or not SHA.fullmatch(declaration["sha256"]):
            fail("UNSAFE_ARCHIVE")
        if type(declaration.get("size_bytes")) is not int or declaration["size_bytes"] < 0:
            fail("UNSAFE_ARCHIVE")
    return value


def validate_archive(path: Path, expected_manifest: dict[str, object] | None = None) -> tuple[dict[str, object], bytes, dict[str, bytes]]:
    data = read_limited(path, MAX_ARCHIVE, "UNSAFE_ARCHIVE")
    if expected_manifest is not None:
        if len(data) != expected_manifest["archive_size_bytes"] or sha(data) != expected_manifest["archive_sha256"]:
            fail("DIGEST_MISMATCH")
    raw_names = raw_central_names(data)
    try:
        archive = zipfile.ZipFile(io.BytesIO(data), "r")
        infos = archive.infolist()
    except zipfile.BadZipFile:
        fail("UNSAFE_ARCHIVE")
    if len(infos) > MAX_MEMBERS or [info.filename for info in infos] != raw_names:
        fail("UNSAFE_ARCHIVE")
    names: set[str] = set()
    contents: dict[str, bytes] = {}
    total = 0
    expected_names = {
        "cognitive-card-os/", "cognitive-card-os/agents/", "cognitive-card-os/references/",
        "cognitive-card-os/scripts/", "cognitive-card-os/release.json",
        *{f"cognitive-card-os/{name}" for name in SOURCE},
    }
    timestamps: set[tuple[int, int, int, int, int, int]] = set()
    try:
        for info in infos:
            normalized = safe_member(info.filename)
            if normalized in names:
                fail("UNSAFE_ARCHIVE")
            names.add(normalized)
            if info.file_size > MAX_MEMBER:
                fail("UNSAFE_ARCHIVE")
            total += info.file_size
            if total > MAX_TOTAL or info.compress_type != zipfile.ZIP_STORED or info.create_system != 3 or info.extra or info.comment:
                fail("UNSAFE_ARCHIVE")
            bits = (info.external_attr >> 16) & 0o177777
            file_type = stat.S_IFMT(bits)
            if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                fail("UNSAFE_ARCHIVE")
            if info.is_dir() != info.filename.endswith("/"):
                fail("UNSAFE_ARCHIVE")
            expected_mode = 0o755 if info.is_dir() else (0o644 if info.filename.endswith("release.json") else SOURCE[info.filename[len("cognitive-card-os/"):]])
            if (info.external_attr >> 16) != expected_mode:
                fail("UNSAFE_ARCHIVE")
            timestamps.add(info.date_time)
            contents[info.filename] = archive.read(info)
    except (KeyError, RuntimeError, zipfile.BadZipFile, OSError):
        fail("UNSAFE_ARCHIVE")
    finally:
        archive.close()
    if len(timestamps) != 1 or {info.filename for info in infos} != expected_names or [info.filename for info in infos] != sorted(expected_names):
        fail("UNSAFE_ARCHIVE")
    release = validate_release_metadata(contents["cognitive-card-os/release.json"])
    files = release["files"]
    assert isinstance(files, dict)
    for name in SOURCE:
        content = contents[f"cognitive-card-os/{name}"]
        declaration = files[name]
        if declaration["size_bytes"] != len(content) or declaration["sha256"] != sha(content):
            fail("UNSAFE_ARCHIVE")
        if TOKEN.search(content):
            fail("UNSAFE_ARCHIVE")
    if expected_manifest is not None:
        if release["version"] != expected_manifest["version"] or release["source_commit"] != expected_manifest["source_commit"]:
            fail("DIGEST_MISMATCH")
        if release["protocol"] != expected_manifest["protocol"] or release["minimum_server_version"] != expected_manifest["minimum_server_version"]:
            fail("DIGEST_MISMATCH")
    return release, data, contents


def ensure_private_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            fail("UNSAFE_INSTALL_ROOT")
        path.chmod(0o700)
        fsync_dir(path)
    else:
        path.mkdir(mode=0o700)
        path.chmod(0o700)
        fsync_dir(path)
        fsync_dir(path.parent)


def write_exclusive(path: Path, data: bytes, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, mode)
    try:
        os.fchmod(descriptor, mode)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0: fail("INSTALL_FAILED")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def ensure_private_tree(path: Path) -> None:
    missing: list[Path] = []
    cursor = path
    while not cursor.exists():
        if cursor.is_symlink(): fail("UNSAFE_INSTALL_ROOT")
        missing.append(cursor)
        if cursor.parent == cursor: fail("UNSAFE_INSTALL_ROOT")
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir(): fail("UNSAFE_INSTALL_ROOT")
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        directory.chmod(0o700)
        fsync_dir(directory)
        fsync_dir(directory.parent)
    if path.is_symlink() or not path.is_dir(): fail("UNSAFE_INSTALL_ROOT")


def durability_checkpoint(event: str) -> None:
    if os.environ.get("CARD_OS_INSTALL_TEST_DURABILITY_TRACE") == "1":
        print(
            f"CARD_OS_INSTALL_TEST_DURABILITY_TRACE:{event}",
            file=sys.stderr,
            flush=True,
        )
    if os.environ.get("CARD_OS_INSTALL_DURABILITY_FAULT") == event:
        os._exit(98)


def trace_transition(event: str) -> None:
    if os.environ.get("CARD_OS_INSTALL_TEST_TRACE") == "1":
        print(f"CARD_OS_INSTALL_TEST_TRACE:{event}", file=sys.stderr, flush=True)


def extract(contents: dict[str, bytes], destination: Path) -> Path:
    destination.mkdir(mode=0o700)
    destination.chmod(0o700)
    fsync_dir(destination)
    fsync_dir(destination.parent)
    skill = destination / "cognitive-card-os"
    skill.mkdir(mode=0o755)
    skill.chmod(0o755)
    for directory in sorted(DIRS - {""}):
        (skill / directory).mkdir(mode=0o755)
        (skill / directory).chmod(0o755)
    write_exclusive(skill / "release.json", contents["cognitive-card-os/release.json"], 0o644)
    for name, mode in sorted(SOURCE.items()):
        write_exclusive(skill / name, contents[f"cognitive-card-os/{name}"], mode)
    for directory in sorted((skill / name for name in DIRS), reverse=True):
        fsync_dir(directory)
    fsync_dir(destination)
    return skill


def tree_matches(left: Path, right: Path) -> bool:
    try:
        if left.is_symlink() or right.is_symlink() or not left.is_dir() or not right.is_dir():
            return False
        expected_files = set(SOURCE) | {"release.json"}
        actual_left: set[str] = set()
        actual_right: set[str] = set()
        directories_left: set[str] = {""}
        directories_right: set[str] = {""}
        for root, directories, files in os.walk(left, followlinks=False):
            base = Path(root)
            for name in directories:
                directory = base / name
                if directory.is_symlink() or stat.S_IMODE(directory.stat().st_mode) != 0o755: return False
                directories_left.add(directory.relative_to(left).as_posix())
            for name in files:
                path = base / name
                if path.is_symlink() or not path.is_file(): return False
                actual_left.add(path.relative_to(left).as_posix())
        for root, directories, files in os.walk(right, followlinks=False):
            base = Path(root)
            for name in directories:
                directory = base / name
                if directory.is_symlink() or stat.S_IMODE(directory.stat().st_mode) != 0o755: return False
                directories_right.add(directory.relative_to(right).as_posix())
            for name in files:
                path = base / name
                if path.is_symlink() or not path.is_file(): return False
                actual_right.add(path.relative_to(right).as_posix())
        if stat.S_IMODE(left.stat().st_mode) != 0o755 or stat.S_IMODE(right.stat().st_mode) != 0o755:
            return False
        if directories_left != DIRS or directories_right != DIRS or actual_left != expected_files or actual_right != expected_files:
            return False
        for name in expected_files:
            a, b = left / name, right / name
            if a.read_bytes() != b.read_bytes() or stat.S_IMODE(a.stat().st_mode) != stat.S_IMODE(b.stat().st_mode):
                return False
        return True
    except OSError:
        return False


def identity(version: str, archive_sha: str) -> dict[str, str]:
    return {"version": version, "archive_sha256": archive_sha}


def valid_identity(value: object) -> bool:
    return isinstance(value, dict) and set(value) == {"version", "archive_sha256"} and isinstance(value["version"], str) and SEMVER.fullmatch(value["version"]) is not None and isinstance(value["archive_sha256"], str) and SHA.fullmatch(value["archive_sha256"]) is not None


def load_state(path: Path, *, absent_ok: bool = True) -> dict[str, object] | None:
    if not path.exists():
        if absent_ok: return None
        fail("INVALID_STATE")
    data = read_limited(path, 16 * 1024, "INVALID_STATE")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        fail("INVALID_STATE")
    value = json_canonical(data, "INVALID_STATE")
    if set(value) != {"schema", "active", "previous"} or value.get("schema") != STATE_SCHEMA:
        fail("INVALID_STATE")
    if not valid_identity(value.get("active")) or (value.get("previous") is not None and not valid_identity(value.get("previous"))):
        fail("INVALID_STATE")
    return value


def atomic_json(
    path: Path,
    value: dict[str, object],
    mode: int = 0o600,
    durability_event: str | None = None,
) -> None:
    temp = path.with_name(path.name + ".new")
    if temp.exists() or temp.is_symlink():
        if temp.is_dir() and not temp.is_symlink(): shutil.rmtree(temp)
        else: temp.unlink()
    write_exclusive(temp, canonical(value), mode)
    os.replace(temp, path)
    fsync_dir(path.parent)
    if durability_event is not None:
        durability_checkpoint(durability_event)


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.skills = root / "skills"
        self.active = self.skills / "cognitive-card-os"
        self.history = root / "skill-releases" / "cognitive-card-os"
        self.state_path = self.history / "state.json"
        self.journal_path = self.history / "transaction.json"
        self.new_active = self.skills / ".cognitive-card-os.new"
        self.backup = self.skills / ".cognitive-card-os.backup"
        self.lock = self.history / ".lock"
        self.lock_guard = self.lock / "guard"
        self.lock_owner = self.lock / "owner.json"
        self.lock_descriptor: int | None = None

    def cache(self, item: dict[str, str]) -> Path:
        return self.history / f"{item['version']}-{item['archive_sha256']}"

    def skill_entry_name(self, path: Path) -> str:
        if path == self.active:
            return "active"
        if path == self.new_active:
            return "new"
        if path == self.backup:
            return "backup"
        fail("INVALID_JOURNAL")

    def replace_skill_entry(self, source: Path, destination: Path) -> None:
        source_name = self.skill_entry_name(source)
        destination_name = self.skill_entry_name(destination)
        os.replace(source, destination)
        fsync_dir(self.skills)
        trace_transition(f"replace:{source_name}->{destination_name}")

    def remove_skill_entry(self, path: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return
        name = self.skill_entry_name(path)
        if path.is_symlink() or not path.is_dir():
            fail("INVALID_JOURNAL")
        shutil.rmtree(path)
        fsync_dir(self.skills)
        trace_transition(f"delete:{name}")

    def materialize_active(self, source: Path) -> None:
        copy_tree(source, self.active)
        fsync_dir(self.skills)
        trace_transition("materialize:cache->active")

    def validate_cache(self, item: dict[str, str]) -> Path:
        cache = self.cache(item)
        if cache.is_symlink() or not cache.is_dir(): fail("INVALID_CACHE")
        try:
            if {entry.name for entry in cache.iterdir()} != {"cognitive-card-os.zip", "skill"}:
                fail("INVALID_CACHE")
            skill_container = cache / "skill"
            if skill_container.is_symlink() or not skill_container.is_dir() or {entry.name for entry in skill_container.iterdir()} != {"cognitive-card-os"}:
                fail("INVALID_CACHE")
        except OSError:
            fail("INVALID_CACHE")
        archive = cache / "cognitive-card-os.zip"
        if stat.S_IMODE(archive.stat().st_mode) != 0o600:
            fail("INVALID_CACHE")
        try:
            release, _, contents = validate_archive(archive)
        except InstallError:
            fail("INVALID_CACHE")
        if sha(archive.read_bytes()) != item["archive_sha256"] or release["version"] != item["version"]:
            fail("INVALID_CACHE")
        extracted = cache / "skill" / "cognitive-card-os"
        with tempfile.TemporaryDirectory(prefix="ccos-cache-check-") as temporary:
            expected = extract(contents, Path(temporary) / "skill")
            if not tree_matches(extracted, expected): fail("INVALID_CACHE")
        return extracted

    def validate_active(self, state: dict[str, object] | None) -> None:
        if self.active.exists() or self.active.is_symlink():
            if state is None or not self.active.is_dir() or self.active.is_symlink():
                fail("UNMANAGED_ACTIVE_SKILL")
            cached = self.validate_cache(state["active"])
            if not tree_matches(self.active, cached): fail("UNMANAGED_ACTIVE_SKILL")
        elif state is not None:
            fail("UNMANAGED_ACTIVE_SKILL")

    def setup(self) -> None:
        if self.root.exists() and (self.root.is_symlink() or not self.root.is_dir()): fail("UNSAFE_INSTALL_ROOT")
        ensure_private_tree(self.root)
        durability_checkpoint("setup:root")
        ensure_private_directory(self.skills)
        durability_checkpoint("setup:skills")
        releases = self.root / "skill-releases"
        ensure_private_directory(releases)
        durability_checkpoint("setup:releases")
        ensure_private_directory(self.history)
        durability_checkpoint("setup:history")

    def acquire(self) -> None:
        ensure_private_directory(self.lock)
        if not self.lock_guard.exists():
            write_exclusive(self.lock_guard, b"", 0o600)
            fsync_dir(self.lock)
        if (
            self.lock_guard.is_symlink()
            or not self.lock_guard.is_file()
            or stat.S_IMODE(self.lock_guard.stat().st_mode) != 0o600
        ):
            fail("INSTALL_LOCKED")
        flags = os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock_guard, flags)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            os.close(descriptor)
            fail("INSTALL_LOCKED")
        self.lock_descriptor = descriptor
        if self.lock_owner.exists():
            try:
                previous = json_canonical(
                    read_limited(self.lock_owner, 4096, "INSTALL_LOCKED"),
                    "INSTALL_LOCKED",
                )
            except InstallError:
                self.release()
                raise
            if (
                set(previous) != {"schema", "pid", "identity"}
                or previous.get("schema") != LOCK_OWNER_SCHEMA
                or type(previous.get("pid")) is not int
                or previous["pid"] <= 0
                or not isinstance(previous.get("identity"), str)
                or SHA.fullmatch(previous["identity"]) is None
            ):
                self.release()
                fail("INSTALL_LOCKED")
            # The advisory lock is authoritative; PID and random identity are
            # diagnostic metadata only. A crash releases the kernel lock, so a
            # surviving record cannot become authoritative after PID reuse.
        current_identity = secrets.token_hex(32)
        atomic_json(
            self.lock_owner,
            {"schema": LOCK_OWNER_SCHEMA, "pid": os.getpid(), "identity": current_identity},
        )
        fsync_dir(self.history)
        durability_checkpoint("lock:container")
        ready = os.environ.get("CARD_OS_INSTALL_TEST_LOCK_READY")
        hold = os.environ.get("CARD_OS_INSTALL_TEST_HOLD_LOCK_SECONDS")
        if ready and hold:
            Path(ready).write_bytes(b"ready\n")
            time.sleep(min(max(float(hold), 0.0), 10.0))

    def release(self) -> None:
        descriptor = self.lock_descriptor
        if descriptor is None:
            return
        try:
            if self.lock_owner.exists() and not self.lock_owner.is_symlink():
                self.lock_owner.unlink()
                fsync_dir(self.lock)
                fsync_dir(self.history)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
            self.lock_descriptor = None

    def install_cache(self, archive: Path, item: dict[str, str], contents: dict[str, bytes]) -> None:
        destination = self.cache(item)
        if destination.exists() or destination.is_symlink():
            self.validate_cache(item)
            if (destination / "cognitive-card-os.zip").read_bytes() != archive.read_bytes(): fail("INVALID_CACHE")
            return
        staging = Path(tempfile.mkdtemp(prefix=".cache-", dir=self.history))
        staging.chmod(0o700)
        fsync_dir(self.history)
        try:
            write_exclusive(staging / "cognitive-card-os.zip", archive.read_bytes(), 0o600)
            extracted = extract(contents, staging / "skill")
            maybe_fault("after_extract")
            with tempfile.TemporaryDirectory(prefix="ccos-cache-verify-") as temporary:
                expected = extract(contents, Path(temporary) / "skill")
                if not tree_matches(extracted, expected): fail("INVALID_CACHE")
            fsync_dir(staging)
            durability_checkpoint("cache:contents")
            os.replace(staging, destination)
            fsync_dir(self.history)
            durability_checkpoint("cache:published")
        finally:
            if staging.exists(): shutil.rmtree(staging, ignore_errors=True)

    def read_journal(self) -> dict[str, object] | None:
        if not self.journal_path.exists(): return None
        if stat.S_IMODE(self.journal_path.stat().st_mode) != 0o600:
            fail("INVALID_JOURNAL")
        value = json_canonical(read_limited(self.journal_path, 32 * 1024, "INVALID_JOURNAL"), "INVALID_JOURNAL")
        if set(value) != {"schema", "phase", "old_state", "new_state"} or value.get("schema") != JOURNAL_SCHEMA:
            fail("INVALID_JOURNAL")
        if value.get("phase") not in {"prepared", "old_moved", "new_active", "state_committed"}:
            fail("INVALID_JOURNAL")
        for key in ("old_state", "new_state"):
            candidate = value.get(key)
            if candidate is not None:
                if not isinstance(candidate, dict) or set(candidate) != {"schema", "active", "previous"} or candidate.get("schema") != STATE_SCHEMA or not valid_identity(candidate.get("active")) or (candidate.get("previous") is not None and not valid_identity(candidate.get("previous"))):
                    fail("INVALID_JOURNAL")
        return value

    def recover(self, *, force_rollback: bool = False) -> None:
        journal = self.read_journal()
        if journal is None: return
        old_state, new_state = journal["old_state"], journal["new_state"]
        if new_state is None: fail("INVALID_JOURNAL")
        new_cached = self.validate_cache(new_state["active"])
        current = load_state(self.state_path)
        committed = current == new_state and self.active.is_dir() and not self.active.is_symlink() and tree_matches(self.active, new_cached)
        if committed and not force_rollback:
            if self.backup.exists():
                if old_state is not None: self.validate_cache(old_state["active"])
                self.remove_skill_entry(self.backup)
            self.remove_skill_entry(self.new_active)
            self.journal_path.unlink()
            fsync_dir(self.history)
            return
        if self.active.exists():
            if journal["phase"] == "prepared":
                if old_state is None:
                    fail("INVALID_JOURNAL")
                old_cached = self.validate_cache(old_state["active"])
                if not tree_matches(self.active, old_cached): fail("INVALID_JOURNAL")
            else:
                if not tree_matches(self.active, new_cached): fail("INVALID_JOURNAL")
                self.remove_skill_entry(self.active)
        if old_state is not None:
            old_cached = self.validate_cache(old_state["active"])
            if self.backup.exists(): self.replace_skill_entry(self.backup, self.active)
            elif not self.active.exists():
                self.materialize_active(old_cached)
            atomic_json(self.state_path, old_state)
        else:
            if self.backup.exists(): fail("INVALID_JOURNAL")
            if self.state_path.exists():
                self.state_path.unlink()
                fsync_dir(self.history)
        self.remove_skill_entry(self.new_active)
        self.validate_active(old_state)
        self.journal_path.unlink()
        fsync_dir(self.history)

    def reclaim_pre_journal_staging(self) -> None:
        if self.journal_path.exists() or self.journal_path.is_symlink():
            return
        new_exists = self.new_active.exists() or self.new_active.is_symlink()
        backup_exists = self.backup.exists() or self.backup.is_symlink()
        if backup_exists:
            fail("INVALID_JOURNAL")
        if not new_exists:
            return
        if self.new_active.is_symlink() or not self.new_active.is_dir():
            fail("INVALID_JOURNAL")

        state = load_state(self.state_path)
        self.validate_active(state)
        matched_cache = False
        try:
            entries = tuple(self.history.iterdir())
        except OSError:
            fail("INVALID_JOURNAL")
        for entry in entries:
            name = entry.name
            if len(name) <= 65 or name[-65] != "-":
                continue
            version, archive_sha = name[:-65], name[-64:]
            if SEMVER.fullmatch(version) is None or SHA.fullmatch(archive_sha) is None:
                continue
            try:
                cached = self.validate_cache(identity(version, archive_sha))
            except InstallError:
                fail("INVALID_JOURNAL")
            if tree_matches(self.new_active, cached):
                matched_cache = True
        if not matched_cache:
            fail("INVALID_JOURNAL")
        self.remove_skill_entry(self.new_active)


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink(): fail("INVALID_STATE")
    destination.mkdir(mode=0o755)
    destination.chmod(0o755)
    for directory in sorted(DIRS - {""}):
        (destination / directory).mkdir(mode=0o755)
        (destination / directory).chmod(0o755)
    for name in sorted(set(SOURCE) | {"release.json"}):
        mode = 0o644 if name == "release.json" else SOURCE[name]
        write_exclusive(destination / name, (source / name).read_bytes(), mode)
    for directory in sorted((destination / name for name in DIRS), reverse=True):
        fsync_dir(directory)
    fsync_dir(destination.parent)


def maybe_fault(name: str) -> None:
    if os.environ.get("CARD_OS_INSTALL_FAULT") == name:
        os._exit(97)


def maybe_error(name: str) -> None:
    if os.environ.get("CARD_OS_INSTALL_ERROR") == name:
        fail("INJECTED_INSTALL_FAILURE")


def activate(store: Store, target: dict[str, str], desired_state: dict[str, object]) -> bool:
    old_state = load_state(store.state_path)
    store.validate_active(old_state)
    target_tree = store.validate_cache(target)
    if old_state == desired_state and tree_matches(store.active, target_tree): return False
    store.recover()
    old_state = load_state(store.state_path)
    store.validate_active(old_state)
    if store.new_active.exists() or store.backup.exists(): fail("INVALID_JOURNAL")
    copy_tree(target_tree, store.new_active)
    durability_checkpoint("active:new")
    if not tree_matches(store.new_active, target_tree): fail("INVALID_CACHE")
    journal = {"schema": JOURNAL_SCHEMA, "phase": "prepared", "old_state": old_state, "new_state": desired_state}
    try:
        atomic_json(store.journal_path, journal)
        maybe_fault("after_journal"); maybe_error("after_journal")
        if store.active.exists(): store.replace_skill_entry(store.active, store.backup)
        maybe_fault("after_old_moved"); maybe_error("after_old_moved")
        journal["phase"] = "old_moved"; atomic_json(store.journal_path, journal)
        store.replace_skill_entry(store.new_active, store.active)
        durability_checkpoint("active:published")
        maybe_fault("after_new_active"); maybe_error("after_new_active")
        journal["phase"] = "new_active"; atomic_json(store.journal_path, journal)
        atomic_json(store.state_path, desired_state, durability_event="state:published")
        maybe_fault("after_state"); maybe_error("after_state")
        journal["phase"] = "state_committed"; atomic_json(store.journal_path, journal)
        store.validate_active(desired_state)
        if store.backup.exists():
            if old_state is not None: store.validate_cache(old_state["active"])
            store.remove_skill_entry(store.backup)
        store.journal_path.unlink(); fsync_dir(store.history)
    except Exception:
        store.recover(force_rollback=True)
        raise
    return True


def locked_operation(root: Path, callback):
    store = Store(root)
    # Refuse an unbound active tree before creating management directories.
    if (store.active.exists() or store.active.is_symlink()) and not store.state_path.exists() and not store.journal_path.exists():
        fail("UNMANAGED_ACTIVE_SKILL")
    # A state-bound active tree must also be proven managed before lock, cache,
    # journal, setup, or stale-staging writes occur in this invocation.
    if store.state_path.exists() and not store.journal_path.exists():
        existing_state = load_state(store.state_path, absent_ok=False)
        store.validate_active(existing_state)
    store.setup(); store.acquire()
    try:
        store.recover()
        store.reclaim_pre_journal_staging()
        for staging in store.history.glob(".cache-*"):
            if staging.is_symlink() or not staging.is_dir(): fail("INVALID_CACHE")
            shutil.rmtree(staging)
        return callback(store)
    finally:
        store.release()


def main(args: list[str]) -> None:
    command = args[0]
    if command == "manifest-url":
        manifest = parse_manifest(Path(args[1]), Path(args[2]), args[3])
        if args[3]:
            print(REGISTRY + f"releases/{args[3]}/cognitive-card-os.zip")
        else:
            print(manifest["archive_url"])
        return
    root = Path(args[1]).expanduser().absolute()
    if command == "rollback":
        def rollback(store: Store):
            state = load_state(store.state_path, absent_ok=False)
            store.validate_active(state)
            previous = state["previous"]
            if previous is None: fail("ROLLBACK_UNAVAILABLE")
            desired = {"schema": STATE_SCHEMA, "active": previous, "previous": state["active"]}
            activate(store, previous, desired)
        locked_operation(root, rollback)
        print("Rollback complete; restart Codex to load the verified Skill.")
        return
    manifest = parse_manifest(Path(args[2]), Path(args[3]), args[4])
    if args[4]:
        checksum = read_limited(Path(args[6]), 256, "DIGEST_MISMATCH")
        match = re.fullmatch(rb"([0-9a-f]{64})  cognitive-card-os\.zip\n", checksum)
        if match is None: fail("DIGEST_MISMATCH")
        release, archive_bytes, contents = validate_archive(Path(args[5]))
        archive_digest = match.group(1).decode("ascii")
        if sha(archive_bytes) != archive_digest: fail("DIGEST_MISMATCH")
        if release["version"] != args[4] or release["protocol"] != {"minimum": 1, "maximum": 1} or release["minimum_server_version"] != "0.3.1":
            fail("DIGEST_MISMATCH")
    else:
        release, _, contents = validate_archive(Path(args[5]), manifest)
        archive_digest = manifest["archive_sha256"]
    target = identity(release["version"], archive_digest)
    store = Store(root)
    if command == "check":
        if store.journal_path.exists(): fail("RECOVERY_REQUIRED")
        state = load_state(store.state_path, absent_ok=False)
        store.validate_active(state)
        store.validate_cache(state["active"])
        print("Verified remote release, cache, state, and active Skill.")
        return
    def install(store: Store):
        current = load_state(store.state_path)
        store.validate_active(current)
        store.install_cache(Path(args[5]), target, contents)
        current = load_state(store.state_path)
        store.validate_active(current)
        if current is not None and current["active"] == target:
            return
        previous = None if current is None else current["active"]
        desired = {"schema": STATE_SCHEMA, "active": target, "previous": previous}
        activate(store, target, desired)
    locked_operation(root, install)
    print("Installation complete; restart Codex to load the verified Skill.")


try:
    main(sys.argv[1:])
except InstallError as error:
    print(canonical({"error": {"code": error.code}}).decode(), end="", file=sys.stderr)
    raise SystemExit(1)
except Exception:
    print(canonical({"error": {"code": "INSTALL_FAILED"}}).decode(), end="", file=sys.stderr)
    raise SystemExit(1)
PY
}

if [ "$ACTION" = rollback ]; then
  run_helper rollback "$INSTALL_ROOT"
  exit 0
fi

MANIFEST_PATH="$WORK_DIR/manifest.json"
ARCHIVE_PATH="$WORK_DIR/cognitive-card-os.zip"
CHECKSUM_PATH='-'
download "$MANIFEST_PATH" 262144 "$MANIFEST_URL"
set +e
ARCHIVE_URL=$(run_helper manifest-url "$MANIFEST_PATH" "$0" "$REQUESTED_VERSION")
status=$?
set -e
[ "$status" -eq 0 ] || exit "$status"
if [ -n "$REQUESTED_VERSION" ]; then
  CHECKSUM_PATH="$WORK_DIR/sha256.txt"
  download "$CHECKSUM_PATH" 256 "${REGISTRY_ROOT}releases/${REQUESTED_VERSION}/sha256.txt"
fi
download "$ARCHIVE_PATH" 29360128 "$ARCHIVE_URL"
run_helper "$ACTION" "$INSTALL_ROOT" "$MANIFEST_PATH" "$0" "$REQUESTED_VERSION" "$ARCHIVE_PATH" "$CHECKSUM_PATH"
