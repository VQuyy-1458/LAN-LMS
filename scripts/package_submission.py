"""Package a committed release without environment, uploads, databases or build caches."""

import argparse
from datetime import datetime, timezone
import io
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile


def package(group, output, root=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    if not re.fullmatch(r"(?:[0-9]{2}|XX)", group):
        raise ValueError("Group must be two digits or XX")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = f"Nhom{group}_LANLMS"
    destination = output / name
    archive = output / (name + ".zip")
    if destination.exists() or archive.exists():
        raise FileExistsError(
            "Use a new output folder; existing delivery was preserved"
        )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    snapshot = subprocess.run(
        ["git", "archive", "--format=tar", head],
        cwd=root,
        capture_output=True,
        check=True,
    ).stdout
    with tempfile.TemporaryDirectory(
        prefix="lan-lms-package-", dir=output
    ) as temporary:
        stage = Path(temporary) / name
        source = stage / "Source" / f"Nhom{group}_LANLMS_Source"
        report = stage / "Report"
        source.mkdir(parents=True)
        report.mkdir()
        with tarfile.open(fileobj=io.BytesIO(snapshot), mode="r:") as tar:
            for member in tar.getmembers():
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError("Release contains unsupported links/special files")
                relative = Path(member.name)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Unsafe archive path")
                if (
                    relative.name == ".env"
                    or relative.name.startswith(".env.")
                    and relative.name != ".env.example"
                    or relative.suffix in (".db", ".sqlite", ".sqlite3")
                    or any(
                        part in (".git", ".venv", "node_modules", ".next", ".runtime")
                        for part in relative.parts
                    )
                ):
                    raise ValueError(
                        "Private/runtime file was committed; review release before packaging"
                    )
                if relative.parts[0] == "storage" and relative.name not in (
                    "README.md",
                    ".gitkeep",
                ):
                    raise ValueError("Private uploaded storage file was committed")
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as content, path.open("xb") as target:
                    shutil.copyfileobj(content, target)
        for suffix in ("docx", "pdf"):
            original = source / "REPORT" / f"NhomXX_LANLMS_Report.{suffix}"
            if not original.is_file() or original.stat().st_size == 0:
                raise ValueError(
                    "Final DOCX/PDF report is missing from committed source"
                )
            shutil.copyfile(original, report / f"Nhom{group}_LANLMS_Report.{suffix}")
        (stage / "VERSION.txt").write_text(
            f"LAN-LMS\nGit commit: {head}\nPackaged UTC: {datetime.now(timezone.utc).isoformat()}\nGroup: {group}\n",
            encoding="utf-8",
        )
        (report / "TRUOC_KHI_NOP.md").write_text(
            "# Trước khi nộp\n\nĐiền đúng thông tin nhóm và đóng góp thực tế, sửa XX nếu còn, đọc lại báo cáo, kiểm tra Compilatio và lưu kết quả thật. Nghiệm thu trên máy demo và hai máy LAN. Làm theo thông báo nộp cuối của giảng viên/lớp trưởng.\n",
            encoding="utf-8",
        )
        stage.rename(destination)
        with zipfile.ZipFile(
            archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zipped:
            for path in sorted(destination.rglob("*")):
                if path.is_file():
                    zipped.write(path, path.relative_to(output).as_posix())
    return archive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--group", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(package(a.group, a.output))


if __name__ == "__main__":
    main()
