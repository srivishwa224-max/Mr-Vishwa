import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backup import backup, integrity, restore


class BackupTests(unittest.TestCase):
    def test_backup_and_restore_preserve_committed_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            live, saved, recovered = root / "live.sqlite", root / "saved.sqlite", root / "recovered.sqlite"
            with sqlite3.connect(live) as db:
                db.execute("CREATE TABLE sample(value TEXT NOT NULL)")
                db.execute("INSERT INTO sample VALUES(?)", ("synthetic-only",))
            backup(live, saved)
            self.assertEqual(["ok"], integrity(saved))
            self.assertEqual(0o600, os.stat(saved).st_mode & 0o777)
            restore(saved, recovered)
            with sqlite3.connect(recovered) as db:
                self.assertEqual("synthetic-only", db.execute("SELECT value FROM sample").fetchone()[0])

    def test_never_overwrites_backup_or_restore_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, existing = root / "source.sqlite", root / "existing.sqlite"
            with sqlite3.connect(source) as db:
                db.execute("CREATE TABLE sample(value)")
            existing.write_text("keep me")
            with self.assertRaises(FileExistsError):
                backup(source, existing)
            self.assertEqual("keep me", existing.read_text())
            with self.assertRaises(FileExistsError):
                restore(source, existing)

    def test_corrupt_source_is_rejected_without_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corrupt, destination = root / "corrupt.sqlite", root / "restored.sqlite"
            corrupt.write_bytes(b"not a sqlite database")
            with self.assertRaises((ValueError, sqlite3.DatabaseError)):
                restore(corrupt, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
