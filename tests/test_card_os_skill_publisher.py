from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "ops" / "cognitive-card-skill" / "build_release.py"
PUBLISHER_PATH = ROOT / "ops" / "cognitive-card-skill" / "publish_release.py"


def load_module(name: str, path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("card_os_registry_test_builder", BUILDER_PATH)
PUBLISHER = load_module("card_os_skill_publisher", PUBLISHER_PATH)


SOURCE_FILES = {
    "SKILL.md": 0o644,
    "agents/openai.yaml": 0o644,
    "scripts/card_os_client.py": 0o755,
    "references/protocol.md": 0o644,
    "references/errors.md": 0o644,
}


class PublisherFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repository = root / "repository"
        self.repository.mkdir()
        skill = self.repository / "skills" / "cognitive-card-os"
        contents = {
            "SKILL.md": b"---\nname: cognitive-card-os\ndescription: Fixture\n---\nFixture.\n",
            "agents/openai.yaml": b"interface:\n  display_name: Fixture\n",
            "scripts/card_os_client.py": b"#!/usr/bin/env python3\nprint('fixture')\n",
            "references/protocol.md": b"# Protocol\n\nFixture.\n",
            "references/errors.md": b"# Errors\n\nFixture.\n",
        }
        for relative, content in contents.items():
            path = skill / relative
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
                "GIT_AUTHOR_DATE": "@1735689600 +0000",
                "GIT_COMMITTER_DATE": "@1735689600 +0000",
            }
        )
        self.git("commit", "-q", "-m", "fixture", env=environment)
        self.commit = self.git("rev-parse", "HEAD")
        result = BUILDER.build_release(
            repository=self.repository,
            expected_commit=self.commit,
            output_root=root / "dist",
        )
        self.archive = Path(str(result["archive_path"]))
        self.registry = root / "registry" / "v1"
        self.installer = root / "install.sh"
        self.installer.write_bytes(b"#!/usr/bin/env bash\nset -eu\n")
        self.installer.chmod(0o755)

    def git(self, *arguments: str, env: dict[str, str] | None = None) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()


class CardOsSkillPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.fixture = PublisherFixture(self.base)
        self.owner = mock.patch.multiple(
            PUBLISHER,
            PRODUCTION_UID=os.geteuid(),
            PRODUCTION_GID=os.getegid(),
        )
        self.owner.start()
        self.addCleanup(self.owner.stop)
        self.when = datetime(2026, 7, 16, 1, 2, 3, tzinfo=timezone.utc)

    def error(self, code: str, callback) -> None:
        with self.assertRaises(PUBLISHER.RegistryError) as raised:
            callback()
        self.assertEqual(code, raised.exception.code)

    def publish_installer(self, *, activate: bool = True) -> dict[str, object]:
        return PUBLISHER.publish_installer(
            registry_root=self.fixture.registry,
            installer=self.fixture.installer,
            activate=activate,
        )

    def publish_release(self, *, activate: bool = True) -> dict[str, object]:
        installer = self.publish_installer(activate=False)
        return PUBLISHER.publish_release(
            registry_root=self.fixture.registry,
            archive=self.fixture.archive,
            installer_digest=str(installer["installer_sha256"]),
            published_at=self.when,
            activate_stable=activate,
        )

    def test_installer_can_publish_before_release_and_switches_one_pointer(self) -> None:
        result = self.publish_installer(activate=True)
        digest = hashlib.sha256(self.fixture.installer.read_bytes()).hexdigest()
        self.assertEqual(digest, result["installer_sha256"])
        snapshot = self.fixture.registry / "installers" / digest
        self.assertEqual(self.fixture.installer.read_bytes(), (snapshot / "install.sh").read_bytes())
        self.assertEqual(
            f"{digest}  install.sh\n".encode("ascii"),
            (snapshot / "install.sh.sha256").read_bytes(),
        )
        current = self.fixture.registry / "installer-current"
        self.assertTrue(current.is_symlink())
        self.assertEqual(f"installers/{digest}", os.readlink(current))
        self.assertFalse((self.fixture.registry / "manifest.json").exists())
        self.assertEqual(0o755, stat.S_IMODE(snapshot.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE((snapshot / "install.sh").stat().st_mode))

    def test_fixture_release_has_exact_bytes_without_manifest(self) -> None:
        result = self.publish_release(activate=False)
        release = self.fixture.registry / "releases" / "0.1.0"
        archive_bytes = self.fixture.archive.read_bytes()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        self.assertEqual(archive_bytes, (release / "cognitive-card-os.zip").read_bytes())
        self.assertEqual(
            f"{digest}  cognitive-card-os.zip\n".encode("ascii"),
            (release / "sha256.txt").read_bytes(),
        )
        self.assertEqual("published", result["status"])
        self.assertFalse((self.fixture.registry / "manifest.json").exists())
        self.assertEqual([], list((self.fixture.registry / "manifests").iterdir()))
        self.assertTrue(PUBLISHER.verify_registry(registry_root=self.fixture.registry)["valid"])

    def test_stable_manifest_is_canonical_and_derived_from_archive(self) -> None:
        installer = self.publish_installer(activate=True)
        result = PUBLISHER.publish_release(
            registry_root=self.fixture.registry,
            archive=self.fixture.archive,
            installer_digest=str(installer["installer_sha256"]),
            published_at=self.when,
            activate_stable=True,
        )
        manifest_bytes = (self.fixture.registry / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        expected = {
            "archive_sha256": hashlib.sha256(self.fixture.archive.read_bytes()).hexdigest(),
            "archive_size_bytes": len(self.fixture.archive.read_bytes()),
            "archive_url": "https://www.yutou.space/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip",
            "channel": "stable",
            "installer": {
                "sha256": installer["installer_sha256"],
                "url": f"https://www.yutou.space/card-os/skill/v1/installers/{installer['installer_sha256']}/install.sh",
            },
            "minimum_server_version": "0.3.1",
            "protocol": {"maximum": 1, "minimum": 1},
            "published_at": "2026-07-16T01:02:03Z",
            "schema": "cognitive-card-skill-registry-v1",
            "source_commit": self.fixture.commit,
            "version": "0.1.0",
        }
        self.assertEqual(expected, manifest)
        self.assertEqual(PUBLISHER.canonical_json(expected), manifest_bytes)
        digest = hashlib.sha256(manifest_bytes).hexdigest()
        self.assertEqual(digest, result["manifest_sha256"])
        self.assertEqual(manifest_bytes, (self.fixture.registry / "manifests" / f"{digest}.json").read_bytes())

    def test_immutable_objects_are_idempotent_but_conflicts_fail(self) -> None:
        installer = self.publish_installer(activate=False)
        arguments = {
            "registry_root": self.fixture.registry,
            "archive": self.fixture.archive,
            "installer_digest": str(installer["installer_sha256"]),
            "published_at": self.when,
            "activate_stable": False,
        }
        first = PUBLISHER.publish_release(**arguments)
        second = PUBLISHER.publish_release(**arguments)
        self.assertEqual(first, second)
        archive = self.fixture.registry / "releases" / "0.1.0" / "cognitive-card-os.zip"
        archive.write_bytes(b"conflict")
        self.error("IMMUTABLE_CONFLICT", lambda: PUBLISHER.publish_release(**arguments))

    def test_missing_installer_and_invalid_owner_fail_closed(self) -> None:
        self.error(
            "INSTALLER_NOT_FOUND",
            lambda: PUBLISHER.publish_release(
                registry_root=self.fixture.registry,
                archive=self.fixture.archive,
                installer_digest="0" * 64,
                published_at=self.when,
                activate_stable=False,
            ),
        )
        with mock.patch.object(PUBLISHER, "PRODUCTION_UID", os.geteuid() + 1):
            self.error("ROOT_REQUIRED", lambda: self.publish_installer(activate=False))

    def test_symlinks_are_refused_except_valid_current_pointer(self) -> None:
        self.publish_installer(activate=True)
        rogue = self.fixture.registry / "releases" / "rogue"
        rogue.symlink_to(self.base)
        self.error("UNSAFE_REGISTRY_SYMLINK", lambda: PUBLISHER.verify_registry(registry_root=self.fixture.registry))
        rogue.unlink()
        (self.fixture.registry / "installer-current").unlink()
        (self.fixture.registry / "installer-current").symlink_to("../outside")
        self.error("INVALID_INSTALLER_POINTER", lambda: PUBLISHER.verify_registry(registry_root=self.fixture.registry))

    def test_faults_before_final_switch_preserve_active_pointers(self) -> None:
        old_installer = self.publish_installer(activate=True)
        old_pointer = os.readlink(self.fixture.registry / "installer-current")
        self.fixture.installer.write_bytes(b"#!/bin/sh\nexit 0\n")
        with mock.patch.object(PUBLISHER, "_fault", side_effect=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "installer_before_switch" else None):
            with self.assertRaises(RuntimeError):
                self.publish_installer(activate=True)
        self.assertEqual(old_pointer, os.readlink(self.fixture.registry / "installer-current"))

        installer_digest = str(old_installer["installer_sha256"])
        old_manifest = b""
        with mock.patch.object(PUBLISHER, "_fault", side_effect=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "manifest_before_switch" else None):
            with self.assertRaises(RuntimeError):
                PUBLISHER.publish_release(
                    registry_root=self.fixture.registry,
                    archive=self.fixture.archive,
                    installer_digest=installer_digest,
                    published_at=self.when,
                    activate_stable=True,
                )
        manifest = self.fixture.registry / "manifest.json"
        self.assertFalse(manifest.exists())
        self.assertEqual(b"", old_manifest)

    def test_every_installer_transition_fault_preserves_old_bootstrap(self) -> None:
        old = self.publish_installer(activate=True)
        old_pointer = os.readlink(self.fixture.registry / "installer-current")
        self.fixture.installer.write_bytes(b"#!/bin/sh\nexit 7\n")
        for point in (
            "installer_snapshot_before_publish",
            "installer_snapshot_after_publish",
            "installer_before_switch",
            "installer_after_switch",
        ):
            with self.subTest(point=point):
                PUBLISHER.activate_installer(
                    registry_root=self.fixture.registry,
                    installer_digest=str(old["installer_sha256"]),
                )
                with mock.patch.object(
                    PUBLISHER,
                    "_fault",
                    side_effect=lambda observed, selected=point: (
                        (_ for _ in ()).throw(RuntimeError(observed))
                        if observed == selected
                        else None
                    ),
                ):
                    with self.assertRaises(RuntimeError):
                        self.publish_installer(activate=True)
                self.assertEqual(
                    old_pointer,
                    os.readlink(self.fixture.registry / "installer-current"),
                )

    def test_every_release_transition_fault_preserves_old_stable_bytes(self) -> None:
        self.publish_release(activate=True)
        stable = self.fixture.registry / "manifest.json"
        old_bytes = stable.read_bytes()
        later = datetime(2026, 7, 18, 1, 2, 3, tzinfo=timezone.utc)
        installer_digest = json.loads(old_bytes)["installer"]["sha256"]
        for point in (
            "release_before_publish",
            "release_after_publish",
            "manifest_snapshot_before_publish",
            "manifest_snapshot_after_publish",
            "manifest_before_switch",
            "manifest_after_switch",
        ):
            with self.subTest(point=point):
                with mock.patch.object(
                    PUBLISHER,
                    "_fault",
                    side_effect=lambda observed, selected=point: (
                        (_ for _ in ()).throw(RuntimeError(observed))
                        if observed == selected
                        else None
                    ),
                ):
                    with self.assertRaises(RuntimeError):
                        PUBLISHER.publish_release(
                            registry_root=self.fixture.registry,
                            archive=self.fixture.archive,
                            installer_digest=installer_digest,
                            published_at=later,
                            activate_stable=True,
                        )
                self.assertEqual(old_bytes, stable.read_bytes())

    def test_post_switch_validation_failure_restores_previous_pointer(self) -> None:
        first = self.publish_installer(activate=True)
        original = os.readlink(self.fixture.registry / "installer-current")
        self.fixture.installer.write_bytes(b"#!/bin/sh\nexit 0\n")
        with mock.patch.object(PUBLISHER, "_fault", side_effect=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "installer_after_switch" else None):
            with self.assertRaises(RuntimeError):
                self.publish_installer(activate=True)
        self.assertEqual(original, os.readlink(self.fixture.registry / "installer-current"))
        self.assertEqual(first["installer_sha256"], original.rsplit("/", 1)[-1])

    def test_rollback_creates_new_snapshot_for_revalidated_old_release(self) -> None:
        self.publish_release(activate=True)
        original = (self.fixture.registry / "manifest.json").read_bytes()
        original_snapshot = self.fixture.registry / "manifests" / f"{hashlib.sha256(original).hexdigest()}.json"
        later = datetime(2026, 7, 17, 1, 2, 3, tzinfo=timezone.utc)
        with mock.patch.object(PUBLISHER, "_utc_now", return_value=later):
            result = PUBLISHER.activate_manifest(
                registry_root=self.fixture.registry,
                snapshot=original_snapshot,
            )
        rolled_back = (self.fixture.registry / "manifest.json").read_bytes()
        self.assertNotEqual(original, rolled_back)
        payload = json.loads(rolled_back)
        self.assertEqual("2026-07-17T01:02:03Z", payload["published_at"])
        self.assertEqual(json.loads(original)["archive_sha256"], payload["archive_sha256"])
        self.assertEqual(
            rolled_back,
            (self.fixture.registry / "manifests" / f"{result['manifest_sha256']}.json").read_bytes(),
        )

    def test_activate_installer_revalidates_digest_before_and_after_switch(self) -> None:
        result = self.publish_installer(activate=False)
        digest = str(result["installer_sha256"])
        with mock.patch.object(PUBLISHER, "_validate_installer_snapshot", wraps=PUBLISHER._validate_installer_snapshot) as validate:
            PUBLISHER.activate_installer(
                registry_root=self.fixture.registry,
                installer_digest=digest,
            )
        self.assertGreaterEqual(validate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
