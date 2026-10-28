from sqlalchemy import select
from ...models import Problems, Students, JudgeResults
from ...services import files
from ...services.activity import iso
from ..coding_exams import service as exams


def payload(db, row, root=None, detail=False):
    p = db.get(Problems, row.problem_id)
    s = db.get(Students, row.student_id)
    r = db.scalar(select(JudgeResults).where(JudgeResults.submission_id == row.id))
    result = dict(
        id=row.id,
        problem_id=row.problem_id,
        exam_session_id=row.exam_session_id,
        student_id=s.student_code,
        language=row.language,
        received_at=iso(row.received_at),
        status=row.status,
        verdict_code=exams.CODES[row.status],
        score=row.score,
        max_score=p.max_score,
        compile_message=r.compile_message if r else "",
        reason_code=r.reason_code if r else None,
        version=row.version,
    )
    if detail:
        result["source_code"] = files.resolve(root, row.source_path).read_text(
            encoding="utf-8"
        )
    return result
