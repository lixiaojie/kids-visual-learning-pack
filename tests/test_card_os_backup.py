from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "ops"
    / "cognitive-card-server"
    / "card_os_backup.py"
)
SPEC = importlib.util.spec_from_file_location("card_os_backup", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load backup module from {MODULE_PATH}")
backup_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = backup_module
SPEC.loader.exec_module(backup_module)

BackupError = backup_module.BackupError
create_backup = backup_module.create_backup
verify_backup = backup_module.verify_backup


class CardOsBackupTests(unittest.TestCase):
    RELEASE_ID = "dc043ba44739" + ("0" * 28)
    NOW = datetime(2026, 7, 14, 3, 0, tzinfo=timezone.utc)

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name).resolve(strict=True)
        self.database = self.base / "card-os.sqlite3"
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("CREATE TABLE probe (value TEXT NOT NULL)")
            connection.execute("INSERT INTO probe VALUES ('rabbit')")
            connection.commit()

        self.candidates = self.base / "candidates"
        (self.candidates / "packet").mkdir(parents=True)
        (self.candidates / "packet" / "result.json").write_text(
            '{"ok":true}', encoding="utf-8"
        )
        self.backups = self.base / "backups"
        self.backups.mkdir()
        self.current = self.base / self.RELEASE_ID
        self.current.mkdir()

    def create(self, **overrides: object):
        arguments: dict[str, object] = {
            "database": self.database,
            "candidate_root": self.candidates,
            "backup_root": self.backups,
            "current_release": self.current,
            "now": self.NOW,
        }
        arguments.update(overrides)
        return create_backup(**arguments)

    def test_creates_verified_online_backup_and_candidate_snapshot(self) -> None:
        result = self.create()

        self.assertEqual(result.backup_dir.name, "20260714T030000Z-dc043ba44739")
        self.assertEqual(verify_backup(result.backup_dir)["status"], "ok")
        with closing(
            sqlite3.connect(result.backup_dir / "card-os.sqlite3")
        ) as connection:
            self.assertEqual(
                connection.execute("SELECT value FROM probe").fetchone()[0],
                "rabbit",
            )
        self.assertEqual(
            (result.backup_dir / "candidates/packet/result.json").read_text(),
            '{"ok":true}',
        )
        self.assertEqual(
            stat.S_IMODE((result.backup_dir / "card-os.sqlite3").stat().st_mode),
            0o600,
        )
        self.assertEqual(
            stat.S_IMODE(
                (result.backup_dir / "candidates/packet/result.json").stat().st_mode
            ),
            0o600,
        )

    def test_rejects_symlink_anywhere_under_candidates(self) -> None:
        (self.candidates / "packet" / "unsafe-link").symlink_to(self.database)

        with self.assertRaisesRegex(BackupError, "^UNSAFE_CANDIDATE_ENTRY$"):
            self.create()

        self.assertEqual([], list(self.backups.iterdir()))

    def test_failed_integrity_verification_is_atomic_and_skips_retention(self) -> None:
        old_backup = self.backups / "20260624T030000Z-aaaaaaaaaaaa"
        old_backup.mkdir()
        sentinel = old_backup / "must-remain"
        sentinel.write_text("old", encoding="utf-8")

        with patch.object(
            backup_module,
            "verify_backup",
            side_effect=BackupError("SQLITE_INTEGRITY_CHECK_FAILED"),
        ):
            with self.assertRaisesRegex(
                BackupError, "^SQLITE_INTEGRITY_CHECK_FAILED$"
            ):
                self.create()

        final = self.backups / "20260714T030000Z-dc043ba44739"
        staging = self.backups / ".20260714T030000Z-dc043ba44739.staging"
        self.assertFalse(final.exists())
        self.assertFalse(staging.exists())
        self.assertEqual("old", sentinel.read_text(encoding="utf-8"))

    def test_success_removes_only_old_verified_batch_directories(self) -> None:
        old = self.create(
            now=datetime(2026, 6, 24, 3, 0, tzinfo=timezone.utc),
            retention_days=100,
        ).backup_dir
        recent = self.create(
            now=datetime(2026, 7, 10, 3, 0, tzinfo=timezone.utc),
            retention_days=100,
        ).backup_dir
        unrelated_file = self.backups / "notes.txt"
        unrelated_file.write_text("keep", encoding="utf-8")
        unrelated_dir = self.backups / "manual-snapshot"
        unrelated_dir.mkdir()
        unverifiable_old = self.backups / "20260620T030000Z-aaaaaaaaaaaa"
        unverifiable_old.mkdir()

        newest = self.create().backup_dir

        self.assertTrue(newest.is_dir())
        self.assertFalse(old.exists())
        self.assertTrue(recent.is_dir())
        self.assertEqual("keep", unrelated_file.read_text(encoding="utf-8"))
        self.assertTrue(unrelated_dir.is_dir())
        self.assertTrue(unverifiable_old.is_dir())

    def test_retention_skips_regex_match_with_invalid_calendar_timestamp(self) -> None:
        invalid_timestamp = self.backups / "99999999T999999Z-aaaaaaaaaaaa"
        invalid_timestamp.mkdir()

        result = self.create()

        self.assertTrue(result.backup_dir.is_dir())
        self.assertTrue(invalid_timestamp.is_dir())

    def test_manifest_is_canonical_portable_and_complete(self) -> None:
        extra = self.candidates / "alpha.txt"
        extra.write_text("owl", encoding="utf-8")
        (self.candidates / "a").mkdir()
        (self.candidates / "a" / "z.txt").write_text("nested", encoding="utf-8")
        (self.candidates / "a-z.txt").write_text("flat", encoding="utf-8")

        result = self.create()
        manifest_bytes = result.manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)

        self.assertEqual(
            manifest_bytes,
            (
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8"),
        )
        self.assertEqual("card-os-backup-v1", manifest["schema"])
        self.assertEqual("2026-07-14T03:00:00Z", manifest["created_at"])
        self.assertEqual(self.RELEASE_ID, manifest["release_id"])
        self.assertEqual("card-os.sqlite3", manifest["database"]["path"])
        database_bytes = (result.backup_dir / "card-os.sqlite3").read_bytes()
        self.assertEqual(
            hashlib.sha256(database_bytes).hexdigest(),
            manifest["database"]["sha256"],
        )
        self.assertEqual(len(database_bytes), manifest["database"]["size"])
        self.assertEqual(
            ["a-z.txt", "a/z.txt", "alpha.txt", "packet/result.json"],
            [entry["path"] for entry in manifest["candidates"]],
        )
        for entry in manifest["candidates"]:
            copied = result.backup_dir / "candidates" / entry["path"]
            copied_bytes = copied.read_bytes()
            self.assertEqual(hashlib.sha256(copied_bytes).hexdigest(), entry["sha256"])
            self.assertEqual(len(copied_bytes), entry["size"])
        self.assertNotIn(str(self.base), manifest_bytes.decode("utf-8"))
        self.assertEqual(stat.S_IMODE(result.manifest_path.stat().st_mode), 0o600)

    def test_verify_rejects_tampering_and_undeclared_files_without_mutation(self) -> None:
        result = self.create()
        candidate = result.backup_dir / "candidates/packet/result.json"
        candidate.write_text('{"ok":false}', encoding="utf-8")
        before = candidate.read_bytes()
        with self.assertRaises(BackupError):
            verify_backup(result.backup_dir)
        self.assertEqual(before, candidate.read_bytes())

        candidate.write_text('{"ok":true}', encoding="utf-8")
        undeclared = result.backup_dir / "unexpected.txt"
        undeclared.write_text("surprise", encoding="utf-8")
        with self.assertRaises(BackupError):
            verify_backup(result.backup_dir)
        self.assertEqual("surprise", undeclared.read_text(encoding="utf-8"))

    def test_rejects_existing_staging_or_final_batch_path(self) -> None:
        staging = self.backups / ".20260714T030000Z-dc043ba44739.staging"
        staging.mkdir(mode=0o700)
        with self.assertRaises(BackupError):
            self.create()
        staging.rmdir()

        final = self.backups / "20260714T030000Z-dc043ba44739"
        final.mkdir()
        with self.assertRaises(BackupError):
            self.create()

    def test_atomic_publication_does_not_clobber_concurrent_final_path(self) -> None:
        final = self.backups / "20260714T030000Z-dc043ba44739"
        staging = self.backups / ".20260714T030000Z-dc043ba44739.staging"
        original_verify = verify_backup
        concurrent_inode: int | None = None

        def verify_then_create_final(backup_dir: Path) -> dict[str, object]:
            nonlocal concurrent_inode
            verification = original_verify(backup_dir)
            final.mkdir()
            concurrent_inode = final.stat().st_ino
            return verification

        with patch.object(
            backup_module, "verify_backup", side_effect=verify_then_create_final
        ):
            with self.assertRaisesRegex(BackupError, "^BACKUP_PATH_EXISTS$"):
                self.create()

        self.assertIsNotNone(concurrent_inode)
        self.assertEqual(concurrent_inode, final.stat().st_ino)
        self.assertEqual([], list(final.iterdir()))
        self.assertFalse(staging.exists())

    def test_cli_create_and_verify_emit_only_canonical_json(self) -> None:
        create_process = subprocess.run(
            [
                sys.executable,
                os.fspath(MODULE_PATH),
                "create",
                "--database",
                os.fspath(self.database),
                "--candidate-root",
                os.fspath(self.candidates),
                "--backup-root",
                os.fspath(self.backups),
                "--current-release",
                os.fspath(self.current),
                "--retention-days",
                "14",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        create_payload = json.loads(create_process.stdout)
        self.assertEqual(
            create_process.stdout,
            json.dumps(create_payload, sort_keys=True, separators=(",", ":")) + "\n",
        )
        self.assertEqual(
            {"backup_dir", "manifest_sha256", "release_id", "status"},
            set(create_payload),
        )
        self.assertEqual("ok", create_payload["status"])
        self.assertEqual(self.RELEASE_ID, create_payload["release_id"])
        self.assertEqual("", create_process.stderr)

        verify_process = subprocess.run(
            [
                sys.executable,
                os.fspath(MODULE_PATH),
                "verify",
                "--backup-dir",
                create_payload["backup_dir"],
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        verify_payload = json.loads(verify_process.stdout)
        self.assertEqual(
            verify_process.stdout,
            json.dumps(verify_payload, sort_keys=True, separators=(",", ":")) + "\n",
        )
        self.assertEqual(
            {"file_count", "release_id", "status"}, set(verify_payload)
        )
        self.assertEqual("", verify_process.stderr)


if __name__ == "__main__":
    unittest.main()
