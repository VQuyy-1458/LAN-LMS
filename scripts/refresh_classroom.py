"""Update the authored classrooms' presentation, timetable and explicitly requested credentials."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import time
from sqlalchemy import select,delete
from server.app.core.config import PROJECT_ROOT, Settings
from server.app.core.database import database, User, AuthSession
from server.app.core.security import hasher
from server.app.models import (Courses, CourseTeachers, Teachers, CourseEnrollments, Students, Classes,
    CourseMaterials, CalendarEvents, Assignments, AssignmentSubmissions, AttendanceSessions, CodingExams, AuditLogs)
from server.app.services import files,idempotency
from demo.classroom_content import COURSES
from demo.classroom_updates import enrich,submission_text
from scripts.seed_classroom import TZ


def refresh(sessions,storage,output,rename_students=False,now=None):
    now=time.time() if now is None else now
    storage=Path(storage);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    old_codes=["DEMO-LTM-2026","DEMO-CTDL-2026"]
    changed=[];saved=[];committed=False;accounts=[]
    credential_path=output/"accounts.csv"
    if credential_path.exists():
        with credential_path.open(encoding="utf-8-sig",newline="") as stream: accounts=list(csv.DictReader(stream))
    try:
        with sessions() as db:
            idempotency.write_lock(db)
            for course_index,content in enumerate(COURSES):
                course=db.scalar(select(Courses).where(Courses.course_code.in_([old_codes[course_index],content["code"]])))
                if not course: continue
                # Only update courses created by the classroom seed utility.
                if not db.scalar(select(AuditLogs.id).where(AuditLogs.action=="seed-demo-classroom",AuditLogs.entity_type=="course",AuditLogs.entity_id==course.id)):
                    raise ValueError("Course code belongs to unrelated data; no changes applied")
                teacher=db.scalar(select(Teachers).join(CourseTeachers).where(CourseTeachers.course_id==course.id))
                course.course_code=content["code"];course.course_name=content["name"];course.description=content["summary"]
                if teacher.full_name=="Giảng viên mẫu": teacher.full_name="Giảng viên phụ trách"
                students=list(db.scalars(select(Students).join(CourseEnrollments).where(CourseEnrollments.course_id==course.id).order_by(Students.id)))
                for student in students:
                    match=re.fullmatch(r"DEMO-(?:NET|ALG)-(\d{3})",student.student_code)
                    if not rename_students or not match: continue
                    index=int(match.group(1))-1;number=course_index*20+index
                    new_code=f"B26DCCN{number+1:03d}"
                    user=db.get(User,student.user_id)
                    if db.scalar(select(User.id).where(User.username==new_code,User.id!=user.id)) or db.scalar(select(Students.id).where(Students.student_code==new_code,Students.id!=student.id)):
                        raise ValueError("New student ID is already in use; no accounts reset")
                    old_code=student.student_code
                    birthday=f"{number%28+1:02d}{(number*5)%12+1:02d}{2006-number%2}"
                    user.username=new_code;user.password_hash=hasher.hash(birthday);user.must_change_password=True
                    student.student_code=new_code;student.date_of_birth=birthday
                    student.email=None
                    cls=db.get(Classes,student.class_id)
                    cls.class_code=f"D26CQCN{course_index*2+index//10+1:02d}-B";cls.class_name="Lớp thực hành "+cls.class_code
                    db.execute(delete(AuthSession).where(AuthSession.user_id==user.id))
                    row=next((row for row in accounts if row["student_id"]==old_code),None)
                    if row is None: row={};accounts.append(row)
                    row.update(course_code=content["code"],student_id=new_code,full_name=student.full_name,class_name=cls.class_code,
                        date_of_birth=birthday,temporary_password=birthday,must_change_password="yes")
                def save(directory,data):
                    path=files.save(storage,directory,data);saved.append(path);return path
                for material in db.scalars(select(CourseMaterials).where(CourseMaterials.course_id==course.id)):
                    if material.original_filename.endswith("-handbook.pdf"):
                        data=(PROJECT_ROOT/"demo/materials"/(content["key"]+"-handbook.pdf")).read_bytes()
                        material.storage_path=save("course_materials",data);material.size_bytes=len(data)
                    elif material.original_filename=="de-cuong.txt":
                        data=(content["name"]+"\n\n"+"\n".join(f"{i+1}. {title}" for i,title in enumerate(content["lessons"]))+"\n\nChuyên cần 10%, bài tập 10%, giữa kỳ 10%, cuối kỳ 70%.\n").encode("utf-8")
                        material.storage_path=save("course_materials",data);material.size_bytes=len(data)
                lessons=list(db.scalars(select(CalendarEvents).where(CalendarEvents.course_id==course.id,CalendarEvents.event_type=="lesson").order_by(CalendarEvents.starts_at)))
                base_lessons=[lesson for lesson in lessons if lesson.title.startswith("Buổi ")]
                anchor=datetime.fromtimestamp(base_lessons[2].starts_at,TZ) if len(base_lessons)>2 else datetime.fromtimestamp(now,TZ).replace(hour=18,minute=30,second=0,microsecond=0)
                for lesson in base_lessons:
                    lesson.description="Chuẩn bị nội dung chuyên đề trước giờ học. Thực hành tại phòng máy và quét mã QR do giảng viên cung cấp để điểm danh."
                past_sessions=list(db.scalars(select(AttendanceSessions).where(AttendanceSessions.course_id==course.id).order_by(AttendanceSessions.starts_at)))
                for index,session in enumerate(past_sessions):
                    if session.title.startswith("[Mẫu]"):
                        session.title=base_lessons[index].title if index<len(base_lessons) else session.title.replace("[Mẫu] ","")
                        if index<len(base_lessons) and not db.scalar(select(AttendanceSessions.id).where(AttendanceSessions.event_id==base_lessons[index].id)):
                            session.event_id=base_lessons[index].id
                for assignment in db.scalars(select(Assignments).where(Assignments.course_id==course.id)):
                    for submission in db.scalars(select(AssignmentSubmissions).where(AssignmentSubmissions.assignment_id==assignment.id)):
                        old=files.resolve(storage,submission.storage_path).read_bytes()
                        if b'B\xc3\x80I N\xe1\xbb\x98P GI\xe1\xba\xa2 L\xe1\xba\xacP' in old:
                            student=db.get(Students,submission.student_id)
                            data=submission_text(content["key"],student.student_code,student.full_name,assignment.title).encode("utf-8")
                            submission.storage_path=save("submissions",data);submission.size_bytes=len(data)
                            submission.original_filename=student.student_code+"-baocao.txt"
                        if submission.feedback and submission.feedback.startswith("[Nhận xét mẫu]"):
                            submission.feedback="Đã trình bày thiết kế và kiểm thử; cần bổ sung minh chứng chạy chương trình."
                    if assignment.attachment_path:
                        data=files.resolve(storage,assignment.attachment_path).read_bytes()
                        cleaned=data.decode("utf-8",errors="replace").replace("ĐỀ BÀI TẬP TỰ SOẠN - ","BÀI TẬP HỌC PHẦN - ")
                        if cleaned.encode("utf-8")!=data: assignment.attachment_path=save("assignment_handouts",cleaned.encode("utf-8"))
                enrich(db,course,teacher,content,anchor,now,save)
                changed.append(course.id)
                db.add(AuditLogs(user_id=teacher.user_id,action="refresh-classroom-presentation",entity_type="course",entity_id=course.id,
                    details_json=json.dumps({"fictional_data_retained_in_documentation":True,"rename_students":rename_students}),created_at=now))
            # Retire demonstration wording in older authored descriptions, keeping their resources/IDs.
            for course in db.scalars(select(Courses)):
                if course.course_code=="DEMO-LTM":course.course_code="LTM-CB-2026"
                course.description=course.description.replace("Dữ liệu mẫu, không phải kết quả chấm giả.","").strip()
            for exam in db.scalars(select(CodingExams).where(CodingExams.title.like("%mẫu%"))):exam.title=exam.title.replace(" mẫu","")
            temporary=output/"accounts.updated.csv"
            if accounts:
                for row in accounts:
                    for old,new in zip(old_codes,[course["code"] for course in COURSES]):
                        if row.get("course_code")==old:row["course_code"]=new
                with temporary.open("w",encoding="utf-8-sig",newline="") as stream:
                    writer=csv.DictWriter(stream,fieldnames=["course_code","student_id","full_name","class_name","date_of_birth","temporary_password","must_change_password"])
                    writer.writeheader();writer.writerows(accounts)
            db.commit();committed=True
        if accounts:
            if credential_path.exists() and not (output/"accounts-before-update.csv").exists():shutil.copy2(credential_path,output/"accounts-before-update.csv")
            temporary.replace(credential_path)
        return {"course_ids":changed,"accounts_updated":len(accounts) if rename_students else 0}
    except BaseException:
        if not committed:
            for path in saved:(storage/path).unlink(missing_ok=True)
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--rename-students",action="store_true")
    parser.add_argument("--output",type=Path,default=PROJECT_ROOT/".runtime/classroom-20261027")
    args=parser.parse_args()
    from scripts.launch_web import make_environment
    env=make_environment(PROJECT_ROOT);engine,sessions=database(env.get("DATABASE_URL") or Settings().database_url)
    try:print(json.dumps(refresh(sessions,Path(env.get("STORAGE_ROOT",str(PROJECT_ROOT/"storage"))),args.output,args.rename_students),ensure_ascii=False))
    finally:engine.dispose()
