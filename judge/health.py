"""Private worker heartbeat files, shared only by processes using the same DB/storage."""
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time
import uuid


def probe(image):
    try:
        result = subprocess.run(["docker", "image", "inspect", image], capture_output=True,
                                timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def write(root, worker_id, database_url, ready, image):
    folder = Path(root) / ".worker-health"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (hashlib.sha256(worker_id.encode()).hexdigest() + ".json")
    temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps({"updated_at": time.time(), "ready": ready, "image": image,
                                     "database": hashlib.sha256(database_url.encode()).hexdigest()}), encoding="utf-8")
    try:
        for attempt in range(5):
            try:
                temporary.replace(path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.03 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)


def status(root, database_url):
    expected = hashlib.sha256(database_url.encode()).hexdigest()
    active = 0
    for path in (Path(root) / ".worker-health").glob("*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            if row["database"] == expected and 0 <= time.time() - row["updated_at"] < 30 and row["ready"]:
                active += 1
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return active


class Heartbeat:
    def __init__(self, root, worker_id, database_url, image):
        self.root, self.worker_id, self.database_url, self.image = root, worker_id, database_url, image
        self.ready = False
        self.checked = threading.Event()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stop.is_set():
            self.ready = probe(self.image)
            self.checked.set()
            try:
                write(self.root, self.worker_id, self.database_url, self.ready, self.image)
            except OSError:
                # Windows readers/antivirus can briefly lock an atomic replace.
                # A failed status write must not kill the heartbeat permanently.
                pass
            self.stop.wait(5)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=6)
        try:
            write(self.root, self.worker_id, self.database_url, False, self.image)
        except OSError:
            pass  # Readers expire stale status after 30 seconds.
