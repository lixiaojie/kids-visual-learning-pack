from __future__ import annotations

import os
import hashlib
import importlib.util
import inspect
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import warnings
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


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

BUILDER_PATH = ROOT / "ops" / "cognitive-card-skill" / "build_release.py"
if not BUILDER_PATH.is_file():
    raise FileNotFoundError(f"missing deterministic release builder: {BUILDER_PATH}")
BUILDER_SPEC = importlib.util.spec_from_file_location(
    "card_os_skill_build_release", BUILDER_PATH
)
assert BUILDER_SPEC is not None and BUILDER_SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(BUILDER)


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


@contextmanager
def process_timezone(value: str):
    previous = os.environ.get("TZ")
    os.environ["TZ"] = value
    if hasattr(time, "tzset"):
        time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        if hasattr(time, "tzset"):
            time.tzset()


class GitSkillFixture:
    def __init__(self, root: Path, *, epoch: int = 1_735_689_601) -> None:
        self.root = root
        self.epoch = epoch
        self.skill_root = root / "skills" / "cognitive-card-os"

    def git(self, *arguments: str, env: dict[str, str] | None = None) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()

    def initialize(self) -> str:
        contents = {
            "SKILL.md": b"---\nname: cognitive-card-os\ndescription: Fixture\n---\nFixture.\n",
            "agents/openai.yaml": b"interface:\n  display_name: Fixture\n",
            "scripts/card_os_client.py": b"#!/usr/bin/env python3\nprint('fixture')\n",
            "references/protocol.md": b"# Protocol\n\nFixture.\n",
            "references/errors.md": b"# Errors\n\nFixture.\n",
        }
        for relative, content in contents.items():
            path = self.skill_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(SOURCE_FILES[relative])

        self.git("init", "-q")
        self.git("config", "user.name", "Card OS Test")
        self.git("config", "user.email", "card-os-test@example.invalid")
        self.git("add", "skills/cognitive-card-os")
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_DATE": f"@{self.epoch} +0000",
                "GIT_COMMITTER_DATE": f"@{self.epoch} +0000",
            }
        )
        self.git("commit", "-q", "-m", "fixture", env=environment)
        return self.git("rev-parse", "HEAD")


class CardOsSkillReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name)
        self.repository = self.base / "repository"
        self.repository.mkdir()
        self.fixture = GitSkillFixture(self.repository)
        self.commit = self.fixture.initialize()

    def build(
        self,
        *,
        repository: Path | None = None,
        output_root: Path | None = None,
        expected_commit: str | None = None,
        version: str = "0.1.0",
    ) -> tuple[dict[str, object], Path]:
        selected_output_root = output_root or (self.base / "dist")
        result = BUILDER.build_release(
            repository=repository or self.repository,
            expected_commit=expected_commit or self.commit,
            output_root=selected_output_root,
            version=version,
        )
        return result, selected_output_root / version / "cognitive-card-os.zip"

    def assert_error(self, code: str, callback) -> None:
        with self.assertRaises(BUILDER.SkillReleaseError) as raised:
            callback()
        self.assertEqual(code, raised.exception.code)

    def rewrite_archive(self, archive: Path, mutate) -> Path:
        with zipfile.ZipFile(archive, "r") as source:
            members = [(info, source.read(info)) for info in source.infolist()]
        destination = archive.with_name(f"mutated-{time.time_ns()}.zip")
        mutated = sorted(mutate(members), key=lambda item: item[0].filename)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as target:
                for info, content in mutated:
                    target.writestr(info, content)
        return destination

    @staticmethod
    def clone_info(info: zipfile.ZipInfo, *, filename: str | None = None) -> zipfile.ZipInfo:
        clone = zipfile.ZipInfo(filename or info.filename, date_time=info.date_time)
        clone.create_system = info.create_system
        clone.compress_type = info.compress_type
        clone.external_attr = info.external_attr
        clone.extra = info.extra
        clone.comment = info.comment
        return clone

    def test_public_interfaces_and_argument_surface_are_stable(self) -> None:
        self.assertTrue(issubclass(BUILDER.SkillReleaseError, RuntimeError))
        self.assertEqual(
            {"repository", "expected_commit", "output_root", "version"},
            set(inspect.signature(BUILDER.build_release).parameters),
        )
        self.assertEqual(
            {"path"}, set(inspect.signature(BUILDER.validate_archive).parameters)
        )
        signature = str(inspect.signature(BUILDER.build_release))
        self.assertNotIn("published", signature)
        self.assertNotIn("channel", signature)

    def test_rejects_invalid_version_commit_and_wrong_head(self) -> None:
        self.assert_error(
            "INVALID_VERSION", lambda: self.build(version="v0.1")
        )
        self.assert_error(
            "INVALID_SOURCE_COMMIT",
            lambda: self.build(expected_commit="ABC"),
        )
        self.assert_error(
            "SOURCE_COMMIT_MISMATCH",
            lambda: self.build(expected_commit="0" * 40),
        )

    def test_rejects_dirty_tracked_and_untracked_source(self) -> None:
        skill = self.fixture.skill_root / "SKILL.md"
        original = skill.read_bytes()
        skill.write_bytes(original + b"dirty\n")
        self.assert_error("SOURCE_TREE_DIRTY", lambda: self.build())
        skill.write_bytes(original)
        extra = self.fixture.skill_root / "extra.txt"
        extra.write_text("untracked", encoding="utf-8")
        self.assert_error("SOURCE_TREE_DIRTY", lambda: self.build())

    def test_rejects_non_regular_git_entry(self) -> None:
        target = self.fixture.skill_root / "references" / "errors.md"
        target.unlink()
        target.symlink_to("protocol.md")
        self.fixture.git("add", "skills/cognitive-card-os/references/errors.md")
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_DATE": f"@{self.fixture.epoch + 2} +0000",
                "GIT_COMMITTER_DATE": f"@{self.fixture.epoch + 2} +0000",
            }
        )
        self.fixture.git("commit", "-q", "-m", "link", env=environment)
        commit = self.fixture.git("rev-parse", "HEAD")
        self.assert_error(
            "UNSAFE_SOURCE_ENTRY", lambda: self.build(expected_commit=commit)
        )

    def test_rejects_committed_source_tree_expansion(self) -> None:
        extra = self.fixture.skill_root / "README.md"
        extra.write_text("not part of the release closure", encoding="utf-8")
        self.fixture.git("add", "skills/cognitive-card-os/README.md")
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_DATE": f"@{self.fixture.epoch + 2} +0000",
                "GIT_COMMITTER_DATE": f"@{self.fixture.epoch + 2} +0000",
            }
        )
        self.fixture.git("commit", "-q", "-m", "extra", env=environment)
        commit = self.fixture.git("rev-parse", "HEAD")
        self.assert_error(
            "SOURCE_TREE_CLOSURE_MISMATCH",
            lambda: self.build(expected_commit=commit),
        )

    def test_identical_commit_is_identical_across_checkout_mtime_and_timezone(self) -> None:
        clone_a = self.base / "checkout-a"
        clone_b = self.base / "different" / "checkout-b"
        clone_b.parent.mkdir()
        subprocess.run(
            ["git", "clone", "-q", str(self.repository), str(clone_a)], check=True
        )
        subprocess.run(
            ["git", "clone", "-q", str(self.repository), str(clone_b)], check=True
        )
        for index, path in enumerate(
            (clone_b / "skills" / "cognitive-card-os").rglob("*")
        ):
            if path.is_file():
                os.utime(path, (2_000_000_000 + index, 2_000_000_000 + index))

        with process_timezone("Asia/Shanghai"):
            _, archive_a = self.build(
                repository=clone_a, output_root=self.base / "dist-a"
            )
        with process_timezone("UTC"):
            _, archive_b = self.build(
                repository=clone_b, output_root=self.base / "dist-b"
            )

        self.assertEqual(archive_a.read_bytes(), archive_b.read_bytes())
        self.assertEqual(
            hashlib.sha256(archive_a.read_bytes()).hexdigest(),
            hashlib.sha256(archive_b.read_bytes()).hexdigest(),
        )

    def test_builder_uses_gmtime_and_canonical_two_second_clamped_zip_time(self) -> None:
        with mock.patch.object(
            BUILDER.time, "gmtime", wraps=time.gmtime
        ) as observed_gmtime, mock.patch.object(
            BUILDER.time,
            "localtime",
            side_effect=AssertionError("local time is forbidden"),
        ):
            _, archive = self.build()
        observed_gmtime.assert_called()
        expected = time.gmtime(self.fixture.epoch)
        expected_tuple = (
            expected.tm_year,
            expected.tm_mon,
            expected.tm_mday,
            expected.tm_hour,
            expected.tm_min,
            expected.tm_sec - expected.tm_sec % 2,
        )
        with zipfile.ZipFile(archive) as release:
            self.assertTrue(release.infolist())
            self.assertEqual(
                {expected_tuple}, {info.date_time for info in release.infolist()}
            )
        self.assertEqual((1980, 1, 1, 0, 0, 0), BUILDER._zip_datetime(-1))
        self.assertEqual(
            (2107, 12, 31, 23, 59, 58), BUILDER._zip_datetime(10**20)
        )

    def test_archive_is_sorted_stored_canonical_closure(self) -> None:
        result, archive = self.build()
        self.assertEqual("0.1.0", result["version"])
        self.assertEqual(self.commit, result["source_commit"])
        self.assertEqual(
            hashlib.sha256(archive.read_bytes()).hexdigest(), result["archive_sha256"]
        )
        self.assertEqual(archive.stat().st_size, result["archive_size_bytes"])
        self.assertEqual(
            f"{result['archive_sha256']}  cognitive-card-os.zip\n",
            archive.with_name("sha256.txt").read_text(encoding="ascii"),
        )

        expected_names = sorted(
            [
                "cognitive-card-os/",
                "cognitive-card-os/agents/",
                "cognitive-card-os/references/",
                "cognitive-card-os/scripts/",
                *[f"cognitive-card-os/{name}" for name in SOURCE_FILES],
                "cognitive-card-os/release.json",
            ]
        )
        with zipfile.ZipFile(archive) as release:
            infos = release.infolist()
            self.assertEqual(expected_names, [info.filename for info in infos])
            self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in infos))
            self.assertTrue(all(info.create_system == 3 for info in infos))
            self.assertTrue(all(info.extra == b"" and info.comment == b"" for info in infos))
            for info in infos:
                mode = info.external_attr >> 16
                expected_mode = (
                    0o755
                    if info.is_dir() or info.filename.endswith("scripts/card_os_client.py")
                    else 0o644
                )
                self.assertEqual(expected_mode, mode, info.filename)

    def test_release_json_declares_exact_sources_without_channel_time(self) -> None:
        _, archive = self.build()
        with zipfile.ZipFile(archive) as release:
            metadata_bytes = release.read("cognitive-card-os/release.json")
            metadata = json.loads(metadata_bytes)
        self.assertEqual(BUILDER.canonical_json(metadata), metadata_bytes)
        self.assertEqual("cognitive-card-skill-release-v1", metadata["schema"])
        self.assertEqual("0.1.0", metadata["version"])
        self.assertEqual(self.commit, metadata["source_commit"])
        self.assertEqual({"minimum": 1, "maximum": 1}, metadata["protocol"])
        self.assertEqual("0.3.1", metadata["minimum_server_version"])
        self.assertEqual(set(SOURCE_FILES), set(metadata["files"]))
        self.assertFalse(
            {"channel", "published_at", "built_at", "timestamp"}.intersection(metadata)
        )
        for relative, declaration in metadata["files"].items():
            source = subprocess.run(
                ["git", "show", f"{self.commit}:skills/cognitive-card-os/{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
            self.assertEqual(hashlib.sha256(source).hexdigest(), declaration["sha256"])
            self.assertEqual(len(source), declaration["size_bytes"])
            self.assertEqual(f"{SOURCE_FILES[relative]:04o}", declaration["mode"])

    def test_validator_rejects_unsafe_names_and_duplicate_paths(self) -> None:
        _, archive = self.build()
        with zipfile.ZipFile(archive) as valid:
            template = valid.getinfo("cognitive-card-os/SKILL.md")
        for bad_name in (
            "/absolute",
            "../escape",
            "cognitive-card-os/../escape",
            "cognitive-card-os\\escape",
        ):
            with self.subTest(name=bad_name):
                malformed = self.rewrite_archive(
                    archive,
                    lambda members, bad_name=bad_name: members
                    + [(self.clone_info(template, filename=bad_name), b"bad")],
                )
                self.assert_error(
                    "UNSAFE_ARCHIVE_PATH",
                    lambda malformed=malformed: BUILDER.validate_archive(malformed),
                )

        duplicate = self.rewrite_archive(
            archive,
            lambda members: members
            + [(self.clone_info(template), dict((i.filename, b) for i, b in members)[template.filename])],
        )
        self.assert_error(
            "DUPLICATE_ARCHIVE_PATH", lambda: BUILDER.validate_archive(duplicate)
        )

        raw_nul = archive.with_name("raw-nul.zip")
        raw = archive.read_bytes()
        marker = b"cognitive-card-os/SKILL.md"
        self.assertGreaterEqual(raw.count(marker), 2)
        raw_nul.write_bytes(raw.replace(marker, b"cognitive-card-os/SKILL.\x00d"))
        self.assert_error(
            "UNSAFE_ARCHIVE_PATH", lambda: BUILDER.validate_archive(raw_nul)
        )

    def test_validator_rejects_link_device_metadata_and_credential_entries(self) -> None:
        _, archive = self.build()
        with zipfile.ZipFile(archive) as valid:
            template = valid.getinfo("cognitive-card-os/SKILL.md")
        for file_type in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO):
            malformed = self.rewrite_archive(
                archive,
                lambda members, file_type=file_type: [
                    (
                        self.clone_info(info),
                        content,
                    )
                    if info.filename != template.filename
                    else (
                        self.clone_info(info),
                        content,
                    )
                    for info, content in members
                ],
            )
            with zipfile.ZipFile(malformed, "a") as target:
                replacement = self.clone_info(template, filename="cognitive-card-os/unsafe")
                replacement.external_attr = (file_type | 0o777) << 16
                target.writestr(replacement, b"unsafe")
            self.assert_error(
                "UNSAFE_ARCHIVE_ENTRY",
                lambda malformed=malformed: BUILDER.validate_archive(malformed),
            )

        cases = {
            "cognitive-card-os/__MACOSX/junk": "MACOS_METADATA_FORBIDDEN",
            "cognitive-card-os/.DS_Store": "MACOS_METADATA_FORBIDDEN",
            "cognitive-card-os/.env": "CREDENTIAL_FILE_FORBIDDEN",
            "cognitive-card-os/client-token.txt": "CREDENTIAL_FILE_FORBIDDEN",
        }
        for name, code in cases.items():
            with self.subTest(name=name):
                malformed = self.rewrite_archive(
                    archive,
                    lambda members, name=name: members
                    + [(self.clone_info(template, filename=name), b"secret")],
                )
                self.assert_error(code, lambda: BUILDER.validate_archive(malformed))

    def test_validator_rejects_closure_digest_and_mode_drift(self) -> None:
        _, archive = self.build()
        missing = self.rewrite_archive(
            archive,
            lambda members: [
                item for item in members if item[0].filename != "cognitive-card-os/SKILL.md"
            ],
        )
        self.assert_error("ARCHIVE_CLOSURE_MISMATCH", lambda: BUILDER.validate_archive(missing))

        with zipfile.ZipFile(archive) as valid:
            template = valid.getinfo("cognitive-card-os/SKILL.md")
        extra = self.rewrite_archive(
            archive,
            lambda members: members
            + [(self.clone_info(template, filename="cognitive-card-os/extra.txt"), b"extra")],
        )
        self.assert_error("ARCHIVE_CLOSURE_MISMATCH", lambda: BUILDER.validate_archive(extra))

        digest = self.rewrite_archive(
            archive,
            lambda members: [
                (info, content + b"changed")
                if info.filename == "cognitive-card-os/SKILL.md"
                else (info, content)
                for info, content in members
            ],
        )
        self.assert_error("ARCHIVE_DIGEST_MISMATCH", lambda: BUILDER.validate_archive(digest))

        def drift_mode(members):
            result = []
            for info, content in members:
                clone = self.clone_info(info)
                if info.filename == "cognitive-card-os/SKILL.md":
                    clone.external_attr = 0o600 << 16
                result.append((clone, content))
            return result

        mode = self.rewrite_archive(archive, drift_mode)
        self.assert_error("ARCHIVE_MODE_MISMATCH", lambda: BUILDER.validate_archive(mode))

    def test_validator_rejects_member_count_per_file_and_total_limits(self) -> None:
        _, archive = self.build()
        with zipfile.ZipFile(archive) as valid:
            member_count = len(valid.infolist())
        with mock.patch.object(BUILDER, "MAX_ARCHIVE_MEMBERS", member_count - 1):
            self.assert_error(
                "ARCHIVE_MEMBER_LIMIT_EXCEEDED",
                lambda: BUILDER.validate_archive(archive),
            )
        with mock.patch.object(BUILDER, "MAX_MEMBER_BYTES", 1):
            self.assert_error(
                "ARCHIVE_MEMBER_TOO_LARGE", lambda: BUILDER.validate_archive(archive)
            )
        with mock.patch.object(BUILDER, "MAX_TOTAL_BYTES", 1):
            self.assert_error(
                "ARCHIVE_TOTAL_TOO_LARGE", lambda: BUILDER.validate_archive(archive)
            )

    def test_existing_version_is_idempotent_only_for_identical_bytes(self) -> None:
        first, archive = self.build()
        first_bytes = archive.read_bytes()
        second, second_archive = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, second_archive.read_bytes())

        archive.write_bytes(first_bytes + b"conflict")
        self.assert_error("VERSION_ALREADY_EXISTS", lambda: self.build())

    def test_cli_build_and_validate_emit_safe_canonical_json(self) -> None:
        output_root = self.base / "cli-dist"
        build = subprocess.run(
            [
                sys.executable,
                str(BUILDER_PATH),
                "--repository",
                str(self.repository),
                "--expected-commit",
                self.commit,
                "--output-root",
                str(output_root),
                "--version",
                "0.1.0",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        build_result = json.loads(build.stdout)
        self.assertEqual(self.commit, build_result["source_commit"])
        self.assertEqual("", build.stderr)
        archive = output_root / "0.1.0" / "cognitive-card-os.zip"
        validate = subprocess.run(
            [
                sys.executable,
                str(BUILDER_PATH),
                "validate",
                "--archive",
                str(archive),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        validate_result = json.loads(validate.stdout)
        self.assertEqual(build_result["archive_sha256"], validate_result["archive_sha256"])
        self.assertEqual("", validate.stderr)


if __name__ == "__main__":
    unittest.main()
