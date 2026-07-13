from __future__ import annotations

import hashlib
import json
import os
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.card_os_asset_inventory import (
    ConfigError,
    canonical_config_digest,
    load_source_config,
    metadata_reader_versions,
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


if __name__ == "__main__":
    unittest.main()
