from __future__ import annotations

import hashlib
import io
import json
import logging
import errno
import os
import random
import sys
import tempfile
import traceback
import unittest
import warnings
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from pathlib import PurePosixPath
from unittest.mock import patch

from PIL import Image
from pypdf import PdfWriter

import scripts.card_os_asset_inventory as inventory_module

from scripts.card_os_asset_inventory import (
    ConfigWarning,
    ConfigError,
    MEDIA_TYPES,
    SourceAliasRecord,
    SourceConfig,
    SourceRule,
    WarningRecord,
    build_inventory,
    canonical_config_digest,
    load_source_config,
    metadata_reader_versions,
    scan_source,
    sha256_descriptor,
    walk_source,
)


SCHEMA = "cognitive-card-migration-sources-v1"
ROOTS_SCHEMA = "cognitive-card-migration-roots-v1"
DEFAULT_EXTENSIONS = [
    ".png",
    ".webp",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".json",
    ".md",
    ".yaml",
    ".yml",
    ".txt",
    ".tsv",
]
DEFAULT_EXCLUDES = [
    ".git",
    ".DS_Store",
    "Thumbs.db",
    "node_modules",
    "dist",
    "tmp",
    "__pycache__",
]


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        # macOS exposes /var as a symlink to /private/var. Use the strict,
        # canonical temporary path so normal fixtures satisfy the no-symlink
        # root contract; dedicated tests below exercise rejection explicitly.
        self.base = Path(self.temporary_directory.name).resolve(strict=True)
        self.workspace = self.base / "workspace"
        self.archive = self.base / "archive"
        self.workspace.mkdir()
        self.archive.mkdir()
        (self.workspace / "assets").mkdir()
        self.config_path = self.base / "inventory-sources.json"
        self.roots_path = self.base / "inventory-roots.local.json"
        self.config = self._config()
        self.roots = {
            "schema": ROOTS_SCHEMA,
            "bases": {
                "workspace": str(self.workspace),
                "codex_archive": str(self.archive),
            },
        }

    def _source(self, **overrides: object) -> dict[str, object]:
        source: dict[str, object] = {
            "root_id": "sample-assets",
            "source_group": "sample-assets",
            "locator": {"base": "workspace", "relative": "assets"},
            "source_thread_id": None,
            "migration_grade": "A",
            "decision": "strict_revalidate",
        }
        source.update(overrides)
        return source

    def _config(self, **overrides: object) -> dict[str, object]:
        config: dict[str, object] = {
            "schema": SCHEMA,
            "defaults": {
                "include_extensions": DEFAULT_EXTENSIONS,
                "exclude_names": DEFAULT_EXCLUDES,
            },
            "sources": [self._source()],
        }
        config.update(overrides)
        return config

    def _write(self) -> None:
        self.config_path.write_text(
            json.dumps(self.config, ensure_ascii=False), encoding="utf-8"
        )
        self.roots_path.write_text(
            json.dumps(self.roots, ensure_ascii=False), encoding="utf-8"
        )

    def _write_raw(self, config: str, roots: str) -> None:
        self.config_path.write_text(config, encoding="utf-8")
        self.roots_path.write_text(roots, encoding="utf-8")

    def _assert_sanitized_error(self, error: ConfigError) -> None:
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        rendered = "".join(
            traceback.TracebackException.from_exception(error).format_exception_only()
        )
        self.assertNotIn(str(self.base), rendered)

    def _load(self, *, strict_roots: bool = False):
        self._write()
        return load_source_config(
            self.config_path, self.roots_path, strict_roots=strict_roots
        )

    def test_loads_valid_source_and_excludes_root_map_from_digest(self) -> None:
        loaded = self._load(strict_roots=True)

        self.assertEqual(SCHEMA, loaded.schema)
        self.assertEqual(1, len(loaded.rules))
        rule = loaded.rules[0]
        self.assertEqual("sample-assets", rule.root_id)
        self.assertEqual("sample-assets", rule.source_group)
        self.assertEqual("workspace", rule.locator_base)
        self.assertEqual("assets", rule.locator_relative)
        self.assertEqual((self.workspace / "assets"), rule.resolved_path)
        self.assertEqual(tuple(DEFAULT_EXTENSIONS), rule.include_extensions)
        self.assertEqual(tuple(DEFAULT_EXCLUDES), rule.exclude_names)
        self.assertEqual((), loaded.warnings)

        first_digest = loaded.config_digest
        self.roots["bases"]["workspace"] = str(self.base / "other-machine")  # type: ignore[index]
        self._write()
        self.assertEqual(first_digest, canonical_config_digest(self.config_path))

    def test_config_digest_is_canonical_json(self) -> None:
        self._write()
        expected_payload = json.dumps(
            self.config,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        expected = "sha256:" + hashlib.sha256(expected_payload).hexdigest()

        self.assertEqual(expected, canonical_config_digest(self.config_path))

        self.config_path.write_text(
            json.dumps(self.config, ensure_ascii=False, indent=4), encoding="utf-8"
        )
        self.assertEqual(expected, canonical_config_digest(self.config_path))

    def test_rejects_wrong_source_and_root_map_schemas(self) -> None:
        for target, invalid_schema in (
            ("config", "wrong-sources-v1"),
            ("roots", "wrong-roots-v1"),
        ):
            with self.subTest(target=target):
                self.config = self._config()
                self.roots["schema"] = ROOTS_SCHEMA
                if target == "config":
                    self.config["schema"] = invalid_schema
                else:
                    self.roots["schema"] = invalid_schema
                with self.assertRaises(ConfigError):
                    self._load()

    def test_rejects_duplicate_json_keys_at_every_object_layer(self) -> None:
        compact_config = json.dumps(
            self.config, ensure_ascii=False, separators=(",", ":")
        )
        compact_roots = json.dumps(
            self.roots, ensure_ascii=False, separators=(",", ":")
        )
        duplicate_configs = {
            "top": compact_config.replace(
                f'"schema":"{SCHEMA}"',
                f'"schema":"{SCHEMA}","schema":"{SCHEMA}"',
                1,
            ),
            "defaults": compact_config.replace(
                '"defaults":{"include_extensions":',
                '"defaults":{"exclude_names":[],"include_extensions":',
                1,
            ),
            "source": compact_config.replace(
                '"root_id":"sample-assets"',
                '"root_id":"sample-assets","root_id":"sample-assets"',
                1,
            ),
            "locator": compact_config.replace(
                '"locator":{"base":"workspace"',
                '"locator":{"base":"workspace","base":"workspace"',
                1,
            ),
        }
        for layer, config_text in duplicate_configs.items():
            with self.subTest(layer=layer):
                self._write_raw(config_text, compact_roots)
                with self.assertRaises(ConfigError) as caught:
                    load_source_config(
                        self.config_path, self.roots_path, strict_roots=False
                    )
                self._assert_sanitized_error(caught.exception)

        duplicate_roots = {
            "root-map": compact_roots.replace(
                f'"schema":"{ROOTS_SCHEMA}"',
                f'"schema":"{ROOTS_SCHEMA}","schema":"{ROOTS_SCHEMA}"',
                1,
            ),
            "bases": compact_roots.replace(
                '"bases":{"workspace":',
                f'"bases":{{"workspace":"{self.workspace}","workspace":',
                1,
            ),
        }
        for layer, roots_text in duplicate_roots.items():
            with self.subTest(layer=layer):
                self._write_raw(compact_config, roots_text)
                with self.assertRaises(ConfigError) as caught:
                    load_source_config(
                        self.config_path, self.roots_path, strict_roots=False
                    )
                self._assert_sanitized_error(caught.exception)

    def test_rejects_unknown_keys_at_every_schema_layer(self) -> None:
        for layer in (
            "top",
            "defaults",
            "source",
            "locator",
            "root-map",
            "bases",
        ):
            with self.subTest(layer=layer):
                self.config = self._config()
                self.roots = {
                    "schema": ROOTS_SCHEMA,
                    "bases": {
                        "workspace": str(self.workspace),
                        "codex_archive": str(self.archive),
                    },
                }
                if layer == "top":
                    self.config["unexpected"] = "value"
                elif layer == "defaults":
                    self.config["defaults"]["unexpected"] = "value"  # type: ignore[index]
                elif layer == "source":
                    self.config["sources"][0]["unexpected"] = "value"  # type: ignore[index]
                elif layer == "locator":
                    self.config["sources"][0]["locator"]["unexpected"] = "value"  # type: ignore[index]
                elif layer == "root-map":
                    self.roots["unexpected"] = "value"
                else:
                    self.roots["bases"]["unexpected"] = str(self.base / "extra")  # type: ignore[index]
                with self.assertRaises(ConfigError) as caught:
                    self._load()
                self._assert_sanitized_error(caught.exception)

    def test_rejects_missing_required_source_field(self) -> None:
        source = self._source()
        del source["source_thread_id"]
        self.config = self._config(sources=[source])
        with self.assertRaises(ConfigError):
            self._load()

    def test_rejects_absolute_strings_in_portable_config_before_digesting(self) -> None:
        absolute_values = (
            "/private/portable-config-must-not-contain-this",
            "C:\\Users\\portable-config-must-not-contain-this",
            "\\\\server\\share\\portable-config-must-not-contain-this",
        )
        for absolute_value in absolute_values:
            with self.subTest(value_kind=absolute_value[:2]):
                self.config = self._config(
                    sources=[self._source(source_thread_id=absolute_value)]
                )
                self._write()
                with self.assertRaises(ConfigError) as caught:
                    canonical_config_digest(self.config_path)
                self.assertNotIn(absolute_value, str(caught.exception))
                self._assert_sanitized_error(caught.exception)

    def test_source_thread_id_must_be_null_or_canonical_codex_uuid(self) -> None:
        valid = "019f02ca-cf3c-79e0-919d-9f8b90a076db"
        self.config = self._config(sources=[self._source(source_thread_id=valid)])
        self.assertEqual(valid, self._load(strict_roots=True).rules[0].source_thread_id)

        invalid_values = (
            "019F02CA-CF3C-79E0-919D-9F8B90A076DB",
            "019f02cacf3c79e0837f59c3420a9854",
            "not-a-thread-id",
            "00000000-0000-0000-0000-000000000000",
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self.config = self._config(
                    sources=[self._source(source_thread_id=value)]
                )
                with self.assertRaises(ConfigError):
                    self._load()

    def test_parse_and_lstat_errors_have_no_path_bearing_exception_chain(self) -> None:
        self.config_path.write_text(
            '{"secret":"/machine/private/config",', encoding="utf-8"
        )
        self.roots_path.write_text("{}", encoding="utf-8")
        with self.assertRaises(ConfigError) as parse_error:
            load_source_config(self.config_path, self.roots_path, strict_roots=False)
        self._assert_sanitized_error(parse_error.exception)
        self.assertNotIn("/machine/private/config", str(parse_error.exception))

        self.config = self._config()
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        missing_roots = self.base / "machine-private-missing-roots.json"
        with self.assertRaises(ConfigError) as root_parse_error:
            load_source_config(self.config_path, missing_roots, strict_roots=False)
        self._assert_sanitized_error(root_parse_error.exception)
        self.assertNotIn(str(missing_roots), str(root_parse_error.exception))

        self.config = self._config()
        self._write()
        leaked_path = str(self.base / "machine-private-lstat")
        with patch.object(
            Path,
            "lstat",
            side_effect=OSError(5, "unsafe filesystem detail", leaked_path),
        ):
            with self.assertRaises(ConfigError) as lstat_error:
                load_source_config(
                    self.config_path, self.roots_path, strict_roots=False
                )
        self._assert_sanitized_error(lstat_error.exception)
        self.assertNotIn(leaked_path, str(lstat_error.exception))

    def test_rejects_duplicate_or_invalid_root_ids(self) -> None:
        for invalid in ("AB", "Upper-case", "has_underscore", "a" * 65):
            with self.subTest(root_id=invalid):
                self.config = self._config(sources=[self._source(root_id=invalid)])
                with self.assertRaises(ConfigError):
                    self._load()

        duplicate = self._source()
        self.config = self._config(sources=[duplicate, dict(duplicate)])
        with self.assertRaises(ConfigError):
            self._load()

    def test_rejects_unknown_locator_base_and_unsafe_relative_paths(self) -> None:
        cases = (
            {"base": "unknown", "relative": "assets"},
            {"base": "workspace", "relative": "../assets"},
            {"base": "workspace", "relative": "nested/../../assets"},
            {"base": "workspace", "relative": "/assets"},
            {"base": "workspace", "relative": "assets\\elsewhere"},
            {"base": "workspace", "relative": ""},
        )
        for locator in cases:
            with self.subTest(locator=locator):
                self.config = self._config(sources=[self._source(locator=locator)])
                with self.assertRaises(ConfigError):
                    self._load()

    def test_rejects_relative_base_mapping(self) -> None:
        self.roots["bases"]["workspace"] = "relative/workspace"  # type: ignore[index]
        with self.assertRaises(ConfigError):
            self._load()

    def test_rejects_existing_non_directory_root(self) -> None:
        file_root = self.workspace / "file-root"
        file_root.write_text("not a directory", encoding="utf-8")
        self.config = self._config(
            sources=[
                self._source(
                    locator={"base": "workspace", "relative": "file-root"}
                )
            ]
        )
        with self.assertRaises(ConfigError):
            self._load()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_symlinked_base_or_root_components(self) -> None:
        linked_base = self.base / "linked-workspace"
        linked_base.symlink_to(self.workspace, target_is_directory=True)
        self.roots["bases"]["workspace"] = str(linked_base)  # type: ignore[index]
        with self.assertRaises(ConfigError):
            self._load()

        self.roots["bases"]["workspace"] = str(self.workspace)  # type: ignore[index]
        target = self.workspace / "real-assets"
        target.mkdir()
        (self.workspace / "linked-assets").symlink_to(target, target_is_directory=True)
        self.config = self._config(
            sources=[
                self._source(
                    locator={"base": "workspace", "relative": "linked-assets"}
                )
            ]
        )
        with self.assertRaises(ConfigError):
            self._load()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_self_loop_and_dangling_symlinks_inside_root_locator(self) -> None:
        links = {
            "locator-self-loop": "locator-self-loop",
            "locator-dangling": "missing-locator-target",
        }
        for name, target in links.items():
            (self.workspace / name).symlink_to(target, target_is_directory=True)
            with self.subTest(name=name):
                self.config = self._config(
                    sources=[
                        self._source(
                            locator={
                                "base": "workspace",
                                "relative": f"{name}/nested",
                            }
                        )
                    ]
                )
                with self.assertRaises(ConfigError) as caught:
                    self._load()
                self.assertNotIn(str(self.base), str(caught.exception))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_self_loop_and_dangling_symlinks_inside_base_mapping(self) -> None:
        links = {
            "base-self-loop": "base-self-loop",
            "base-dangling": "missing-base-target",
        }
        for name, target in links.items():
            (self.base / name).symlink_to(target, target_is_directory=True)
            with self.subTest(name=name):
                self.roots["bases"]["workspace"] = str(  # type: ignore[index]
                    self.base / name / "nested"
                )
                with self.assertRaises(ConfigError) as caught:
                    self._load()
                self.assertNotIn(str(self.base), str(caught.exception))

    def test_missing_root_warns_or_fails_in_strict_mode_without_absolute_paths(self) -> None:
        self.config = self._config(
            sources=[
                self._source(
                    locator={"base": "workspace", "relative": "missing-assets"}
                )
            ]
        )
        loaded = self._load(strict_roots=False)
        self.assertEqual(1, len(loaded.warnings))
        warning = loaded.warnings[0]
        self.assertEqual("sample-assets", warning.root_id)
        self.assertEqual("missing_root", warning.code)
        self.assertNotIn(str(self.workspace), warning.detail)

        with self.assertRaises(ConfigError):
            self._load(strict_roots=True)

    def test_rejects_duplicate_resolved_roots(self) -> None:
        second = self._source(
            root_id="second-assets",
            source_group="second-assets",
        )
        self.config = self._config(sources=[self._source(), second])
        with self.assertRaises(ConfigError):
            self._load()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_duplicate_roots_reached_through_symlink(self) -> None:
        (self.workspace / "assets-link").symlink_to(
            self.workspace / "assets", target_is_directory=True
        )
        second = self._source(
            root_id="second-assets",
            source_group="second-assets",
            locator={"base": "workspace", "relative": "assets-link"},
        )
        self.config = self._config(sources=[self._source(), second])
        with self.assertRaises(ConfigError):
            self._load()

    def test_rejects_unknown_grades_and_decisions(self) -> None:
        for field, invalid in (
            ("migration_grade", "E"),
            ("decision", "publish"),
        ):
            with self.subTest(field=field):
                self.config = self._config(
                    sources=[self._source(**{field: invalid})]
                )
                with self.assertRaises(ConfigError):
                    self._load()

    def test_source_specific_extensions_are_added_without_changing_defaults(self) -> None:
        self.config = self._config(
            sources=[
                self._source(
                    additional_extensions=[".html", ".css", ".js", ".ts", ".tsx"]
                )
            ]
        )
        rule = self._load(strict_roots=True).rules[0]
        self.assertEqual(
            tuple(DEFAULT_EXTENSIONS + [".html", ".css", ".js", ".ts", ".tsx"]),
            rule.include_extensions,
        )

    def test_rejects_invalid_extension_and_exclusion_declarations(self) -> None:
        bad_configs = (
            self._config(defaults={"include_extensions": ["png"], "exclude_names": DEFAULT_EXCLUDES}),
            self._config(defaults={"include_extensions": [".PNG"], "exclude_names": DEFAULT_EXCLUDES}),
            self._config(defaults={"include_extensions": [".png", ".png"], "exclude_names": DEFAULT_EXCLUDES}),
            self._config(defaults={"include_extensions": DEFAULT_EXTENSIONS, "exclude_names": ["nested/name"]}),
        )
        for config in bad_configs:
            with self.subTest(config=config):
                self.config = config
                with self.assertRaises(ConfigError):
                    self._load()

    def test_metadata_reader_versions_have_stable_contract(self) -> None:
        versions = metadata_reader_versions()
        self.assertEqual({"pillow", "pypdf"}, set(versions))
        for value in versions.values():
            self.assertIsInstance(value, str)
            self.assertTrue(value)

    def test_checked_in_config_declares_exact_historical_roots(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        checked_in = json.loads(
            (repository / "migration/card-os/inventory-sources.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "rabbit-full-v01": (
                "codex_archive",
                "2026-07-11/new-chat/outputs/life/animal_mammal/rabbit/20260712_214042__rabbit__full_package__v01",
                None,
                "A",
                "strict_revalidate",
            ),
            "paleobiology-packages-20260707": (
                "workspace",
                "outputs",
                None,
                "B",
                "upgrade_revalidate",
            ),
            "shenzhen-plants-20260626": (
                "codex_archive",
                "2026-06-26/h/outputs",
                "019f02ca-cf3c-79e0-919d-9f8b90a076db",
                "C",
                "rebuild",
            ),
            "kids-world-current": (
                "workspace",
                "boards/kids-world",
                None,
                "C",
                "rebuild",
            ),
            "kids-world-batch-20260612": (
                "codex_archive",
                "2026-06-12/files-mentioned-by-the-user-kids/outputs/kids-world-hotspot-v1-png",
                None,
                "C",
                "provenance_only",
            ),
            "kids-world-regenerated-20260614": (
                "codex_archive",
                "2026-06-14/files-mentioned-by-the-user-kids/outputs/kids-world-regenerated-2026-06-14",
                None,
                "C",
                "provenance_only",
            ),
            "llm-last-image-20260614": (
                "codex_archive",
                "2026-06-14/files-mentioned-by-the-user-kids-2/outputs",
                None,
                "D",
                "provenance_only",
            ),
            "kids-world-older-copies": (
                "codex_archive",
                "2026-05-12/files-mentioned-by-the-user-kids/boards/kids-world",
                None,
                "D",
                "provenance_only",
            ),
            "spider-verse": (
                "workspace",
                "boards/spider-verse",
                None,
                "legacy-gallery",
                "legacy_gallery",
            ),
            "paw-patrol": (
                "workspace",
                "boards/paw-patrol",
                None,
                "legacy-gallery",
                "legacy_gallery",
            ),
        }
        actual = {
            source["root_id"]: (
                source["locator"]["base"],
                source["locator"]["relative"],
                source["source_thread_id"],
                source["migration_grade"],
                source["decision"],
            )
            for source in checked_in["sources"]
        }
        self.assertEqual(expected, actual)

        defaults = checked_in["defaults"]
        self.assertEqual(DEFAULT_EXTENSIONS, defaults["include_extensions"])
        self.assertEqual(DEFAULT_EXCLUDES, defaults["exclude_names"])
        legacy_extensions = [".html", ".css", ".js", ".ts", ".tsx"]
        for source in checked_in["sources"]:
            expected_extra = (
                legacy_extensions
                if source["root_id"] in {"spider-verse", "paw-patrol"}
                else []
            )
            self.assertEqual(expected_extra, source.get("additional_extensions", []))


class ScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name).resolve(strict=True)
        self.source = self.base / "source"
        self.source.mkdir()
        self.rule = SourceRule(
            root_id="scanner-assets",
            source_group="scanner-assets",
            locator_base="workspace",
            locator_relative="source",
            resolved_path=self.source,
            source_thread_id=None,
            migration_grade="A",
            decision="strict_revalidate",
            include_extensions=tuple(
                DEFAULT_EXTENSIONS + [".html", ".css", ".js", ".ts", ".tsx"]
            ),
            exclude_names=tuple(DEFAULT_EXCLUDES),
        )

    def _write_image(
        self,
        relative_path: str,
        *,
        image_format: str,
        size: tuple[int, int],
    ) -> bytes:
        buffer = io.BytesIO()
        Image.new("RGB", size, color=(24, 92, 160)).save(
            buffer, format=image_format
        )
        payload = buffer.getvalue()
        target = self.source / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return payload

    def _write_pdf(self, relative_path: str, *, pages: int) -> bytes:
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=72, height=72)
        buffer = io.BytesIO()
        writer.write(buffer)
        payload = buffer.getvalue()
        target = self.source / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return payload

    def _snapshot_source_files(self) -> dict[str, tuple[bytes, int, int]]:
        snapshot: dict[str, tuple[bytes, int, int]] = {}
        for path in sorted(self.source.rglob("*")):
            if path.is_file() and not path.is_symlink():
                item_stat = path.stat()
                snapshot[path.relative_to(self.source).as_posix()] = (
                    path.read_bytes(),
                    item_stat.st_size,
                    item_stat.st_mtime_ns,
                )
        return snapshot

    def _assert_warnings_sanitized(self, warnings: object) -> None:
        rendered = repr(warnings)
        self.assertNotIn(str(self.base), rendered)
        self.assertNotIn("/machine/private", rendered)

    def test_walk_and_scan_are_stably_sorted_with_explicit_skip_reasons(self) -> None:
        # Deliberately create entries in the opposite order from their logical paths.
        (self.source / "zeta.txt").write_text("zeta", encoding="utf-8")
        (self.source / "nested").mkdir()
        (self.source / "nested" / "bravo.json").write_text("{}", encoding="utf-8")
        (self.source / "alpha.md").write_text("alpha", encoding="utf-8")
        (self.source / "unsupported.bin").write_bytes(b"binary")
        (self.source / ".DS_Store").write_bytes(b"metadata")
        (self.source / "dist").mkdir()
        (self.source / "dist" / "hidden.txt").write_text("hidden", encoding="utf-8")

        aliases, warnings = scan_source(self.rule)

        self.assertEqual(
            ["alpha.md", "nested/bravo.json", "zeta.txt"],
            [alias.relative_path for alias in aliases],
        )
        self.assertEqual(
            [
                (".DS_Store", "excluded_name"),
                ("dist", "excluded_name"),
                ("unsupported.bin", "unsupported_extension"),
            ],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self._assert_warnings_sanitized(warnings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_files_and_directories_are_skipped_and_never_opened(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "never.txt").write_text("never", encoding="utf-8")
        (self.source / "safe.txt").write_text("safe", encoding="utf-8")
        (self.source / "linked-file.txt").symlink_to(outside / "never.txt")
        (self.source / "linked-dir").symlink_to(outside, target_is_directory=True)
        real_open = os.open
        child_open_names: list[str] = []

        def recording_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            if isinstance(path, str) and kwargs.get("dir_fd") is not None:
                child_open_names.append(path)
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.card_os_asset_inventory.os.open", side_effect=recording_open):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual(["safe.txt"], [alias.relative_path for alias in aliases])
        self.assertEqual(
            [("linked-dir", "symlink"), ("linked-file.txt", "symlink")],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self.assertNotIn("linked-dir", child_open_names)
        self.assertNotIn("linked-file.txt", child_open_names)
        self.assertNotIn("never.txt", child_open_names)
        self._assert_warnings_sanitized(warnings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlink_reason_precedes_excluded_name_for_files_and_directories(self) -> None:
        outside = self.base / "outside-excluded"
        outside.mkdir()
        outside_file = outside / "never.txt"
        outside_file.write_text("never", encoding="utf-8")
        (self.source / ".DS_Store").symlink_to(outside_file)
        (self.source / "dist").symlink_to(outside, target_is_directory=True)
        real_open = os.open
        child_open_names: list[str] = []

        def recording_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            if isinstance(path, str) and kwargs.get("dir_fd") is not None:
                child_open_names.append(path)
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.card_os_asset_inventory.os.open", side_effect=recording_open):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual([], aliases)
        self.assertEqual(
            [(".DS_Store", "symlink"), ("dist", "symlink")],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self.assertNotIn(".DS_Store", child_open_names)
        self.assertNotIn("dist", child_open_names)
        self.assertNotIn("never.txt", child_open_names)
        self._assert_warnings_sanitized(warnings)

    def test_hashes_in_one_mib_chunks_and_does_not_mutate_source_files(self) -> None:
        payload = (b"0123456789abcdef" * 150_000) + b"tail"
        target = self.source / "large.txt"
        target.write_bytes(payload)
        before = self._snapshot_source_files()
        real_read = os.read
        requested_sizes: list[int] = []

        def recording_read(descriptor: int, amount: int) -> bytes:
            requested_sizes.append(amount)
            return real_read(descriptor, amount)

        with patch("scripts.card_os_asset_inventory.os.read", side_effect=recording_read):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual([], warnings)
        self.assertEqual(1, len(aliases))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), aliases[0].sha256)
        self.assertEqual(len(payload), aliases[0].size_bytes)
        self.assertTrue(requested_sizes)
        self.assertEqual({1024 * 1024}, set(requested_sizes))
        self.assertEqual(before, self._snapshot_source_files())

    def test_sha256_descriptor_rejects_changed_expected_identity(self) -> None:
        target = self.source / "identity.txt"
        target.write_bytes(b"identity")
        descriptor = os.open(target, os.O_RDONLY)
        self.addCleanup(os.close, descriptor)
        expected = os.fstat(descriptor)
        changed = list(expected)
        changed[6] += 1
        mismatched = os.stat_result(changed)

        with self.assertRaises(ValueError) as caught:
            sha256_descriptor(descriptor, expected_stat=mismatched)

        self.assertEqual("source_changed_during_scan", str(caught.exception))

    def test_records_fixed_mime_types_and_observed_image_and_pdf_metadata(self) -> None:
        self._write_image("images/sample.png", image_format="PNG", size=(13, 17))
        self._write_image("images/sample.jpg", image_format="JPEG", size=(19, 23))
        self._write_image("images/sample.webp", image_format="WEBP", size=(29, 31))
        self._write_pdf("documents/sample.pdf", pages=3)
        fixed = {
            "data.json": "application/json",
            "notes.md": "text/markdown",
            "config.yaml": "application/yaml",
            "config.yml": "application/yaml",
            "readme.txt": "text/plain",
            "table.tsv": "text/tab-separated-values",
            "page.html": "text/html",
            "style.css": "text/css",
            "script.js": "text/javascript",
            "types.ts": "text/typescript",
            "component.tsx": "text/typescript",
        }
        for name in reversed(tuple(fixed)):
            (self.source / name).write_text(name, encoding="utf-8")

        aliases, warnings = scan_source(self.rule)
        by_path = {alias.relative_path: alias for alias in aliases}

        self.assertEqual([], warnings)
        self.assertEqual(
            {
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
            },
            MEDIA_TYPES,
        )
        for relative_path, media_type in fixed.items():
            alias = by_path[relative_path]
            self.assertEqual(media_type, alias.media_type)
            self.assertIsNone(alias.image_width)
            self.assertIsNone(alias.image_height)
            self.assertIsNone(alias.pdf_page_count)
            self.assertEqual("not_applicable", alias.metadata_status)
        for name, expected_type, dimensions in (
            ("images/sample.png", "image/png", (13, 17)),
            ("images/sample.jpg", "image/jpeg", (19, 23)),
            ("images/sample.webp", "image/webp", (29, 31)),
        ):
            alias = by_path[name]
            self.assertEqual(expected_type, alias.media_type)
            self.assertEqual(dimensions, (alias.image_width, alias.image_height))
            self.assertIsNone(alias.pdf_page_count)
            self.assertEqual("ok", alias.metadata_status)
        pdf = by_path["documents/sample.pdf"]
        self.assertEqual("application/pdf", pdf.media_type)
        self.assertEqual(3, pdf.pdf_page_count)
        self.assertIsNone(pdf.image_width)
        self.assertIsNone(pdf.image_height)
        self.assertEqual("ok", pdf.metadata_status)

    def test_observed_image_type_wins_and_malformed_metadata_is_retained(self) -> None:
        mismatched_payload = self._write_image(
            "mismatch.jpg", image_format="PNG", size=(7, 11)
        )
        (self.source / "broken.png").write_bytes(b"not an image")
        (self.source / "broken.pdf").write_bytes(b"not a pdf")

        aliases, warnings = scan_source(self.rule)
        by_path = {alias.relative_path: alias for alias in aliases}

        mismatch = by_path["mismatch.jpg"]
        self.assertEqual(hashlib.sha256(mismatched_payload).hexdigest(), mismatch.sha256)
        self.assertEqual("image/png", mismatch.media_type)
        self.assertEqual((7, 11), (mismatch.image_width, mismatch.image_height))
        self.assertEqual("ok", mismatch.metadata_status)
        for name, expected_type in (
            ("broken.png", "image/png"),
            ("broken.pdf", "application/pdf"),
        ):
            alias = by_path[name]
            self.assertEqual(expected_type, alias.media_type)
            self.assertIsNone(alias.image_width)
            self.assertIsNone(alias.image_height)
            self.assertIsNone(alias.pdf_page_count)
            self.assertEqual("unreadable", alias.metadata_status)
        self.assertEqual(
            [
                ("broken.pdf", "metadata_unreadable"),
                ("broken.png", "metadata_unreadable"),
                ("mismatch.jpg", "media_type_mismatch"),
            ],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self._assert_warnings_sanitized(warnings)

    def test_permission_error_becomes_sanitized_warning(self) -> None:
        (self.source / "denied.txt").write_text("private", encoding="utf-8")
        (self.source / "safe.txt").write_text("safe", encoding="utf-8")
        real_open = os.open

        def permission_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            if path == "denied.txt" and kwargs.get("dir_fd") is not None:
                raise PermissionError(13, "denied", "/machine/private/denied.txt")
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.card_os_asset_inventory.os.open", side_effect=permission_open):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual(["safe.txt"], [alias.relative_path for alias in aliases])
        self.assertEqual(
            [("denied.txt", "unreadable_file")],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self._assert_warnings_sanitized(warnings)

    def test_file_changed_during_hash_is_excluded(self) -> None:
        target = self.source / "changing.txt"
        target.write_bytes(b"before")
        real_read = os.read
        changed = False

        def mutating_read(descriptor: int, amount: int) -> bytes:
            nonlocal changed
            chunk = real_read(descriptor, amount)
            if chunk and not changed:
                changed = True
                target.write_bytes(b"after-source-change")
            return chunk

        with patch("scripts.card_os_asset_inventory.os.read", side_effect=mutating_read):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual([], aliases)
        self.assertEqual(
            [("changing.txt", "source_changed_during_scan")],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self._assert_warnings_sanitized(warnings)

    def test_declared_root_replaced_during_hash_rejects_every_old_root_alias(self) -> None:
        (self.source / "inside.txt").write_text("inside", encoding="utf-8")
        displaced = self.base / "displaced-source"
        real_read = os.read
        replaced = False

        def replacing_read(descriptor: int, amount: int) -> bytes:
            nonlocal replaced
            chunk = real_read(descriptor, amount)
            if chunk and not replaced:
                replaced = True
                self.source.rename(displaced)
                self.source.mkdir()
                (self.source / "never.txt").write_text("new root", encoding="utf-8")
            return chunk

        with patch("scripts.card_os_asset_inventory.os.read", side_effect=replacing_read):
            aliases, scan_warnings = scan_source(self.rule)

        self.assertTrue(replaced)
        self.assertEqual([], aliases)
        self.assertEqual(
            [(".", "unsafe_source_entry")],
            [
                (warning.relative_path, warning.code)
                for warning in scan_warnings
                if warning.relative_path == "."
            ],
        )
        self.assertNotIn("never.txt", [alias.relative_path for alias in aliases])
        self._assert_warnings_sanitized(scan_warnings)

    def test_pillow_bomb_warning_and_error_are_isolated_as_unreadable_metadata(self) -> None:
        self._write_image("warning.png", image_format="PNG", size=(15, 15))
        self._write_image("error.png", image_format="PNG", size=(20, 20))

        with warnings.catch_warnings(record=True) as leaked_warnings:
            warnings.simplefilter("always")
            with patch.object(Image, "MAX_IMAGE_PIXELS", 150):
                aliases, scan_warnings = scan_source(self.rule)

        self.assertEqual([], leaked_warnings)
        by_path = {alias.relative_path: alias for alias in aliases}
        self.assertEqual({"error.png", "warning.png"}, set(by_path))
        for alias in by_path.values():
            self.assertEqual("unreadable", alias.metadata_status)
            self.assertIsNone(alias.image_width)
            self.assertIsNone(alias.image_height)
            self.assertIsNone(alias.pdf_page_count)
        self.assertEqual(
            [
                ("error.png", "metadata_unreadable"),
                ("warning.png", "metadata_unreadable"),
            ],
            [(warning.relative_path, warning.code) for warning in scan_warnings],
        )
        self._assert_warnings_sanitized(scan_warnings)

    def test_noisy_pypdf_attribute_error_is_scoped_and_retains_hashed_alias(self) -> None:
        payload = self._write_pdf("mutated.pdf", pages=1)
        private_path = "/machine/private/mutated.pdf"
        stderr_capture = io.StringIO()
        log_capture = io.StringIO()
        logger = logging.getLogger("pypdf")
        handler = logging.StreamHandler(log_capture)
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)
        logger_state = (
            list(logger.handlers),
            logger.level,
            logger.propagate,
            logger.disabled,
        )

        def noisy_reader(*_args: object, **_kwargs: object) -> object:
            print(private_path, file=sys.stderr)
            logger.warning("failed reader for %s", private_path)
            raise AttributeError(private_path)

        with patch("pypdf.PdfReader", side_effect=noisy_reader):
            with redirect_stderr(stderr_capture):
                aliases, scan_warnings = scan_source(self.rule)

        self.assertEqual("", stderr_capture.getvalue())
        self.assertEqual("", log_capture.getvalue())
        self.assertEqual(
            logger_state,
            (
                list(logger.handlers),
                logger.level,
                logger.propagate,
                logger.disabled,
            ),
        )
        self.assertEqual(1, len(aliases))
        alias = aliases[0]
        self.assertEqual(hashlib.sha256(payload).hexdigest(), alias.sha256)
        self.assertEqual("application/pdf", alias.media_type)
        self.assertEqual("unreadable", alias.metadata_status)
        self.assertIsNone(alias.pdf_page_count)
        self.assertEqual(
            [("mutated.pdf", "metadata_unreadable")],
            [(warning.relative_path, warning.code) for warning in scan_warnings],
        )
        self._assert_warnings_sanitized(scan_warnings)

    def test_fdopen_failure_does_not_leak_image_or_pdf_duplicate_descriptors(self) -> None:
        self._write_image("fdopen-image.png", image_format="PNG", size=(8, 9))
        self._write_pdf("fdopen.pdf", pages=1)
        before_fds = {
            int(name) for name in os.listdir("/dev/fd") if name.isdigit()
        }

        with patch(
            "scripts.card_os_asset_inventory.os.fdopen",
            side_effect=OSError(5, "fdopen failed", "/machine/private/reader"),
        ):
            aliases, scan_warnings = scan_source(self.rule)

        after_fds = {
            int(name) for name in os.listdir("/dev/fd") if name.isdigit()
        }
        leaked_fds = after_fds - before_fds

        def close_if_open(descriptor: int) -> None:
            try:
                os.close(descriptor)
            except OSError:
                pass

        for descriptor in leaked_fds:
            self.addCleanup(close_if_open, descriptor)

        self.assertEqual(before_fds, after_fds)
        self.assertEqual(
            {"fdopen-image.png", "fdopen.pdf"},
            {alias.relative_path for alias in aliases},
        )
        for alias in aliases:
            self.assertEqual("unreadable", alias.metadata_status)
            self.assertIsNone(alias.image_width)
            self.assertIsNone(alias.image_height)
            self.assertIsNone(alias.pdf_page_count)
        self.assertEqual(
            {
                ("fdopen-image.png", "metadata_unreadable"),
                ("fdopen.pdf", "metadata_unreadable"),
            },
            {(warning.relative_path, warning.code) for warning in scan_warnings},
        )
        self._assert_warnings_sanitized(scan_warnings)

    def test_missing_descriptor_platform_capability_fails_closed(self) -> None:
        (self.source / "never.txt").write_text("never", encoding="utf-8")

        with patch.object(os, "supports_dir_fd", set()):
            aliases, scan_warnings = scan_source(self.rule)

        self.assertEqual([], aliases)
        self.assertEqual(
            [(".", "unsafe_source_entry")],
            [(warning.relative_path, warning.code) for warning in scan_warnings],
        )
        self._assert_warnings_sanitized(scan_warnings)

    def test_unsupported_child_descriptor_open_fails_closed_without_path_leak(self) -> None:
        (self.source / "child").mkdir()
        (self.source / "child" / "never.txt").write_text("never", encoding="utf-8")
        real_open = os.open
        errors = (
            NotImplementedError("/machine/private/not-supported"),
            TypeError("/machine/private/bad-signature"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                def unsupported_open(
                    path: object,
                    flags: int,
                    *args: object,
                    **kwargs: object,
                ) -> int:
                    if path == "child" and kwargs.get("dir_fd") is not None:
                        raise error
                    return real_open(path, flags, *args, **kwargs)

                with patch(
                    "scripts.card_os_asset_inventory.os.open",
                    side_effect=unsupported_open,
                ):
                    aliases, scan_warnings = scan_source(self.rule)

                self.assertEqual([], aliases)
                self.assertEqual(
                    [("child", "unsafe_source_entry")],
                    [
                        (warning.relative_path, warning.code)
                        for warning in scan_warnings
                    ],
                )
                self._assert_warnings_sanitized(scan_warnings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_directory_replaced_with_symlink_fails_closed(self) -> None:
        checked = self.source / "replace-me"
        checked.mkdir()
        (checked / "original.txt").write_text("original", encoding="utf-8")
        outside = self.base / "outside-target"
        outside.mkdir()
        (outside / "never.txt").write_text("never", encoding="utf-8")
        displaced = self.source / "displaced"
        real_open = os.open
        replaced = False

        def replacing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal replaced
            if (
                path == "replace-me"
                and kwargs.get("dir_fd") is not None
                and flags & getattr(os, "O_DIRECTORY", 0)
                and not replaced
            ):
                replaced = True
                checked.rename(displaced)
                checked.symlink_to(outside, target_is_directory=True)
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.card_os_asset_inventory.os.open", side_effect=replacing_open):
            aliases, warnings = scan_source(self.rule)

        self.assertEqual([], aliases)
        self.assertTrue(replaced)
        self.assertEqual(
            [
                (".", "unsafe_source_entry"),
                ("replace-me", "unsafe_source_entry"),
            ],
            [(warning.relative_path, warning.code) for warning in warnings],
        )
        self.assertNotIn("never.txt", [alias.relative_path for alias in aliases])
        self._assert_warnings_sanitized(warnings)

    def test_walk_source_passes_only_logical_paths_and_read_only_descriptors(self) -> None:
        (self.source / "nested").mkdir()
        (self.source / "nested" / "item.txt").write_text("value", encoding="utf-8")
        observed: list[tuple[PurePosixPath, bytes]] = []

        def on_file(
            relative_path: PurePosixPath,
            descriptor: int,
            _expected_stat: os.stat_result,
        ) -> None:
            self.assertFalse(relative_path.is_absolute())
            observed.append((relative_path, os.read(descriptor, 1024)))

        warnings = walk_source(self.rule, on_file)

        self.assertEqual([(PurePosixPath("nested/item.txt"), b"value")], observed)
        self.assertEqual([], warnings)

    def test_walk_source_does_not_disguise_callback_programming_errors(self) -> None:
        (self.source / "item.txt").write_text("value", encoding="utf-8")
        errors = (
            TypeError("/machine/private/programming-bug"),
            NotImplementedError("/machine/private/not-a-platform-error"),
        )

        for error in errors:
            with self.subTest(error=type(error).__name__):
                def broken_callback(
                    _relative_path: PurePosixPath,
                    _descriptor: int,
                    _expected_stat: os.stat_result,
                ) -> None:
                    raise error

                with self.assertRaises(type(error)) as caught:
                    walk_source(self.rule, broken_callback)

                self.assertIs(error, caught.exception)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_backslash_entries_are_skipped_at_the_nearest_safe_parent(self) -> None:
        outside = self.base / "outside-backslash"
        outside.mkdir()
        (outside / "never.txt").write_text("never", encoding="utf-8")

        dangerous_names = {
            "top\\file.txt",
            "top\\directory",
            "nested\\file.txt",
            "nested\\directory",
        }
        (self.source / "top\\file.txt").write_text("unsafe", encoding="utf-8")
        top_directory = self.source / "top\\directory"
        top_directory.mkdir()
        (top_directory / "escape").symlink_to(outside, target_is_directory=True)
        safe_parent = self.source / "safe"
        safe_parent.mkdir()
        (safe_parent / "nested\\file.txt").write_text("unsafe", encoding="utf-8")
        nested_directory = safe_parent / "nested\\directory"
        nested_directory.mkdir()
        (nested_directory / "escape").symlink_to(outside, target_is_directory=True)

        (self.source / "普通.txt").write_text("unicode", encoding="utf-8")
        (safe_parent / "line\nbreak.txt").write_text("newline", encoding="utf-8")
        real_open = os.open
        opened_child_names: list[str] = []

        def recording_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            if isinstance(path, str) and kwargs.get("dir_fd") is not None:
                opened_child_names.append(path)
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.card_os_asset_inventory.os.open", side_effect=recording_open):
            aliases, scan_warnings = scan_source(self.rule)

        self.assertEqual(
            {"safe/line\nbreak.txt", "普通.txt"},
            {alias.relative_path for alias in aliases},
        )
        self.assertEqual(
            [
                (".", "unsafe_source_entry"),
                (".", "unsafe_source_entry"),
                ("safe", "unsafe_source_entry"),
                ("safe", "unsafe_source_entry"),
            ],
            [(warning.relative_path, warning.code) for warning in scan_warnings],
        )
        for warning in scan_warnings:
            self.assertFalse(
                any(mark in warning.detail for mark in ("/", "\\", "\r", "\n"))
            )
        self.assertTrue(dangerous_names.isdisjoint(opened_child_names))
        self.assertNotIn("never.txt", opened_child_names)
        self._assert_warnings_sanitized(scan_warnings)

        inventory = build_inventory(
            SourceConfig(
                schema=SCHEMA,
                rules=(self.rule,),
                warnings=(),
                config_digest="sha256:" + ("0" * 64),
            ),
            aliases,
            scan_warnings,
            generated_at="2026-07-13T00:00:00Z",
        )
        self.assertEqual(2, inventory["summary"]["source_alias_count"])
        self.assertEqual(4, inventory["summary"]["warning_count"])


class AggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = (
            self._rule("root-alpha", "shared-group", "A", "strict_revalidate"),
            self._rule("root-bravo", "shared-group", "C", "rebuild"),
            self._rule("root-charlie", "other-group", "legacy-gallery", "legacy_gallery"),
        )
        self.config = SourceConfig(
            schema=SCHEMA,
            rules=self.rules,
            warnings=(),
            config_digest="sha256:" + "c" * 64,
        )

    def _rule(
        self,
        root_id: str,
        source_group: str,
        grade: str,
        decision: str,
    ) -> SourceRule:
        return SourceRule(
            root_id=root_id,
            source_group=source_group,
            locator_base="workspace",
            locator_relative=f"fixtures/{root_id}",
            resolved_path=Path(f"/unused/{root_id}"),
            source_thread_id=None,
            migration_grade=grade,
            decision=decision,
            include_extensions=tuple(DEFAULT_EXTENSIONS),
            exclude_names=tuple(DEFAULT_EXCLUDES),
        )

    def _alias(
        self,
        root_id: str,
        relative_path: str,
        payload: bytes,
        *,
        media_type: str | None = None,
    ) -> SourceAliasRecord:
        rule = next(rule for rule in self.rules if rule.root_id == root_id)
        extension = PurePosixPath(relative_path).suffix.casefold()
        return SourceAliasRecord(
            root_id=root_id,
            relative_path=relative_path,
            source_thread_id=rule.source_thread_id,
            source_group=rule.source_group,
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            media_type=media_type or MEDIA_TYPES[extension],
            image_width=None,
            image_height=None,
            pdf_page_count=None,
            metadata_status="not_applicable",
        )

    def _build(
        self,
        aliases: list[SourceAliasRecord],
        *,
        warnings: list[object] | None = None,
    ) -> dict[str, object]:
        with patch(
            "scripts.card_os_asset_inventory.metadata_reader_versions",
            return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
        ):
            return build_inventory(
                self.config,
                aliases,
                warnings or [],  # type: ignore[arg-type]
                generated_at="2026-07-13T00:00:00Z",
            )

    def test_identical_bytes_merge_aliases_grades_decisions_and_duplicate_group(self) -> None:
        payload = b"one content object"
        aliases = [
            self._alias("root-bravo", "zeta/shared.json", payload),
            self._alias("root-alpha", "alpha/shared.json", payload),
        ]

        inventory = self._build(aliases)

        self.assertEqual(1, len(inventory["assets"]))
        asset = inventory["assets"][0]
        digest = hashlib.sha256(payload).hexdigest()
        self.assertEqual("mig_sha256_" + digest, asset["migration_asset_id"])
        self.assertEqual(digest, asset["sha256"])
        self.assertEqual(
            [("root-alpha", "alpha/shared.json"), ("root-bravo", "zeta/shared.json")],
            [
                (alias["root_id"], alias["relative_path"])
                for alias in asset["source_aliases"]
            ],
        )
        self.assertEqual(["A", "C"], asset["migration_grades"])
        self.assertEqual(["rebuild", "strict_revalidate"], asset["decisions"])
        duplicate_id = "dup_sha256_" + digest
        self.assertEqual(duplicate_id, asset["duplicate_group"])
        self.assertEqual(
            [
                {
                    "duplicate_group": duplicate_id,
                    "sha256": digest,
                    "migration_asset_id": "mig_sha256_" + digest,
                    "alias_count": 2,
                    "aliases": [
                        {"root_id": "root-alpha", "relative_path": "alpha/shared.json"},
                        {"root_id": "root-bravo", "relative_path": "zeta/shared.json"},
                    ],
                }
            ],
            inventory["duplicate_groups"],
        )
        self.assertEqual(2 * len(payload), inventory["summary"]["total_source_bytes"])
        self.assertEqual(len(payload), inventory["summary"]["unique_content_bytes"])

    def test_same_normalized_name_with_distinct_bytes_remains_distinct(self) -> None:
        aliases = [
            self._alias("root-alpha", "one/Caf\u00e9.JSON", b"first"),
            self._alias("root-bravo", "two/CAFE\u0301.json", b"second"),
        ]

        inventory = self._build(aliases)

        self.assertEqual(2, len(inventory["assets"]))
        self.assertEqual([], inventory["duplicate_groups"])
        normalized = "caf\u00e9.json"
        group = inventory["same_name_candidate_groups"][0]
        self.assertEqual(normalized, group["normalized_basename"])
        self.assertEqual(
            "name_sha256_" + hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            group["group_id"],
        )
        self.assertEqual("review_required", group["status"])
        self.assertEqual(
            sorted("mig_sha256_" + alias.sha256 for alias in aliases),
            group["members"],
        )

    def test_derivative_groups_are_partitioned_by_source_group_and_ordered(self) -> None:
        aliases = [
            self._alias("root-charlie", "Topic/HERO.WEBP", b"other webp"),
            self._alias("root-alpha", "Topic/Hero.WEBP", b"shared webp"),
            self._alias("root-bravo", "topic/hero.png", b"shared png"),
            self._alias("root-charlie", "topic/hero.png", b"other png"),
            self._alias("root-alpha", "unpaired/only.png", b"unpaired"),
        ]

        inventory = self._build(aliases)

        groups = inventory["derivative_candidate_groups"]
        self.assertEqual(2, len(groups))
        for group in groups:
            self.assertEqual("topic/hero", group["normalized_stem"])
            self.assertEqual("review_required", group["status"])
            self.assertEqual(
                ["source_candidate", "derivative_candidate"],
                [member["role"] for member in group["members"]],
            )
            self.assertEqual(
                [".png", ".webp"],
                [member["extension"] for member in group["members"]],
            )
            self.assertRegex(group["group_id"], r"^deriv_sha256_[0-9a-f]{64}$")
        self.assertNotEqual(groups[0]["group_id"], groups[1]["group_id"])

    def test_structural_evidence_uses_only_exact_lowercase_components_and_basenames(self) -> None:
        positive_paths = (
            "01_content/fact.json",
            "01_content/semantic-core.json",
            "01_content/final_cards.json",
            "01_content/content_lock.json",
            "06_qa/manifest.json",
            "05_print/pdf/rabbit.pdf",
        )
        aliases = [
            self._alias("root-alpha", path, f"payload-{index}".encode())
            for index, path in enumerate(positive_paths)
        ]
        aliases.extend(
            [
                self._alias("root-alpha", "01_content/artifact.json", b"artifact"),
                self._alias("root-alpha", "not_qa/qa_notes.json", b"qa negative"),
                self._alias("root-alpha", "printable/rabbit.pdf", b"print negative"),
                self._alias("root-alpha", "QA/manifest.JSON", b"case negative"),
            ]
        )

        inventory = self._build(aliases)
        by_path = {
            asset["source_aliases"][0]["relative_path"]: asset
            for asset in inventory["assets"]
        }

        self.assertTrue(by_path["01_content/fact.json"]["structural_evidence"]["fact"])
        self.assertTrue(
            by_path["01_content/semantic-core.json"]["structural_evidence"]["propositions"]
        )
        self.assertTrue(
            by_path["01_content/content_lock.json"]["structural_evidence"]["content_lock"]
        )
        self.assertTrue(
            by_path["01_content/final_cards.json"]["structural_evidence"]["four_cards"]
        )
        self.assertTrue(by_path["06_qa/manifest.json"]["structural_evidence"]["qa"])
        self.assertTrue(
            by_path["06_qa/manifest.json"]["structural_evidence"]["manifest"]
        )
        self.assertTrue(by_path["05_print/pdf/rabbit.pdf"]["structural_evidence"]["print_pdf"])
        for negative in (
            "01_content/artifact.json",
            "not_qa/qa_notes.json",
            "printable/rabbit.pdf",
            "QA/manifest.JSON",
        ):
            self.assertFalse(any(by_path[negative]["structural_evidence"].values()))

    def test_no_semantic_rights_package_or_preferred_alias_is_inferred(self) -> None:
        inventory = self._build(
            [
                self._alias("root-bravo", "rabbit/fact.json", b"same"),
                self._alias("root-alpha", "preferred/fact.json", b"same"),
            ]
        )
        asset = inventory["assets"][0]

        self.assertIsNone(asset["object_name"])
        self.assertIsNone(asset["classification"])
        self.assertEqual("review_required", asset["rights_status"])
        self.assertIsNone(asset["target_package_id"])
        self.assertNotIn("preferred_alias", asset)

    def test_machine_fields_roots_readers_warnings_and_summary_are_stable(self) -> None:
        self.config = SourceConfig(
            schema=self.config.schema,
            rules=self.config.rules,
            warnings=(
                ConfigWarning(
                    root_id="root-charlie",
                    code="missing_root",
                    detail="declared source root does not exist on this machine",
                ),
            ),
            config_digest=self.config.config_digest,
        )
        warning = WarningRecord(
            root_id="root-alpha",
            relative_path="ignored.bin",
            code="unsupported_extension",
            detail="extension .bin is not enabled for this root",
        )

        inventory = self._build([], warnings=[warning])

        self.assertEqual("cognitive-card-migration-inventory-v1", inventory["schema"])
        self.assertEqual("2026-07-13T00:00:00Z", inventory["generated_at"])
        self.assertEqual(self.config.config_digest, inventory["config_digest"])
        self.assertEqual(
            {"pillow": "12.0.0", "pypdf": "6.0.0"},
            inventory["metadata_readers"],
        )
        self.assertEqual(
            [
                {
                    "root_id": "root-alpha",
                    "locator": {"base": "workspace", "relative": "fixtures/root-alpha"},
                    "status": "scanned",
                },
                {
                    "root_id": "root-bravo",
                    "locator": {"base": "workspace", "relative": "fixtures/root-bravo"},
                    "status": "scanned",
                },
                {
                    "root_id": "root-charlie",
                    "locator": {"base": "workspace", "relative": "fixtures/root-charlie"},
                    "status": "missing",
                },
            ],
            inventory["scan_roots"],
        )
        self.assertEqual(
            {
                "source_alias_count": 0,
                "content_object_count": 0,
                "duplicate_group_count": 0,
                "same_name_candidate_group_count": 0,
                "derivative_candidate_group_count": 0,
                "warning_count": 2,
                "total_source_bytes": 0,
                "unique_content_bytes": 0,
            },
            inventory["summary"],
        )

    def test_full_digest_ids_are_stable_and_identity_collisions_fail_closed(self) -> None:
        aliases = [
            self._alias("root-alpha", "a.txt", b"alpha"),
            self._alias("root-bravo", "b.txt", b"bravo"),
        ]
        inventory = self._build(aliases)
        ids = [asset["migration_asset_id"] for asset in inventory["assets"]]
        self.assertEqual(2, len(set(ids)))
        for asset_id, alias in zip(ids, sorted(aliases, key=lambda item: item.sha256)):
            self.assertEqual("mig_sha256_" + alias.sha256, asset_id)
            self.assertEqual(75, len(asset_id))

        with patch(
            "scripts.card_os_asset_inventory._migration_asset_id",
            return_value="mig_sha256_" + "0" * 64,
        ):
            with self.assertRaisesRegex(ValueError, "^identity_collision$"):
                self._build(aliases)

    def test_aliases_must_match_declared_source_identity_and_safe_logical_path(self) -> None:
        valid = self._alias("root-alpha", "safe/item.json", b"valid")
        invalid_aliases = (
            replace(valid, root_id="unknown-root"),
            replace(valid, source_group="other-group"),
            replace(valid, source_thread_id="019f02ca-cf3c-79e0-919d-9f8b90a076db"),
            *(replace(valid, relative_path=path) for path in (
                "",
                ".",
                "/absolute/item.json",
                "../item.json",
                "safe/../item.json",
                "safe\\item.json",
                "C:\\private\\item.json",
                "C:/private/item.json",
                "safe/\x00item.json",
            )),
        )

        for alias in invalid_aliases:
            with self.subTest(root_id=alias.root_id, path=repr(alias.relative_path)):
                with self.assertRaisesRegex(ValueError, "^invalid_alias_record$"):
                    self._build([alias])

    def test_warnings_must_use_declared_roots_safe_paths_and_sanitized_fields(self) -> None:
        valid = WarningRecord(
            root_id="root-alpha",
            relative_path=".",
            code="unsafe_source_entry",
            detail="declared source root failed descriptor safety checks",
        )
        invalid_warnings = (
            replace(valid, root_id="unknown-root"),
            replace(valid, relative_path="/machine/private/item"),
            replace(valid, relative_path="C:\\machine\\private\\item"),
            replace(valid, relative_path="../item"),
            replace(valid, relative_path="nested\\item"),
            replace(valid, code="Unstable Code"),
            replace(valid, code="unknown_warning_code"),
            replace(valid, detail="failed at /machine/private/item"),
            replace(valid, detail="failed at C:\\machine\\private\\item"),
        )

        self._build([], warnings=[valid])
        for warning in invalid_warnings:
            with self.subTest(warning=repr(warning)):
                with self.assertRaisesRegex(ValueError, "^invalid_warning_record$"):
                    self._build([], warnings=[warning])

    def test_repeated_exact_alias_is_an_identity_collision(self) -> None:
        alias = self._alias("root-alpha", "same/item.json", b"same")

        with self.assertRaisesRegex(ValueError, "^identity_collision$"):
            self._build([alias, alias])

    def test_same_asset_with_png_and_webp_aliases_is_not_self_derivative(self) -> None:
        payload = b"one byte identity with two filename extensions"
        aliases = [
            self._alias("root-alpha", "topic/hero.png", payload),
            self._alias("root-bravo", "topic/HERO.WEBP", payload),
        ]

        inventory = self._build(aliases)

        self.assertEqual(1, len(inventory["assets"]))
        self.assertEqual([], inventory["derivative_candidate_groups"])

    def test_derivative_members_are_unique_assets_and_omit_ambiguous_identity(self) -> None:
        aliases = [
            self._alias("root-alpha", "topic/hero.png", b"ambiguous"),
            self._alias("root-alpha", "topic/HERO.webp", b"ambiguous"),
            self._alias("root-bravo", "topic/hero.png", b"source"),
            self._alias("root-bravo", "topic/hero.webp", b"derivative"),
        ]

        inventory = self._build(aliases)

        groups = inventory["derivative_candidate_groups"]
        self.assertEqual(1, len(groups))
        member_ids = [member["migration_asset_id"] for member in groups[0]["members"]]
        self.assertEqual(2, len(member_ids))
        self.assertEqual(2, len(set(member_ids)))
        self.assertNotIn(
            "mig_sha256_" + hashlib.sha256(b"ambiguous").hexdigest(),
            member_ids,
        )

    def test_duplicate_aliases_or_merge_structural_evidence_and_media_types(self) -> None:
        payload = b"shared structural content"
        aliases = [
            self._alias("root-alpha", "01_content/fact.json", payload),
            self._alias("root-bravo", "notes/copy.txt", payload),
        ]

        inventory = self._build(aliases)
        asset = inventory["assets"][0]

        self.assertTrue(asset["structural_evidence"]["fact"])
        self.assertEqual(
            ["application/json", "text/plain"], asset["media_types"]
        )
        self.assertEqual(2, len(asset["source_aliases"]))

    def test_aggregation_is_independent_of_random_alias_input_order(self) -> None:
        aliases = [
            self._alias("root-alpha", "topic/hero.png", b"png"),
            self._alias("root-bravo", "topic/HERO.webp", b"webp"),
            self._alias("root-alpha", "one/Caf\u00e9.json", b"first"),
            self._alias("root-charlie", "two/CAFE\u0301.JSON", b"second"),
            self._alias("root-alpha", "copies/shared.txt", b"shared"),
            self._alias("root-bravo", "other/shared-copy.txt", b"shared"),
        ]
        expected = self._build(aliases)
        generator = random.Random(20260713)

        for _ in range(10):
            shuffled = list(aliases)
            generator.shuffle(shuffled)
            self.assertEqual(expected, self._build(shuffled))


class WriterAndCliTests(unittest.TestCase):
    GENERATED_AT = "2026-07-13T02:03:04Z"

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name).resolve(strict=True)
        self.source = self.base / "source"
        self.source.mkdir()
        self.config_path = self.base / "inventory-sources.json"
        self.roots_path = self.base / "inventory-roots.json"
        self.output = self.base / "generated"
        self._write_config()

    def _write_config(self, *, config_override: object | None = None) -> None:
        config: object = config_override or {
            "schema": SCHEMA,
            "defaults": {
                "include_extensions": [".txt", ".md"],
                "exclude_names": [".git", "tmp"],
            },
            "sources": [
                {
                    "root_id": "fixture-root",
                    "source_group": "fixture-root",
                    "locator": {"base": "workspace", "relative": "source"},
                    "source_thread_id": None,
                    "migration_grade": "A",
                    "decision": "strict_revalidate",
                }
            ],
        }
        roots = {
            "schema": ROOTS_SCHEMA,
            "bases": {
                "workspace": str(self.base),
                "codex_archive": str(self.base / "archive"),
            },
        }
        (self.base / "archive").mkdir(exist_ok=True)
        self.config_path.write_text(
            json.dumps(config, ensure_ascii=False), encoding="utf-8"
        )
        self.roots_path.write_text(
            json.dumps(roots, ensure_ascii=False), encoding="utf-8"
        )

    def _config(self) -> SourceConfig:
        return load_source_config(
            self.config_path, self.roots_path, strict_roots=True
        )

    def _alias(
        self, relative_path: str, payload: bytes, *, root_id: str = "fixture-root"
    ) -> SourceAliasRecord:
        return SourceAliasRecord(
            root_id=root_id,
            relative_path=relative_path,
            source_thread_id=None,
            source_group="fixture-root",
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            media_type="text/plain",
            image_width=None,
            image_height=None,
            pdf_page_count=None,
            metadata_status="not_applicable",
        )

    def _publish(
        self,
        aliases: list[SourceAliasRecord],
        warnings: list[WarningRecord] | None = None,
        *,
        generated_at: str | None = None,
    ) -> dict[str, object]:
        with patch.object(
            inventory_module,
            "metadata_reader_versions",
            return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
        ):
            return inventory_module.publish_inventory_snapshot(
                self._config(),
                aliases,
                warnings or [],
                config_path=self.config_path,
                roots_path=self.roots_path,
                output_root=self.output,
                generated_at=generated_at or self.GENERATED_AT,
            )

    def test_deterministic_json_uses_utf8_sorted_indent_and_newline(self) -> None:
        rendered = inventory_module.deterministic_json_text(
            {"z": "兔子", "a": {"b": 1}}
        )

        self.assertEqual(
            '{\n  "a": {\n    "b": 1\n  },\n  "z": "兔子"\n}\n', rendered
        )

    def test_snapshot_documents_share_identity_and_markdown_escapes_values(self) -> None:
        aliases = [
            self._alias("one/odd|`[name]\n\x85\u2028\u200b.txt", b"first"),
            self._alias("two/odd|`[name]\n.txt", b"second"),
            self._alias("copies/shared.txt", b"first"),
        ]
        warning_records = [
            WarningRecord(
                root_id="fixture-root",
                relative_path="odd|`[name]\n.txt",
                code="unsupported_extension",
                detail="extension is not enabled for this root",
            )
        ]

        with patch.object(
            inventory_module,
            "metadata_reader_versions",
            return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
        ):
            documents = inventory_module.build_snapshot_documents(
                self._config(), aliases, warning_records, generated_at=self.GENERATED_AT
            )

        inventory = json.loads(documents["inventory.json"])
        warnings_document = json.loads(documents["scan-warnings.json"])
        report = documents["duplicate-report.md"]
        run_id = inventory["run_id"]
        digest = inventory["snapshot_digest"]
        self.assertRegex(run_id, r"^inv_sha256_[0-9a-f]{64}$")
        self.assertEqual("sha256:" + run_id.removeprefix("inv_sha256_"), digest)
        self.assertEqual(run_id, warnings_document["run_id"])
        self.assertEqual(digest, warnings_document["snapshot_digest"])
        self.assertIn(f'run_id: "{run_id}"', report)
        self.assertIn(f'snapshot_digest: "{digest}"', report)
        for field in (
            "content_object_count",
            "duplicate_group_count",
            "same_name_candidate_group_count",
            "total_source_bytes",
            "unique_content_bytes",
            "Aliases",
            "Same-name, different-digest candidates",
        ):
            self.assertIn(field, report)
        self.assertNotIn("odd|`[name]\n.txt", report)
        self.assertIn(r"odd\|\`\[name\]\\n.txt", report)
        for unsafe_character, escaped in (
            ("\x85", r"\u0085"),
            ("\u2028", r"\u2028"),
            ("\u200b", r"\u200b"),
        ):
            self.assertNotIn(unsafe_character, report)
            self.assertIn(escaped, report)

    def test_warnings_document_preserves_all_required_reason_codes(self) -> None:
        required_codes = (
            "missing_root",
            "symlink",
            "unreadable_file",
            "unsupported_extension",
            "source_changed_during_scan",
        )
        warnings = [
            WarningRecord(
                root_id="fixture-root",
                relative_path=".",
                code=code,
                detail="source entry was not included in this inventory",
            )
            for code in required_codes
        ]

        with patch.object(
            inventory_module,
            "metadata_reader_versions",
            return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
        ):
            document = json.loads(
                inventory_module.build_snapshot_documents(
                    self._config(), [], warnings, generated_at=self.GENERATED_AT
                )["scan-warnings.json"]
            )

        self.assertEqual(list(required_codes), [item["code"] for item in document["warnings"]])

    def test_publication_path_validation_rejects_collisions_containment_and_symlinks(self) -> None:
        config = self._config()
        unsafe_outputs = (
            self.source,
            self.source / "nested-output",
            self.base,
            self.config_path,
            self.roots_path,
        )
        for output in unsafe_outputs:
            with self.subTest(output=output.name):
                with self.assertRaises(ConfigError):
                    inventory_module.validate_publication_paths(
                        config,
                        config_path=self.config_path,
                        roots_path=self.roots_path,
                        output_root=output,
                    )

        with self.assertRaises(ConfigError):
            inventory_module.validate_publication_paths(
                config,
                config_path=self.config_path,
                roots_path=self.config_path,
                output_root=self.output,
            )

        symlink = self.base / "output-link"
        try:
            symlink.symlink_to(self.base / "real-output", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ConfigError):
            inventory_module.validate_publication_paths(
                config,
                config_path=self.config_path,
                roots_path=self.roots_path,
                output_root=symlink / "nested",
            )
        self.assertFalse((self.base / "real-output").exists())

    def test_publication_rejects_config_and_root_map_containment_before_writing(self) -> None:
        config = self._config()
        for protected_kind in ("config", "roots"):
            with self.subTest(protected_kind=protected_kind):
                output = self.base / f"publish-{protected_kind}"
                output.mkdir()
                protected = output / "latest.json"
                original_path = (
                    self.config_path if protected_kind == "config" else self.roots_path
                )
                protected.write_bytes(original_path.read_bytes())
                before = protected.read_bytes()
                kwargs = {
                    "config_path": protected if protected_kind == "config" else self.config_path,
                    "roots_path": protected if protected_kind == "roots" else self.roots_path,
                    "output_root": output,
                    "generated_at": self.GENERATED_AT,
                }

                with self.assertRaises(ConfigError) as caught:
                    inventory_module.publish_inventory_snapshot(
                        config, [], [], **kwargs
                    )

                self.assertEqual(before, protected.read_bytes())
                self.assertEqual(["latest.json"], sorted(path.name for path in output.iterdir()))
                self.assertNotIn(str(self.base), str(caught.exception))

        protected_directory = self.base / "protected-files"
        protected_directory.mkdir()
        protected_config = protected_directory / "config.json"
        protected_roots = protected_directory / "roots.json"
        protected_config.write_bytes(self.config_path.read_bytes())
        protected_roots.write_bytes(self.roots_path.read_bytes())
        for output, config_path, roots_path in (
            (protected_directory, protected_config, self.roots_path),
            (protected_directory, self.config_path, protected_roots),
            (protected_config / "nested", protected_config, self.roots_path),
            (protected_roots / "nested", self.config_path, protected_roots),
        ):
            with self.subTest(output=str(output.relative_to(self.base))):
                with self.assertRaises(ConfigError) as caught:
                    inventory_module.validate_publication_paths(
                        config,
                        config_path=config_path,
                        roots_path=roots_path,
                        output_root=output,
                    )
                self.assertNotIn(str(self.base), str(caught.exception))

        alias_directory = self.base / "path-alias"
        try:
            alias_directory.symlink_to(protected_directory, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        for config_path, roots_path in (
            (alias_directory / "config.json", self.roots_path),
            (self.config_path, alias_directory / "roots.json"),
        ):
            with self.subTest(alias=config_path.name if config_path != self.config_path else roots_path.name):
                with self.assertRaises(ConfigError):
                    inventory_module.validate_publication_paths(
                        config,
                        config_path=config_path,
                        roots_path=roots_path,
                        output_root=self.base / "unrelated-output",
                    )

    def test_failure_before_snapshot_rename_preserves_prior_publication(self) -> None:
        first = self._publish([self._alias("first.txt", b"first")])
        prior_latest = (self.output / "latest.json").read_bytes()
        prior_snapshot = self.output / "snapshots" / str(first["run_id"])
        prior_files = {
            path.name: path.read_bytes() for path in prior_snapshot.iterdir()
        }

        with patch.object(
            inventory_module,
            "_rename_staging_to_snapshot",
            side_effect=OSError("simulated publication failure"),
        ):
            with self.assertRaises(ConfigError):
                self._publish([self._alias("second.txt", b"second")])

        self.assertEqual(prior_latest, (self.output / "latest.json").read_bytes())
        self.assertEqual(
            prior_files,
            {path.name: path.read_bytes() for path in prior_snapshot.iterdir()},
        )
        self.assertEqual([], list(self.output.glob(".staging-*")))

    def test_no_replace_race_preserves_inserted_snapshot_inode(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        inserted_inode: int | None = None
        inserted_run_id: str | None = None

        def racing_noreplace(
            source_dir_fd, source_name, destination_dir_fd, destination_name
        ):
            nonlocal inserted_inode, inserted_run_id
            os.mkdir(destination_name, 0o755, dir_fd=destination_dir_fd)
            inserted_inode = os.stat(
                destination_name,
                dir_fd=destination_dir_fd,
                follow_symlinks=False,
            ).st_ino
            inserted_run_id = destination_name
            raise FileExistsError(errno.EEXIST, "destination exists")

        with patch.object(
            inventory_module,
            "_rename_directory_noreplace",
            side_effect=racing_noreplace,
        ):
            with self.assertRaises(ConfigError):
                self._publish(aliases)

        self.assertIsNotNone(inserted_run_id)
        destination = self.output / "snapshots" / str(inserted_run_id)
        self.assertTrue(destination.is_dir())
        self.assertEqual(inserted_inode, destination.stat().st_ino)
        self.assertEqual([], list(destination.iterdir()))
        self.assertEqual([], list(self.output.glob(".staging-*")))
        self.assertFalse((self.output / "latest.json").exists())

    def test_first_staging_open_failure_cleans_only_new_staging_directory(self) -> None:
        self.output.mkdir()
        unrelated = self.output / "keep.txt"
        unrelated.write_bytes(b"unrelated output must remain")
        real_open = os.open
        injected = False

        def failing_first_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal injected
            if (
                not injected
                and isinstance(path, str)
                and path.startswith(".staging-")
                and dir_fd is not None
            ):
                injected = True
                raise OSError("simulated first staging open failure")
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with patch.object(os, "open", side_effect=failing_first_open):
            with self.assertRaises(ConfigError):
                self._publish([self._alias("item.txt", b"payload")])

        self.assertTrue(injected)
        self.assertEqual(b"unrelated output must remain", unrelated.read_bytes())
        self.assertEqual([], list(self.output.glob(".staging-*")))

    def test_cleanup_preserves_same_name_replacement_after_initial_stat_race(self) -> None:
        self.output.mkdir()
        real_stat = os.stat
        injected = False
        replacement_name: str | None = None
        replacement_inode: int | None = None
        orphan_name = ".orphaned-original-staging"

        def replacing_stat(path, *args, **kwargs):
            nonlocal injected, replacement_name, replacement_inode
            directory_fd = kwargs.get("dir_fd")
            if (
                not injected
                and isinstance(path, str)
                and path.startswith(".staging-")
                and directory_fd is not None
            ):
                injected = True
                replacement_name = path
                os.rename(
                    path,
                    orphan_name,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
                os.mkdir(path, 0o700, dir_fd=directory_fd)
                replacement_inode = real_stat(
                    path, dir_fd=directory_fd, follow_symlinks=False
                ).st_ino
                raise OSError("simulated identity stat race")
            return real_stat(path, *args, **kwargs)

        with patch.object(os, "stat", side_effect=replacing_stat):
            with self.assertRaises(ConfigError):
                self._publish([self._alias("item.txt", b"payload")])

        self.assertTrue(injected)
        replacement = self.output / str(replacement_name)
        self.assertTrue(replacement.is_dir())
        self.assertEqual(replacement_inode, replacement.stat().st_ino)
        self.assertTrue((self.output / orphan_name).is_dir())

    def test_first_staging_stat_failure_also_cleans_new_empty_directory(self) -> None:
        self.output.mkdir()
        unrelated = self.output / "keep.txt"
        unrelated.write_bytes(b"unrelated output must remain")
        real_stat = os.stat
        injected = False

        def failing_first_stat(path, *args, **kwargs):
            nonlocal injected
            if (
                not injected
                and isinstance(path, str)
                and path.startswith(".staging-")
                and kwargs.get("dir_fd") is not None
            ):
                injected = True
                raise OSError("simulated first staging stat failure")
            return real_stat(path, *args, **kwargs)

        with patch.object(os, "stat", side_effect=failing_first_stat):
            with self.assertRaises(ConfigError):
                self._publish([self._alias("item.txt", b"payload")])

        self.assertTrue(injected)
        self.assertEqual(b"unrelated output must remain", unrelated.read_bytes())
        self.assertEqual([], list(self.output.glob(".staging-*")))

    def test_staging_orphan_remains_visible_when_identity_cannot_be_captured(self) -> None:
        self.output.mkdir()
        real_open = os.open
        real_stat = os.stat

        def unavailable_open(path, flags, mode=0o777, *, dir_fd=None):
            if (
                isinstance(path, str)
                and path.startswith(".staging-")
                and dir_fd is not None
            ):
                raise OSError("staging open unavailable")
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        def unavailable_stat(path, *args, **kwargs):
            if (
                isinstance(path, str)
                and path.startswith(".staging-")
                and kwargs.get("dir_fd") is not None
            ):
                raise OSError("staging stat unavailable")
            return real_stat(path, *args, **kwargs)

        with patch.object(os, "open", side_effect=unavailable_open):
            with patch.object(os, "stat", side_effect=unavailable_stat):
                with self.assertRaises(ConfigError):
                    self._publish([self._alias("item.txt", b"payload")])

        orphans = list(self.output.glob(".staging-*"))
        self.assertEqual(1, len(orphans))
        self.assertTrue(orphans[0].is_dir())
        self.assertEqual([], list(orphans[0].iterdir()))

    def test_output_swap_race_never_writes_through_symlink_into_source(self) -> None:
        output = self.base / "race-output"
        output.mkdir()
        source_file = self.source / "unchanged.txt"
        source_file.write_bytes(b"source must stay byte-for-byte unchanged")
        before_bytes = source_file.read_bytes()
        before_entries = sorted(path.name for path in self.source.iterdir())
        displaced = self.base / "race-output-detached"
        real_mkdir = os.mkdir
        swapped = False

        def racing_mkdir(path, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            if not swapped and Path(path).name == "snapshots":
                swapped = True
                output.rename(displaced)
                output.symlink_to(self.source, target_is_directory=True)
            if dir_fd is None:
                return real_mkdir(path, mode)
            return real_mkdir(path, mode, dir_fd=dir_fd)

        with patch.object(os, "mkdir", side_effect=racing_mkdir):
            with self.assertRaises(ConfigError):
                inventory_module.publish_inventory_snapshot(
                    self._config(), [], [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=output,
                    generated_at=self.GENERATED_AT,
                )

        self.assertTrue(swapped)
        self.assertEqual(before_bytes, source_file.read_bytes())
        self.assertEqual(before_entries, sorted(path.name for path in self.source.iterdir()))

    def test_check_ignores_only_generated_at_and_requires_complete_snapshot(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        self._publish(aliases)

        with patch.object(
            inventory_module,
            "metadata_reader_versions",
            return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
        ):
            self.assertTrue(
                inventory_module.check_inventory_snapshot(
                    self._config(),
                    aliases,
                    [],
                    config_path=self.config_path,
                    roots_path=self.roots_path,
                    output_root=self.output,
                    generated_at="2030-01-02T03:04:05Z",
                )
            )

        latest_path = self.output / "latest.json"
        latest_text = latest_path.read_text(encoding="utf-8")
        external_latest = self.base / "outside-latest.json"
        external_latest.write_text(latest_text, encoding="utf-8")
        latest_path.unlink()
        try:
            latest_path.symlink_to(external_latest)
        except (OSError, NotImplementedError):
            latest_path.write_text(latest_text, encoding="utf-8")
        else:
            with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
                self.assertFalse(
                    inventory_module.check_inventory_snapshot(
                        self._config(), aliases, [], config_path=self.config_path,
                        roots_path=self.roots_path, output_root=self.output,
                        generated_at=self.GENERATED_AT,
                    )
                )
            latest_path.unlink()
            latest_path.write_text(latest_text, encoding="utf-8")

        latest = json.loads(latest_text)
        inventory_path = self.output / latest["inventory"]
        original = inventory_path.read_text(encoding="utf-8")
        changed = json.loads(original)
        changed["summary"]["content_object_count"] += 1
        inventory_path.write_text(json.dumps(changed), encoding="utf-8")
        with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
            self.assertFalse(
                inventory_module.check_inventory_snapshot(
                    self._config(), aliases, [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=self.output,
                    generated_at=self.GENERATED_AT,
                )
            )
        inventory_path.write_text(original, encoding="utf-8")
        report_path = self.output / latest["duplicates"]
        original_report = report_path.read_text(encoding="utf-8")
        report_path.write_text(original_report.rstrip("\n"), encoding="utf-8")
        with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
            self.assertFalse(
                inventory_module.check_inventory_snapshot(
                    self._config(), aliases, [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=self.output,
                    generated_at=self.GENERATED_AT,
                )
            )
        report_path.write_text(original_report, encoding="utf-8")
        report_path.unlink()
        with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
            self.assertFalse(
                inventory_module.check_inventory_snapshot(
                    self._config(), aliases, [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=self.output,
                    generated_at=self.GENERATED_AT,
                )
            )

    def test_existing_snapshot_is_immutable_and_must_be_semantically_equal(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        published = self._publish(aliases)
        snapshot = self.output / "snapshots" / str(published["run_id"])
        inventory_path = snapshot / "inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["summary"]["source_alias_count"] += 1
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

        with self.assertRaises(ConfigError):
            self._publish(aliases, generated_at="2030-01-02T03:04:05Z")

    def test_snapshot_files_with_external_hardlinks_are_rejected(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        published = self._publish(aliases)
        snapshot = self.output / "snapshots" / str(published["run_id"])
        linked = self.base / "external-inventory-link.json"
        try:
            os.link(snapshot / "inventory.json", linked)
        except OSError:
            self.skipTest("hard links unavailable")

        with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
            self.assertFalse(
                inventory_module.check_inventory_snapshot(
                    self._config(), aliases, [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=self.output,
                    generated_at="2030-01-02T03:04:05Z",
                )
            )
        with self.assertRaises(ConfigError):
            self._publish(aliases, generated_at="2030-01-02T03:04:05Z")

    def test_snapshot_identity_is_reverified_inside_latest_replacement(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        published = self._publish(aliases)
        snapshot = self.output / "snapshots" / str(published["run_id"])
        inventory_path = snapshot / "inventory.json"
        prior_latest = (self.output / "latest.json").read_bytes()
        real_write = inventory_module._write_new_file_at
        replaced = False

        def racing_write(directory_fd, name, content):
            nonlocal replaced
            real_write(directory_fd, name, content)
            if not replaced and name.startswith(".latest-"):
                replaced = True
                payload = inventory_path.read_bytes()
                old_path = snapshot / "inventory.old"
                inventory_path.rename(old_path)
                inventory_path.write_bytes(payload)
                old_path.unlink()

        with patch.object(
            inventory_module, "_write_new_file_at", side_effect=racing_write
        ):
            with self.assertRaises(ConfigError):
                self._publish(aliases, generated_at="2030-01-02T03:04:05Z")

        self.assertTrue(replaced)
        self.assertEqual(prior_latest, (self.output / "latest.json").read_bytes())

    def test_publication_attach_failure_does_not_leak_descriptors(self) -> None:
        fd_root = Path("/dev/fd") if Path("/dev/fd").is_dir() else Path("/proc/self/fd")
        if not fd_root.is_dir():
            self.skipTest("descriptor count is unavailable")
        output = self.base / "fd-output"
        output.mkdir()
        before = len(list(fd_root.iterdir()))
        real_stat = os.stat
        injected = False

        def failing_stat(path, *args, **kwargs):
            nonlocal injected
            if not injected and path == output.name and kwargs.get("dir_fd") is not None:
                injected = True
                raise OSError("simulated descriptor identity failure")
            return real_stat(path, *args, **kwargs)

        with patch.object(os, "stat", side_effect=failing_stat):
            with self.assertRaises(ConfigError):
                inventory_module.publish_inventory_snapshot(
                    self._config(), [], [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=output,
                    generated_at=self.GENERATED_AT,
                )

        self.assertTrue(injected)
        self.assertEqual(before, len(list(fd_root.iterdir())))

    def test_latest_rejects_duplicate_keys_at_the_first_or_last_position(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        self._publish(aliases)
        latest_path = self.output / "latest.json"
        original = latest_path.read_text(encoding="utf-8")
        duplicate_documents = (
            original.replace("{\n", '{\n  "run_id": "attacker-first",\n', 1),
            original.rstrip("\n}") + ',\n  "run_id": "' + json.loads(original)["run_id"] + '"\n}\n',
        )

        for index, document in enumerate(duplicate_documents):
            with self.subTest(position=index):
                latest_path.write_text(document, encoding="utf-8")
                with patch.object(inventory_module, "metadata_reader_versions", return_value={"pillow": "12.0.0", "pypdf": "6.0.0"}):
                    self.assertFalse(
                        inventory_module.check_inventory_snapshot(
                            self._config(), aliases, [], config_path=self.config_path,
                            roots_path=self.roots_path, output_root=self.output,
                            generated_at="2030-01-02T03:04:05Z",
                        )
                    )
        latest_path.write_text(original, encoding="utf-8")

    def test_check_requires_valid_top_level_generated_at_in_complete_documents(self) -> None:
        aliases = [self._alias("item.txt", b"payload")]
        published = self._publish(aliases)
        snapshot = self.output / "snapshots" / str(published["run_id"])

        def check() -> bool:
            with patch.object(
                inventory_module,
                "metadata_reader_versions",
                return_value={"pillow": "12.0.0", "pypdf": "6.0.0"},
            ):
                return inventory_module.check_inventory_snapshot(
                    self._config(), aliases, [], config_path=self.config_path,
                    roots_path=self.roots_path, output_root=self.output,
                    generated_at="2030-01-02T03:04:05Z",
                )

        for filename in ("inventory.json", "scan-warnings.json"):
            document_path = snapshot / filename
            original = document_path.read_text(encoding="utf-8")
            value = json.loads(original)
            mutations = []
            missing = dict(value)
            del missing["generated_at"]
            mutations.append(json.dumps(missing, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            wrong_type = dict(value)
            wrong_type["generated_at"] = 42
            mutations.append(json.dumps(wrong_type, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            nested = json.loads(original)
            nested.setdefault("summary", {})["generated_at"] = self.GENERATED_AT
            mutations.append(json.dumps(nested, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            duplicate = original.replace(
                f'  "generated_at": "{self.GENERATED_AT}",',
                f'  "generated_at": "{self.GENERATED_AT}",\n  "generated_at": "{self.GENERATED_AT}",',
                1,
            )
            mutations.append(duplicate)
            for index, mutated in enumerate(mutations):
                with self.subTest(filename=filename, mutation=index):
                    document_path.write_text(mutated, encoding="utf-8")
                    self.assertFalse(check())
            document_path.write_text(original, encoding="utf-8")

        report_path = snapshot / "duplicate-report.md"
        original_report = report_path.read_text(encoding="utf-8")
        report_path.write_text(
            original_report.replace(
                f'generated_at: "{self.GENERATED_AT}"\n', "", 1
            ),
            encoding="utf-8",
        )
        self.assertFalse(check())

    def test_dry_run_summary_hashes_sorted_descriptors_without_reading_contents(self) -> None:
        first = self.source / "b.txt"
        second = self.source / "a.md"
        unsupported = self.source / "ignored.bin"
        first.write_bytes(b"12345")
        second.write_bytes(b"678")
        unsupported.write_bytes(b"ignored")
        rows = []
        for path in (first, second):
            file_stat = path.stat()
            rows.append(
                (
                    file_stat.st_dev,
                    file_stat.st_ino,
                    path.relative_to(self.source).as_posix(),
                    file_stat.st_size,
                    file_stat.st_mtime_ns,
                    file_stat.st_ctime_ns,
                )
            )
        expected_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                sorted(rows), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

        with patch.object(
            inventory_module,
            "sha256_descriptor",
            side_effect=AssertionError("content hashing is forbidden"),
        ):
            summary = inventory_module.build_dry_run_summary(self._config())

        self.assertEqual(1, summary["declared_root_count"])
        self.assertEqual(2, summary["eligible_file_count"])
        self.assertEqual(8, summary["eligible_byte_count"])
        self.assertEqual(expected_digest, summary["descriptor_digest"])
        self.assertFalse(self.output.exists())

    def test_dry_run_fails_closed_on_walk_warnings_even_after_callback(self) -> None:
        source_file = self.source / "item.txt"
        source_file.write_bytes(b"unchanged source")
        original_bytes = source_file.read_bytes()
        warning_codes = (
            "source_changed_during_scan",
            "unsafe_source_entry",
            "unreadable_file",
            "unreadable_directory",
        )

        for warning_code in warning_codes:
            def warning_walk(rule, on_file, code=warning_code):
                descriptor = os.open(source_file, os.O_RDONLY)
                try:
                    on_file(
                        PurePosixPath("item.txt"), descriptor, os.fstat(descriptor)
                    )
                finally:
                    os.close(descriptor)
                return [
                    WarningRecord(
                        root_id=rule.root_id,
                        relative_path="item.txt",
                        code=code,
                        detail="declared source could not be summarized safely",
                    )
                ]

            with self.subTest(code=warning_code):
                with patch.object(inventory_module, "walk_source", side_effect=warning_walk):
                    with self.assertRaises(ConfigError):
                        inventory_module.build_dry_run_summary(self._config())

        missing_config = replace(
            self._config(),
            warnings=(
                ConfigWarning(
                    root_id="fixture-root",
                    code="missing_root",
                    detail="declared source root does not exist on this machine",
                ),
            ),
        )
        with self.assertRaises(ConfigError):
            inventory_module.build_dry_run_summary(missing_config)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(inventory_module, "walk_source", side_effect=warning_walk):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = inventory_module.main(
                    [
                        "--config", str(self.config_path),
                        "--roots", str(self.roots_path),
                        "--output-root", str(self.output),
                        "--dry-run-summary",
                    ]
                )
        self.assertNotEqual(0, status)
        self.assertEqual("", stdout.getvalue())
        self.assertEqual(original_bytes, source_file.read_bytes())

    def test_cli_dry_run_writes_only_stdout_and_validates_generated_at(self) -> None:
        (self.source / "item.txt").write_text("兔子", encoding="utf-8")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = inventory_module.main(
                [
                    "--config", str(self.config_path),
                    "--roots", str(self.roots_path),
                    "--output-root", str(self.output),
                    "--generated-at", self.GENERATED_AT,
                    "--dry-run-summary",
                ]
            )
        self.assertEqual(0, status)
        self.assertEqual(1, json.loads(stdout.getvalue())["eligible_file_count"])
        self.assertFalse(self.output.exists())

        for invalid in (
            "2026-07-13T02:03:04+00:00",
            "2026-07-13T02:03:04.000Z",
            "2026-02-30T02:03:04Z",
            "not-a-time",
        ):
            with self.subTest(invalid=invalid):
                with redirect_stderr(io.StringIO()):
                    self.assertNotEqual(
                        0,
                        inventory_module.main(
                            [
                                "--config", str(self.config_path),
                                "--roots", str(self.roots_path),
                                "--output-root", str(self.output),
                                "--generated-at", invalid,
                                "--dry-run-summary",
                            ]
                        ),
                    )

    def test_cli_invalid_config_is_nonzero_and_source_tree_is_unchanged(self) -> None:
        source_file = self.source / "keep.txt"
        source_file.write_bytes(b"must remain unchanged")
        before = (source_file.stat(), source_file.read_bytes())
        self._write_config(config_override={"schema": "wrong"})

        with redirect_stderr(io.StringIO()):
            status = inventory_module.main(
                [
                    "--config", str(self.config_path),
                    "--roots", str(self.roots_path),
                    "--output-root", str(self.output),
                ]
            )

        after = (source_file.stat(), source_file.read_bytes())
        self.assertNotEqual(0, status)
        self.assertEqual(before, after)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
