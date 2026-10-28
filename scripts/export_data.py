"""Local administrator export; use the authenticated HTTP endpoint for browser users."""

import argparse
from pathlib import Path
from server.app.core.config import Settings
from server.app.core.database import database
from server.app.models import Courses
from server.app.modules.gradebook.service import rows
from server.app.modules.gradebook.router import safe_text
import csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    engine, sessions = database(Settings().database_url)
    try:
        with sessions() as db:
            if not db.get(Courses, args.course_id):
                raise SystemExit("Course not found")
            data = rows(db, args.course_id)
        with args.output.open("x", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "student_id",
                    "full_name",
                    "class_name",
                    "attendance_score",
                    "homework_score",
                    "midterm_score",
                    "final_score",
                    "total_score",
                ],
            )
            writer.writeheader()
            for row in data:
                writer.writerow(
                    {
                        k: safe_text(v) if isinstance(v, str) else v
                        for k, v in row.items()
                    }
                )
        print("Export completed")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
