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


def build(output, reuse_dependencies=None):
    if sys.platform != "win32" or sys.version_info[:2] != (3, 12):
        raise RuntimeError("Build this kit on Windows with Python 3.12")
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError("Choose a new output folder")
    if output == ROOT or ROOT.is_relative_to(output): raise ValueError("Output cannot contain the source project")
    node = shutil.which("node")
    docker = shutil.which("docker")
    if not node or (not docker and not reuse_dependencies): raise RuntimeError("Node.js and running Docker (or a verified older kit) are required")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    image = os.environ.get("JUDGE_IMAGE", "lan-lms-judge:day25")
    previous = None
    if reuse_dependencies:
        previous_root = Path(reuse_dependencies).resolve()
        previous = json.loads((previous_root / "manifest.json").read_text(encoding="utf-8"))
        if previous.get("format") != "lan-lms-offline" or previous.get("version") != 1 or previous["machine"] != platform.machine() or previous["python"] != "3.12" or previous["node"] != version or previous["judge_image"] != image:
            raise ValueError("Previous kit platform/runtime does not match")
        for relative in ("client/package-lock.json", "server/requirements.lock", "judge/Dockerfile", "judge/sandbox_entry.py"):
            if previous["files"].get("LAN-LMS/" + relative) != checksum(ROOT / relative):
                raise ValueError("Dependencies/image inputs changed; build a fresh kit online")
        for name, digest in previous["files"].items():
            if not name.startswith("dependencies/"): continue
            source_path = (previous_root / name).resolve()
            if not source_path.is_relative_to(previous_root) or source_path.is_symlink() or checksum(source_path) != digest:
                raise ValueError("Previous dependency checksum failed")
        image_id = previous["judge_image_id"]
    else:
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
    if previous:
        shutil.copytree(previous_root / "dependencies", dependencies, dirs_exist_ok=True)
        print("Reused checksum-verified dependency/image bundle.", flush=True)
    else:
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
    shutil.copy2(ROOT / "CAI_VA_CHAY_LMS.cmd", output / "CAI_VA_CHAY_LMS.cmd")
    manifest = {"format": "lan-lms-offline", "version": 1, "platform": sys.platform,
                "machine": platform.machine(), "python": "3.12", "node": version,
                "judge_image": image, "judge_image_id": image_id, "files": {}}
    for path in output.rglob("*"):
        if path.is_file(): manifest["files"][path.relative_to(output).as_posix()] = checksum(path)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "START_HERE.txt").write_text(
        "Copy this entire folder to a short local path, e.g. D:\\LAN-LMS-USB.\n"
        "Run CAI_VA_CHAY_LMS.cmd. It checks/install missing Python 3.12, Node.js 24 and Docker/WSL2, then prepares data and opens the web.\n"
        "Internet is required to download missing system software; existing libraries and judge image are bundled.\n"
        "Allow UAC if prompted. Read/accept Docker terms yourself in Docker Desktop. WSL setup may require a reboot; one-shot continuation resumes after sign-in.\n"
        "Needs compatible Windows x64, 8GB+ RAM and BIOS virtualization enabled. ARM/Windows Server are unsupported by this kit.\n"
        "Existing data is preserved. Bundled classroom snapshot, if present, is restored only on a new installation.\n"
        "Students only use a browser. Details: LAN-LMS\\docs\\ONE_FILE_SETUP.md.\n", encoding="utf-8")
    print("Offline kit ready: " + str(output), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reuse-dependencies", help="Path to an older verified kit with unchanged lockfiles and judge image inputs")
    args=parser.parse_args()
    build(args.output,args.reuse_dependencies)
