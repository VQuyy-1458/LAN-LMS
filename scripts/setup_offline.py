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


def install(root=ROOT, create_teacher=True, *, resume=False):
    root = Path(root).resolve()
    kit = root.parent
    manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "lan-lms-offline" or manifest.get("version") != 1:
        raise ValueError("Unsupported offline kit")
    if sys.platform != "win32" or platform.machine() != manifest["machine"] or sys.version_info[:2] != (3, 12) or sys.maxsize < 2**32:
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
    state_path=root/".runtime"/"setup-offline.json"
    signature=checksum(root/"server/requirements.lock")+checksum(root/"client/package-lock.json")
    state={"format":1,"root":str(root),"signature":signature,"owned":[],"done":[]}
    if state_path.exists():
        state=json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("root")!=str(root) or state.get("signature")!=signature or state.get("format")!=1:
            raise ValueError("Setup location/dependencies changed; use a fresh kit folder, preserving existing data")
        if not resume: raise FileExistsError("Setup already started. Use CAI_VA_CHAY_LMS.cmd to resume")
    def save():
        state_path.parent.mkdir(parents=True,exist_ok=True)
        temporary=state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state,indent=2),encoding="utf-8");temporary.replace(state_path)
    def own(name,path):
        if name not in state["owned"]:
            if path.exists():raise FileExistsError("Existing unmanaged installation preserved: "+str(path))
            state["owned"].append(name);save()
    def done(name):
        if name not in state["done"]:state["done"].append(name)
        save()
    venv = root / ".venv"
    own("venv",venv)
    env = dict(os.environ, PYTHONUTF8="1", PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1", NEXT_TELEMETRY_DISABLED="1", DISABLE_SQLALCHEMY_CEXT_RUNTIME="1", RAYON_NUM_THREADS="2", NODE_OPTIONS="--max-old-space-size=1536")
    if "venv" not in state["done"] or not (venv/"Scripts/python.exe").is_file():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, env=env)
        done("venv")
    python = venv / "Scripts" / "python.exe"
    dependencies = kit / "dependencies"
    if "pip" not in state["done"]:
        subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(dependencies / "wheels"), "-r", str(root / "server/requirements.lock")], check=True, env=env)
        done("pip")
    modules = root / "client" / "node_modules"
    own("modules",modules)
    if "modules" not in state["done"] or not (modules/"next/dist/bin/next").is_file():
        modules.mkdir(exist_ok=True)
        with zipfile.ZipFile(dependencies / "node_modules.zip") as archive:
            for entry in archive.infolist():
                path = (modules / entry.filename).resolve()
                if not path.is_relative_to(modules) or path==modules or path.is_symlink() or entry.filename.startswith(("/", "\\")) or "\\" in entry.filename or ":" in entry.filename or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Unsafe npm archive entry")
                if entry.is_dir(): path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as src, path.open("wb") as dst: shutil.copyfileobj(src, dst)
        done("modules")
    target_nginx = root / "tools" / "nginx"
    own("nginx",target_nginx)
    if "nginx" not in state["done"] or not (target_nginx/"nginx.exe").is_file():
        target_nginx.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(dependencies / "nginx", target_nginx,dirs_exist_ok=True)
        done("nginx")
    inspected = subprocess.run([docker, "image", "inspect", manifest["judge_image"], "--format", "{{.Id}}"], capture_output=True, text=True, timeout=15)
    if inspected.returncode or inspected.stdout.strip() != manifest["judge_image_id"]:
        print("Loading Docker image; this can take several minutes...", flush=True)
        subprocess.run([docker, "load", "--input", str(dependencies / "judge-image.tar")], check=True, timeout=300)
    image_id = subprocess.check_output([docker, "image", "inspect", manifest["judge_image"], "--format", "{{.Id}}"], text=True, timeout=15).strip()
    if image_id != manifest["judge_image_id"]: raise ValueError("Docker image ID mismatch")
    config = root / "server" / ".env"
    if not config.exists(): shutil.copy2(root / "server" / ".env.example", config)
    snapshot = kit / "classroom-data" / "server-snapshot" / "manifest.json"
    if not snapshot.is_file():
        subprocess.run([str(python), "-m", "alembic", "-c", "server/alembic.ini", "upgrade", "head"], cwd=root, env=env, check=True)
    if "build" not in state["done"] or not (root/"client/.next/BUILD_ID").exists():
        subprocess.run([node, str(modules / "next/dist/bin/next"), "build", "--webpack"], cwd=root / "client", env=env, check=True)
        done("build")
    from scripts.launch_web import fingerprint
    launcher = root / ".runtime" / "launcher"
    launcher.mkdir(parents=True, exist_ok=True)
    (launcher / "build-fingerprint.txt").write_text(fingerprint(root / "client"))
    snapshot = kit / "classroom-data" / "server-snapshot" / "manifest.json"
    if snapshot.is_file():
        print("Offline setup complete. Run NAP_DU_LIEU_LOP.cmd at the kit root, then LAN-LMS\\CHAY_LAN.cmd. Existing classroom accounts are preserved.", flush=True)
    else:
        if create_teacher: subprocess.run([str(python), "-m", "server.app.seed"], cwd=root, env=env, check=True)
        print("Offline setup complete. Run CHAY_LAN.cmd, then import your course ZIP.", flush=True)


if __name__ == "__main__": install()
