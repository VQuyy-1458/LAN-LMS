"""Build the real Docker judge image after Docker Desktop's Linux engine is running."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Chưa có Docker. Cài/mở Docker Desktop với Linux Engine.")
    try:
        result = subprocess.run([docker,"info","--format","{{.OSType}}"],capture_output=True,text=True,timeout=10)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Docker Engine chưa phản hồi. Chưa thể chấm code thật.") from error
    if result.returncode or result.stdout.strip() != "linux":
        raise RuntimeError("Docker Linux Engine chưa chạy. Mở Docker Desktop và chờ Engine running trước.")
    from dotenv import dotenv_values
    image = os.environ.get("JUDGE_IMAGE") or dotenv_values(ROOT/"server"/".env").get("JUDGE_IMAGE") or "lan-lms-judge:day25"
    inspected = subprocess.run([docker,"image","inspect",image],capture_output=True,timeout=10)
    if inspected.returncode:
        print("Đang tạo image chấm C/C++/Java thật; lần đầu cần Internet…",flush=True)
        subprocess.run([docker,"build","-t",image,str(ROOT/"judge")],cwd=ROOT,check=True)
    print("Image bộ chấm đã sẵn sàng. Nếu web đang chạy, worker sẽ tự nhận sau vài giây.")
    print("Nếu web chưa chạy, mở CHAY_LAN.cmd.")


if __name__=="__main__":
    try:
        main()
    except (RuntimeError,OSError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1)
