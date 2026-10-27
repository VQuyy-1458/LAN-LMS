"""Install a verified USB kit locally without pip/npm network access."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile
from scripts.prepare_usb import checksum

ROOT = Path(__file__).resolve().parents[1]


def install(root=ROOT, create_teacher=True):
    root = Path(root).resolve()
    kit = root.parent
    manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "lan-lms-offline" or manifest.get("version") != 1:
        raise ValueError("Unsupported offline kit")
    if sys.platform != "win32" or platform.machine() != manifest["machine"] or sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use the same Windows architecture and Python 3.12 as the kit")
    node = shutil.which("node"); docker = shutil.which("docker")
    if not node or not docker: raise RuntimeError("Install Node.js and Docker Desktop first")
    actual = subprocess.check_output([node, "--version"], text=True).strip()
    if actual.split('.')[0] != manifest["node"].split('.')[0]: raise RuntimeError("Node.js major must match the kit: " + manifest["node"])
    subprocess.run([docker, "info"], check=True, stdout=subprocess.DEVNULL, timeout=15)
    print("Verifying every kit file...", flush=True)
    for name, digest in manifest["files"].items():
        path = (kit / name).resolve()
        if not path.is_relative_to(kit) or not path.is_file() or path.is_symlink() or checksum(path) != digest:
            raise ValueError("Missing or modified kit file: " + name)
    venv = root / ".venv"
    if venv.exists(): raise FileExistsError("This folder already has .venv; preserve it and unpack the kit into a fresh folder")
    env = dict(os.environ, PYTHONUTF8="1", PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1", NEXT_TELEMETRY_DISABLED="1", DISABLE_SQLALCHEMY_CEXT_RUNTIME="1")
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, env=env)
    python = venv / "Scripts" / "python.exe"
    dependencies = kit / "dependencies"
    subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(dependencies / "wheels"), "-r", str(root / "server/requirements.lock")], check=True, env=env)
    modules = root / "client" / "node_modules"
    if modules.exists(): raise FileExistsError("node_modules already exists; use a fresh source folder")
    modules.mkdir()
    with zipfile.ZipFile(dependencies / "node_modules.zip") as archive:
        for entry in archive.infolist():
            path = (modules / entry.filename).resolve()
            if not path.is_relative_to(modules) or entry.filename.startswith(("/", "\\")) or "\\" in entry.filename or ":" in entry.filename:
                raise ValueError("Unsafe npm archive entry")
            if entry.is_dir(): path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as src, path.open("xb") as dst: shutil.copyfileobj(src, dst)
    target_nginx = root / "tools" / "nginx"
    if target_nginx.exists(): raise FileExistsError("Nginx folder already exists; use fresh source")
    target_nginx.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(dependencies / "nginx", target_nginx)
    inspected = subprocess.run([docker, "image", "inspect", manifest["judge_image"], "--format", "{{.Id}}"], capture_output=True, text=True, timeout=15)
    if inspected.returncode or inspected.stdout.strip() != manifest["judge_image_id"]:
        print("Loading Docker image; this can take several minutes...", flush=True)
        subprocess.run([docker, "load", "--input", str(dependencies / "judge-image.tar")], check=True, timeout=300)
    image_id = subprocess.check_output([docker, "image", "inspect", manifest["judge_image"], "--format", "{{.Id}}"], text=True, timeout=15).strip()
    if image_id != manifest["judge_image_id"]: raise ValueError("Docker image ID mismatch")
    config = root / "server" / ".env"
    if not config.exists(): shutil.copy2(root / "server" / ".env.example", config)
    subprocess.run([str(python), "-m", "alembic", "-c", "server/alembic.ini", "upgrade", "head"], cwd=root, env=env, check=True)
    subprocess.run([node, str(modules / "next/dist/bin/next"), "build"], cwd=root / "client", env=env, check=True)
    if create_teacher: subprocess.run([str(python), "-m", "server.app.seed"], cwd=root, env=env, check=True)
    print("Offline setup complete. Run CHAY_LAN.cmd, then import your course ZIP.", flush=True)


if __name__ == "__main__": install()
