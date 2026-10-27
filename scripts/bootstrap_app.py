"""Resumable app/data stage of the Windows one-file bootstrap (no elevation)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def dependency_signature(root):
    digest = hashlib.sha256()
    for name in ("server/requirements.lock", "client/package-lock.json", "judge/Dockerfile", "judge/sandbox_entry.py"):
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def kit_for(root):
    kit = root.parent
    path = kit / "manifest.json"
    if not path.is_file():
        return None
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("format") != "lan-lms-offline" or manifest.get("version") != 1:
        raise ValueError("Unknown parent manifest; no installation was changed")
    return kit


def prepare_data(root, kit, run):
    """Never shadow or overwrite a populated installation with bundled/demo data."""
    from scripts.backup_database import restore
    target = root / ".runtime/web/demo.db"
    storage = root / ".runtime/web/storage"
    if target.exists():
        if not storage.is_dir():
            raise FileNotFoundError("Existing web database has no storage folder; restore its own backup")
        return "existing"
    # Respect an explicitly configured database/storage, including external locations.
    from scripts.launch_web import make_environment
    env = make_environment(root)
    configured = env.get("DATABASE_URL")
    if configured:
        from sqlalchemy.engine import make_url
        url = make_url(configured)
        if not url.drivername.startswith("sqlite"):
            return "configured"
        path = Path(url.database or "")
        if not path.is_absolute():
            path = root / path
        if path.resolve() != (root / "database/lan_lms.db").resolve():
            if not path.is_file():
                raise FileNotFoundError("Configured database is missing; refusing to replace it with classroom data")
            return "configured"
    default = root / "database/lan_lms.db"
    if default.is_file():
        with sqlite3.connect(default) as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "users" in tables and db.execute("SELECT count(*) FROM users").fetchone()[0]:
                return "existing"
    snapshot = kit / "classroom-data/server-snapshot" if kit else None
    credentials = kit / "classroom-data" if kit else None
    if snapshot is not None and (snapshot / "manifest.json").is_file():
        restore(snapshot, target, storage)
        result = "restored-snapshot"
    else:
        generated = root / ".runtime/bootstrap/classrooms"
        if not (generated / "database.db").is_file():
            if generated.exists():
                raise FileExistsError("Incomplete classroom build preserved; inspect .runtime/bootstrap/classrooms")
            run([str(root / ".venv/Scripts/python.exe"), "-m", "scripts.build_fresh_classrooms", "--output", str(generated)])
        # Check SQLite content before handing it to backup/restore validation.
        from scripts.backup_database import backup
        snapshot = generated / "snapshot"
        if not snapshot.exists():
            backup(generated / "database.db", generated / "storage", snapshot)
        restore(snapshot, target, storage)
        credentials = generated
        result = "new-classrooms"
    accounts = root / ".runtime/accounts"
    accounts.mkdir(parents=True, exist_ok=True)
    for name in ("LOGIN.txt", "students.csv"):
        source = credentials / name
        destination = accounts / name
        if source.is_file() and not destination.exists():
            shutil.copy2(source, destination)
    print("Data: " + result + ". Account notes: .runtime/accounts (private).", flush=True)
    return result


def main(no_open=False, prepare_only=False):
    if sys.platform != "win32":
        raise RuntimeError("One-file bootstrap targets Windows x64")
    os.chdir(ROOT)
    env = dict(os.environ, PYTHONUTF8="1", DISABLE_SQLALCHEMY_CEXT_RUNTIME="1", RAYON_NUM_THREADS="2", NODE_OPTIONS="--max-old-space-size=1536", NEXT_TELEMETRY_DISABLED="1")
    os.environ.update(env)
    kit = kit_for(ROOT)
    venv = ROOT / ".venv/Scripts/python.exe"
    marker = ROOT / ".runtime/bootstrap/app-ready.json"
    dependencies_marker = ROOT / ".runtime/bootstrap/dependencies-ready.json"
    signature = dependency_signature(ROOT)
    ready = any(path.is_file() and json.loads(path.read_text()).get("signature") == signature for path in (marker, dependencies_marker))
    ready = ready and venv.is_file() and (ROOT / "client/node_modules/next/dist/bin/next").is_file() and (ROOT / "tools/nginx/nginx.exe").is_file()

    def run(command):
        subprocess.run(command, cwd=ROOT, env=env, check=True)

    if not ready:
        if kit:
            from scripts.setup_offline import install
            install(ROOT, create_teacher=False, resume=True)
        else:
            if not venv.is_file():
                run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
            run([str(venv), "-m", "pip", "install", "-r", str(ROOT / "server/requirements.lock")])
            npm = shutil.which("npm.cmd")
            if not npm:
                raise FileNotFoundError("npm.cmd is missing from Node's PATH")
            subprocess.run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=ROOT / "client", env=env, check=True)
            run(["docker", "build", "-t", "lan-lms-judge:day25", str(ROOT / "judge")])
        dependencies_marker.parent.mkdir(parents=True, exist_ok=True)
        dependencies_marker.write_text(json.dumps({"format": 1, "signature": signature}), encoding="utf-8")
        # Data/modules need the project interpreter, not the bare bootstrap Python.
    if Path(sys.executable).resolve() != venv.resolve():
        command = [str(venv), "-m", "scripts.bootstrap_app", "--dependencies-ready"]
        if no_open:
            command.append("--no-open")
        if prepare_only:
            command.append("--prepare-only")
        run(command)
        return
    finish(no_open, prepare_only, kit, run, signature)


def finish(no_open, prepare_only, kit, run, signature):
    prepare_data(ROOT, kit, run)
    probe = subprocess.run(["docker", "image", "inspect", "lan-lms-judge:day25", "--format", "{{.Id}}"], capture_output=True, text=True, timeout=20)
    expected = json.loads((kit / "manifest.json").read_text())["judge_image_id"] if kit else None
    if probe.returncode or (expected and probe.stdout.strip() != expected):
        if kit:
            run(["docker", "load", "--input", str(kit / "dependencies/judge-image.tar")])
        else:
            run(["docker", "build", "-t", "lan-lms-judge:day25", str(ROOT / "judge")])
        probe = subprocess.run(["docker", "image", "inspect", "lan-lms-judge:day25", "--format", "{{.Id}}"], capture_output=True, text=True, check=True, timeout=20)
    image_id = probe.stdout.strip()
    if expected and image_id != expected:
        raise RuntimeError("Judge image does not match the verified kit")
    check_marker = ROOT / ".runtime/bootstrap/judge-verified.json"
    if not check_marker.is_file() or json.loads(check_marker.read_text()).get("image") != image_id:
        from judge.runners.container import DockerJudge, TestCase
        from judge.limits import Limits
        sources = {
            "c": '#include <stdio.h>\nint main(){int a,b;scanf("%d%d",&a,&b);printf("%d\\n",a+b);}',
            "cpp": '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}',
            "java": 'import java.util.*;public class Main{public static void main(String[]a){Scanner s=new Scanner(System.in);System.out.println(s.nextInt()+s.nextInt());}}',
        }
        for language, source in sources.items():
            result = DockerJudge().grade(source, language, [TestCase(b"2 3\n", b"5\n", 10)], limits=Limits(memory_mib=512))
            if result.verdict != "Accepted":
                raise RuntimeError("Judge self-check failed for " + language + ": " + result.verdict)
            print("Judge check: " + language + " AC", flush=True)
        check_marker.parent.mkdir(parents=True, exist_ok=True)
        check_marker.write_text(json.dumps({"image": image_id}), encoding="utf-8")
    marker = ROOT / ".runtime/bootstrap/app-ready.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"format": 1, "signature": signature}), encoding="utf-8")
    if not prepare_only:
        from scripts.launch_web import lan_addresses
        command = [str(ROOT / ".venv/Scripts/python.exe"), "scripts/launch_web.py"]
        addresses = lan_addresses()
        if addresses:
            command += ["--lan"]
        else:
            print("No LAN address: opening this computer only. Connect LAN and run again to share.")
            command += ["--local"]
        if no_open:
            command.append("--no-open")
        run(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--dependencies-ready", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.dependencies_ready:
        os.chdir(ROOT)
        def run(command): subprocess.run(command, cwd=ROOT, check=True)
        finish(args.no_open, args.prepare_only, kit_for(ROOT), run, dependency_signature(ROOT))
    else:
        main(args.no_open, args.prepare_only)
