"""Installer planning, interruption recovery and preservation of existing data."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

from scripts import bootstrap_app, setup_offline
from scripts.backup_database import backup
from scripts.prepare_usb import checksum


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("STORAGE_ROOT", raising=False)
    root = tmp_path / "LAN-LMS"
    (root / "server").mkdir(parents=True)
    return root


def db_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT)")
        db.execute("INSERT INTO users VALUES(1,'keep-account')")


def test_existing_database_and_files_are_never_replaced(root):
    target = root / ".runtime/web/demo.db"
    db_file(target)
    storage = root / ".runtime/web/storage"
    storage.mkdir()
    (storage / "keep").write_text("student-work")
    before = target.read_bytes()
    assert bootstrap_app.prepare_data(root, None, lambda cmd: pytest.fail("Unexpected install")) == "existing"
    assert target.read_bytes() == before
    assert (storage / "keep").read_text() == "student-work"


def test_missing_storage_is_not_replaced_with_new_classroom(root):
    db_file(root / ".runtime/web/demo.db")
    with pytest.raises(FileNotFoundError, match="storage"):
        bootstrap_app.prepare_data(root, None, lambda cmd: None)


def test_populated_default_database_is_kept(root):
    target = root / "database/lan_lms.db"
    db_file(target)
    (root / "server/.env").write_text("DATABASE_URL=sqlite:///./database/lan_lms.db\n")
    assert bootstrap_app.prepare_data(root, None, lambda cmd: pytest.fail("Do not seed")) == "existing"
    assert not (root / ".runtime/web/demo.db").exists()


def test_custom_database_missing_fails_without_seeding(root):
    (root / "server/.env").write_text("DATABASE_URL=sqlite:///./external/missing.db\n")
    with pytest.raises(FileNotFoundError, match="Configured"):
        bootstrap_app.prepare_data(root, None, lambda cmd: pytest.fail("Do not seed"))


def test_snapshot_restored_despite_default_example_env(root, tmp_path):
    kit = root.parent
    old_db = tmp_path / "original.db"
    db_file(old_db)
    old_storage = tmp_path / "original-storage"
    old_storage.mkdir()
    (old_storage / "handout.txt").write_text("same teaching material")
    snapshot = kit / "classroom-data/server-snapshot"
    backup(old_db, old_storage, snapshot)
    (kit / "classroom-data/LOGIN.txt").write_text("private account notes")
    (root / "server/.env").write_text("DATABASE_URL=sqlite:///./database/lan_lms.db\n")
    assert bootstrap_app.prepare_data(root, kit, lambda cmd: pytest.fail("Do not rebuild")) == "restored-snapshot"
    assert (root / ".runtime/web/storage/handout.txt").read_text() == "same teaching material"
    assert (root / ".runtime/accounts/LOGIN.txt").read_text() == "private account notes"
    assert bootstrap_app.prepare_data(root, kit, lambda cmd: None) == "existing"


@pytest.fixture
def fake_kit(root, monkeypatch):
    kit = root.parent
    for name in ("server/requirements.lock", "server/.env.example", "client/package-lock.json", "client/package.json", "client/next.config.ts", "client/tsconfig.json", "client/postcss.config.mjs"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    deps = kit / "dependencies"
    (deps / "nginx").mkdir(parents=True)
    (deps / "nginx/nginx.exe").write_bytes(b"fixture")
    with zipfile.ZipFile(deps / "node_modules.zip", "w") as archive:
        archive.writestr("next/dist/bin/next", "fixture")
    snapshot = kit / "classroom-data/server-snapshot/manifest.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text("{}")
    manifest = {"format": "lan-lms-offline", "version": 1, "machine": "AMD64", "node": "v24.14.1", "judge_image": "fixture", "judge_image_id": "sha256:fixture", "files": {}}
    for path in kit.rglob("*"):
        if path.is_file(): manifest["files"][path.relative_to(kit).as_posix()] = checksum(path)
    (kit / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(setup_offline.sys, "platform", "win32")
    monkeypatch.setattr(setup_offline.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(setup_offline.shutil, "which", lambda name: name)
    monkeypatch.setattr(setup_offline.subprocess, "check_output", lambda args, **kwargs: "v24.14.1" if args[-1] == "--version" else "sha256:fixture")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if "venv" in args:
            python = root / ".venv/Scripts/python.exe"
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_bytes(b"fixture")
        if "build" in args:
            build = root / "client/.next/BUILD_ID"
            build.parent.mkdir(parents=True, exist_ok=True)
            build.write_text("fixture")
        return SimpleNamespace(returncode=0, stdout="sha256:fixture")
    monkeypatch.setattr(setup_offline.subprocess, "run", run)
    return root, calls, run


def test_offline_install_resumes_after_pip_failure_without_recreating_venv(fake_kit, monkeypatch):
    root, calls, run = fake_kit
    fail_once = [True]
    def interrupted(args, **kwargs):
        if "pip" in args and fail_once[0]:
            fail_once[0] = False
            raise subprocess.CalledProcessError(1, args)
        return run(args, **kwargs)
    monkeypatch.setattr(setup_offline.subprocess, "run", interrupted)
    with pytest.raises(subprocess.CalledProcessError):
        setup_offline.install(root, create_teacher=False, resume=True)
    setup_offline.install(root, create_teacher=False, resume=True)
    setup_offline.install(root, create_teacher=False, resume=True)
    assert sum("venv" in command for command in calls) == 1
    assert sum("build" in command for command in calls) == 1
    assert (root / "tools/nginx/nginx.exe").is_file()
    assert not any("server.app.seed" in command for command in calls)
    assert not any("alembic" in command for command in calls)


def test_existing_unmanaged_virtualenv_is_preserved(fake_kit):
    root, calls, _ = fake_kit
    keep = root / ".venv/keep.txt"
    keep.parent.mkdir(); keep.write_text("owned by user")
    with pytest.raises(FileExistsError, match="unmanaged"):
        setup_offline.install(root, create_teacher=False, resume=True)
    assert keep.read_text() == "owned by user"
    assert not any("venv" in command for command in calls)


def test_tampered_kit_rejected_before_install(fake_kit):
    root, calls, _ = fake_kit
    (root / "server/requirements.lock").write_text("tampered")
    with pytest.raises(ValueError, match="modified"):
        setup_offline.install(root, create_teacher=False, resume=True)
    assert not (root / ".venv").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell process argument handling")
def test_windows_planning_and_native_arguments():
    script = Path(__file__).resolve().parents[2] / "scripts/bootstrap_windows.ps1"
    command = "$ErrorActionPreference='Stop'; . '" + str(script).replace("'", "''") + "' -LibraryOnly; " + r'''
    $facts=@{Supported=$true;Virtualization=$true;Python=$false;Node=$false;Wsl='0.0.0';Docker=$false;Firewall=$false}
    $clean=@(Get-BootstrapPlan $facts)
    if ('install-python' -notin $clean -or 'install-node' -notin $clean -or 'install-docker' -notin $clean -or 'install-wsl' -notin $clean) {throw 'Missing prerequisites'}
    $facts.Virtualization=$false
    if ((Get-BootstrapPlan $facts) -ne 'enable-bios-virtualization') {throw 'BIOS detection'}
    $facts.Supported=$false
    if ((Get-BootstrapPlan $facts) -ne 'unsupported') {throw 'Unsupported platform'}
    $r=Invoke-Native 'PYTHON_PATH' @('-c','import sys,json; print(json.dumps(sys.argv[1:]))','path with space','trailing space\','quote"inside')
    if($r.Code -ne 0) {throw $r.Text}
    Write-Output $r.Text
    '''.replace("PYTHON_PATH", sys.executable.replace("'", "''"))
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], check=True, capture_output=True, text=True, timeout=30)
    assert json.loads(result.stdout) == ["path with space", "trailing space\\", 'quote"inside']
