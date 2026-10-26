"""Add one complete networking demo course without resetting any existing users/data."""
import argparse
import json
import time
from pathlib import Path
from sqlalchemy import select
from server.app.core.config import Settings, PROJECT_ROOT
from server.app.core.database import database, User
from server.app.models import (Courses, Teachers, Students, CourseTeachers, CourseEnrollments,
                               CalendarEvents, Assignments, CourseMaterials, CodingExams, Problems, TestCases)
from server.app.services import files
from demo.network_exam import problems

COURSE_CODE = "LTM-THUCHANH-2026"


def seed_lab(sessions, storage, teacher_username, student_usernames, now=None):
    now = now or time.time()
    saved = []
    try:
        with sessions.begin() as db:
            teacher = db.scalar(select(Teachers).join(User).where(User.username == teacher_username))
            students = list(db.scalars(select(Students).join(User).where(User.username.in_(student_usernames))))
            if not teacher or len(students) != len(set(student_usernames)):
                raise ValueError("Teacher/student phải tồn tại; script không tạo lại hoặc đổi mật khẩu tài khoản.")
            course = db.scalar(select(Courses).where(Courses.course_code == COURSE_CODE))
            if course:
                ownership = db.scalar(select(CourseTeachers).where(CourseTeachers.course_id == course.id, CourseTeachers.teacher_id == teacher.id))
                if not ownership:
                    raise ValueError("Khóa demo hiện có thuộc giảng viên khác; giữ nguyên dữ liệu.")
                return {"course_id": course.id, "created": False, "message": "Đã có khóa demo; không ghi đè đề, thời gian hoặc bài nộp."}
            course = Courses(course_code=COURSE_CODE, course_name="Lập trình mạng — Phòng thực hành thi trực tuyến",
                description="Khóa thực hành có lịch học, tài liệu, bài tập và 2 đề thi mạng. Nộp code qua HTTP, lưu hàng đợi bền vững, chấm Docker thật và nhận trạng thái qua WebSocket. Dữ liệu mẫu, không phải kết quả chấm giả.",
                semester="1", academic_year="2026-2027", status="active", grades_published=False,
                final_grade_policy="single_final_exam")
            db.add(course); db.flush()
            db.add(CourseTeachers(course_id=course.id, teacher_id=teacher.id, role="primary"))
            for student in students:
                db.add(CourseEnrollments(course_id=course.id, student_id=student.id, status="active"))
            db.add(CalendarEvents(course_id=course.id, created_by=teacher.user_id, title="Thực hành HTTP, WebSocket và chấm bài qua mạng",
                description="Chọn buổi học để tạo QR điểm danh. Sau đó vào Thi lập trình để nộp thử các bài mạng.",
                event_type="lesson", starts_at=now-900, ends_at=now+3600))
            db.add(Assignments(course_id=course.id, created_by=teacher.id, title="Phân tích gói tin HTTP và WebSocket",
                description="Mở công cụ Network của trình duyệt. Chụp request nộp code (HTTP 202), response submission_id và thông điệp submission.updated trên WebSocket. Giải thích idempotency, heartbeat và cách khôi phục khi mất kết nối. Nộp báo cáo PDF.",
                due_at=now+2*86400, allow_resubmit=True))
            path = files.save(storage, "course_materials", (
                "LAN-LMS: HTTP -> API -> SQLite queue -> Docker worker -> result -> WebSocket.\n"
                "1. Chọn khóa học, điểm danh QR tại buổi học.\n"
                "2. Vào Thi lập trình, chọn đề, bắt đầu phiên, chọn bài và C/C++/Java.\n"
                "3. Nộp source; theo dõi Pending/Compiling/Running và AC/WA/CE/RTE/TLE/MLE/SE.\n"
                "4. Chỉ bài AC được tính là đã giải; 0/1/2/3/4/5 bài -> 0/5/7/8/9/10 điểm.\n"
                "5. Trong DevTools, xem REST /submissions và frame WebSocket /ws.\n"
                "6. Khi worker offline, bài được lưu trong queue, không giả lập AC.\n"
                "Hai kỳ thi demo mở trong 7 ngày từ lúc seed; giảng viên tự tạo lịch phù hợp cho kỳ thi thật.\n"
            ).encode("utf-8"))
            saved.append(path)
            db.add(CourseMaterials(course_id=course.id, uploaded_by=teacher.user_id, title="Hướng dẫn thực hành giao thức thi trực tuyến",
                                   original_filename="huong-dan-thi-mang.txt", storage_path=path,
                                   size_bytes=files.resolve(storage,path).stat().st_size, uploaded_at=now))
            exams = []
            for component, specs in problems().items():
                exam = CodingExams(course_id=course.id, created_by=teacher.id,
                    title=("Giữa kỳ — Nền tảng giao thức mạng" if component=="midterm" else "Cuối kỳ — Xử lý dữ liệu và thuật toán mạng"),
                    grade_component=component, starts_at=now-60, ends_at=now+7*86400,
                    status="scheduled", results_published=False, score_ladder_json="[0,5,7,8,9,10]")
                db.add(exam); db.flush()
                for spec in specs:
                    problem = Problems(exam_id=exam.id, title=f"{spec.code}. {spec.title}", statement=spec.statement,
                        languages_json='["c","cpp","java"]', io_mode="stdio", max_score=100,
                        time_limit_ms=2000, memory_limit_mib=512, comparator="normalized")
                    db.add(problem); db.flush()
                    for index, (input_text, output_text) in enumerate(spec.cases):
                        inp = files.save(storage,"test_cases",input_text.encode("utf-8")); saved.append(inp)
                        out = files.save(storage,"test_cases",output_text.encode("utf-8")); saved.append(out)
                        db.add(TestCases(problem_id=problem.id, input_path=inp, expected_output_path=out,
                                         weight=100/len(spec.cases), sort_order=index+1, is_sample=index==0))
                exams.append({"id":exam.id,"component":component,"problems":len(specs)})
            return {"created":True,"course_id":course.id,"exams":exams,"test_cases":sum(len(p.cases) for group in problems().values() for p in group)}
    except BaseException:
        for path in saved:
            files.resolve(storage,path).unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher", default="review_teacher")
    parser.add_argument("--student", action="append", default=None)
    parser.add_argument("--database-url")
    parser.add_argument("--storage-root", type=Path)
    args = parser.parse_args()
    from scripts.launch_web import make_environment
    env = make_environment(PROJECT_ROOT)
    database_url = args.database_url or env.get("DATABASE_URL") or Settings().database_url
    storage = args.storage_root or Path(env.get("STORAGE_ROOT", str(PROJECT_ROOT/"storage")))
    engine,sessions = database(database_url)
    try:
        print(json.dumps(seed_lab(sessions,storage,args.teacher,args.student or ["review001"]),ensure_ascii=False,indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
