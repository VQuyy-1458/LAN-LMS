"""Release packaging must preserve private data boundaries and existing deliveries."""

from pathlib import Path
import subprocess
import zipfile

import pytest

from scripts.package_submission import package


def git(root, *args):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Packaging Test",
            "-c",
            "user.email=test@example.invalid",
            *args,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def release(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init")
    (root / "REPORT").mkdir()
    for suffix in ("docx", "pdf"):
        (root / "REPORT" / f"NhomXX_LANLMS_Report.{suffix}").write_bytes(
            b"report fixture"
        )
    (root / "README.md").write_text("Release fixture", encoding="utf-8")
    (root / ".gitignore").write_text(".env\n.runtime/\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Release fixture")
    return root


def test_package_uses_committed_snapshot_and_preserves_delivery(release, tmp_path):
    (release / ".env").write_text("PRIVATE=do-not-package", encoding="utf-8")
    (release / "untracked.txt").write_text("private working file", encoding="utf-8")
    (release / "README.md").write_text("Uncommitted change", encoding="utf-8")
    archive = package("07", tmp_path / "output", root=release)
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        names = zipped.namelist()
        assert "Nhom07_LANLMS/Report/Nhom07_LANLMS_Report.docx" in names
        assert "Nhom07_LANLMS/Report/Nhom07_LANLMS_Report.pdf" in names
        source = "Nhom07_LANLMS/Source/Nhom07_LANLMS_Source/"
        assert zipped.read(source + "README.md") == b"Release fixture"
        assert not any(name.endswith((".env", "untracked.txt")) for name in names)
        assert (
            git(release, "rev-parse", "HEAD").stdout.strip()
            in zipped.read("Nhom07_LANLMS/VERSION.txt").decode()
        )
    before = archive.read_bytes()
    with pytest.raises(FileExistsError):
        package("07", tmp_path / "output", root=release)
    assert archive.read_bytes() == before


def test_package_rejects_committed_private_environment(release, tmp_path):
    (release / ".env").write_text("PRIVATE=do-not-package", encoding="utf-8")
    git(release, "add", "-f", ".env")
    git(release, "commit", "-m", "Unsafe fixture")
    with pytest.raises(ValueError, match="Private/runtime"):
        package("XX", tmp_path / "output", root=release)
    assert not (tmp_path / "output" / "NhomXX_LANLMS.zip").exists()


def test_package_rejects_invalid_group(release, tmp_path):
    with pytest.raises(ValueError, match="Group"):
        package("../escape", tmp_path / "output", root=release)
