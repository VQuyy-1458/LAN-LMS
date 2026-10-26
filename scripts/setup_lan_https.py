"""Create a private LAN CA and server certificate; never install trust automatically."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess


def openssl_path():
    for path in (os.environ.get("OPENSSL_PATH"), shutil.which("openssl"),
                 r"C:\Program Files\Git\usr\bin\openssl.exe"):
        if path and Path(path).is_file():
            return str(path)
    raise RuntimeError("Cần OpenSSL (có sẵn cùng Git for Windows) để tạo HTTPS LAN.")


def prepare_tls(root: Path, address: str):
    ip = ipaddress.IPv4Address(address)
    if not ip.is_private or ip.is_loopback or ip.is_unspecified:
        raise ValueError("Chọn IP LAN của máy chủ.")
    folder = root / ".runtime" / "tls"
    folder.mkdir(parents=True, exist_ok=True)
    executable = openssl_path()

    def run(*args):
        return subprocess.run([executable, *map(str, args)], cwd=folder, check=True,
                              capture_output=True, timeout=40,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    ca, ca_key = folder / "ca.pem", folder / "ca.key"
    if ca.exists() != ca_key.exists():
        raise RuntimeError("Thiếu một phần của CA cũ. Giữ nguyên file; cần khôi phục đủ ca.pem và ca.key.")
    if not ca.exists():
        run("req", "-x509", "-newkey", "rsa:3072", "-sha256", "-nodes", "-days", "3650",
            "-keyout", ca_key, "-out", ca, "-subj", "/CN=LAN-LMS Local CA",
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    certificate, key = folder / "server.pem", folder / "server.key"
    stamp = folder / "address.txt"
    renew = not certificate.exists() or not key.exists() or not stamp.exists() or stamp.read_text() != address
    if not renew:
        try:
            run("x509", "-checkend", "604800", "-noout", "-in", certificate)
            run("verify", "-CAfile", ca, certificate)
        except subprocess.CalledProcessError:
            renew = True
    if renew:
        extensions = folder / "server.ext"
        extensions.write_text("basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1,IP:"+address+"\n", encoding="ascii")
        run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", folder / "server.csr", "-subj", "/CN=LAN-LMS Server")
        run("x509", "-req", "-in", folder / "server.csr", "-CA", ca, "-CAkey", ca_key,
            "-CAcreateserial", "-out", certificate, "-days", "397", "-sha256", "-extfile", extensions)
        run("verify", "-CAfile", ca, certificate)
        stamp.write_text(address)
    public = folder / "LAN-LMS-CA.cer"
    run("x509", "-in", ca, "-outform", "DER", "-out", public)
    digest = hashlib.sha256(public.read_bytes()).hexdigest().upper()
    return {"certificate": str(certificate), "key": str(key), "ca": str(public),
            "fingerprint": ":".join(digest[i:i+2] for i in range(0, len(digest), 2)),
            "origin": f"https://{address}:8443"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_tls(Path(__file__).resolve().parents[1], args.ip), indent=2))
