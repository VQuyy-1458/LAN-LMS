"""Consistent SQLite + private-storage backup. Prefer stopping API/workers first."""

from contextlib import closing
import argparse
import hashlib
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def regular_files(root):
    if root.is_symlink():
        raise ValueError("Storage root cannot be a symlink")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Backup refuses symlinks")
        if path.is_file():
            yield path


def backup(database, storage, destination):
    database = Path(database).resolve()
    storage = Path(storage).resolve()
    destination = Path(destination).resolve()
    if not database.is_file() or not storage.is_dir():
        raise ValueError("Database/storage must exist")
    if destination.exists() or destination.is_relative_to(storage):
        raise ValueError("Use a new backup folder outside storage")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A writer reservation prevents metadata commits while committed private files are copied.
    # The SQLite backup API reads from a separate connection, avoiding self-backup of a write transaction.
    with tempfile.TemporaryDirectory(
        prefix="lan-lms-backup-", dir=destination.parent
    ) as temp:
        stage = Path(temp) / "snapshot"
        stage.mkdir()
        with closing(sqlite3.connect(str(database), timeout=10)) as guard:
            guard.execute("PRAGMA busy_timeout=10000")
            guard.execute("BEGIN IMMEDIATE")
            try:
                with closing(
                    sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
                ) as source, closing(
                    sqlite3.connect(stage / "database.sqlite3")
                ) as target:
                    source.backup(target)
                    if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ValueError("Database integrity check failed")
                    if target.execute("PRAGMA foreign_key_check").fetchall():
                        raise ValueError("Database foreign keys are invalid")
                (stage / "storage").mkdir()
                for path in regular_files(storage):
                    target = stage / "storage" / path.relative_to(storage)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
            finally:
                guard.rollback()
        hashes = {
            p.relative_to(stage).as_posix(): sha256(p) for p in regular_files(stage)
        }
        (stage / "manifest.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "files": hashes,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        # rename does not merge into an existing directory; destination must be new.
        if destination.exists():
            raise FileExistsError(destination)
        stage.rename(destination)
    return destination


def verify(snapshot):
    snapshot = Path(snapshot).resolve()
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unsupported backup format")
    if "database.sqlite3" not in manifest["files"]:
        raise ValueError("Database is missing")
    for name, expected in manifest["files"].items():
        if (
            not isinstance(name, str)
            or "\\" in name
            or ":" in name
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise ValueError("Unsafe backup path")
        original = snapshot / name
        if any(part.is_symlink() for part in (original, *original.parents)):
            raise ValueError("Backup refuses symlinks")
        path = (snapshot / name).resolve()
        if not path.is_relative_to(snapshot) or (
            name != "database.sqlite3" and not name.startswith("storage/")
        ):
            raise ValueError("Unsafe backup path")
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            raise ValueError("Backup file checksum mismatch")
    return manifest


def restore(snapshot, database, storage):
    snapshot = Path(snapshot).resolve()
    database = Path(database).resolve()
    storage = Path(storage).resolve()
    manifest = verify(snapshot)
    if database.exists() or storage.exists():
        raise ValueError(
            "Restore requires a new database path and new storage directory"
        )
    if (
        database.is_relative_to(storage)
        or storage.is_relative_to(snapshot)
        or database.is_relative_to(snapshot)
    ):
        raise ValueError("Overlapping restore/backup paths")
    database.parent.mkdir(parents=True, exist_ok=True)
    storage.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="lan-lms-restore-", dir=database.parent
    ) as temp:
        stage = Path(temp) / "database.sqlite3"
        shutil.copyfile(snapshot / "database.sqlite3", stage)
        with closing(sqlite3.connect(stage)) as db:
            if (
                db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or db.execute("PRAGMA foreign_key_check").fetchall()
            ):
                raise ValueError("Restored database is invalid")
            tables = {
                r[0]
                for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            # A restored server starts with revoked sessions and recoverable pending judge work.
            if "auth_sessions" in tables:
                db.execute("DELETE FROM auth_sessions")
            if "realtime_events" in tables:
                db.execute("DELETE FROM realtime_events")
            if "judge_jobs" in tables:
                db.execute(
                    "UPDATE judge_jobs SET status='pending',attempt_id=NULL,lease_until=NULL,worker_id=NULL,attempt_count=0 WHERE status='running'"
                )
                db.execute(
                    "UPDATE code_submissions SET status='Pending',version=version+1 WHERE status IN ('Compiling','Running')"
                )
            db.commit()
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        # Build storage as a sibling staging folder, then rename only after successful copying.
        with tempfile.TemporaryDirectory(
            prefix="lan-lms-storage-", dir=storage.parent
        ) as temp_storage:
            staged_storage = Path(temp_storage) / "storage"
            staged_storage.mkdir()
            for name in manifest["files"]:
                if name.startswith("storage/"):
                    relative = Path(name).relative_to("storage")
                    target = staged_storage / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(snapshot / name, target)
            if storage.exists() or database.exists():
                raise FileExistsError("Restore targets already exist")
            with database.open("xb") as out, stage.open("rb") as src:
                shutil.copyfileobj(src, out)
            try:
                staged_storage.rename(storage)
            except BaseException:
                database.unlink()
                raise
    return database, storage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--database", type=Path, required=True)
    b.add_argument("--storage", type=Path, required=True)
    b.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("snapshot", type=Path)
    r = sub.add_parser("restore")
    r.add_argument("snapshot", type=Path)
    r.add_argument("--database", type=Path, required=True)
    r.add_argument("--storage", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "backup":
        backup(args.database, args.storage, args.output)
    elif args.command == "verify":
        verify(args.snapshot)
    else:
        restore(args.snapshot, args.database, args.storage)
    print(f"{args.command}: completed")


if __name__ == "__main__":
    main()
