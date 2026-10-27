"""Build a Windows offline kit from tracked source and this machine's dependencies."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def build(output):
    if sys.platform != "win32" or sys.version_info[:2] != (3, 12):
        raise RuntimeError("Build this kit on Windows with Python 3.12")
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError("Choose a new output folder")
    if output == ROOT or ROOT.is_relative_to(output): raise ValueError("Output cannot contain the source project")
    node = shutil.which("node")
    docker = shutil.which("docker")
    if not node or not docker: raise RuntimeError("Node.js and running Docker are required")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    image = os.environ.get("JUDGE_IMAGE", "lan-lms-judge:day25")
    image_id = subprocess.check_output([docker, "image", "inspect", image, "--format", "{{.Id}}"], text=True, timeout=15).strip()
    from scripts.launch_web import find_nginx
    nginx = Path(find_nginx()).parent
    modules = ROOT / "client" / "node_modules"
    if not (modules / "next" / "dist" / "bin" / "next").is_file(): raise RuntimeError("Install frontend dependencies first")
    output.mkdir(parents=True)
    source, dependencies = output / "LAN-LMS", output / "dependencies"
    source.mkdir(); dependencies.mkdir()
    # Only tracked source, never .env, DB, credentials, runtime, or user untracked files.
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for name in filter(None, names):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or any(part in (".git", ".runtime", ".venv", "node_modules", ".next") for part in relative.parts):
            raise ValueError("Unexpected tracked private/runtime file")
        path = ROOT / relative
        if path.is_symlink(): raise ValueError("Source links are unsupported")
        if not path.is_file(): continue
        if path.name.startswith(".env") and path.name != ".env.example": raise ValueError("Tracked secret file")
        if path.suffix in (".db", ".sqlite", ".sqlite3"): raise ValueError("Tracked database")
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
    wheels = dependencies / "wheels"; wheels.mkdir()
    print("Preparing Windows Python wheels (Internet required on build machine)...", flush=True)
    if importlib.util.find_spec("pip") is None:
        subprocess.run([sys.executable, "-m", "ensurepip"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "download", "--only-binary=:all:", "-r", str(ROOT / "server/requirements.lock"), "-d", str(wheels)], check=True)
    print("Packing installed Windows frontend dependencies...", flush=True)
    with zipfile.ZipFile(dependencies / "node_modules.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in modules.rglob("*"):
            if path.is_symlink(): raise ValueError("Install npm dependencies without links before packaging")
            if path.is_file(): archive.write(path, path.relative_to(modules).as_posix())
    shutil.copytree(nginx, dependencies / "nginx", ignore=shutil.ignore_patterns("logs", "*_temp"))
    print("Saving Docker compiler image...", flush=True)
    subprocess.run([docker, "save", "--output", str(dependencies / "judge-image.tar"), image], check=True, timeout=300)
    manifest = {"format": "lan-lms-offline", "version": 1, "platform": sys.platform,
                "machine": platform.machine(), "python": "3.12", "node": version,
                "judge_image": image, "judge_image_id": image_id, "files": {}}
    for path in output.rglob("*"):
        if path.is_file(): manifest["files"][path.relative_to(output).as_posix()] = checksum(path)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "START_HERE.txt").write_text(
        "Copy this entire folder to a short local path, e.g. D:\\LAN-LMS-USB.\n"
        "Requires Windows x64, Python 3.12, Node.js major " + version.split('.')[0].lstrip('v') +
        ", Docker Desktop with WSL2/Linux Engine running.\n"
        "Run LAN-LMS\\CAI_OFFLINE.cmd once; no Internet is used by that setup.\n"
        "Then run LAN-LMS\\CHAY_LAN.cmd. Students only use a browser.\n"
        "Sign in with the teacher created during setup and import the course ZIP.\n"
        "Course ZIP/data and software installers are separate from this source/dependency kit.\n", encoding="utf-8")
    print("Offline kit ready: " + str(output), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    build(parser.parse_args().output)
