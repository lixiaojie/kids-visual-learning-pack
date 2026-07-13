"""Read-only discovery and atomic reporting for Cognitive Card assets."""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import errno
import hashlib
import io
import json
import logging
import os
import re
import secrets
import stat
import sys
import unicodedata
import warnings
from contextlib import contextmanager, redirect_stderr
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable, Mapping, Sequence


SOURCE_SCHEMA = "cognitive-card-migration-sources-v1"
ROOTS_SCHEMA = "cognitive-card-migration-roots-v1"
ROOT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
THREAD_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
VALID_GRADES = frozenset({"A", "B", "C", "D", "legacy-gallery"})
VALID_DECISIONS = frozenset(
    {
        "strict_revalidate",
        "upgrade_revalidate",
        "rebuild",
        "provenance_only",
        "legacy_gallery",
        "exclude",
    }
)
SOURCE_TOP_LEVEL_KEYS = frozenset({"schema", "defaults", "sources"})
SOURCE_DEFAULT_KEYS = frozenset({"include_extensions", "exclude_names"})
SOURCE_REQUIRED_KEYS = frozenset(
    {
        "root_id",
        "source_group",
        "locator",
        "source_thread_id",
        "migration_grade",
        "decision",
    }
)
SOURCE_OPTIONAL_KEYS = frozenset({"additional_extensions"})
LOCATOR_KEYS = frozenset({"base", "relative"})
ROOT_MAP_KEYS = frozenset({"schema", "bases"})
ROOT_BASE_KEYS = frozenset({"workspace", "codex_archive"})
READ_CHUNK_SIZE = 1024 * 1024
MEDIA_TYPES = {
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
    ".json": "application/json",
    ".md": "text/markdown",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".txt": "text/plain",
    ".tsv": "text/tab-separated-values",
    ".html": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".tsx": "text/typescript",
}
IMAGE_FORMAT_MEDIA_TYPES = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}
UNSAFE_LOGICAL_NAME_DETAIL = "source entry has an unsafe logical name"
FACT_BASENAMES = frozenset({"fact.json", "facts.json"})
PROPOSITION_BASENAMES = frozenset(
    {"proposition_alignment.json", "semantic_core.json", "semantic-core.json"}
)
CONTENT_LOCK_BASENAMES = frozenset({"content_lock.json", "content-lock.json"})
FOUR_CARD_BASENAMES = frozenset(
    {"final_cards.json", "four_cards.json", "four-cards.json"}
)
FOUR_CARD_COMPONENTS = frozenset({"final_cards"})
QA_COMPONENTS = frozenset({"qa", "06_qa"})
PRINT_COMPONENTS = frozenset({"print", "05_print"})
MANIFEST_BASENAMES = frozenset(
    {"manifest.json", "package_manifest.json", "package-manifest.json"}
)
GRADE_ORDER = {grade: index for index, grade in enumerate(("A", "B", "C", "D", "legacy-gallery"))}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
RFC3339_UTC_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
VALID_WARNING_CODES = frozenset(
    {
        "missing_root",
        "unsafe_source_entry",
        "unreadable_directory",
        "symlink",
        "excluded_name",
        "unsupported_extension",
        "unreadable_file",
        "source_changed_during_scan",
        "metadata_unreadable",
        "media_type_mismatch",
    }
)
_OS_OPEN_SUPPORT_TARGET = os.open
_OS_SCANDIR_SUPPORT_TARGET = os.scandir
_OS_STAT_SUPPORT_TARGET = os.stat
_DESCRIPTOR_UNSUPPORTED_ERRORS = (NotImplementedError, TypeError)


class ConfigError(ValueError):
    """Raised when inventory configuration cannot be used safely."""


class _MetadataUnreadable(ValueError):
    pass


class _DescriptorOperationsUnsupported(RuntimeError):
    pass


class _SourceFileUnreadable(RuntimeError):
    pass


class _SourceChangedDuringScan(ValueError):
    def __init__(self) -> None:
        super().__init__("source_changed_during_scan")


@dataclass(frozen=True)
class ConfigWarning:
    root_id: str
    code: str
    detail: str


@dataclass(frozen=True)
class SourceRule:
    root_id: str
    source_group: str
    locator_base: str
    locator_relative: str
    resolved_path: Path
    source_thread_id: str | None
    migration_grade: str
    decision: str
    include_extensions: tuple[str, ...]
    exclude_names: tuple[str, ...]


@dataclass(frozen=True)
class SourceConfig:
    schema: str
    rules: tuple[SourceRule, ...]
    warnings: tuple[ConfigWarning, ...]
    config_digest: str


@dataclass(frozen=True)
class WarningRecord:
    root_id: str
    relative_path: str
    code: str
    detail: str


@dataclass(frozen=True)
class SourceAliasRecord:
    root_id: str
    relative_path: str
    source_thread_id: str | None
    source_group: str
    sha256: str
    size_bytes: int
    media_type: str
    image_width: int | None
    image_height: int | None
    pdf_page_count: int | None
    metadata_status: str


class _DuplicateJsonKey(ValueError):
    pass


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateJsonKey
        value[key] = item
    return value


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    failed = False
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJsonKey):
        failed = True
    if failed:
        raise ConfigError(f"cannot read {label}")
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a JSON object")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_config_digest(path: Path) -> str:
    """Hash parsed portable configuration, independent of formatting and roots."""

    config = _read_json_object(path, "source config")
    _validate_portable_source_shape(config)
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(config)).hexdigest()


def metadata_reader_versions() -> dict[str, str]:
    """Return the reader-version fields used by later semantic run payloads."""

    try:
        import PIL
        import pypdf
    except ImportError as error:
        raise ConfigError(
            "metadata readers are unavailable; install requirements-card-os-inventory.txt"
        ) from error
    return {"pillow": str(PIL.__version__), "pypdf": str(pypdf.__version__)}


def _string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ConfigError(f"{field} must be a non-empty string")
    return value


def _require_exact_keys(
    value: Mapping[str, Any],
    required: frozenset[str],
    label: str,
    *,
    optional: frozenset[str] = frozenset(),
) -> None:
    keys = frozenset(value)
    if not required.issubset(keys) or not keys.issubset(required | optional):
        raise ConfigError(f"{label} has invalid fields")


def _contains_absolute_string(value: Any) -> bool:
    if isinstance(value, str):
        windows_path = PureWindowsPath(value)
        return (
            PurePosixPath(value).is_absolute()
            or windows_path.is_absolute()
            or bool(windows_path.drive)
            or value.startswith("\\")
        )
    if isinstance(value, dict):
        return any(_contains_absolute_string(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_absolute_string(item) for item in value)
    return False


def _validate_portable_source_shape(
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], list[Any]]:
    if _contains_absolute_string(config):
        raise ConfigError("portable source config contains an absolute string value")
    _require_exact_keys(config, SOURCE_TOP_LEVEL_KEYS, "source config")
    if config.get("schema") != SOURCE_SCHEMA:
        raise ConfigError(f"source config schema must equal {SOURCE_SCHEMA}")

    defaults = config.get("defaults")
    if not isinstance(defaults, dict):
        raise ConfigError("source config defaults must be an object")
    _require_exact_keys(defaults, SOURCE_DEFAULT_KEYS, "source config defaults")

    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ConfigError("source config sources must be a non-empty array")
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ConfigError(f"sources[{index}] must be an object")
        _require_exact_keys(
            source,
            SOURCE_REQUIRED_KEYS,
            f"sources[{index}]",
            optional=SOURCE_OPTIONAL_KEYS,
        )
        locator = source.get("locator")
        if not isinstance(locator, dict):
            raise ConfigError(f"sources[{index}].locator must be an object")
        _require_exact_keys(locator, LOCATOR_KEYS, f"sources[{index}].locator")
    return defaults, sources


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigError(f"{field} must be an array")
    result = tuple(_string(item, field) for item in value)
    if len(set(result)) != len(result):
        raise ConfigError(f"{field} contains duplicates")
    return result


def _extensions(value: Any, field: str) -> tuple[str, ...]:
    result = _string_list(value, field)
    for extension in result:
        if (
            not extension.startswith(".")
            or len(extension) < 2
            or extension != extension.lower()
            or "/" in extension
            or "\\" in extension
        ):
            raise ConfigError(f"{field} contains an invalid extension")
    return result


def _exclude_names(value: Any, field: str) -> tuple[str, ...]:
    result = _string_list(value, field)
    for name in result:
        if name in {".", ".."} or "/" in name or "\\" in name or "\x00" in name:
            raise ConfigError(f"{field} contains an invalid name")
    return result


def _safe_relative(value: Any, field: str) -> tuple[str, PurePosixPath]:
    relative = _string(value, field)
    if "\\" in relative or "\x00" in relative:
        raise ConfigError(f"{field} must be a POSIX relative path")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ConfigError(f"{field} must be a safe relative path")
    canonical = path.as_posix()
    if canonical != relative:
        raise ConfigError(f"{field} must be normalized")
    return canonical, path


def _lstat_existing_prefixes(path: Path, field: str) -> os.stat_result | None:
    """Inspect every existing path component without following symbolic links."""

    current = Path(path.anchor)
    unsafe = False
    try:
        current_stat = current.lstat()
    except OSError:
        unsafe = True
    if unsafe:
        raise ConfigError(f"{field} cannot be validated safely")
    if stat.S_ISLNK(current_stat.st_mode):
        raise ConfigError(f"{field} must not contain symlink components")

    for component in path.parts[1:]:
        current = current / component
        unsafe = False
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            return None
        except OSError:
            unsafe = True
        if unsafe:
            raise ConfigError(f"{field} cannot be validated safely")
        if stat.S_ISLNK(current_stat.st_mode):
            raise ConfigError(f"{field} must not contain symlink components")
    return current_stat


def _absolute_base(value: Any, field: str) -> Path:
    raw = _string(value, field)
    base = Path(raw)
    if not base.is_absolute():
        raise ConfigError(f"{field} must be absolute")
    normalized = Path(os.path.abspath(os.path.normpath(raw)))
    if normalized != base:
        raise ConfigError(f"{field} must be normalized")
    base_stat = _lstat_existing_prefixes(normalized, field)
    if base_stat is not None and not stat.S_ISDIR(base_stat.st_mode):
        raise ConfigError(f"{field} must name a non-symlink directory")
    return normalized


def _resolved_root(
    base: Path, relative: PurePosixPath, root_id: str
) -> tuple[Path, bool]:
    candidate = base.joinpath(*relative.parts)
    normalized = Path(os.path.abspath(os.path.normpath(str(candidate))))
    if candidate != normalized:
        raise ConfigError(f"root {root_id} has a non-normalized path")
    root_stat = _lstat_existing_prefixes(normalized, f"root {root_id}")
    if root_stat is not None and not stat.S_ISDIR(root_stat.st_mode):
        raise ConfigError(f"root {root_id} must be a non-symlink directory")
    return normalized, root_stat is not None


def _validated_bases(roots: Mapping[str, Any]) -> dict[str, Path]:
    _require_exact_keys(roots, ROOT_MAP_KEYS, "root map")
    if roots.get("schema") != ROOTS_SCHEMA:
        raise ConfigError(f"root map schema must equal {ROOTS_SCHEMA}")
    raw_bases = roots.get("bases")
    if not isinstance(raw_bases, dict) or not raw_bases:
        raise ConfigError("root map bases must be a non-empty object")
    _require_exact_keys(raw_bases, ROOT_BASE_KEYS, "root map bases")
    return {
        _string(name, "base key"): _absolute_base(value, f"base {name}")
        for name, value in raw_bases.items()
    }


def load_source_config(
    path: Path,
    roots_path: Path,
    *,
    strict_roots: bool,
) -> SourceConfig:
    """Load portable rules and resolve them through a machine-local root map."""

    config = _read_json_object(path, "source config")
    roots = _read_json_object(roots_path, "root map")
    defaults, raw_sources = _validate_portable_source_shape(config)
    bases = _validated_bases(roots)

    default_extensions = _extensions(
        defaults.get("include_extensions"), "defaults.include_extensions"
    )
    default_excludes = _exclude_names(
        defaults.get("exclude_names"), "defaults.exclude_names"
    )

    rules: list[SourceRule] = []
    warnings: list[ConfigWarning] = []
    seen_ids: set[str] = set()
    seen_paths: dict[Path, str] = {}
    for index, raw_source in enumerate(raw_sources):
        root_id = _string(raw_source.get("root_id"), f"sources[{index}].root_id")
        if not ROOT_ID_PATTERN.fullmatch(root_id):
            raise ConfigError(f"root_id {root_id!r} is invalid")
        if root_id in seen_ids:
            raise ConfigError(f"duplicate root_id {root_id}")
        seen_ids.add(root_id)

        source_group = _string(
            raw_source.get("source_group"), f"source {root_id}.source_group"
        )
        if not ROOT_ID_PATTERN.fullmatch(source_group):
            raise ConfigError(f"source {root_id} has invalid source_group")
        locator = raw_source.get("locator")
        locator_base = _string(locator.get("base"), f"source {root_id}.locator.base")
        if locator_base not in bases:
            raise ConfigError(f"source {root_id} uses an unknown base")
        locator_relative, relative_path = _safe_relative(
            locator.get("relative"), f"source {root_id}.locator.relative"
        )

        migration_grade = _string(
            raw_source.get("migration_grade"), f"source {root_id}.migration_grade"
        )
        if migration_grade not in VALID_GRADES:
            raise ConfigError(f"source {root_id} has an invalid migration grade")
        decision = _string(raw_source.get("decision"), f"source {root_id}.decision")
        if decision not in VALID_DECISIONS:
            raise ConfigError(f"source {root_id} has an invalid decision")
        source_thread_id = raw_source.get("source_thread_id")
        if source_thread_id is not None:
            source_thread_id = _string(
                source_thread_id, f"source {root_id}.source_thread_id"
            )
            if not THREAD_ID_PATTERN.fullmatch(source_thread_id):
                raise ConfigError(f"source {root_id} has an invalid source_thread_id")

        additional_extensions = _extensions(
            raw_source.get("additional_extensions", []),
            f"source {root_id}.additional_extensions",
        )
        include_extensions = default_extensions + additional_extensions
        if len(set(include_extensions)) != len(include_extensions):
            raise ConfigError(f"source {root_id} repeats an enabled extension")

        resolved_path, root_exists = _resolved_root(
            bases[locator_base], relative_path, root_id
        )
        previous_root = seen_paths.get(resolved_path)
        if previous_root is not None:
            raise ConfigError(
                f"sources {previous_root} and {root_id} resolve to the same path"
            )
        seen_paths[resolved_path] = root_id
        if not root_exists:
            if strict_roots:
                raise ConfigError(f"source root {root_id} is missing")
            warnings.append(
                ConfigWarning(
                    root_id=root_id,
                    code="missing_root",
                    detail="declared source root does not exist on this machine",
                )
            )

        rules.append(
            SourceRule(
                root_id=root_id,
                source_group=source_group,
                locator_base=locator_base,
                locator_relative=locator_relative,
                resolved_path=resolved_path,
                source_thread_id=source_thread_id,
                migration_grade=migration_grade,
                decision=decision,
                include_extensions=include_extensions,
                exclude_names=default_excludes,
            )
        )

    return SourceConfig(
        schema=SOURCE_SCHEMA,
        rules=tuple(rules),
        warnings=tuple(warnings),
        config_digest="sha256:"
        + hashlib.sha256(_canonical_json_bytes(config)).hexdigest(),
    )


def _warning(
    rule: SourceRule,
    relative_path: PurePosixPath,
    code: str,
    detail: str,
) -> WarningRecord:
    return WarningRecord(
        root_id=rule.root_id,
        relative_path=relative_path.as_posix(),
        code=code,
        detail=detail,
    )


def _identity(stat_result: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return _identity(left) == _identity(right)


def _descriptor_flags(*, directory: bool) -> int | None:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or (directory and directory_flag is None):
        return None
    flags = os.O_RDONLY | no_follow
    if directory:
        flags |= directory_flag
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _descriptor_operations_supported() -> bool:
    try:
        return (
            _OS_OPEN_SUPPORT_TARGET in os.supports_dir_fd
            and _OS_SCANDIR_SUPPORT_TARGET in os.supports_fd
            and _OS_STAT_SUPPORT_TARGET in os.supports_dir_fd
            and _OS_STAT_SUPPORT_TARGET in os.supports_follow_symlinks
        )
    except (AttributeError, TypeError):
        return False


def _unsupported_descriptor_operation() -> _DescriptorOperationsUnsupported:
    return _DescriptorOperationsUnsupported("descriptor operation is unsupported")


def _descriptor_open(
    path: str | Path,
    flags: int,
    *,
    dir_fd: int | None = None,
) -> int:
    try:
        if dir_fd is None:
            return os.open(path, flags)
        return os.open(path, flags, dir_fd=dir_fd)
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


def _descriptor_scandir(descriptor: int):
    try:
        return os.scandir(descriptor)
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


def _descriptor_lstat(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


def _descriptor_entry_stat(entry: os.DirEntry[str]) -> os.stat_result:
    try:
        return entry.stat(follow_symlinks=False)
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


def _descriptor_fstat(descriptor: int) -> os.stat_result:
    try:
        return os.fstat(descriptor)
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


def _descriptor_stat_at(name: str, parent_descriptor: int) -> os.stat_result:
    try:
        return os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except _DESCRIPTOR_UNSUPPORTED_ERRORS:
        raise _unsupported_descriptor_operation() from None


@contextmanager
def _isolated_library_logger(name: str):
    """Temporarily silence one parser logger and restore its exact state."""

    logger = logging.getLogger(name)
    previous_handlers = list(logger.handlers)
    previous_level = logger.level
    previous_propagate = logger.propagate
    previous_disabled = logger.disabled
    logger.handlers = [logging.NullHandler()]
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False
    logger.disabled = False
    try:
        yield
    finally:
        logger.handlers = previous_handlers
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
        logger.disabled = previous_disabled


@contextmanager
def _duplicate_binary_reader(descriptor: int):
    """Transfer one duplicate descriptor to fdopen or close it on construction failure."""

    duplicate_descriptor: int | None = os.dup(descriptor)
    try:
        reader = os.fdopen(duplicate_descriptor, "rb")
        duplicate_descriptor = None
        with reader:
            yield reader
    finally:
        if duplicate_descriptor is not None:
            try:
                os.close(duplicate_descriptor)
            except OSError:
                pass


def sha256_descriptor(
    descriptor: int, *, expected_stat: os.stat_result
) -> tuple[str, int, os.stat_result]:
    """Hash one already-open regular file without reopening its pathname."""

    try:
        before = _descriptor_fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not _same_identity(
            expected_stat, before
        ):
            raise _SourceChangedDuringScan
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, READ_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
        after = _descriptor_fstat(descriptor)
    except (_DescriptorOperationsUnsupported, _SourceChangedDuringScan):
        raise
    except OSError:
        raise _SourceFileUnreadable("source file could not be read") from None
    if (
        not _same_identity(expected_stat, after)
        or not _same_identity(before, after)
        or total != after.st_size
    ):
        raise _SourceChangedDuringScan
    return digest.hexdigest(), total, after


def walk_source(
    rule: SourceRule,
    on_file: Callable[[PurePosixPath, int, os.stat_result], None],
) -> list[WarningRecord]:
    """Walk a declared source through directory descriptors without following links."""

    warnings: list[WarningRecord] = []
    root_relative = PurePosixPath(".")
    directory_flags = _descriptor_flags(directory=True)
    file_flags = _descriptor_flags(directory=False)
    if (
        directory_flags is None
        or file_flags is None
        or not _descriptor_operations_supported()
    ):
        return [
            _warning(
                rule,
                root_relative,
                "unsafe_source_entry",
                "required no-follow descriptor operations are unavailable",
            )
        ]

    try:
        root_lstat = _descriptor_lstat(rule.resolved_path)
    except FileNotFoundError:
        return [
            _warning(
                rule,
                root_relative,
                "missing_root",
                "declared source root does not exist on this machine",
            )
        ]
    except (_DescriptorOperationsUnsupported, OSError):
        return [
            _warning(
                rule,
                root_relative,
                "unsafe_source_entry",
                "declared source root could not be inspected safely",
            )
        ]
    if stat.S_ISLNK(root_lstat.st_mode) or not stat.S_ISDIR(root_lstat.st_mode):
        return [
            _warning(
                rule,
                root_relative,
                "unsafe_source_entry",
                "declared source root is not a non-symlink directory",
            )
        ]

    try:
        root_descriptor = _descriptor_open(rule.resolved_path, directory_flags)
    except (_DescriptorOperationsUnsupported, OSError):
        return [
            _warning(
                rule,
                root_relative,
                "unsafe_source_entry",
                "declared source root could not be opened safely",
            )
        ]

    def traverse(parent_descriptor: int, logical_parent: PurePosixPath) -> None:
        try:
            with _descriptor_scandir(parent_descriptor) as iterator:
                entries = sorted(iterator, key=lambda candidate: candidate.name)
        except _DescriptorOperationsUnsupported:
            warnings.append(
                _warning(
                    rule,
                    logical_parent,
                    "unsafe_source_entry",
                    "directory descriptor traversal is unsupported",
                )
            )
            return
        except OSError:
            warnings.append(
                _warning(
                    rule,
                    logical_parent,
                    "unreadable_directory",
                    "source directory could not be read",
                )
            )
            return

        for entry in entries:
            name = entry.name
            if not isinstance(name, str) or name in {"", ".", ".."} or "/" in name:
                warnings.append(
                    _warning(
                        rule,
                        logical_parent,
                        "unsafe_source_entry",
                        UNSAFE_LOGICAL_NAME_DETAIL,
                    )
                )
                continue
            relative_path = logical_parent / name
            try:
                discovery_stat = _descriptor_entry_stat(entry)
            except (_DescriptorOperationsUnsupported, OSError):
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "unsafe_source_entry",
                        "source entry could not be inspected safely",
                    )
                )
                continue
            if not _is_safe_logical_path(
                relative_path.as_posix(), allow_root=False
            ):
                warnings.append(
                    _warning(
                        rule,
                        logical_parent,
                        "unsafe_source_entry",
                        UNSAFE_LOGICAL_NAME_DETAIL,
                    )
                )
                continue
            if stat.S_ISLNK(discovery_stat.st_mode):
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "symlink",
                        "symbolic links are not followed",
                    )
                )
                continue
            if name in rule.exclude_names:
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "excluded_name",
                        "entry name is excluded by the source rule",
                    )
                )
                continue
            if stat.S_ISDIR(discovery_stat.st_mode):
                try:
                    child_descriptor = _descriptor_open(
                        name,
                        directory_flags,
                        dir_fd=parent_descriptor,
                    )
                except (_DescriptorOperationsUnsupported, OSError):
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "unsafe_source_entry",
                            "source directory failed descriptor safety checks",
                        )
                    )
                    continue
                try:
                    try:
                        child_stat = _descriptor_fstat(child_descriptor)
                    except (_DescriptorOperationsUnsupported, OSError):
                        warnings.append(
                            _warning(
                                rule,
                                relative_path,
                                "unsafe_source_entry",
                                "source directory failed descriptor safety checks",
                            )
                        )
                        continue
                    if not stat.S_ISDIR(child_stat.st_mode) or not _same_identity(
                        discovery_stat, child_stat
                    ):
                        warnings.append(
                            _warning(
                                rule,
                                relative_path,
                                "unsafe_source_entry",
                                "source directory changed before traversal",
                            )
                        )
                        continue
                    traverse(child_descriptor, relative_path)
                    try:
                        final_entry_stat = _descriptor_stat_at(
                            name, parent_descriptor
                        )
                    except (_DescriptorOperationsUnsupported, OSError):
                        final_entry_stat = None
                    if final_entry_stat is None or not _same_identity(
                        discovery_stat, final_entry_stat
                    ):
                        warnings.append(
                            _warning(
                                rule,
                                relative_path,
                                "unsafe_source_entry",
                                "source directory changed during traversal",
                            )
                        )
                finally:
                    os.close(child_descriptor)
                continue
            if not stat.S_ISREG(discovery_stat.st_mode):
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "unsafe_source_entry",
                        "non-regular source entries are not scanned",
                    )
                )
                continue
            extension = relative_path.suffix.lower()
            if extension not in rule.include_extensions:
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "unsupported_extension",
                        f"extension {extension or '[none]'} is not enabled for this root",
                    )
                )
                continue
            try:
                file_descriptor = _descriptor_open(
                    name,
                    file_flags,
                    dir_fd=parent_descriptor,
                )
            except PermissionError:
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "unreadable_file",
                        "source file could not be opened for reading",
                    )
                )
                continue
            except (_DescriptorOperationsUnsupported, OSError):
                warnings.append(
                    _warning(
                        rule,
                        relative_path,
                        "unsafe_source_entry",
                        "source file failed descriptor safety checks",
                    )
                )
                continue
            try:
                try:
                    opened_stat = _descriptor_fstat(file_descriptor)
                except (_DescriptorOperationsUnsupported, OSError):
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "unsafe_source_entry",
                            "source file failed descriptor safety checks",
                        )
                    )
                    continue
                if not stat.S_ISREG(opened_stat.st_mode) or not _same_identity(
                    discovery_stat, opened_stat
                ):
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "unsafe_source_entry",
                            "source file changed before it was opened",
                        )
                    )
                    continue
                try:
                    on_file(relative_path, file_descriptor, discovery_stat)
                    final_stat = _descriptor_fstat(file_descriptor)
                    try:
                        final_entry_stat = _descriptor_stat_at(
                            name, parent_descriptor
                        )
                    except OSError:
                        final_entry_stat = None
                    if (
                        not _same_identity(discovery_stat, final_stat)
                        or final_entry_stat is None
                        or not _same_identity(discovery_stat, final_entry_stat)
                    ):
                        raise _SourceChangedDuringScan
                except _SourceChangedDuringScan:
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "source_changed_during_scan",
                            "source file changed during the scan",
                        )
                    )
                except _DescriptorOperationsUnsupported:
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "unsafe_source_entry",
                            "source file descriptor operations are unsupported",
                        )
                    )
                except _SourceFileUnreadable:
                    warnings.append(
                        _warning(
                            rule,
                            relative_path,
                            "unreadable_file",
                            "source file could not be read",
                        )
                    )
            finally:
                os.close(file_descriptor)

    try:
        try:
            opened_root_stat = _descriptor_fstat(root_descriptor)
        except (_DescriptorOperationsUnsupported, OSError):
            warnings.append(
                _warning(
                    rule,
                    root_relative,
                    "unsafe_source_entry",
                    "declared source root failed descriptor safety checks",
                )
            )
        else:
            if not stat.S_ISDIR(opened_root_stat.st_mode) or not _same_identity(
                root_lstat, opened_root_stat
            ):
                warnings.append(
                    _warning(
                        rule,
                        root_relative,
                        "unsafe_source_entry",
                        "declared source root changed before traversal",
                    )
                )
            else:
                traverse(root_descriptor, PurePosixPath())
                try:
                    final_root_descriptor_stat = _descriptor_fstat(root_descriptor)
                    final_root_path_stat = _descriptor_lstat(rule.resolved_path)
                except (_DescriptorOperationsUnsupported, OSError):
                    final_root_descriptor_stat = None
                    final_root_path_stat = None
                if (
                    final_root_descriptor_stat is None
                    or final_root_path_stat is None
                    or not stat.S_ISDIR(final_root_descriptor_stat.st_mode)
                    or not stat.S_ISDIR(final_root_path_stat.st_mode)
                    or stat.S_ISLNK(final_root_path_stat.st_mode)
                    or not _same_identity(root_lstat, final_root_descriptor_stat)
                    or not _same_identity(root_lstat, final_root_path_stat)
                ):
                    warnings.append(
                        _warning(
                            rule,
                            root_relative,
                            "unsafe_source_entry",
                            "declared source root changed during traversal",
                        )
                    )
    finally:
        os.close(root_descriptor)
    warnings.sort(key=lambda warning: (warning.relative_path, warning.code))
    return warnings


def _image_metadata(descriptor: int) -> tuple[str, int, int]:
    from PIL import Image

    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        with _duplicate_binary_reader(descriptor) as source:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(source) as image:
                    observed_media_type = IMAGE_FORMAT_MEDIA_TYPES.get(
                        str(image.format)
                    )
                    if observed_media_type is None:
                        raise _MetadataUnreadable
                    width, height = image.size
    except Exception:
        raise _MetadataUnreadable from None
    return observed_media_type, int(width), int(height)


def _pdf_metadata(descriptor: int) -> int:
    from pypdf import PdfReader

    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        with _duplicate_binary_reader(descriptor) as source:
            with _isolated_library_logger("pypdf"):
                with redirect_stderr(io.StringIO()):
                    return len(PdfReader(source, strict=True).pages)
    except Exception:
        raise _MetadataUnreadable from None


def scan_source(
    rule: SourceRule,
) -> tuple[list[SourceAliasRecord], list[WarningRecord]]:
    """Hash and describe every eligible alias in one declared source root."""

    aliases: list[SourceAliasRecord] = []
    metadata_warnings: list[WarningRecord] = []

    def scan_file(
        relative_path: PurePosixPath,
        descriptor: int,
        expected_stat: os.stat_result,
    ) -> None:
        digest, size_bytes, _ = sha256_descriptor(
            descriptor, expected_stat=expected_stat
        )
        extension = relative_path.suffix.lower()
        media_type = MEDIA_TYPES[extension]
        image_width: int | None = None
        image_height: int | None = None
        pdf_page_count: int | None = None
        metadata_status = "not_applicable"
        pending_warning: WarningRecord | None = None
        if extension in {".png", ".webp", ".jpg", ".jpeg"}:
            try:
                observed_type, image_width, image_height = _image_metadata(descriptor)
            except _MetadataUnreadable:
                metadata_status = "unreadable"
                pending_warning = _warning(
                    rule,
                    relative_path,
                    "metadata_unreadable",
                    "image metadata could not be read",
                )
            else:
                metadata_status = "ok"
                if observed_type != media_type:
                    media_type = observed_type
                    pending_warning = _warning(
                        rule,
                        relative_path,
                        "media_type_mismatch",
                        "observed image media type differs from the filename extension",
                    )
        elif extension == ".pdf":
            try:
                pdf_page_count = _pdf_metadata(descriptor)
            except _MetadataUnreadable:
                metadata_status = "unreadable"
                pending_warning = _warning(
                    rule,
                    relative_path,
                    "metadata_unreadable",
                    "PDF metadata could not be read",
                )
            else:
                metadata_status = "ok"
        try:
            final_stat = _descriptor_fstat(descriptor)
        except OSError:
            raise _SourceFileUnreadable("source file could not be read") from None
        if not _same_identity(expected_stat, final_stat):
            raise _SourceChangedDuringScan
        aliases.append(
            SourceAliasRecord(
                root_id=rule.root_id,
                relative_path=relative_path.as_posix(),
                source_thread_id=rule.source_thread_id,
                source_group=rule.source_group,
                sha256=digest,
                size_bytes=size_bytes,
                media_type=media_type,
                image_width=image_width,
                image_height=image_height,
                pdf_page_count=pdf_page_count,
                metadata_status=metadata_status,
            )
        )
        if pending_warning is not None:
            metadata_warnings.append(pending_warning)

    walk_warnings = walk_source(rule, scan_file)
    reject_entire_root = any(
        warning.relative_path == "."
        and warning.code == "unsafe_source_entry"
        and warning.detail != UNSAFE_LOGICAL_NAME_DETAIL
        for warning in walk_warnings
    )
    rejected_paths = {
        warning.relative_path
        for warning in walk_warnings
        if warning.code in {"source_changed_during_scan", "unsafe_source_entry"}
        and warning.detail != UNSAFE_LOGICAL_NAME_DETAIL
    }
    rejected_prefixes = tuple(path + "/" for path in rejected_paths)
    if reject_entire_root:
        aliases = []
        metadata_warnings = []
    else:
        aliases = [
            alias
            for alias in aliases
            if alias.relative_path not in rejected_paths
            and not alias.relative_path.startswith(rejected_prefixes)
        ]
        metadata_warnings = [
            warning
            for warning in metadata_warnings
            if warning.relative_path not in rejected_paths
            and not warning.relative_path.startswith(rejected_prefixes)
        ]
    aliases.sort(key=lambda alias: (alias.relative_path, alias.sha256))
    warnings = [*walk_warnings, *metadata_warnings]
    warnings.sort(key=lambda warning: (warning.relative_path, warning.code))
    return aliases, warnings


def _migration_asset_id(digest: str) -> str:
    return "mig_sha256_" + digest


def _duplicate_group_id(digest: str) -> str:
    return "dup_sha256_" + digest


def _normalized_basename(relative_path: str) -> str:
    return unicodedata.normalize(
        "NFC", PurePosixPath(relative_path).name
    ).casefold()


def _normalized_stem(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    stem_path = path.with_suffix("")
    return unicodedata.normalize("NFC", stem_path.as_posix()).casefold()


def _structural_evidence(relative_path: str) -> dict[str, bool]:
    path = PurePosixPath(relative_path)
    basename = path.name
    components = frozenset(path.parts[:-1])
    return {
        "fact": basename in FACT_BASENAMES,
        "propositions": basename in PROPOSITION_BASENAMES,
        "content_lock": basename in CONTENT_LOCK_BASENAMES,
        "four_cards": basename in FOUR_CARD_BASENAMES
        or bool(components & FOUR_CARD_COMPONENTS),
        "qa": bool(components & QA_COMPONENTS),
        "print_pdf": path.suffix == ".pdf" and bool(components & PRINT_COMPONENTS),
        "manifest": basename in MANIFEST_BASENAMES,
    }


def _alias_payload(alias: SourceAliasRecord) -> dict[str, object]:
    return {
        "root_id": alias.root_id,
        "relative_path": alias.relative_path,
        "source_thread_id": alias.source_thread_id,
        "source_group": alias.source_group,
        "media_type": alias.media_type,
        "image_width": alias.image_width,
        "image_height": alias.image_height,
        "pdf_page_count": alias.pdf_page_count,
        "metadata_status": alias.metadata_status,
    }


def _is_safe_logical_path(value: object, *, allow_root: bool) -> bool:
    if not isinstance(value, str) or "\x00" in value or "\\" in value:
        return False
    if allow_root and value == ".":
        return True
    if not value or value == ".":
        return False
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    return (
        not posix_path.is_absolute()
        and not windows_path.is_absolute()
        and not windows_path.drive
        and bool(posix_path.parts)
        and all(part not in {"", ".", ".."} for part in posix_path.parts)
        and posix_path.as_posix() == value
    )


def _is_sanitized_warning_field(code: object, detail: object) -> bool:
    return (
        isinstance(code, str)
        and code in VALID_WARNING_CODES
        and isinstance(detail, str)
        and bool(detail)
        and not any(character in detail for character in ("/", "\\", "\x00", "\r", "\n"))
    )


def _register_identity(
    identities: dict[str, object], identity: str, semantic_value: object
) -> None:
    prior = identities.get(identity)
    if prior is not None and prior != semantic_value:
        raise ValueError("identity_collision")
    identities[identity] = semantic_value


def build_inventory(
    config: SourceConfig,
    alias_records: Sequence[SourceAliasRecord],
    warnings: Sequence[WarningRecord],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Aggregate scanned aliases into deterministic, byte-identified objects.

    This pure aggregation stage deliberately does not assign the semantic
    snapshot ``run_id`` or write any files; those are publication concerns of
    the later atomic-output stage.
    """

    rules = {rule.root_id: rule for rule in config.rules}
    if len(rules) != len(config.rules):
        raise ValueError("identity_collision")

    for warning in config.warnings:
        if (
            not isinstance(warning.root_id, str)
            or warning.root_id not in rules
            or not _is_sanitized_warning_field(warning.code, warning.detail)
        ):
            raise ValueError("invalid_warning_record")
    for warning in warnings:
        if (
            not isinstance(warning.root_id, str)
            or warning.root_id not in rules
            or not _is_safe_logical_path(warning.relative_path, allow_root=True)
            or not _is_sanitized_warning_field(warning.code, warning.detail)
        ):
            raise ValueError("invalid_warning_record")

    aliases_by_digest: dict[str, list[SourceAliasRecord]] = {}
    alias_locations: dict[tuple[str, str], SourceAliasRecord] = {}
    for alias in alias_records:
        rule = rules.get(alias.root_id) if isinstance(alias.root_id, str) else None
        if (
            rule is None
            or not isinstance(alias.source_group, str)
            or alias.source_group != rule.source_group
            or alias.source_thread_id != rule.source_thread_id
            or not _is_safe_logical_path(alias.relative_path, allow_root=False)
            or not isinstance(alias.sha256, str)
            or not SHA256_PATTERN.fullmatch(alias.sha256)
            or not isinstance(alias.size_bytes, int)
            or isinstance(alias.size_bytes, bool)
            or alias.size_bytes < 0
        ):
            raise ValueError("invalid_alias_record")
        location = (alias.root_id, alias.relative_path)
        prior_alias = alias_locations.get(location)
        if prior_alias is not None:
            raise ValueError("identity_collision")
        alias_locations[location] = alias
        aliases_by_digest.setdefault(alias.sha256, []).append(alias)

    identity_registry: dict[str, object] = {}
    assets: list[dict[str, object]] = []
    duplicate_groups: list[dict[str, object]] = []
    asset_id_by_digest: dict[str, str] = {}

    for digest in sorted(aliases_by_digest):
        aliases = sorted(
            aliases_by_digest[digest],
            key=lambda item: (item.root_id, item.relative_path),
        )
        sizes = {alias.size_bytes for alias in aliases}
        if len(sizes) != 1:
            raise ValueError("identity_collision")
        asset_id = _migration_asset_id(digest)
        _register_identity(identity_registry, asset_id, ("asset", digest))
        asset_id_by_digest[digest] = asset_id

        evidence = {
            "fact": False,
            "propositions": False,
            "content_lock": False,
            "four_cards": False,
            "qa": False,
            "print_pdf": False,
            "manifest": False,
        }
        for alias in aliases:
            alias_evidence = _structural_evidence(alias.relative_path)
            for field in evidence:
                evidence[field] = evidence[field] or alias_evidence[field]

        duplicate_group: str | None = None
        if len(aliases) >= 2:
            duplicate_group = _duplicate_group_id(digest)
            _register_identity(
                identity_registry, duplicate_group, ("duplicate", digest)
            )
            duplicate_groups.append(
                {
                    "duplicate_group": duplicate_group,
                    "sha256": digest,
                    "migration_asset_id": asset_id,
                    "alias_count": len(aliases),
                    "aliases": [
                        {
                            "root_id": alias.root_id,
                            "relative_path": alias.relative_path,
                        }
                        for alias in aliases
                    ],
                }
            )

        grades = sorted(
            {rules[alias.root_id].migration_grade for alias in aliases},
            key=GRADE_ORDER.__getitem__,
        )
        decisions = sorted(
            {rules[alias.root_id].decision for alias in aliases}
        )
        assets.append(
            {
                "migration_asset_id": asset_id,
                "sha256": digest,
                "size_bytes": sizes.pop(),
                "source_aliases": [_alias_payload(alias) for alias in aliases],
                "object_name": None,
                "classification": None,
                "rights_status": "review_required",
                "structural_evidence": evidence,
                "migration_grades": grades,
                "media_types": sorted({alias.media_type for alias in aliases}),
                "duplicate_group": duplicate_group,
                "target_package_id": None,
                "decisions": decisions,
            }
        )

    same_name_members: dict[str, set[str]] = {}
    for alias in alias_locations.values():
        same_name_members.setdefault(
            _normalized_basename(alias.relative_path), set()
        ).add(alias.sha256)
    same_name_candidate_groups: list[dict[str, object]] = []
    for normalized_basename, digests in same_name_members.items():
        if len(digests) < 2:
            continue
        group_id = "name_sha256_" + hashlib.sha256(
            normalized_basename.encode("utf-8")
        ).hexdigest()
        _register_identity(
            identity_registry,
            group_id,
            ("same_name", normalized_basename),
        )
        same_name_candidate_groups.append(
            {
                "group_id": group_id,
                "normalized_basename": normalized_basename,
                "status": "review_required",
                "members": sorted(asset_id_by_digest[digest] for digest in digests),
            }
        )
    same_name_candidate_groups.sort(
        key=lambda group: (group["normalized_basename"], group["group_id"])
    )

    derivative_members: dict[
        tuple[str, str], dict[str, set[tuple[str, str]]]
    ] = {}
    for alias in alias_locations.values():
        extension = PurePosixPath(alias.relative_path).suffix.casefold()
        if extension not in {".png", ".webp"}:
            continue
        role = (
            "source_candidate" if extension == ".png" else "derivative_candidate"
        )
        key = (alias.source_group, _normalized_stem(alias.relative_path))
        derivative_members.setdefault(key, {}).setdefault(alias.sha256, set()).add(
            (extension, role)
        )

    derivative_with_order: list[tuple[str, str, dict[str, object]]] = []
    for (source_group, normalized_stem), members_by_digest in derivative_members.items():
        canonical_members = sorted(
            (digest, *next(iter(extension_roles)))
            for digest, extension_roles in members_by_digest.items()
            if len(extension_roles) == 1
        )
        extensions = {extension for _digest, extension, _role in canonical_members}
        if len(canonical_members) < 2 or extensions != {".png", ".webp"}:
            continue
        identity_payload = {
            "source_group": source_group,
            "normalized_stem": normalized_stem,
            "members": [
                {"sha256": digest, "extension": extension, "role": role}
                for digest, extension, role in canonical_members
            ],
        }
        group_id = "deriv_sha256_" + hashlib.sha256(
            _canonical_json_bytes(identity_payload)
        ).hexdigest()
        _register_identity(
            identity_registry,
            group_id,
            (
                "derivative",
                source_group,
                normalized_stem,
                tuple(canonical_members),
            ),
        )
        display_members = sorted(
            canonical_members,
            key=lambda member: (
                0 if member[2] == "source_candidate" else 1,
                asset_id_by_digest[member[0]],
                member[1],
            ),
        )
        derivative_with_order.append(
            (
                source_group,
                normalized_stem,
                {
                    "group_id": group_id,
                    "status": "review_required",
                    "normalized_stem": normalized_stem,
                    "members": [
                        {
                            "migration_asset_id": asset_id_by_digest[digest],
                            "role": role,
                            "extension": extension,
                        }
                        for digest, extension, role in display_members
                    ],
                },
            )
        )
    derivative_with_order.sort(
        key=lambda item: (item[0], item[1], item[2]["group_id"])
    )
    derivative_candidate_groups = [item[2] for item in derivative_with_order]

    duplicate_groups.sort(key=lambda group: group["duplicate_group"])
    assets.sort(
        key=lambda asset: (asset["sha256"], asset["migration_asset_id"])
    )
    missing_roots = {
        warning.root_id
        for warning in config.warnings
        if warning.code == "missing_root"
    }
    scan_roots = [
        {
            "root_id": rule.root_id,
            "locator": {
                "base": rule.locator_base,
                "relative": rule.locator_relative,
            },
            "status": "missing" if rule.root_id in missing_roots else "scanned",
        }
        for rule in sorted(config.rules, key=lambda item: item.root_id)
    ]
    total_source_bytes = sum(alias.size_bytes for alias in alias_locations.values())
    unique_content_bytes = sum(asset["size_bytes"] for asset in assets)
    return {
        "schema": "cognitive-card-migration-inventory-v1",
        "generated_at": generated_at,
        "config_digest": config.config_digest,
        "scan_roots": scan_roots,
        "metadata_readers": metadata_reader_versions(),
        "summary": {
            "source_alias_count": len(alias_locations),
            "content_object_count": len(assets),
            "duplicate_group_count": len(duplicate_groups),
            "same_name_candidate_group_count": len(same_name_candidate_groups),
            "derivative_candidate_group_count": len(derivative_candidate_groups),
            "warning_count": len(config.warnings) + len(warnings),
            "total_source_bytes": total_source_bytes,
            "unique_content_bytes": unique_content_bytes,
        },
        "assets": assets,
        "duplicate_groups": duplicate_groups,
        "same_name_candidate_groups": same_name_candidate_groups,
        "derivative_candidate_groups": derivative_candidate_groups,
    }


def deterministic_json_text(value: object) -> str:
    """Serialize one public JSON document with the repository-wide format."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"


def _warning_payloads(
    config: SourceConfig, scan_warnings: Sequence[WarningRecord]
) -> list[dict[str, str]]:
    values = [
        {
            "root_id": warning.root_id,
            "relative_path": ".",
            "code": warning.code,
            "detail": warning.detail,
        }
        for warning in config.warnings
    ]
    values.extend(
        {
            "root_id": warning.root_id,
            "relative_path": warning.relative_path,
            "code": warning.code,
            "detail": warning.detail,
        }
        for warning in scan_warnings
    )
    return values


def _markdown_escape(value: object) -> str:
    text = str(value)
    rendered: list[str] = []
    markdown_characters = frozenset("\\`*_{}[]<>()|")
    for character in text:
        codepoint = ord(character)
        category = unicodedata.category(character)
        if character == "\n":
            rendered.append("\\\\n")
        elif character == "\r":
            rendered.append("\\\\r")
        elif character == "\t":
            rendered.append("\\\\t")
        elif category.startswith("C") or category in {"Zl", "Zp"}:
            escape = "u" if codepoint <= 0xFFFF else "U"
            width = 4 if codepoint <= 0xFFFF else 8
            rendered.append(f"\\{escape}{codepoint:0{width}x}")
        elif character in markdown_characters:
            rendered.append("\\" + character)
        else:
            rendered.append(character)
    return "".join(rendered)


def _markdown_report(
    inventory: Mapping[str, Any],
    warnings_document: Mapping[str, Any],
) -> str:
    summary = inventory["summary"]
    lines = [
        "---",
        'schema: "cognitive-card-migration-duplicate-report-v1"',
        f'generated_at: "{inventory["generated_at"]}"',
        f'run_id: "{inventory["run_id"]}"',
        f'snapshot_digest: "{inventory["snapshot_digest"]}"',
        "---",
        "",
        "# Cognitive Card asset inventory report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for field in (
        "source_alias_count",
        "content_object_count",
        "duplicate_group_count",
        "same_name_candidate_group_count",
        "derivative_candidate_group_count",
        "warning_count",
        "total_source_bytes",
        "unique_content_bytes",
    ):
        lines.append(f"| {field} | {summary[field]} |")

    lines.extend(
        [
            "",
            "## Aliases",
            "",
            "| Asset | Root | Relative path | Bytes |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for asset in inventory["assets"]:
        for alias in asset["source_aliases"]:
            lines.append(
                "| "
                + " | ".join(
                    (
                        _markdown_escape(asset["migration_asset_id"]),
                        _markdown_escape(alias["root_id"]),
                        _markdown_escape(alias["relative_path"]),
                        str(asset["size_bytes"]),
                    )
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Duplicate groups",
            "",
            "| Group | Alias count | Aliases |",
            "| --- | ---: | --- |",
        ]
    )
    for group in inventory["duplicate_groups"]:
        aliases = ", ".join(
            f'{_markdown_escape(alias["root_id"])}:{_markdown_escape(alias["relative_path"])}'
            for alias in group["aliases"]
        )
        lines.append(
            f'| {_markdown_escape(group["duplicate_group"])} | {group["alias_count"]} | {aliases} |'
        )

    lines.extend(
        [
            "",
            "## Same-name, different-digest candidates",
            "",
            "| Group | Normalized basename | Members |",
            "| --- | --- | --- |",
        ]
    )
    for group in inventory["same_name_candidate_groups"]:
        members = ", ".join(_markdown_escape(item) for item in group["members"])
        lines.append(
            f'| {_markdown_escape(group["group_id"])} | '
            f'{_markdown_escape(group["normalized_basename"])} | {members} |'
        )

    lines.extend(
        [
            "",
            "## Warnings",
            "",
            "| Root | Relative path | Reason | Detail |",
            "| --- | --- | --- | --- |",
        ]
    )
    for warning in warnings_document["warnings"]:
        lines.append(
            "| "
            + " | ".join(
                _markdown_escape(warning[field])
                for field in ("root_id", "relative_path", "code", "detail")
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _semantic_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in inventory.items()
        if key not in {"generated_at", "run_id", "snapshot_digest"}
    }


def build_snapshot_documents(
    config: SourceConfig,
    alias_records: Sequence[SourceAliasRecord],
    scan_warnings: Sequence[WarningRecord],
    *,
    generated_at: str,
) -> dict[str, str]:
    """Build the three mutually bound snapshot documents in memory."""

    _validate_generated_at(generated_at)
    inventory = build_inventory(
        config,
        alias_records,
        scan_warnings,
        generated_at=generated_at,
    )
    warning_values = _warning_payloads(config, scan_warnings)
    semantic_payload = {
        "inventory": _semantic_inventory(inventory),
        "warnings": warning_values,
    }
    snapshot_hex = hashlib.sha256(_canonical_json_bytes(semantic_payload)).hexdigest()
    run_id = "inv_sha256_" + snapshot_hex
    snapshot_digest = "sha256:" + snapshot_hex
    inventory["run_id"] = run_id
    inventory["snapshot_digest"] = snapshot_digest
    warnings_document: dict[str, Any] = {
        "schema": "cognitive-card-migration-warnings-v1",
        "generated_at": generated_at,
        "run_id": run_id,
        "snapshot_digest": snapshot_digest,
        "warnings": warning_values,
    }
    return {
        "inventory.json": deterministic_json_text(inventory),
        "scan-warnings.json": deterministic_json_text(warnings_document),
        "duplicate-report.md": _markdown_report(inventory, warnings_document),
    }


def _absolute_normalized(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(os.fspath(path))))


def _contains_path(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_output_ancestors(output_root: Path) -> None:
    output_stat = _lstat_existing_prefixes(output_root, "output root")
    if output_stat is not None and not stat.S_ISDIR(output_stat.st_mode):
        raise ConfigError("output root must name a non-symlink directory")


def _validated_protected_file(
    path: Path, label: str
) -> tuple[Path, os.stat_result]:
    normalized = _absolute_normalized(path)
    path_stat = _lstat_existing_prefixes(normalized, label)
    if path_stat is None or not stat.S_ISREG(path_stat.st_mode):
        raise ConfigError(f"{label} must name a non-symlink regular file")
    try:
        resolved = normalized.resolve(strict=True)
    except OSError:
        raise ConfigError(f"{label} cannot be validated safely") from None
    return resolved, path_stat


def validate_publication_paths(
    config: SourceConfig,
    *,
    config_path: Path,
    roots_path: Path,
    output_root: Path,
) -> Path:
    """Validate every destination boundary before publication can write."""

    normalized_config, config_stat = _validated_protected_file(
        config_path, "source config"
    )
    normalized_roots, roots_stat = _validated_protected_file(
        roots_path, "root map"
    )
    normalized_output = _absolute_normalized(output_root)
    _validate_output_ancestors(normalized_output)
    try:
        resolved_output = normalized_output.resolve(strict=False)
    except OSError:
        raise ConfigError("output root cannot be validated safely") from None
    if (
        normalized_config == normalized_roots
        or resolved_output == normalized_config
        or resolved_output == normalized_roots
        or (config_stat.st_dev, config_stat.st_ino)
        == (roots_stat.st_dev, roots_stat.st_ino)
    ):
        raise ConfigError("source config and root map must be distinct")
    for protected in (normalized_config, normalized_roots):
        if _contains_path(protected, resolved_output) or _contains_path(
            resolved_output, protected
        ):
            raise ConfigError(
                "output root and configuration files must not contain each other"
            )
    for rule in config.rules:
        source = _absolute_normalized(rule.resolved_path)
        if _contains_path(source, resolved_output) or _contains_path(
            resolved_output, source
        ):
            raise ConfigError("output root and source roots must not contain each other")
    return resolved_output


def _without_generated_at_json(text: str) -> object:
    value = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    if not isinstance(value, dict):
        raise ValueError
    generated_at = value.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValueError
    _validate_generated_at(generated_at)
    del value["generated_at"]
    return value


def _without_generated_at_markdown(text: str) -> str:
    pattern = re.compile(r'^generated_at: "([^"\r\n]+)"$', re.MULTILINE)
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise ValueError
    _validate_generated_at(matches[0])
    return pattern.sub('generated_at: "<ignored>"', text)


def _verify_shared_identity(documents: Mapping[str, str]) -> tuple[str, str]:
    try:
        inventory = json.loads(documents["inventory.json"])
        warnings_document = json.loads(documents["scan-warnings.json"])
        run_id = inventory["run_id"]
        digest = inventory["snapshot_digest"]
        if (
            warnings_document["run_id"] != run_id
            or warnings_document["snapshot_digest"] != digest
            or f'run_id: "{run_id}"' not in documents["duplicate-report.md"]
            or f'snapshot_digest: "{digest}"' not in documents["duplicate-report.md"]
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ConfigError("snapshot documents do not share one identity") from None
    return str(run_id), str(digest)


def _rename_staging_to_snapshot(
    staging: str,
    snapshot: str,
    *,
    output_fd: int,
    snapshots_fd: int,
) -> None:
    _rename_directory_noreplace(
        output_fd,
        staging,
        snapshots_fd,
        snapshot,
    )


def _rename_directory_noreplace(
    source_dir_fd: int,
    source_name: str,
    destination_dir_fd: int,
    destination_name: str,
) -> None:
    """Atomically rename one directory entry without replacing a destination."""

    for name in (source_name, destination_name):
        if not name or "/" in name or "\x00" in name or name in {".", ".."}:
            raise ConfigError("atomic rename name is unsafe")
    try:
        library = ctypes.CDLL(None, use_errno=True)
    except OSError:
        raise ConfigError("atomic no-replace rename is unavailable") from None

    if sys.platform == "darwin":
        function = getattr(library, "renameatx_np", None)
        flags = 0x00000004  # RENAME_EXCL from Darwin sys/stdio.h.
    elif sys.platform.startswith("linux"):
        function = getattr(library, "renameat2", None)
        flags = 0x00000001  # RENAME_NOREPLACE from linux/fs.h.
    else:
        function = None
        flags = 0
    if function is None:
        raise ConfigError("atomic no-replace rename is unavailable")

    function.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    function.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = function(
        source_dir_fd,
        os.fsencode(source_name),
        destination_dir_fd,
        os.fsencode(destination_name),
        flags,
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise FileExistsError(errno.EEXIST, "destination already exists")
    unsupported_errors = {
        errno.ENOSYS,
        errno.EINVAL,
        getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
        errno.EOPNOTSUPP,
    }
    if error_number in unsupported_errors:
        raise ConfigError("atomic no-replace rename is unavailable")
    raise OSError(error_number, "atomic no-replace rename failed")


def _directory_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _directory_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _stable_file_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


@dataclass
class _DirectoryLink:
    parent_fd: int
    name: str
    child_fd: int


class _TrustedDirectoryChain:
    def __init__(self, parent_path: Path) -> None:
        if not parent_path.is_absolute():
            raise ConfigError("publication parent must be absolute")
        self._fds: list[int] = []
        self._links: list[_DirectoryLink] = []
        flags = _directory_open_flags()
        try:
            current = os.open(parent_path.anchor, flags)
            self._fds.append(current)
            for component in parent_path.parts[1:]:
                child = os.open(component, flags, dir_fd=current)
                self._fds.append(child)
                child_stat = os.fstat(child)
                entry_stat = os.stat(
                    component, dir_fd=current, follow_symlinks=False
                )
                if (
                    not stat.S_ISDIR(child_stat.st_mode)
                    or not stat.S_ISDIR(entry_stat.st_mode)
                    or _directory_identity(child_stat)
                    != _directory_identity(entry_stat)
                ):
                    raise ConfigError("publication directory identity changed")
                self._links.append(_DirectoryLink(current, component, child))
                current = child
        except (OSError, ConfigError):
            self.close()
            raise ConfigError("publication directory chain is unsafe") from None

    @property
    def current_fd(self) -> int:
        return self._fds[-1]

    def verify(self) -> None:
        try:
            for link in self._links:
                child_stat = os.fstat(link.child_fd)
                entry_stat = os.stat(
                    link.name,
                    dir_fd=link.parent_fd,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(entry_stat.st_mode)
                    or _directory_identity(child_stat)
                    != _directory_identity(entry_stat)
                ):
                    raise ConfigError("publication directory identity changed")
        except OSError:
            raise ConfigError("publication directory identity changed") from None

    def attach(self, name: str, *, create: bool) -> int:
        if not name or "/" in name or name in {".", ".."}:
            raise ConfigError("publication directory name is unsafe")
        self.verify()
        parent_fd = self.current_fd
        if create:
            try:
                os.mkdir(name, 0o755, dir_fd=parent_fd)
            except FileExistsError:
                pass
            except OSError:
                raise ConfigError("publication directory could not be created") from None
        self.verify()
        child: int | None = None
        try:
            child = os.open(name, _directory_open_flags(), dir_fd=parent_fd)
            child_stat = os.fstat(child)
            entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError:
            if child is not None:
                os.close(child)
            raise ConfigError("publication directory is unsafe") from None
        if (
            not stat.S_ISDIR(child_stat.st_mode)
            or not stat.S_ISDIR(entry_stat.st_mode)
            or _directory_identity(child_stat) != _directory_identity(entry_stat)
        ):
            os.close(child)
            raise ConfigError("publication directory identity changed")
        self._fds.append(child)
        self._links.append(_DirectoryLink(parent_fd, name, child))
        self.verify()
        return child

    def close(self) -> None:
        for descriptor in reversed(self._fds):
            try:
                os.close(descriptor)
            except OSError:
                pass
        self._fds = []
        self._links = []

    def __enter__(self) -> "_TrustedDirectoryChain":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


@dataclass
class _PublicationDirectories:
    chain: _TrustedDirectoryChain
    output_fd: int
    snapshots_fd: int

    def verify(self) -> None:
        self.chain.verify()


@contextmanager
def _publication_directories(
    output_root: Path, *, create: bool
):
    parent = output_root.parent
    if parent == output_root:
        raise ConfigError("output root must have a trusted parent")
    with _TrustedDirectoryChain(parent) as chain:
        output_fd = chain.attach(output_root.name, create=create)
        snapshots_fd = chain.attach("snapshots", create=create)
        directories = _PublicationDirectories(chain, output_fd, snapshots_fd)
        directories.verify()
        yield directories


def _write_new_file_at(directory_fd: int, name: str, content: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor = os.open(name, flags, 0o644, dir_fd=directory_fd)
    try:
        payload = content.encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _open_directory_at(parent_fd: int, name: str) -> int:
    descriptor: int | None = None
    try:
        descriptor = os.open(name, _directory_open_flags(), dir_fd=parent_fd)
        descriptor_stat = os.fstat(descriptor)
        entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    if (
        not stat.S_ISDIR(descriptor_stat.st_mode)
        or not stat.S_ISDIR(entry_stat.st_mode)
        or _directory_identity(descriptor_stat) != _directory_identity(entry_stat)
    ):
        os.close(descriptor)
        raise ConfigError("snapshot directory identity changed")
    return descriptor


def _verify_directory_entry(parent_fd: int, name: str, directory_fd: int) -> None:
    descriptor_stat = os.fstat(directory_fd)
    entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if (
        not stat.S_ISDIR(entry_stat.st_mode)
        or _directory_identity(descriptor_stat) != _directory_identity(entry_stat)
    ):
        raise ConfigError("snapshot directory identity changed")


def _read_regular_file_with_identity_at(
    directory_fd: int, name: str
) -> tuple[str, tuple[int, ...]]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    try:
        before = os.fstat(descriptor)
        entry_before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(entry_before.st_mode)
            or before.st_nlink != 1
            or entry_before.st_nlink != 1
            or _stable_file_identity(before) != _stable_file_identity(entry_before)
        ):
            raise ConfigError("snapshot file is unsafe")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, READ_CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        entry_after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            _stable_file_identity(before) != _stable_file_identity(after)
            or _stable_file_identity(after) != _stable_file_identity(entry_after)
        ):
            raise ConfigError("snapshot file changed while being read")
        return (
            b"".join(chunks).decode("utf-8"),
            _stable_file_identity(after),
        )
    except UnicodeError:
        raise ConfigError("snapshot file is not UTF-8") from None
    finally:
        os.close(descriptor)


def _read_regular_file_at(directory_fd: int, name: str) -> str:
    return _read_regular_file_with_identity_at(directory_fd, name)[0]


def _verified_snapshot_identity_at(
    snapshots_fd: int, run_id: str, documents: Mapping[str, str]
) -> tuple[tuple[int, int], tuple[tuple[str, tuple[int, ...]], ...]] | None:
    snapshot_fd: int | None = None
    try:
        snapshot_fd = _open_directory_at(snapshots_fd, run_id)
        directory_identity = _directory_identity(os.fstat(snapshot_fd))
        if frozenset(os.listdir(snapshot_fd)) != frozenset(documents):
            return None
        actual_documents: dict[str, str] = {}
        file_identities: list[tuple[str, tuple[int, ...]]] = []
        for name in sorted(documents):
            text, file_identity = _read_regular_file_with_identity_at(
                snapshot_fd, name
            )
            actual_documents[name] = text
            file_identities.append((name, file_identity))
        _verify_directory_entry(snapshots_fd, run_id, snapshot_fd)
        if _directory_identity(os.fstat(snapshot_fd)) != directory_identity:
            return None
        for name, expected in documents.items():
            actual = actual_documents[name]
            if name.endswith(".json"):
                if _without_generated_at_json(actual) != _without_generated_at_json(
                    expected
                ):
                    return None
            elif _without_generated_at_markdown(
                actual
            ) != _without_generated_at_markdown(expected):
                return None
        return directory_identity, tuple(file_identities)
    except (OSError, ConfigError, ValueError, json.JSONDecodeError, _DuplicateJsonKey):
        return None
    finally:
        if snapshot_fd is not None:
            os.close(snapshot_fd)


def _snapshot_matches_documents_at(
    snapshots_fd: int, run_id: str, documents: Mapping[str, str]
) -> bool:
    return _verified_snapshot_identity_at(snapshots_fd, run_id, documents) is not None


def _cleanup_staging_at(
    output_fd: int,
    staging_name: str,
    expected_identity: tuple[int, int] | None,
) -> None:
    if expected_identity is None:
        return
    staging_fd: int | None = None
    try:
        entry_stat = os.stat(
            staging_name, dir_fd=output_fd, follow_symlinks=False
        )
        if (
            not stat.S_ISDIR(entry_stat.st_mode)
            or _directory_identity(entry_stat) != expected_identity
        ):
            return
        try:
            staging_fd = _open_directory_at(output_fd, staging_name)
        except (OSError, ConfigError):
            return
        if _directory_identity(os.fstat(staging_fd)) != expected_identity:
            return
        for name in os.listdir(staging_fd):
            entry_stat = os.stat(name, dir_fd=staging_fd, follow_symlinks=False)
            if stat.S_ISDIR(entry_stat.st_mode):
                return
            os.unlink(name, dir_fd=staging_fd)
        entry_after = os.stat(
            staging_name, dir_fd=output_fd, follow_symlinks=False
        )
        if (
            not stat.S_ISDIR(entry_after.st_mode)
            or _directory_identity(entry_after) != expected_identity
        ):
            return
        os.close(staging_fd)
        staging_fd = None
        os.rmdir(staging_name, dir_fd=output_fd)
    except OSError:
        return
    finally:
        if staging_fd is not None:
            os.close(staging_fd)


def _strict_latest_document(text: str) -> dict[str, str] | None:
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (json.JSONDecodeError, _DuplicateJsonKey):
        return None
    required = {
        "schema",
        "run_id",
        "snapshot_digest",
        "inventory",
        "duplicates",
        "warnings",
    }
    if not isinstance(value, dict) or set(value) != required:
        return None
    if not all(isinstance(value[field], str) for field in required):
        return None
    run_id = value["run_id"]
    snapshot_digest = value["snapshot_digest"]
    if (
        value["schema"] != "cognitive-card-migration-latest-v1"
        or not re.fullmatch(r"inv_sha256_[0-9a-f]{64}", run_id)
        or snapshot_digest != "sha256:" + run_id.removeprefix("inv_sha256_")
    ):
        return None
    expected_paths = {
        "inventory": f"snapshots/{run_id}/inventory.json",
        "duplicates": f"snapshots/{run_id}/duplicate-report.md",
        "warnings": f"snapshots/{run_id}/scan-warnings.json",
    }
    if any(value[field] != expected for field, expected in expected_paths.items()):
        return None
    return value


def _read_latest_at(output_fd: int) -> dict[str, str] | None:
    try:
        return _strict_latest_document(_read_regular_file_at(output_fd, "latest.json"))
    except (OSError, ConfigError):
        return None


def _atomic_replace_latest_at(
    directories: _PublicationDirectories,
    document: Mapping[str, Any],
    *,
    run_id: str,
    documents: Mapping[str, str],
    expected_snapshot_identity: tuple[
        tuple[int, int], tuple[tuple[str, tuple[int, ...]], ...]
    ],
) -> None:
    temporary = ".latest-" + secrets.token_hex(12) + ".json"
    try:
        directories.verify()
        _write_new_file_at(
            directories.output_fd, temporary, deterministic_json_text(document)
        )
        directories.verify()
        current_snapshot_identity = _verified_snapshot_identity_at(
            directories.snapshots_fd, run_id, documents
        )
        if current_snapshot_identity != expected_snapshot_identity:
            raise ConfigError("snapshot identity changed before latest replacement")
        os.replace(
            temporary,
            "latest.json",
            src_dir_fd=directories.output_fd,
            dst_dir_fd=directories.output_fd,
        )
        os.fsync(directories.output_fd)
        directories.verify()
    finally:
        try:
            os.unlink(temporary, dir_fd=directories.output_fd)
        except OSError:
            pass


def publish_inventory_snapshot(
    config: SourceConfig,
    alias_records: Sequence[SourceAliasRecord],
    scan_warnings: Sequence[WarningRecord],
    *,
    config_path: Path,
    roots_path: Path,
    output_root: Path,
    generated_at: str,
) -> dict[str, object]:
    """Stage, verify, publish an immutable snapshot, then replace latest."""

    normalized_output = validate_publication_paths(
        config,
        config_path=config_path,
        roots_path=roots_path,
        output_root=output_root,
    )
    documents = build_snapshot_documents(
        config,
        alias_records,
        scan_warnings,
        generated_at=generated_at,
    )
    run_id, snapshot_digest = _verify_shared_identity(documents)
    try:
        with _publication_directories(normalized_output, create=True) as directories:
            staging_name = ".staging-" + secrets.token_hex(12)
            directories.verify()
            os.mkdir(staging_name, 0o700, dir_fd=directories.output_fd)
            staging_present = True
            staging_fd = -1
            staging_identity: tuple[int, int] | None = None
            try:
                try:
                    staging_fd = os.open(
                        staging_name,
                        _directory_open_flags(),
                        dir_fd=directories.output_fd,
                    )
                except OSError:
                    try:
                        fallback_stat = os.stat(
                            staging_name,
                            dir_fd=directories.output_fd,
                            follow_symlinks=False,
                        )
                    except OSError:
                        pass
                    else:
                        if stat.S_ISDIR(fallback_stat.st_mode):
                            staging_identity = _directory_identity(fallback_stat)
                    raise
                opened_stat = os.fstat(staging_fd)
                if not stat.S_ISDIR(opened_stat.st_mode):
                    raise ConfigError("staging directory is unsafe")
                staging_identity = _directory_identity(opened_stat)
                staging_stat = os.stat(
                    staging_name,
                    dir_fd=directories.output_fd,
                    follow_symlinks=False,
                )
                if not stat.S_ISDIR(staging_stat.st_mode):
                    raise ConfigError("staging directory is unsafe")
                if _directory_identity(staging_stat) != staging_identity:
                    raise ConfigError("staging directory identity changed")
                directories.verify()
                for name, content in documents.items():
                    directories.verify()
                    _verify_directory_entry(
                        directories.output_fd, staging_name, staging_fd
                    )
                    _write_new_file_at(staging_fd, name, content)
                os.fsync(staging_fd)
                if not _snapshot_matches_documents_at(
                    directories.output_fd, staging_name, documents
                ):
                    raise ConfigError("staged snapshot verification failed")

                directories.verify()
                try:
                    _rename_staging_to_snapshot(
                        staging_name,
                        run_id,
                        output_fd=directories.output_fd,
                        snapshots_fd=directories.snapshots_fd,
                    )
                except FileExistsError:
                    if not _snapshot_matches_documents_at(
                        directories.snapshots_fd, run_id, documents
                    ):
                        raise ConfigError(
                            "existing immutable snapshot differs semantically"
                        )
                    os.close(staging_fd)
                    staging_fd = -1
                    _cleanup_staging_at(
                        directories.output_fd, staging_name, staging_identity
                    )
                    staging_present = False
                else:
                    staging_present = False
                    os.fsync(directories.snapshots_fd)
                    directories.verify()
                    _verify_directory_entry(
                        directories.snapshots_fd, run_id, staging_fd
                    )

                snapshot_identity = _verified_snapshot_identity_at(
                    directories.snapshots_fd, run_id, documents
                )
                if snapshot_identity is None:
                    raise ConfigError("snapshot changed before latest publication")
                latest: dict[str, object] = {
                    "schema": "cognitive-card-migration-latest-v1",
                    "run_id": run_id,
                    "snapshot_digest": snapshot_digest,
                    "inventory": f"snapshots/{run_id}/inventory.json",
                    "duplicates": f"snapshots/{run_id}/duplicate-report.md",
                    "warnings": f"snapshots/{run_id}/scan-warnings.json",
                }
                _atomic_replace_latest_at(
                    directories,
                    latest,
                    run_id=run_id,
                    documents=documents,
                    expected_snapshot_identity=snapshot_identity,
                )
                return latest
            finally:
                if staging_fd >= 0:
                    os.close(staging_fd)
                if staging_present:
                    _cleanup_staging_at(
                        directories.output_fd, staging_name, staging_identity
                    )
    except ConfigError:
        raise
    except OSError:
        raise ConfigError("snapshot publication failed") from None


def check_inventory_snapshot(
    config: SourceConfig,
    alias_records: Sequence[SourceAliasRecord],
    scan_warnings: Sequence[WarningRecord],
    *,
    config_path: Path,
    roots_path: Path,
    output_root: Path,
    generated_at: str,
) -> bool:
    normalized_output = validate_publication_paths(
        config,
        config_path=config_path,
        roots_path=roots_path,
        output_root=output_root,
    )
    documents = build_snapshot_documents(
        config,
        alias_records,
        scan_warnings,
        generated_at=generated_at,
    )
    run_id, snapshot_digest = _verify_shared_identity(documents)
    expected_latest = {
        "schema": "cognitive-card-migration-latest-v1",
        "run_id": run_id,
        "snapshot_digest": snapshot_digest,
        "inventory": f"snapshots/{run_id}/inventory.json",
        "duplicates": f"snapshots/{run_id}/duplicate-report.md",
        "warnings": f"snapshots/{run_id}/scan-warnings.json",
    }
    try:
        with _publication_directories(
            normalized_output, create=False
        ) as directories:
            directories.verify()
            latest = _read_latest_at(directories.output_fd)
            if latest != expected_latest:
                return False
            matched = _snapshot_matches_documents_at(
                directories.snapshots_fd, run_id, documents
            )
            directories.verify()
            return matched
    except (OSError, ConfigError):
        return False


def build_dry_run_summary(config: SourceConfig) -> dict[str, object]:
    fatal_warning_codes = {
        "missing_root",
        "unsafe_source_entry",
        "unreadable_directory",
        "unreadable_file",
        "source_changed_during_scan",
    }
    if any(warning.code in fatal_warning_codes for warning in config.warnings):
        raise ConfigError("dry-run source summary is incomplete")
    descriptors: list[tuple[int, int, str, int, int, int]] = []
    for rule in config.rules:
        def collect(
            relative_path: PurePosixPath,
            _descriptor: int,
            file_stat: os.stat_result,
        ) -> None:
            descriptors.append(
                (
                    file_stat.st_dev,
                    file_stat.st_ino,
                    relative_path.as_posix(),
                    file_stat.st_size,
                    file_stat.st_mtime_ns,
                    file_stat.st_ctime_ns,
                )
            )

        walk_warnings = walk_source(rule, collect)
        if any(warning.code in fatal_warning_codes for warning in walk_warnings):
            raise ConfigError("dry-run source summary is incomplete")
    descriptors.sort()
    digest = hashlib.sha256(_canonical_json_bytes(descriptors)).hexdigest()
    return {
        "schema": "cognitive-card-migration-dry-run-summary-v1",
        "declared_root_count": len(config.rules),
        "eligible_file_count": len(descriptors),
        "eligible_byte_count": sum(item[3] for item in descriptors),
        "descriptor_digest": "sha256:" + digest,
    }


def _validate_generated_at(value: str) -> str:
    if not isinstance(value, str) or not RFC3339_UTC_PATTERN.fullmatch(value):
        raise ConfigError("generated_at must be RFC3339 UTC at whole-second precision")
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ConfigError("generated_at must be RFC3339 UTC at whole-second precision") from None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ConfigError("generated_at must be RFC3339 UTC at whole-second precision")
    return value


def _current_generated_at() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory declared Cognitive Card assets")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--roots", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--strict-roots", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--generated-at")
    parser.add_argument("--dry-run-summary", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        generated_at = _validate_generated_at(args.generated_at or _current_generated_at())
        config = load_source_config(
            args.config,
            args.roots,
            strict_roots=args.strict_roots,
        )
        output_root = validate_publication_paths(
            config,
            config_path=args.config,
            roots_path=args.roots,
            output_root=args.output_root,
        )
        if args.dry_run_summary:
            sys.stdout.write(deterministic_json_text(build_dry_run_summary(config)))
            return 0

        aliases: list[SourceAliasRecord] = []
        scan_warnings: list[WarningRecord] = []
        for rule in config.rules:
            rule_aliases, rule_warnings = scan_source(rule)
            aliases.extend(rule_aliases)
            scan_warnings.extend(rule_warnings)
        if args.check:
            matched = check_inventory_snapshot(
                config,
                aliases,
                scan_warnings,
                config_path=args.config,
                roots_path=args.roots,
                output_root=output_root,
                generated_at=generated_at,
            )
            return 0 if matched else 1
        latest = publish_inventory_snapshot(
            config,
            aliases,
            scan_warnings,
            config_path=args.config,
            roots_path=args.roots,
            output_root=output_root,
            generated_at=generated_at,
        )
        sys.stdout.write(deterministic_json_text(latest))
        return 0
    except (ConfigError, ValueError):
        print("error: inventory command failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
