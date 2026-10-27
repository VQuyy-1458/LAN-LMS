"""Build a new classroom bundle separately; never erase the running database."""
import argparse,csv,json,secrets,subprocess,sys,time
from datetime import datetime,timedelta
from pathlib import Path
from sqlalchemy import select,delete
from server.app.core.config import PROJECT_ROOT as ROOT
from server.app.core.database import database,User
from server.app.core.security import hasher,Principal
from server.app.models import *
from server.app.services import files
from scripts.seed_classroom import seed,TZ

NAMES=["Nguyễn Hoàng Anh","Trần Đức Bảo","Lê Minh Châu","Phạm Khánh Chi","Hoàng Tiến Dũng","Vũ Thùy Dương","Đặng Quang Huy","Bùi Ngọc Hà","Đỗ Minh Hiếu","Ngô Thu Hương","Dương Gia Khánh","Phan Bảo Linh","Nguyễn Đức Long","Trần Hải Nam","Lê Bảo Ngọc","Phạm Minh Phúc","Vũ Anh Quân","Đặng Phương Thảo","Bùi Minh Tuấn","Đỗ Hải Yến","Nguyễn Minh Bảo","Trần Ngọc Bích","Lê Đức Cường","Phạm Thùy Dung","Hoàng Minh Đức","Vũ Hương Giang","Đặng Trung Hiếu","Bùi Khánh Hòa","Đỗ Quang Hưng","Ngô Gia Hân","Dương Tuấn Kiệt","Phan Thảo Linh","Nguyễn Hoài Nam","Trần Hà My","Lê Quang Phúc","Phạm Anh Quân","Vũ Đức Sơn","Đặng Hoài Thương","Bùi Anh Tú","Đỗ Minh Trang"]
TASKS=[
 ["Truyền file qua TCP","Thông báo trong mạng UDP","Máy chủ xử lý nhiều kết nối","Gửi lại yêu cầu an toàn","Theo dõi sự kiện WebSocket","Tích hợp và triển khai trong LAN"],
 ["Danh sách liên kết","Hàng đợi tác vụ","Bảng băm và tra cứu","Cây tìm kiếm","Sắp xếp topo","Quy hoạch động"]]

def normalize_times(sessions):
    with sessions.begin() as db:
        for assignment in db.scalars(select(Assignments)):
            assignment.due_at=datetime.fromtimestamp(assignment.due_at,TZ).replace(hour=23,minute=59,second=0,microsecond=0).timestamp()
        for exam in db.scalars(select(CodingExams)):
            exam.starts_at=datetime.fromtimestamp(exam.starts_at,TZ).replace(hour=0 if exam.grade_component=="practice" else 8,minute=0,second=0,microsecond=0).timestamp()
            if exam.grade_component=="practice":exam.ends_at=datetime.fromtimestamp(exam.ends_at,TZ).replace(hour=23,minute=59,second=0,microsecond=0).timestamp()
            else:exam.ends_at=exam.starts_at+(7200 if exam.grade_component=="final" else 5400)
        for session in db.scalars(select(AttendanceSessions)):
            event=db.get(CalendarEvents,session.event_id) if session.event_id else None
            if event:
                session.starts_at=event.starts_at;session.expires_at=event.starts_at+900
                for record in db.scalars(select(AttendanceRecords).where(AttendanceRecords.session_id==session.id)):
                    record.checked_in_at=event.starts_at+({'late':600,'absent':900}.get(record.status,120))
        for event in db.scalars(select(CalendarEvents).where(CalendarEvents.event_type=="announcement")):
            event.starts_at=datetime.fromtimestamp(event.starts_at,TZ).replace(hour=8,minute=0,second=0,microsecond=0).timestamp()
            event.ends_at=event.starts_at+86400

def build(output,now=None):
    output=Path(output).resolve()
    if output.exists():raise FileExistsError("Chọn thư mục mới để không ghi đè dữ liệu")
    output.mkdir(parents=True);storage=output/"storage";storage.mkdir()
    now=time.time() if now is None else now
    db_url="sqlite:///"+(output/"database.db").as_posix()
    import os
    env=dict(os.environ,DATABASE_URL=db_url,PYTHONUTF8="1",DISABLE_SQLALCHEMY_CEXT_RUNTIME="1")
    subprocess.run([sys.executable,"-m","alembic","-c","server/alembic.ini","upgrade","head"],cwd=ROOT,env=env,check=True)
    engine,sessions=database(db_url);password=secrets.token_urlsafe(12)
    try:
        with sessions.begin() as db:
            user=User(username="GV001",password_hash=hasher.hash(password),role="teacher",must_change_password=False,active=True)
            db.add(user);db.flush();db.add(Teachers(user_id=user.id,teacher_code="GV001",full_name="Nguyễn Thanh Nam"))
        summary=seed(sessions,storage,"GV001",output,now=now)
        credentials=[]
        with sessions.begin() as db:
            teacher=db.scalar(select(Teachers));user=db.get(User,teacher.user_id)
            for index,student in enumerate(db.scalars(select(Students).order_by(Students.id))):
                old_code,old_name=student.student_code,student.full_name
                code=f"B24DCCN{index+101:03d}";student.student_code=code;student.full_name=NAMES[index]
                account=db.get(User,student.user_id);account.username=code
                cls=db.get(Classes,student.class_id);cls.class_code=cls.class_code.replace("D26","D24");cls.class_name="Lớp "+cls.class_code
                for sub in db.scalars(select(AssignmentSubmissions).where(AssignmentSubmissions.student_id==student.id)):
                    data=files.resolve(storage,sub.storage_path).read_text(encoding="utf-8").replace(old_code,code).replace(old_name,student.full_name).encode("utf-8")
                    sub.storage_path=files.save(storage,"submissions",data);sub.size_bytes=len(data);sub.original_filename=code+"-baocao.txt"
                credentials.append(dict(student_id=code,full_name=student.full_name,class_name=cls.class_code,date_of_birth=student.date_of_birth,password=student.date_of_birth))
            for number,course in enumerate(db.scalars(select(Courses).order_by(Courses.id))):
                course.course_code=["LTM-D24-01","CTDL-D24-01"][number]
                course.end_date=(datetime.fromtimestamp(now,TZ)+timedelta(days=56)).date().isoformat()
                # Eliminate manually copied exam events; the calendar derives them now.
                db.execute(delete(CalendarEvents).where(CalendarEvents.course_id==course.id,CalendarEvents.event_type.in_(["exam","deadline"])))
                lessons=list(db.scalars(select(CalendarEvents).where(CalendarEvents.course_id==course.id,CalendarEvents.event_type=="lesson").order_by(CalendarEvents.starts_at)))
                lectures=[e for e in lessons if e.title.startswith("Buổi ")]
                old_sessions=list(db.scalars(select(AttendanceSessions).where(AttendanceSessions.course_id==course.id).order_by(AttendanceSessions.id)))
                for session,event in zip(old_sessions,lectures):
                    session.event_id=event.id;session.starts_at=event.starts_at;session.expires_at=event.starts_at+900
                anchor=datetime.fromtimestamp(lectures[2].starts_at,TZ)
                for week in [7,8]:
                    for offset,title in [(0,"Tích hợp hệ thống" if week==7 else "Ôn tập và đánh giá"),(2,"Thực hành và báo cáo nhóm")]:
                        start=(anchor+timedelta(days=(week-3)*7+offset)).timestamp()
                        db.add(CalendarEvents(course_id=course.id,created_by=user.id,event_type="lesson",title=f"Tuần {week}: {title}",description="Chuẩn bị source và báo cáo trước buổi học. Điểm danh QR theo hướng dẫn của giảng viên.",starts_at=start,ends_at=start+7200))
                for i,title in enumerate(TASKS[number],7):
                    description=f"{title}: trình bày thiết kế, cài đặt, kiểm tra ít nhất 5 trường hợp và phân tích kết quả. Nộp source cùng README hướng dẫn chạy, báo cáo PDF và minh chứng thực hiện tại phòng máy."
                    a=Assignments(course_id=course.id,created_by=teacher.id,title=f"BT{i:02d} - {title}",description=description,due_at=now+(8+(i-7)*6)*86400,allow_resubmit=True)
                    db.add(a);db.flush()
                    data=(a.title+"\n\n"+description+"\n\nĐánh giá: đúng yêu cầu 4; thiết kế 2; kiểm thử 2; trình bày và tái lập 2 điểm.\n").encode("utf-8")
                    path=files.save(storage,"assignment_handouts",data)
                    db.add(AssignmentAttachments(assignment_id=a.id,original_filename=f"BT{i:02d}-de-bai.txt",storage_path=path,size_bytes=len(data)))
                for a in db.scalars(select(Assignments).where(Assignments.course_id==course.id)):
                    if a.attachment_path:
                        db.add(AssignmentAttachments(assignment_id=a.id,original_filename=a.attachment_filename,storage_path=a.attachment_path,size_bytes=files.resolve(storage,a.attachment_path).stat().st_size))
                    data=(a.title+"\n\nCHECKLIST NỘP BÀI\n- Mã sinh viên và họ tên\n- Hướng dẫn chạy chương trình\n- Minh chứng kiểm thử\n- Đánh giá kết quả và các giới hạn\n").encode("utf-8")
                    db.add(AssignmentAttachments(assignment_id=a.id,original_filename="huong-dan-nop-bai.txt",storage_path=files.save(storage,"assignment_handouts",data),size_bytes=len(data)))
                mids=list(db.scalars(select(CodingExams).where(CodingExams.course_id==course.id,CodingExams.grade_component=="midterm").order_by(CodingExams.id)))
                for exam,day in zip(mids,[12,26]):exam.starts_at=now+day*86400;exam.ends_at=exam.starts_at+5400
                final=db.scalar(select(CodingExams).where(CodingExams.course_id==course.id,CodingExams.grade_component=="final"));final.starts_at=now+47*86400;final.ends_at=final.starts_at+7200
                summary['courses'][number].update(code=course.course_code,assignments=12,lessons=16)
        normalize_times(sessions)
        with (output/"students.csv").open("w",encoding="utf-8-sig",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(credentials[0]));writer.writeheader();writer.writerows(credentials)
        # Runtime-only passwords are never committed to Git or shown in application text.
        (output/"LOGIN.txt").write_text("GIẢNG VIÊN\nTên đăng nhập: GV001\nMật khẩu: "+password+"\n\nSINH VIÊN\nMã: B24DCCN101 đến B24DCCN140\nMật khẩu ban đầu: ngày sinh DDMMYYYY, bắt buộc đổi lần đầu.\nXem students.csv để lấy ngày sinh từng tài khoản.\n",encoding="utf-8-sig")
        (output/"accounts.csv").unlink(missing_ok=True)
        summary.update(database=str(output/"database.db"),storage=str(storage),fictional_data=True,credentials_file=str(output/"students.csv"))
        (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
        # Existing unreferenced seed files are omitted from the active storage snapshot.
        referenced=set()
        for model in [CourseMaterials,Assignments,AssignmentAttachments,AssignmentSubmissions,TestCases]:
            with sessions() as db:
                for row in db.scalars(select(model)):
                    for column in ["storage_path","attachment_path","input_path","expected_output_path"]:
                        value=getattr(row,column,None)
                        if value:referenced.add(files.resolve(storage,value))
        for path in storage.rglob('*'):
            if path.is_file() and path.resolve() not in referenced:
                if not path.resolve().is_relative_to(storage.resolve()):raise ValueError("Invalid storage path")
                path.unlink()
        return summary
    finally:engine.dispose()

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True)
    print(json.dumps(build(parser.parse_args().output),ensure_ascii=False,indent=2))
