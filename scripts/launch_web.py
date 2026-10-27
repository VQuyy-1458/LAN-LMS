"""Windows launcher: one menu for local/LAN web, with verified process ownership.

Does not install software, change firewall/network profiles or reset user data.
Internal API/Next ports stay on loopback; LAN mode binds only the selected IP.
"""

import argparse
from contextlib import contextmanager
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "launcher"
STATE = RUNTIME / "state.json"
PRIVATE_LANS = tuple(
    ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@contextmanager
def launcher_lock():
    import msvcrt

    RUNTIME.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / "launcher.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError(
                "Trình chạy đang được mở ở cửa sổ khác. Hãy dùng cửa sổ đó."
            ) from error
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def private_ipv4(value):
    address = ipaddress.IPv4Address(value)
    if not any(address in network for network in PRIVATE_LANS):
        raise ValueError("Chỉ chọn IPv4 LAN thuộc 10.x, 172.16–31.x hoặc 192.168.x.")
    return str(address)


def powershell(script):
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();" + script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        creationflags=NO_WINDOW,
        check=True,
    )
    return result.stdout.strip()


def process_snapshot():
    raw = powershell(
        "Get-CimInstance Win32_Process | Where-Object { $_.CreationDate -and $_.CommandLine } | ForEach-Object { [pscustomobject]@{pid=[int]$_.ProcessId;parent=[int]$_.ParentProcessId;command=$_.CommandLine;created=$_.CreationDate.ToUniversalTime().ToString('o')} } | ConvertTo-Json -Compress"
    )
    entries = json.loads(raw or "[]")
    return {entry["pid"]: entry for entry in entries}


def owned_processes(saved, current):
    """PID alone is insufficient: match creation time AND exact command line."""
    return [
        item
        for item in saved
        if item.get("pid") in current
        and item.get("created")
        and item.get("command")
        and current[item["pid"]].get("created") == item["created"]
        and current[item["pid"]].get("command") == item["command"]
    ]


def descendants(roots, snapshot):
    found = set(roots)
    while True:
        added = {
            pid for pid, item in snapshot.items() if item["parent"] in found
        } - found
        if not added:
            break
        found.update(added)
    return [snapshot[pid] for pid in found if pid in snapshot]


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None


def write_state(state):
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(STATE)


def stop():
    state = load_state()
    if not state:
        print("Không có phiên web nào do trình chạy này quản lý.")
        return
    current = process_snapshot()
    matches = owned_processes(state.get("processes", []), current)
    root_ids = {item["pid"] for item in matches}
    # A matched parent also proves ownership of descendants created since startup.
    targets = descendants(root_ids, current)
    # Stop parents with their trees first: killing an Nginx worker alone makes
    # its master spawn a replacement between snapshots.
    targets.sort(key=lambda item: item["parent"] in root_ids)
    for item in targets:
        # No shell-composed commands and no global kill by image name.
        subprocess.run(
            ["taskkill.exe", "/PID", str(item["pid"]), "/T", "/F"],
            capture_output=True,
            creationflags=NO_WINDOW,
            timeout=10,
        )
    remaining = owned_processes(targets, process_snapshot()) if targets else []
    if remaining:
        state["processes"] = remaining
        write_state(state)
        raise RuntimeError(
            "Còn tiến trình chưa dừng được; đã giữ thông tin để thử lại."
        )
    STATE.unlink(missing_ok=True)
    print("Đã dừng các tiến trình web của project.")


def lan_addresses():
    raw = powershell(
        "Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } | ForEach-Object { foreach($a in $_.IPv4Address) { [pscustomobject]@{name=$_.InterfaceAlias;ip=$a.IPAddress} } } | ConvertTo-Json -Compress"
    )
    entries = json.loads(raw or "[]")
    if isinstance(entries, dict):
        entries = [entries]
    result = []
    for item in entries:
        try:
            item["ip"] = private_ipv4(item["ip"])
        except ValueError:
            continue
        if not any(old["ip"] == item["ip"] for old in result):
            result.append(item)
    return result


def choose_lan(explicit=None):
    options = lan_addresses()
    if explicit:
        address = private_ipv4(explicit)
        if address not in {entry["ip"] for entry in options}:
            raise ValueError("IP này không thuộc kết nối LAN đang hoạt động của máy.")
        return address
    if not options:
        raise RuntimeError(
            "Chưa thấy kết nối LAN đang hoạt động. Kiểm tra dây mạng/Wi-Fi."
        )
    if len(options) == 1:
        print(f"Mạng đang dùng: {options[0]['name']} — {options[0]['ip']}")
        return options[0]["ip"]
    print("Chọn mạng để các máy khác truy cập:")
    for i, entry in enumerate(options, 1):
        print(f"  {i}. {entry['name']} — {entry['ip']}")
    value = int(input("Số mạng: ").strip())
    if not 1 <= value <= len(options):
        raise ValueError("Số mạng không hợp lệ.")
    return options[value - 1]["ip"]


def make_environment(root, address=None, tls=None):
    env = {
        key: value
        for key, value in dotenv_values(root / "server" / ".env").items()
        if value is not None
    }
    env.update(os.environ)
    env.update(
        PYTHONUTF8="1", DISABLE_SQLALCHEMY_CEXT_RUNTIME="1", NEXT_TELEMETRY_DISABLED="1"
    )
    origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
    if address:
        origins.append(f"http://{private_ipv4(address)}:8080")
    if tls:
        origins.append(tls["origin"])
        env["PUBLIC_ORIGIN"] = f"http://{private_ipv4(address)}:8080"
        env["HTTPS_ORIGIN"] = tls["origin"]
        env["LAN_CA_CERTIFICATE"] = tls["ca"]
    env["ALLOWED_ORIGINS"] = ",".join(origins)
    demo = root / ".runtime" / "web" / "demo.db"
    if demo.is_file():
        env["DATABASE_URL"] = "sqlite:///" + demo.as_posix()
        env["STORAGE_ROOT"] = str(root / ".runtime" / "web" / "storage")
    # Otherwise Settings loads server/.env and the normal project database.
    return env


def make_proxy_config(source, address=None, tls=None):
    listener = "listen 127.0.0.1:8080;"
    if address:
        listener += "\n        listen " + private_ipv4(address) + ":8080;"
    if source.count("listen 8080;") != 1:
        raise ValueError("Không nhận diện được listener mẫu trong scripts/nginx.conf.")
    normal = source.replace("listen 8080;", listener)
    if not tls:
        return normal
    if not address or "http {" not in source:
        raise ValueError("HTTPS cần cấu hình HTTP đầy đủ và IP LAN.")
    paths = []
    for name in ("certificate", "key"):
        path = Path(tls[name]).resolve().as_posix()
        if any(c in path for c in '\r\n"{};'):
            raise ValueError("Đường dẫn chứng chỉ không hợp lệ.")
        paths.append(path)
    start = source.index("server {")
    depth = 0
    end = start
    for index in range(source.index("{", start), len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            end = index + 1
            break
    block = source[start:end].replace("listen 8080;", f'listen {private_ipv4(address)}:8443 ssl;\n        ssl_certificate "{paths[0]}";\n        ssl_certificate_key "{paths[1]}";\n        ssl_protocols TLSv1.2 TLSv1.3;')
    head, tail = normal.rsplit("}", 1)
    return head + "\n    " + block + "\n}" + tail


def find_nginx():
    candidates = [
        os.environ.get("NGINX_PATH"),
        shutil.which("nginx.exe"),
        str(ROOT / "tools" / "nginx" / "nginx.exe"),
    ]
    candidates += [
        str(p)
        for p in sorted(
            (ROOT / "tmp" / "nginx-review").glob("*/nginx.exe"), reverse=True
        )
    ]
    for value in candidates:
        if value and Path(value).is_file():
            return str(Path(value).resolve())
    raise FileNotFoundError(
        "Chưa tìm thấy Nginx. Đặt biến NGINX_PATH trỏ tới nginx.exe đã cài."
    )


def fingerprint(client):
    paths = [p for p in (client / "src").rglob("*") if p.is_file()]
    paths += [p for p in (client / "public").rglob("*") if p.is_file()]
    paths += [
        client / name
        for name in (
            "package.json",
            "package-lock.json",
            "next.config.ts",
            "tsconfig.json",
            "postcss.config.mjs",
        )
    ]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(client).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def ensure_build(node, env):
    client = ROOT / "client"
    next_cli = client / "node_modules" / "next" / "dist" / "bin" / "next"
    if not next_cli.exists():
        raise FileNotFoundError(
            "Chưa cài frontend. Chạy npm ci trong client một lần trước."
        )
    checksum = fingerprint(client)
    saved = RUNTIME / "build-fingerprint.txt"
    if (
        not (client / ".next" / "BUILD_ID").exists()
        or not saved.exists()
        or saved.read_text() != checksum
    ):
        print(
            "Đang chuẩn bị giao diện; các lần sau chỉ build lại khi code thay đổi…",
            flush=True,
        )
        subprocess.run([node, str(next_cli), "build"], cwd=client, env=env, check=True)
        saved.write_text(checksum)
    return next_cli


def http_ok(path="/api/ready"):
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:8080" + path, timeout=2) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def available(address=None, tls=None):
    checks = [("127.0.0.1", port) for port in (8000, 3000, 8080)]
    if address:
        checks.append((address, 8080))
        if tls:
            checks.append((address, 8443))
    for host, port in checks:
        with socket.socket() as probe:
            try:
                probe.bind((host, port))
            except OSError as error:
                raise RuntimeError(
                    f"Cổng {host}:{port} đang được dùng. Trình chạy giữ nguyên tiến trình đó; hãy dừng phiên cũ trước."
                ) from error


def start(address=None, open_browser=True):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    tls = None
    if address:
        try:
            from scripts.setup_lan_https import prepare_tls, openssl_path
        except ModuleNotFoundError:
            from setup_lan_https import prepare_tls, openssl_path
        try:
            openssl_path()
        except RuntimeError:
            print("Chưa có OpenSSL: chạy HTTP LAN; HTTPS là tùy chọn.", flush=True)
        else:
            tls = prepare_tls(ROOT, address)
    source_version = fingerprint(ROOT / "client")
    server_hash = hashlib.sha256()
    server_inputs = list((ROOT / "server" / "app").rglob("*.py"))
    server_inputs += list((ROOT / "judge").rglob("*.py"))
    server_inputs += [Path(__file__), ROOT / "scripts" / "nginx.conf", ROOT / "scripts" / "setup_lan_https.py"]
    for path in sorted(server_inputs):
        server_hash.update(path.read_bytes())
    if tls:
        server_hash.update(Path(tls["certificate"]).read_bytes())
    server_version = server_hash.hexdigest()
    old = load_state()
    if old:
        alive = owned_processes(old.get("processes", []), process_snapshot())
        if alive and old.get("lan_ip") == address and old.get("source_version") == source_version and old.get("server_version") == server_version and old.get("tls_fingerprint") == (tls["fingerprint"] if tls else None) and http_ok() and http_ok("/login"):
            show(old, open_browser)
            return
        if alive:
            stop()
        else:
            STATE.unlink(missing_ok=True)
    available(address, tls)
    nginx = find_nginx()
    node = shutil.which("node.exe") or shutil.which("node")
    if not node:
        raise FileNotFoundError("Chưa tìm thấy Node.js trong PATH.")
    env = make_environment(ROOT, address, tls)
    next_cli = ensure_build(node, env)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "server/alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    prefix = RUNTIME / "nginx"
    for child in ("logs", "temp"):
        (prefix / child).mkdir(parents=True, exist_ok=True)
    config = prefix / "nginx.conf"
    config.write_text(
        make_proxy_config(
            (ROOT / "scripts" / "nginx.conf").read_text(encoding="utf-8"), address, tls
        ),
        encoding="utf-8",
    )
    nginx_args = [nginx, "-p", prefix.as_posix() + "/", "-c", str(config)]
    subprocess.run(
        nginx_args + ["-t"], capture_output=True, check=True, creationflags=NO_WINDOW
    )
    jobs = [
        (
            "api",
            ROOT,
            [
                sys.executable,
                "-m",
                "uvicorn",
                "server.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--workers",
                "1",
                "--proxy-headers",
                "--forwarded-allow-ips",
                "127.0.0.1",
                "--ws-max-size",
                "4096",
            ],
        ),
        (
            "web",
            ROOT / "client",
            [node, str(next_cli), "start", "-H", "127.0.0.1", "-p", "3000"],
        ),
        ("proxy", ROOT, nginx_args + ["-g", "daemon off;"]),
    ]
    children = []
    state = {
        "lan_ip": address,
        "url": "http://localhost:8080",
        "processes": [],
        "judge": False,
        "source_version": source_version,
        "server_version": server_version,
        "tls_fingerprint": tls["fingerprint"] if tls else None,
        "lan_url": tls["origin"] if tls else None,
        "database": env.get("DATABASE_URL", "server/.env hoặc database/lan_lms.db"),
    }
    try:
        for name, cwd, command in jobs:
            with (RUNTIME / (name + ".log")).open("ab") as log:
                children.append(
                    subprocess.Popen(
                        command,
                        cwd=cwd,
                        env=env,
                        stdout=log,
                        stderr=log,
                        creationflags=NO_WINDOW,
                    )
                )
            state["processes"] = descendants(
                {p.pid for p in children}, process_snapshot()
            )
            write_state(state)
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if any(p.poll() is not None for p in children):
                raise RuntimeError(
                    "Một dịch vụ không khởi động được. Xem log trong .runtime/launcher/."
                )
            if http_ok() and http_ok("/login"):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(
                "Web chưa sẵn sàng sau 35 giây. Xem log .runtime/launcher/."
            )
        docker = shutil.which("docker.exe") or shutil.which("docker")
        if docker:
            try:
                inspect = subprocess.run(
                    [
                        docker,
                        "image",
                        "inspect",
                        env.get("JUDGE_IMAGE", "lan-lms-judge:day25"),
                    ],
                    capture_output=True,
                    timeout=4,
                    creationflags=NO_WINDOW,
                )
                state["judge"] = inspect.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                pass
            with (RUNTIME / "worker.log").open("ab") as log:
                children.append(subprocess.Popen([sys.executable, "-m", "judge.worker"], cwd=ROOT,
                    env=env, stdout=log, stderr=log, creationflags=NO_WINDOW))
            state["worker_started"] = True
        state["processes"] = descendants({p.pid for p in children}, process_snapshot())
        write_state(state)
    except BaseException:
        # Persist every proven child before cleanup if startup fails partway.
        state["processes"] = descendants({p.pid for p in children}, process_snapshot())
        write_state(state)
        stop()
        raise
    show(state, open_browser)


def show(state, open_browser=False):
    print("\nWEB ĐÃ SẴN SÀNG: " + state["url"])
    if state.get("lan_ip"):
        print("Máy khác cùng LAN mở: http://" + state["lan_ip"] + ":8080")
        print("Điểm danh: Chụp QR để mở camera hệ thống; không cần cài chứng chỉ.")
        print("Tùy chọn quét liên tục HTTPS: " + str(state.get("lan_url") or "chưa bật"))
        print("Cài HTTPS (tùy chọn): http://" + state["lan_ip"] + ":8080/setup")
        if state.get("tls_fingerprint"):
            print("Chứng chỉ CA SHA-256: " + state["tls_fingerprint"])
        print("Nếu máy khác chưa vào được, kiểm tra quyền firewall TCP 8080/8443 cho LAN.")
    print(
        "Chấm code: "
        + (
            "worker đã khởi động."
            if state.get("judge")
            else "worker đang chờ Docker Engine/image; xem trạng thái trong mục Thi lập trình."
        )
    )
    print("Dữ liệu: " + state.get("database", ""))
    print("Web chạy nền. Muốn dừng, nhấp đúp DUNG_WEB.cmd.")
    if open_browser:
        webbrowser.open(state["url"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--local", action="store_true")
    mode.add_argument("--lan", action="store_true")
    mode.add_argument("--stop", action="store_true")
    mode.add_argument("--status", action="store_true")
    parser.add_argument("--ip", help="IPv4 LAN đang hoạt động; dùng cùng --lan")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("Launcher này dành cho Windows; Linux dùng lệnh trong README.")
    if args.ip and not args.lan:
        parser.error("--ip chỉ dùng cùng --lan")
    if not any((args.local, args.lan, args.stop, args.status)):
        print(
            "\nLAN-LMS — CHẠY WEB\n  1. Mở trên máy này\n  2. Cho các máy cùng LAN truy cập\n  3. Dừng web\n"
        )
        choice = input("Chọn 1, 2 hoặc 3: ").strip()
        if choice not in ("1", "2", "3"):
            raise ValueError("Lựa chọn không hợp lệ.")
        args.local, args.lan, args.stop = choice == "1", choice == "2", choice == "3"
    if args.stop:
        stop()
    elif args.status:
        state = load_state()
        if (
            state
            and owned_processes(state.get("processes", []), process_snapshot())
            and http_ok()
        ):
            show(state)
        else:
            print("Web chưa chạy bằng launcher này.")
    else:
        start(choose_lan(args.ip) if args.lan else None, not args.no_open)


if __name__ == "__main__":
    try:
        if os.name == "nt":
            with launcher_lock():
                main()
        else:
            main()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print("\nKhông chạy được web: " + str(error), file=sys.stderr)
        raise SystemExit(1)
