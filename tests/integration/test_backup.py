"""Integrity and safety of a consistent database + private file round trip."""

import sqlite3
from pathlib import Path
import pytest
from scripts.backup_database import backup, restore, verify


def test_backup_restore_and_tamper_detection(tmp_path):
    db = tmp_path / "live.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "material.txt").write_bytes(b"private material")
    with sqlite3.connect(db) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE content(path TEXT)")
        c.execute("INSERT INTO content VALUES ('material.txt')")
        c.execute("CREATE TABLE auth_sessions(token TEXT)")
        c.execute("INSERT INTO auth_sessions VALUES ('revoked-on-restore')")
    snap = backup(db, storage, tmp_path / "backup")
    verify(snap)
    restore(snap, tmp_path / "restored.db", tmp_path / "restored-storage")
    assert (
        tmp_path / "restored-storage/material.txt"
    ).read_bytes() == b"private material"
    with sqlite3.connect(tmp_path / "restored.db") as c:
        assert c.execute("SELECT path FROM content").fetchone()[0] == "material.txt"
        assert c.execute("SELECT count(*) FROM auth_sessions").fetchone()[0] == 0
    with pytest.raises(ValueError):
        restore(snap, tmp_path / "restored.db", tmp_path / "other")
    (snap / "storage/material.txt").write_bytes(b"corrupted")
    with pytest.raises(ValueError):
        verify(snap)
    with pytest.raises(ValueError):
        restore(snap, tmp_path / "bad.db", tmp_path / "bad-storage")
    assert not (tmp_path / "bad.db").exists()
