from __future__ import annotations

import os
import re
import stat
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "cognitive-card-os"

SOURCE_FILES = {
    "SKILL.md": 0o644,
    "agents/openai.yaml": 0o644,
    "scripts/card_os_client.py": 0o755,
    "references/protocol.md": 0o644,
    "references/errors.md": 0o644,
}

FORBIDDEN_AUXILIARY_FILES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "CHANGELOG.md",
}
RAW_CARD_OS_TOKEN = re.compile(
    rb"ccos_v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+"
)
ABSOLUTE_WORKSTATION_PATH = re.compile(
    rb"(?:/Users/[^\s\x00]+|/home/[^\s\x00]+|[A-Za-z]:\\\\[^\s\x00]+)"
)


class CardOsSkillSourceTests(unittest.TestCase):
    def test_source_tree_is_the_exact_five_file_closure(self) -> None:
        self.assertTrue(
            SKILL_ROOT.is_dir(),
            "missing governed Skill source: skills/cognitive-card-os",
        )

        actual_files: set[str] = set()
        for directory, directory_names, file_names in os.walk(
            SKILL_ROOT, followlinks=False
        ):
            directory_path = Path(directory)
            for name in directory_names:
                path = directory_path / name
                self.assertFalse(path.is_symlink(), f"directory is a symlink: {path}")
            for name in file_names:
                path = directory_path / name
                relative = path.relative_to(SKILL_ROOT).as_posix()
                actual_files.add(relative)
                self.assertFalse(path.is_symlink(), f"file is a symlink: {relative}")
                self.assertTrue(path.is_file(), f"not a regular file: {relative}")

        self.assertEqual(set(SOURCE_FILES), actual_files)
        self.assertTrue(FORBIDDEN_AUXILIARY_FILES.isdisjoint(actual_files))

    def test_source_modes_are_canonical(self) -> None:
        for relative, expected_mode in SOURCE_FILES.items():
            path = SKILL_ROOT / relative
            self.assertTrue(path.exists(), f"missing source file: {relative}")
            self.assertFalse(path.is_symlink(), f"source file is a symlink: {relative}")
            self.assertTrue(path.is_file(), f"not a regular file: {relative}")
            self.assertEqual(expected_mode, stat.S_IMODE(path.stat().st_mode), relative)

    def test_source_contains_no_credentials_or_workstation_paths(self) -> None:
        for relative in SOURCE_FILES:
            content = (SKILL_ROOT / relative).read_bytes()
            self.assertIsNone(RAW_CARD_OS_TOKEN.search(content), relative)
            self.assertNotIn(b"OPENAI_API_KEY", content, relative)
            self.assertIsNone(ABSOLUTE_WORKSTATION_PATH.search(content), relative)

    def test_skill_frontmatter_has_only_name_and_description(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        _, frontmatter, body = skill.split("---\n", maxsplit=2)

        fields: dict[str, str] = {}
        for line in frontmatter.splitlines():
            key, separator, value = line.partition(":")
            self.assertEqual(":", separator, f"invalid frontmatter line: {line!r}")
            fields[key.strip()] = value.strip()

        self.assertEqual({"name", "description"}, set(fields))
        self.assertEqual("cognitive-card-os", fields["name"])
        self.assertTrue(fields["description"])
        self.assertTrue(body.strip())


if __name__ == "__main__":
    unittest.main()
