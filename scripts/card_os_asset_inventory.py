"""Configuration contract for the read-only Cognitive Card asset inventory.

Task 1 intentionally stops at source declaration and validation. Traversal,
hashing, aggregation, and report generation are implemented by later tasks.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping


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


class ConfigError(ValueError):
    """Raised when inventory configuration cannot be used safely."""


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
