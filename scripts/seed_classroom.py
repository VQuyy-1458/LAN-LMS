"""Add two complete, clearly fictional classroom datasets without changing existing data."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import secrets
import time
import zipfile
from sqlalchemy import select
from server.app.core.config import PROJECT_ROOT, Settings
from server.app.core.database import User, database
from server.app.core.security import hasher
from server.app.models import (Assignments, AssignmentSubmissions, AttendanceRecords, AttendanceSessions,
    AuditLogs, CalendarEvents, Classes, CodingExams, CourseClasses, CourseEnrollments, CourseMaterials,
    Courses, CourseTeachers, GradeComponents, Problems, Students, Teachers, TestCases)
from server.app.services import files, idempotency
from demo.classroom_content import COURSES
from demo.classroom_problems import bank, exam_groups

TZ = timezone(timedelta(hours=7))
SURNAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng"]
GIVEN_NAMES = ["Minh Anh", "Tuấn Anh", "Bảo Châu", "Ngọc Diệp", "Gia Huy", "Khánh Linh", "Quang Minh", "Phương Nam"]


def starter_zip(course):
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", "Tài liệu thực hành tự soạn - LAN-LMS\n"+course["name"]+"\n"
            "C: gcc -std=c17 Main.c -o main\nC++: g++ -std=c++17 Main.cpp -o main\nJava: javac Main.java && java Main\n"
            "Đọc đề, kiểm tra giới hạn, tự viết lời giải. Không in lời nhắc input. Java không khai báo package.\n"
            "Nếu đề yêu cầu file, dùng đúng tên file phân biệt hoa/thường.\n")
        z.writestr("c/Main.c", "#include <stdio.h>\nint main(void) { /* TODO: doc input, xu ly, in output */ return 0; }\n")
        z.writestr("cpp/Main.cpp", "#include <iostream>\nusing namespace std;\nint main() { /* TODO */ return 0; }\n")
        z.writestr("java/Main.java", "import java.util.*;\npublic class Main { public static void main(String[] args) { /* TODO */ } }\n")
        z.writestr("checklist.txt", "[ ] Đọc input/output\n[ ] Chọn kiểu số phù hợp\n[ ] Test biên và ví dụ\n[ ] Kiểm tra ngôn ngữ trước khi nộp\n[ ] Chờ verdict\n[ ] Gửi hết bài cần chấm trước khi kết thúc phiên\n")
    return output.getvalue()


def export_question_bank(output, questions):
    path=Path(output)/"teacher-question-bank.zip"
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", "TÀI LIỆU CHO GIẢNG VIÊN - có lời giải và testcase ẩn. Không đăng vào Tài liệu khóa học.\n"
            "Mỗi bài có statement.txt, reference.cpp và tests.zip. Nhập tests.zip ở bài chưa có testcase.\n"
            "Các file sample_01.in/out là ví dụ công khai; các file khác là test ẩn.\n")
        for group, specs in questions.items():
            for spec in specs:
                prefix=f"{group}/{spec.code}"
                archive.writestr(prefix+"/statement.txt",spec.title+"\n\n"+spec.statement)
                archive.writestr(prefix+"/reference.cpp",spec.solution)
                packed=io.BytesIO()
                with zipfile.ZipFile(packed,"w",zipfile.ZIP_DEFLATED) as test_zip:
                    for index,(inp,out) in enumerate(spec.cases):
                        name="sample_01" if index==0 else f"{index+1:02d}"
                        test_zip.writestr(name+".in",inp);test_zip.writestr(name+".out",out)
                archive.writestr(prefix+"/tests.zip",packed.getvalue())
    return path


def seed(sessions, storage, teacher_username, output, now=None):
    now=time.time() if now is None else now
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    storage=Path(storage)
    questions=bank()
    pdfs={course["key"]:PROJECT_ROOT/"demo/materials"/(course["key"]+"-handbook.pdf") for course in COURSES}
    if any(not p.is_file() for p in pdfs.values()): raise ValueError("Missing authored PDF handbooks; keep demo/materials with the source")
    saved=[];credentials=[];result=[];temporary=output/"accounts.pending.csv"
    committed=False
    try:
        with sessions() as db:
            idempotency.write_lock(db)
            teacher=db.scalar(select(Teachers).join(User).where(User.username==teacher_username))
            if not teacher: raise ValueError("Teacher account must exist; no teacher password is changed")
            for course_index, content in enumerate(COURSES):
                old=db.scalar(select(Courses).where(Courses.course_code==content["code"]))
                if old:
                    if not db.scalar(select(CourseTeachers.id).where(CourseTeachers.course_id==old.id,CourseTeachers.teacher_id==teacher.id)):
                        raise ValueError("Existing sample course belongs to another teacher")
                    result.append({"id":old.id,"code":content["code"],"created":False});continue
                course=Courses(course_code=content["code"],course_name=content["name"],description=content["summary"],
                    semester="1",academic_year="2026-2027",status="active",grades_published=False,final_grade_policy="single_final_exam")
                db.add(course);db.flush()
                db.add(CourseTeachers(course_id=course.id,teacher_id=teacher.id,role="primary"))
                classes=[]
                for group in range(2):
                    code=f"DEMO-{'NET' if course_index==0 else 'ALG'}-{group+1:02d}"
                    if db.scalar(select(Classes.id).where(Classes.class_code==code)): raise ValueError("Sample class code already exists; existing data preserved")
                    cls=Classes(class_code=code,class_name=f"Lớp thực hành mẫu {code}",academic_year="2026-2027")
                    db.add(cls);db.flush();classes.append(cls)
                    db.add(CourseClasses(course_id=course.id,class_id=cls.id))
                students=[]
                for index in range(20):
                    number=course_index*20+index
                    username=f"DEMO-{'NET' if course_index==0 else 'ALG'}-{index+1:03d}"
                    if db.scalar(select(User.id).where(User.username==username)) or db.scalar(select(Students.id).where(Students.student_code==username)):
                        raise ValueError("Sample student code exists outside these courses; no password/profile overwritten")
                    password=secrets.token_urlsafe(9)
                    user=User(username=username,password_hash=hasher.hash(password),role="student",must_change_password=True,active=True)
                    db.add(user);db.flush()
                    name=SURNAMES[number//len(GIVEN_NAMES)]+" "+GIVEN_NAMES[number%len(GIVEN_NAMES)]
                    student=Students(user_id=user.id,student_code=username,full_name=name,class_id=classes[index//10].id,
                        date_of_birth="06062006",email=username.lower()+"@example.invalid")
                    db.add(student);db.flush();students.append(student)
                    db.add(CourseEnrollments(course_id=course.id,student_id=student.id,status="active"))
                    credentials.append({"course_code":content["code"],"student_id":username,"full_name":name,
                        "class_name":classes[index//10].class_code,"temporary_password":password,"must_change_password":"yes"})
                def save(directory,data):
                    path=files.save(storage,directory,data);saved.append(path);return path
                for title,filename,data in [("Sổ tay học phần - 6 chuyên đề",content["key"]+"-handbook.pdf",pdfs[content["key"]].read_bytes()),
                    ("Khung source C/C++/Java và checklist","starter-code.zip",starter_zip(content)),
                    ("Đề cương và cách đánh giá","de-cuong.txt",("DỮ LIỆU MẪU - "+content["name"]+"\n\n"+"\n".join(f"{i+1}. {title}" for i,title in enumerate(content["lessons"]))+
                        "\n\nChuyên cần 10%, bài tập 10%, trung bình giữa kỳ 10%, cuối kỳ 70%.\nTest luyện tập không tính tổng kết.\n").encode("utf-8"))]:
                    db.add(CourseMaterials(course_id=course.id,uploaded_by=teacher.user_id,title=title,
                        original_filename=filename,storage_path=save("course_materials",data),size_bytes=len(data),uploaded_at=now))
                anchor=datetime.fromtimestamp(now,TZ).replace(hour=18,minute=30,second=0,microsecond=0)+timedelta(days=course_index)
                for index,title in enumerate(content["lessons"]):
                    start=(anchor+timedelta(days=(index-2)*7)).timestamp()
                    db.add(CalendarEvents(course_id=course.id,created_by=teacher.user_id,title=f"Buổi {index+1}: {title}",
                        description="Lịch thực hành mẫu. Mang laptop, đọc chuyên đề tương ứng, điểm danh QR khi giảng viên mở phiên.",
                        event_type="lesson",starts_at=start,ends_at=start+2*3600))
                db.add(CalendarEvents(course_id=course.id,created_by=teacher.user_id,title="Thông báo: Quy định nộp bài và giữ tab thi",
                    description="Đọc kỹ input/output; source chỉ được tính khi đã gửi chấm. Khi thi bật toàn màn hình; rời tab được ghi nhật ký. Nộp sớm sẽ khóa gửi thêm bài.",
                    event_type="announcement",starts_at=now,ends_at=now+86400))
                for session_index in range(2):
                    attendance=AttendanceSessions(course_id=course.id,created_by=teacher.id,title=f"[Mẫu] Điểm danh buổi {session_index+1}",
                        token_hash=secrets.token_hex(32),starts_at=now-(14-session_index*7)*86400,
                        expires_at=now-(14-session_index*7)*86400+900,status="closed")
                    db.add(attendance);db.flush()
                    for index,student in enumerate(students):
                        status="absent" if (index+session_index)%10==0 else "late" if index%9==0 else "present"
                        db.add(AttendanceRecords(session_id=attendance.id,student_id=student.id,status=status,
                            checked_in_at=attendance.starts_at+(600 if status=="late" else 120)))
                for assignment_index,(title,description,days) in enumerate(content["assignments"]):
                    handout=("ĐỀ BÀI TẬP TỰ SOẠN - "+content["name"]+"\n\n"+title+"\n\n"+description+
                        "\n\nYÊU CẦU NỘP\n1. Ghi mã SV, tên và lớp trong README.\n2. Nộp file hoặc ZIP tối đa 20 MiB.\n3. Kèm cách chạy và testcase tự thiết kế.\n"
                        "RUBRIC 10 ĐIỂM\nĐúng yêu cầu 4; giải thích thiết kế 2; test biên 2; hướng dẫn tái lập 2.\n").encode("utf-8")
                    assignment=Assignments(course_id=course.id,created_by=teacher.id,title=title,description=description,due_at=now+days*86400,allow_resubmit=True,
                        attachment_path=save("assignment_handouts",handout),attachment_filename=f"de-bt{assignment_index+1:02d}.txt")
                    db.add(assignment);db.flush()
                    for index,student in enumerate(students[:15 if assignment_index==0 else 4 if assignment_index==1 else 0]):
                        text=("BÀI NỘP GIẢ LẬP - không phải bài làm/điểm thật của sinh viên\n"+student.student_code+" - "+student.full_name+
                            "\n"+title+"\n\nThiết kế: chia xử lý input, logic và output; kiểm tra dữ liệu biên.\n"
                            "Test đã mô phỏng: input tối thiểu, dữ liệu trùng, giá trị lớn, dữ liệu không hợp lệ.\n"
                            "Đây là dữ liệu để thử luồng tải bài, chấm điểm và nhập/xuất khóa học.\n").encode("utf-8")
                        db.add(AssignmentSubmissions(assignment_id=assignment.id,student_id=student.id,attempt_no=1,
                            original_filename=student.student_code+"-baocao.txt",size_bytes=len(text),storage_path=save("submissions",text),
                            received_at=assignment.due_at-3600 if assignment_index==0 else now-600,
                            score=round(7+(index%6)*0.5,1) if assignment_index==0 and index<12 else None,
                            feedback="[Nhận xét mẫu] Đã có thiết kế và test; bổ sung bằng chứng chạy thực tế." if assignment_index==0 and index<12 else None))
                exams=[]
                for exam_index,(component,title,specs) in enumerate(exam_groups(questions[content["key"]])):
                    start=now-300 if component=="practice" else now+(exam_index*3)*86400
                    end=now+30*86400 if component=="practice" else start+90*60
                    ladder=[0,5,7,8,9,10] if len(specs)==5 else [round(10*i/len(specs),2) for i in range(len(specs)+1)]
                    exam=CodingExams(course_id=course.id,created_by=teacher.id,title=title,grade_component=component,
                        starts_at=start,ends_at=end,status="scheduled",results_published=False,score_ladder_json=json.dumps(ladder))
                    db.add(exam);db.flush()
                    for spec in specs:
                        problem=Problems(exam_id=exam.id,title=spec.code+". "+spec.title,statement=spec.statement,languages_json='["c","cpp","java"]',
                            io_mode=spec.io_mode,input_filename=spec.input_filename,output_filename=spec.output_filename,
                            max_score=100,time_limit_ms=2000,memory_limit_mib=512,comparator="normalized")
                        db.add(problem);db.flush()
                        for index,(inp,out) in enumerate(spec.cases):
                            db.add(TestCases(problem_id=problem.id,input_path=save("test_cases",inp.encode("utf-8")),expected_output_path=save("test_cases",out.encode("utf-8")),
                                weight=100/len(spec.cases),sort_order=index+1,is_sample=index==0))
                    exams.append({"id":exam.id,"component":component,"questions":len(specs)})
                    db.add(CalendarEvents(course_id=course.id,created_by=teacher.user_id,title="Thi: "+title,
                        description="Vào Thi lập trình để xem đề và bắt đầu phiên khi đến giờ.",event_type="exam",starts_at=start,ends_at=end))
                for code,weight in [("attendance",10),("homework",10),("midterm",10),("final",70)]:
                    db.add(GradeComponents(course_id=course.id,component_code=code,weight=weight,max_score=10))
                db.add(AuditLogs(user_id=teacher.user_id,action="seed-demo-classroom",entity_type="course",entity_id=course.id,
                    details_json=json.dumps({"fictional":True,"students":20,"attendance_and_homework_are_sample_data":True}),created_at=now))
                result.append({"id":course.id,"code":content["code"],"created":True,"students":20,"exams":exams})
            if credentials:
                previous=[]
                destination=output/"accounts.csv"
                if destination.exists():
                    with destination.open(encoding="utf-8-sig",newline="") as stream: previous=list(csv.DictReader(stream))
                with temporary.open("w",encoding="utf-8-sig",newline="") as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(credentials[0]));writer.writeheader();writer.writerows(previous+credentials)
            db.commit()
            committed=True
        if credentials: temporary.replace(output/"accounts.csv")
        export_question_bank(output,questions)
        summary={"fictional_data":True,"courses":result,"new_students":len(credentials),"credentials_file":str(output/"accounts.csv")}
        (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
        return summary
    except BaseException:
        # Roll back only files created before a failed DB transaction; never reset old data.
        # Once committed, retain source/files even if a local export cannot be renamed.
        if not committed:
            temporary.unlink(missing_ok=True)
            for path in saved: (storage/path).unlink(missing_ok=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher",default="review_teacher")
    parser.add_argument("--output",type=Path,default=PROJECT_ROOT/".runtime/classroom-20261027")
    parser.add_argument("--database-url")
    parser.add_argument("--storage-root",type=Path)
    args=parser.parse_args()
    from scripts.launch_web import make_environment
    env=make_environment(PROJECT_ROOT)
    engine,sessions=database(args.database_url or env.get("DATABASE_URL") or Settings().database_url)
    try:
        result=seed(sessions,args.storage_root or Path(env.get("STORAGE_ROOT",str(PROJECT_ROOT/"storage"))),args.teacher,args.output)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally: engine.dispose()


if __name__=="__main__": main()
