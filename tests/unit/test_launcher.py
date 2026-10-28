from pathlib import Path

import pytest

from scripts.launch_web import (
    descendants,
    fingerprint,
    make_environment,
    make_proxy_config,
    owned_processes,
    private_ipv4,
)


def test_lan_listener_is_scoped_and_origin_is_exact(tmp_path):
    base = "server { listen 8080; }"
    assert make_proxy_config(base) == "server { listen 127.0.0.1:8080; }"
    lan = make_proxy_config(base, "192.168.1.100")
    assert "listen 192.168.1.100:8080;" in lan
    assert "0.0.0.0" not in lan
    env = make_environment(tmp_path, "192.168.1.100")
    assert env["ALLOWED_ORIGINS"].split(",") == [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://192.168.1.100:8080",
    ]
    for invalid in ("8.8.8.8", "127.0.0.1", "0.0.0.0", "::1", "192.168.1.100:8080"):
        with pytest.raises(ValueError):
            private_ipv4(invalid)


def test_pid_reuse_never_proves_ownership():
    saved = [{"pid": 30, "command": "node next start", "created": "old"}]
    assert not owned_processes(
        saved, {30: {"pid": 30, "command": "node next start", "created": "new"}}
    )
    assert not owned_processes(
        saved, {30: {"pid": 30, "command": "different program", "created": "old"}}
    )
    assert not owned_processes([{"pid": 30}], {30: saved[0]})
    assert owned_processes(saved, {30: dict(saved[0])}) == saved


def test_descendants_are_only_from_owned_roots():
    snapshot = {
        1: {"pid": 1, "parent": 0},
        2: {"pid": 2, "parent": 1},
        3: {"pid": 3, "parent": 2},
        9: {"pid": 9, "parent": 0},
    }
    assert {p["pid"] for p in descendants({1}, snapshot)} == {1, 2, 3}


def test_existing_demo_data_and_env_are_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / "server").mkdir()
    (tmp_path / "server" / ".env").write_text(
        "DATABASE_URL=sqlite:///custom.db\nJUDGE_IMAGE=custom:tag\n"
    )
    assert make_environment(tmp_path)["DATABASE_URL"] == "sqlite:///custom.db"
    demo = tmp_path / ".runtime/web/demo.db"
    demo.parent.mkdir(parents=True)
    demo.write_bytes(b"unchanged database fixture")
    env = make_environment(tmp_path)
    assert env["DATABASE_URL"] == "sqlite:///" + demo.as_posix()
    assert env["STORAGE_ROOT"] == str(demo.parent / "storage")
    assert env["JUDGE_IMAGE"] == "custom:tag"
    assert demo.read_bytes() == b"unchanged database fixture"


def test_only_frontend_inputs_change_build_fingerprint(tmp_path):
    (tmp_path / "src").mkdir()
    source = tmp_path / "src/page.tsx"
    source.write_text("first version")
    for name in (
        "package.json",
        "package-lock.json",
        "next.config.ts",
        "tsconfig.json",
        "postcss.config.mjs",
    ):
        (tmp_path / name).write_text("{}")
    before = fingerprint(tmp_path)
    (tmp_path / ".next").mkdir()
    (tmp_path / ".next/cache").write_text("generated")
    assert fingerprint(tmp_path) == before
    source.write_text("second version")
    assert fingerprint(tmp_path) != before
