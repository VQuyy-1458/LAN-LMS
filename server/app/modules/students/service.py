import csv
import io
from datetime import datetime
from sqlalchemy import select
from ...models import Students, Classes
from ...core.database import User


def inspect_rows(db, content):
    errors = []
    rows = []
    seen = set()
    new = 0
    existing = 0
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
        if not {"student_id", "full_name", "date_of_birth", "class_name"} <= set(
            reader.fieldnames or []
        ):
            return (
                [],
                [
                    dict(
                        row=1,
                        field="header",
                        code="INVALID_CSV",
                        message="Thiếu cột bắt buộc",
                    )
                ],
                0,
                0,
            )
        for number, row in enumerate(reader, 2):
            if number > 2001:
                errors.append(
                    dict(
                        row=number,
                        field="file",
                        code="TOO_MANY_ROWS",
                        message="Tối đa 2000 sinh viên",
                    )
                )
                break
            clean = {
                k: (row.get(k) or "").strip()
                for k in [
                    "student_id",
                    "full_name",
                    "date_of_birth",
                    "class_name",
                    "email",
                ]
            }
            problem = None
            if None in row or any(
                not clean[k]
                for k in ["student_id", "full_name", "date_of_birth", "class_name"]
            ):
                problem = "Thiếu hoặc thừa dữ liệu"
            elif (
                any(len(clean[k]) > 128 for k in ["student_id", "class_name"])
                or len(clean["full_name"]) > 200
                or len(clean["email"]) > 254
            ):
                problem = "Dữ liệu quá dài"
            elif clean["student_id"] in seen:
                problem = "Mã sinh viên trùng trong file"
            else:
                try:
                    if (
                        len(clean["date_of_birth"]) != 8
                        or not clean["date_of_birth"].isdigit()
                    ):
                        raise ValueError()
                    datetime.strptime(clean["date_of_birth"], "%d%m%Y")
                except ValueError:
                    problem = "Ngày sinh không hợp lệ"
            seen.add(clean["student_id"])
            student = db.scalar(
                select(Students).where(Students.student_code == clean["student_id"])
            )
            account = db.scalar(
                select(User).where(User.username == clean["student_id"])
            )
            if not problem and student:
                cls = db.get(Classes, student.class_id) if student.class_id else None
                if (
                    student.full_name != clean["full_name"]
                    or student.date_of_birth != clean["date_of_birth"]
                    or not cls
                    or cls.class_code != clean["class_name"]
                    or (student.email or "") != clean["email"]
                ):
                    problem = "Hồ sơ hiện tại khác CSV; cần giảng viên kiểm tra"
                elif not account or account.id != student.user_id:
                    problem = "Mã tài khoản và hồ sơ không khớp"
            elif not problem and account:
                problem = "Tài khoản đã tồn tại nhưng chưa khớp hồ sơ sinh viên"
            if problem:
                errors.append(
                    dict(
                        row=number, field="row", code="INVALID_CSV_ROW", message=problem
                    )
                )
            else:
                rows.append(clean)
                if account:
                    existing += 1
                else:
                    new += 1
        if not rows and not errors:
            errors.append(
                dict(
                    row=1,
                    field="file",
                    code="EMPTY_CSV",
                    message="File không có sinh viên",
                )
            )
    except (UnicodeError, csv.Error):
        errors.append(
            dict(
                row=1,
                field="file",
                code="INVALID_CSV",
                message="CSV phải là UTF-8 hợp lệ",
            )
        )
    return rows, errors, new, existing
