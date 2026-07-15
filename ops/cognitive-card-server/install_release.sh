#!/usr/bin/env bash
set -euo pipefail

API_UNIT=cognitive-card-server.service
BACKUP_TIMER=cognitive-card-backup.timer
RELEASE_SCHEMA=cognitive-card-server-release-v1
INSTALL_SCHEMA=cognitive-card-server-install-v1

INSTALL_TEMPORARY_DIR=""
INSTALL_RELEASE_DIR=""
INSTALL_CURRENT_PATH=/opt/cognitive-card-server/current
INSTALL_CURRENT_LINK=""
INSTALL_RELEASE_CREATED=0
INSTALL_ACTIVATED=0
INSTALL_PRESERVE_RELEASE=0
INSTALL_OLD_CURRENT_TARGET=""
INSTALL_OLD_API_ACTIVE=inactive
INSTALL_OLD_API_ENABLED=disabled
INSTALL_OLD_TIMER_ACTIVE=inactive
INSTALL_OLD_TIMER_ENABLED=disabled
INSTALL_API_STARTED=0
INSTALL_TIMER_STARTED=0

fail() {
    printf 'error=%s\n' "$1" >&2
    return 1
}

normalize_freeze() {
    python3 -c '
import re
import sys

name_pattern = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
version_pattern = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.!+_-]*[A-Za-z0-9])?$")
entries = []
seen = set()
try:
    for raw_line in sys.stdin:
        line = raw_line.rstrip("\n")
        if not line or line != line.strip() or line.count("==") != 1:
            raise ValueError
        name, version = line.split("==", 1)
        if not name_pattern.fullmatch(name) or not version_pattern.fullmatch(version):
            raise ValueError
        normalized_name = re.sub(r"[-_.]+", "-", name).lower()
        if normalized_name in seen:
            raise ValueError
        seen.add(normalized_name)
        entries.append((normalized_name, version))
except ValueError:
    print("error=INVALID_FREEZE", file=sys.stderr)
    raise SystemExit(1)
for name, version in sorted(entries):
    print(f"{name}=={version}")
'
}

validate_archive() {
    local archive=$1
    python3 - "$archive" <<'PY' || {
import re
import sys
import tarfile
from pathlib import PurePosixPath

archive = sys.argv[1]
fixed = {
    "runtime-requirements.lock",
    "ops/card_os_backup.py",
    "ops/card_os_acceptance.py",
    "ops/install_nginx_include.py",
    "env/card-os.env",
    "systemd/cognitive-card-server.service",
    "systemd/cognitive-card-backup.service",
    "systemd/cognitive-card-backup.timer",
    "nginx/card-os.conf",
    "release-manifest.json",
}
wheel_pattern = re.compile(r"^cognitive_card_server-0\.3\.0-[A-Za-z0-9_.-]+\.whl$")
try:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError
        wheels = [name for name in names if wheel_pattern.fullmatch(name)]
        if len(wheels) != 1 or set(names) != fixed | set(wheels):
            raise ValueError
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or "." in path.parts:
                raise ValueError
            if not member.isfile():
                raise ValueError
except (OSError, tarfile.TarError, ValueError):
    raise SystemExit(1)
PY
        fail UNSAFE_ARCHIVE
    }
}

verify_checksum_binding() {
    local archive=$1
    local checksum_file=$2
    python3 - "$archive" "$checksum_file" <<'PY' || fail CHECKSUM_FILE_INVALID
import pathlib
import re
import sys
import hashlib

archive = pathlib.Path(sys.argv[1])
checksum_file = pathlib.Path(sys.argv[2])
try:
    content = checksum_file.read_text(encoding="ascii")
except (OSError, UnicodeError):
    raise SystemExit(1)
match = re.fullmatch(r"([0-9a-f]{64})  ([^/\n]+)\n", content)
if match is None or match.group(2) != archive.name:
    raise SystemExit(1)
digest = hashlib.sha256()
try:
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
except OSError:
    raise SystemExit(1)
if digest.hexdigest() != match.group(1):
    raise SystemExit(1)
print(match.group(1))
PY
}

verify_release() {
    local release_root=$1
    python3 - "$release_root" "$RELEASE_SCHEMA" <<'PY'
import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime

root = pathlib.Path(sys.argv[1])
schema = sys.argv[2]
manifest_path = root / "release-manifest.json"
expected_keys = {
    "schema", "application_commit", "operations_commit", "application_version",
    "python_version", "built_at", "lock_sha256", "wheel_sha256", "files",
}
fixed = {
    "runtime-requirements.lock",
    "ops/card_os_backup.py",
    "ops/card_os_acceptance.py",
    "ops/install_nginx_include.py",
    "env/card-os.env",
    "systemd/cognitive-card-server.service",
    "systemd/cognitive-card-backup.service",
    "systemd/cognitive-card-backup.timer",
    "nginx/card-os.conf",
}
wheel_pattern = re.compile(r"^cognitive_card_server-0\.3\.0-[A-Za-z0-9_.-]+\.whl$")
commit_pattern = re.compile(r"^[0-9a-f]{40}$")
timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

try:
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    canonical = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if raw_manifest != canonical or set(manifest) != expected_keys:
        raise ValueError
    if manifest["schema"] != schema or manifest["application_version"] != "0.3.0":
        raise ValueError
    if not commit_pattern.fullmatch(manifest["application_commit"]):
        raise ValueError
    if not commit_pattern.fullmatch(manifest["operations_commit"]):
        raise ValueError
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["python_version"]):
        raise ValueError
    if not timestamp_pattern.fullmatch(manifest["built_at"]):
        raise ValueError
    if datetime.strptime(manifest["built_at"], "%Y-%m-%dT%H:%M:%SZ").strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    ) != manifest["built_at"]:
        raise ValueError
    files = manifest["files"]
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError
    if files != sorted(files, key=lambda item: item.get("path", "")):
        raise ValueError
    paths = []
    for item in files:
        if set(item) != {"path", "sha256", "size"}:
            raise ValueError
        path = item["path"]
        payload = root / path
        if not payload.is_file() or payload.is_symlink():
            raise ValueError
        if item["size"] != payload.stat().st_size or item["sha256"] != digest(payload):
            raise ValueError
        paths.append(path)
    wheels = [path for path in paths if wheel_pattern.fullmatch(path)]
    if len(wheels) != 1 or set(paths) != fixed | set(wheels) or len(paths) != len(set(paths)):
        raise ValueError
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_files != set(paths) | {"release-manifest.json"}:
        raise ValueError
    if manifest["lock_sha256"] != digest(root / "runtime-requirements.lock"):
        raise ValueError
    if manifest["wheel_sha256"] != digest(root / wheels[0]):
        raise ValueError
except (OSError, TypeError, ValueError, json.JSONDecodeError):
    print("error=RELEASE_MANIFEST_INVALID", file=sys.stderr)
    raise SystemExit(1)
print(manifest["application_commit"])
PY
}

compare_environment() {
    local template=$1
    local installed=$2
    python3 - "$template" "$installed" <<'PY' || fail ENVIRONMENT_MISMATCH
import pathlib
import sys

def values(path):
    result = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError
        key, value = line.split("=", 1)
        if not key or key in result:
            raise ValueError
        result[key] = value
    return result

try:
    expected = values(sys.argv[1])
    actual = values(sys.argv[2])
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ValueError
except (OSError, UnicodeError, ValueError):
    raise SystemExit(1)
PY
}

write_install_manifest() {
    local release_dir=$1
    local archive_digest=$2
    local application_commit=$3
    local operations_commit=$4
    local runtime_digest=$5
    local server_python=$6
    python3 - "$release_dir/install-manifest.json" "$INSTALL_SCHEMA" \
        "$application_commit" "$operations_commit" "$archive_digest" \
        "$server_python" "$runtime_digest" <<'PY'
import datetime
import json
import pathlib
import sys

output = pathlib.Path(sys.argv[1])
manifest = {
    "schema": sys.argv[2],
    "application_commit": sys.argv[3],
    "operations_commit": sys.argv[4],
    "archive_sha256": sys.argv[5],
    "python_version": sys.argv[6],
    "installed_runtime_sha256": sys.argv[7],
    "installed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
output.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
PY
}

atomic_restore_current() {
    local current_path=$1
    local old_target=$2
    local temporary_link="${current_path}.rollback.$$"
    rm -f -- "$temporary_link"
    ln -s -- "$old_target" "$temporary_link"
    python3 - "$temporary_link" "$current_path" <<'PY'
import os
import sys
os.replace(sys.argv[1], sys.argv[2])
PY
}

rollback_activation() {
    local current_path=$1
    local release_dir=$2
    local old_current_target=$3
    local old_api_active=$4
    local old_api_enabled=$5
    local old_timer_active=$6
    local old_timer_enabled=$7
    local api_started=$8
    local timer_started=$9
    local rollback_status=0

    if [[ "$api_started" == 1 ]]; then
        systemctl stop "$API_UNIT" || rollback_status=1
    fi
    if [[ "$timer_started" == 1 ]]; then
        systemctl stop "$BACKUP_TIMER" || rollback_status=1
    fi

    if [[ -n "$old_current_target" ]]; then
        atomic_restore_current "$current_path" "$old_current_target" || rollback_status=1
    else
        rm -f -- "$current_path" || rollback_status=1
    fi

    if [[ "$old_api_enabled" == enabled ]]; then
        systemctl enable "$API_UNIT" || rollback_status=1
    else
        systemctl disable "$API_UNIT" || rollback_status=1
    fi
    if [[ "$old_timer_enabled" == enabled ]]; then
        systemctl enable "$BACKUP_TIMER" || rollback_status=1
    else
        systemctl disable "$BACKUP_TIMER" || rollback_status=1
    fi

    if [[ "$old_api_active" == active && -n "$old_current_target" ]]; then
        systemctl start "$API_UNIT" || rollback_status=1
    fi
    if [[ "$old_timer_active" == active && -n "$old_current_target" ]]; then
        systemctl start "$BACKUP_TIMER" || rollback_status=1
    fi

    if [[ -n "$old_current_target" ]]; then
        [[ -L "$current_path" && "$(readlink "$current_path")" == "$old_current_target" ]] \
            || rollback_status=1
    else
        [[ ! -e "$current_path" && ! -L "$current_path" ]] || rollback_status=1
    fi

    if [[ "$rollback_status" != 0 ]]; then
        fail INSTALL_ROLLBACK_FAILED
        return 1
    fi
    rm -rf -- "$release_dir" || {
        fail INSTALL_ROLLBACK_FAILED
        return 1
    }
}

install_cleanup() {
    local status=$?
    local rollback_status=0
    trap - EXIT
    set +e

    if [[ -n "$INSTALL_CURRENT_LINK" ]]; then
        rm -f -- "$INSTALL_CURRENT_LINK"
    fi
    if [[ -n "$INSTALL_TEMPORARY_DIR" ]]; then
        rm -rf -- "$INSTALL_TEMPORARY_DIR"
    fi

    if [[ "$status" != 0 && "$INSTALL_ACTIVATED" == 1 ]]; then
        INSTALL_PRESERVE_RELEASE=1
        rollback_activation \
            "$INSTALL_CURRENT_PATH" \
            "$INSTALL_RELEASE_DIR" \
            "$INSTALL_OLD_CURRENT_TARGET" \
            "$INSTALL_OLD_API_ACTIVE" \
            "$INSTALL_OLD_API_ENABLED" \
            "$INSTALL_OLD_TIMER_ACTIVE" \
            "$INSTALL_OLD_TIMER_ENABLED" \
            "$INSTALL_API_STARTED" \
            "$INSTALL_TIMER_STARTED" || rollback_status=1
        if [[ "$rollback_status" == 0 ]]; then
            INSTALL_RELEASE_CREATED=0
            INSTALL_ACTIVATED=0
            INSTALL_PRESERVE_RELEASE=0
        fi
    elif [[ "$status" != 0 && "$INSTALL_RELEASE_CREATED" == 1 \
        && "$INSTALL_PRESERVE_RELEASE" == 0 ]]; then
        rm -rf -- "$INSTALL_RELEASE_DIR"
    fi

    if [[ "$rollback_status" != 0 ]]; then
        status=1
    fi
    exit "$status"
}

main() {
    if [[ $# -ne 2 ]]; then
        printf 'usage: %s ARCHIVE SHA256_FILE\n' "$0" >&2
        return 2
    fi
    local archive sha_file archive_dir archive_digest temporary_dir extracted
    local release_id release_dir wheel pip_path installed_runtime normalized_lock filtered_runtime
    local operations_commit server_python runtime_digest old_current_target=""
    local old_api_active=inactive old_api_enabled=disabled
    local old_timer_active=inactive old_timer_enabled=disabled

    INSTALL_TEMPORARY_DIR=""
    INSTALL_RELEASE_DIR=""
    INSTALL_CURRENT_LINK=""
    INSTALL_RELEASE_CREATED=0
    INSTALL_ACTIVATED=0
    INSTALL_PRESERVE_RELEASE=0
    INSTALL_OLD_CURRENT_TARGET=""
    INSTALL_OLD_API_ACTIVE=inactive
    INSTALL_OLD_API_ENABLED=disabled
    INSTALL_OLD_TIMER_ACTIVE=inactive
    INSTALL_OLD_TIMER_ENABLED=disabled
    INSTALL_API_STARTED=0
    INSTALL_TIMER_STARTED=0

    archive=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1")
    sha_file=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$2")
    [[ -f "$archive" && -f "$sha_file" ]] || fail INPUT_MISSING
    archive_dir=$(dirname "$archive")
    (
        cd "$archive_dir"
        SHA256_FILE=$sha_file
        sha256sum --check "$SHA256_FILE"
    )
    archive_digest=$(verify_checksum_binding "$archive" "$sha_file")
    exec 9>/run/lock/cognitive-card-server-install.lock
    flock -n 9 || fail INSTALL_IN_PROGRESS

    apt-get update
    apt-get install -y python3-venv sqlite3
    id cardos >/dev/null 2>&1 || useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin cardos
    install -d -o root -g root -m 0755 /opt/cognitive-card-server/releases
    install -d -o cardos -g cardos -m 0700 /var/lib/cognitive-card-server/candidates
    install -d -o root -g cardos -m 0750 /etc/cognitive-card-server
    install -d -o root -g root -m 0700 /var/backups/cognitive-card-server

    temporary_dir=$(mktemp -d /opt/cognitive-card-server/.install.XXXXXX)
    INSTALL_TEMPORARY_DIR=$temporary_dir
    extracted="$temporary_dir/payload"
    mkdir "$extracted"
    trap install_cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    cp -- "$archive" "$temporary_dir/archive.tar.gz"
    [[ "$(sha256sum "$temporary_dir/archive.tar.gz" | awk '{print $1}')" == "$archive_digest" ]] \
        || fail ARCHIVE_CHANGED
    validate_archive "$temporary_dir/archive.tar.gz"
    tar --no-same-owner --no-same-permissions -xzf "$temporary_dir/archive.tar.gz" -C "$extracted"
    release_id=$(verify_release "$extracted")
    [[ "$release_id" =~ ^[0-9a-f]{40}$ ]] || fail RELEASE_ID_INVALID
    release_dir="/opt/cognitive-card-server/releases/$release_id"
    RELEASE_DIR=$release_dir
    INSTALL_RELEASE_DIR=$release_dir
    mkdir --mode=0755 "$RELEASE_DIR" 2>/dev/null || fail RELEASE_EXISTS
    INSTALL_RELEASE_CREATED=1
    mv -- "$extracted"/* "$RELEASE_DIR"/
    rmdir "$extracted"

    python3 -m venv "$RELEASE_DIR/.venv"
    pip_path="$RELEASE_DIR/.venv/bin/pip"
    "$pip_path" install --requirement "$RELEASE_DIR/runtime-requirements.lock"
    wheel=$(find "$RELEASE_DIR" -maxdepth 1 -type f -name 'cognitive_card_server-0.3.0-*.whl')
    [[ -n "$wheel" && "$(printf '%s\n' "$wheel" | wc -l | tr -d ' ')" == 1 ]] || fail APPLICATION_WHEEL_INVALID
    WHEEL=$wheel
    "$pip_path" install --no-deps "$WHEEL"
    "$pip_path" check

    installed_runtime="$RELEASE_DIR/installed-runtime.txt"
    "$pip_path" freeze --all | normalize_freeze >"$installed_runtime"
    normalized_lock="$temporary_dir/normalized-lock.txt"
    normalize_freeze <"$RELEASE_DIR/runtime-requirements.lock" >"$normalized_lock"
    filtered_runtime="$temporary_dir/filtered-runtime.txt"
    awk -F '==' '$1 != "cognitive-card-server" && $1 != "pip" && $1 != "setuptools" && $1 != "wheel"' \
        "$installed_runtime" >"$filtered_runtime"
    cmp -s "$normalized_lock" "$filtered_runtime" || fail RUNTIME_LOCK_MISMATCH

    operations_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["operations_commit"])' \
        "$RELEASE_DIR/release-manifest.json")
    server_python=$("$RELEASE_DIR/.venv/bin/python" -c 'import platform; print(platform.python_version())')
    runtime_digest=$(sha256sum "$installed_runtime" | awk '{print $1}')
    write_install_manifest "$RELEASE_DIR" "$archive_digest" "$release_id" \
        "$operations_commit" "$runtime_digest" "$server_python"
    chown root:root "$installed_runtime" "$RELEASE_DIR/install-manifest.json"
    chmod 0644 "$installed_runtime" "$RELEASE_DIR/install-manifest.json"

    if [[ ! -e /etc/cognitive-card-server/card-os.env ]]; then
        install -o root -g cardos -m 0640 "$RELEASE_DIR/env/card-os.env" /etc/cognitive-card-server/card-os.env
    else
        compare_environment "$RELEASE_DIR/env/card-os.env" /etc/cognitive-card-server/card-os.env
    fi
    install -o root -g root -m 0644 "$RELEASE_DIR/systemd/cognitive-card-server.service" /etc/systemd/system/cognitive-card-server.service
    install -o root -g root -m 0644 "$RELEASE_DIR/systemd/cognitive-card-backup.service" /etc/systemd/system/cognitive-card-backup.service
    install -o root -g root -m 0644 "$RELEASE_DIR/systemd/cognitive-card-backup.timer" /etc/systemd/system/cognitive-card-backup.timer

    if [[ -L /opt/cognitive-card-server/current ]]; then
        old_current_target=$(readlink /opt/cognitive-card-server/current)
    elif [[ -e /opt/cognitive-card-server/current ]]; then
        fail CURRENT_NOT_SYMLINK
    fi
    systemctl is-active --quiet "$API_UNIT" && old_api_active=active || true
    systemctl is-enabled --quiet "$API_UNIT" && old_api_enabled=enabled || true
    systemctl is-active --quiet "$BACKUP_TIMER" && old_timer_active=active || true
    systemctl is-enabled --quiet "$BACKUP_TIMER" && old_timer_enabled=enabled || true
    INSTALL_OLD_CURRENT_TARGET=$old_current_target
    INSTALL_OLD_API_ACTIVE=$old_api_active
    INSTALL_OLD_API_ENABLED=$old_api_enabled
    INSTALL_OLD_TIMER_ACTIVE=$old_timer_active
    INSTALL_OLD_TIMER_ENABLED=$old_timer_enabled

    systemctl daemon-reload
    INSTALL_CURRENT_LINK="/opt/cognitive-card-server/.current.$$.tmp"
    rm -f -- "$INSTALL_CURRENT_LINK"
    ln -s "releases/$release_id" "$INSTALL_CURRENT_LINK"
    CURRENT_LINK=$INSTALL_CURRENT_LINK
    INSTALL_ACTIVATED=1
    mv -T "$CURRENT_LINK" /opt/cognitive-card-server/current

    INSTALL_API_STARTED=1
    if [[ "$old_api_active" == active ]]; then
        systemctl enable "$API_UNIT"
        systemctl restart "$API_UNIT"
    else
        systemctl enable --now cognitive-card-server.service
    fi

    INSTALL_TIMER_STARTED=1
    systemctl enable --now cognitive-card-backup.timer
    rm -rf -- "$temporary_dir"
    INSTALL_TEMPORARY_DIR=""
    trap - INT TERM EXIT
    printf 'status=installed release=%s\n' "$release_id"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
