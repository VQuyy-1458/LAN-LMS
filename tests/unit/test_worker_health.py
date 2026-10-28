from pathlib import Path
from judge import health


def test_windows_transient_file_lock_does_not_lose_heartbeat(tmp_path, monkeypatch):
    original = Path.replace
    attempts = []
    def locked_once(path, destination):
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("Windows file is briefly open")
        return original(path, destination)
    monkeypatch.setattr(Path, "replace", locked_once)
    health.write(tmp_path, "worker", "db", True, "judge")
    assert len(attempts) == 2
    assert health.status(tmp_path, "db") == 1
    assert not list((tmp_path / ".worker-health").glob("*.tmp"))
