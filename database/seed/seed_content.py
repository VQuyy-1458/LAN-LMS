"""Optional synthetic course content after the interactive teacher/demo-account seed."""
import argparse
import time
from sqlalchemy import select
from server.app.core.config import Settings,PROJECT_ROOT
from server.app.core.database import database
from server.app.models import User,Teachers,Courses,CalendarEvents,CourseMaterials,Assignments,CodingExams,Problems,TestCases
from server.app.services.files import save

PROBLEMS=[
 ('Tổng hai số','Cho hai số nguyên a và b. In tổng a + b.\nInput: hai số nguyên, mỗi số có trị tuyệt đối không quá 10^6.\nOutput: một số nguyên.\nVí dụ: input 1 2; output 3.','stdio',[(b'1 2\n',b'3\n'),(b'-5 8\n',b'3\n')]),
 ('Giá trị lớn nhất','Cho hai số nguyên a, b. In số lớn hơn.\nVí dụ: input 3 7; output 7.','stdio',[(b'3 7\n',b'7\n'),(b'-4 -9\n',b'-4\n')]),
 ('Kiểm tra số chẵn','Cho số nguyên n. In YES nếu n chẵn, ngược lại in NO.\nVí dụ: input 4; output YES.','stdio',[(b'4\n',b'YES\n'),(b'7\n',b'NO\n')]),
 ('Tổng từ 1 đến N','Cho 1 <= n <= 10^6. In tổng các số nguyên từ 1 tới n. Dùng kiểu số nguyên 64 bit.\nVí dụ: input 5; output 15.','stdio',[(b'5\n',b'15\n'),(b'1000000\n',b'500000500000\n')]),
 ('Giai thừa','Đọc n từ input.txt, ghi n! vào output.txt. Giới hạn 0 <= n <= 15.\nVí dụ: input.txt chứa 5; output.txt chứa 120.','file',[(b'5\n',b'120\n'),(b'0\n',b'1\n')]),
]


def seed_content(db,teacher_username,storage):
    user=db.scalar(select(User).where(User.username==teacher_username,User.role=='teacher'))
    if not user:raise ValueError('Create the teacher first')
    teacher=db.scalar(select(Teachers).where(Teachers.user_id==user.id))
    course=db.scalar(select(Courses).where(Courses.course_code=='DEMO-LTM'))
    if not teacher or not course:raise ValueError('Run database.seed.seed_demo first')
    now=time.time()
    if not db.scalar(select(CalendarEvents.id).where(CalendarEvents.course_id==course.id,CalendarEvents.title=='Buổi học lập trình mạng')):
        db.add(CalendarEvents(course_id=course.id,created_by=user.id,title='Buổi học lập trình mạng',description='Dữ liệu mẫu để thử lịch học và dashboard.',event_type='lesson',starts_at=now+3600,ends_at=now+7200))
        db.add(CalendarEvents(course_id=course.id,created_by=user.id,title='Hướng dẫn học tập',description='Đọc tài liệu, nộp bài tập và làm đề mẫu. Đây là dữ liệu giả lập.',event_type='announcement',starts_at=now,ends_at=now+86400))
    if not db.scalar(select(CourseMaterials.id).where(CourseMaterials.course_id==course.id,CourseMaterials.title=='Hướng dẫn sử dụng khóa học')):
        content='LAN-LMS demo\n1. Đổi mật khẩu lần đầu.\n2. Xem lịch, tài liệu và bài tập.\n3. Bắt đầu phiên thi khi đến giờ.\n4. Chỉ bài AC được tính vào điểm thi.\n'.encode('utf-8')
        db.add(CourseMaterials(course_id=course.id,uploaded_by=user.id,title='Hướng dẫn sử dụng khóa học',storage_path=save(storage,'course_materials',content),original_filename='huong-dan.txt',size_bytes=len(content),uploaded_at=now))
    if not db.scalar(select(Assignments.id).where(Assignments.course_id==course.id,Assignments.title=='Báo cáo giao tiếp Client Server')):
        db.add(Assignments(course_id=course.id,created_by=teacher.id,title='Báo cáo giao tiếp Client Server',description='Mô tả một luồng HTTP và một luồng WebSocket. Nộp PDF, DOCX hoặc ZIP.',due_at=now+86400,allow_resubmit=True))
    for kind,delay,label in [('midterm',900,'Giữa kỳ'),('final',86400,'Cuối kỳ')]:
        exam=db.scalar(select(CodingExams).where(CodingExams.course_id==course.id,CodingExams.grade_component==kind))
        if exam:continue
        exam=CodingExams(course_id=course.id,created_by=teacher.id,title=f'{label} lập trình mẫu',grade_component=kind,starts_at=now+delay,ends_at=now+delay+7200,status='draft',results_published=False,score_ladder_json='[0,5,7,8,9,10]');db.add(exam);db.flush()
        for title,statement,mode,cases in PROBLEMS:
            p=Problems(exam_id=exam.id,title=title,statement=statement,languages_json='["c","cpp","java"]',io_mode=mode,input_filename='input.txt' if mode=='file' else None,output_filename='output.txt' if mode=='file' else None,time_limit_ms=2000,memory_limit_mib=256,max_score=100,comparator='normalized');db.add(p);db.flush()
            for index,(inp,out) in enumerate(cases,1):db.add(TestCases(problem_id=p.id,input_path=save(storage,'test_cases',inp),expected_output_path=save(storage,'test_cases',out),weight=50,sort_order=index,is_sample=index==1))
    return course.id


def main():
    from pathlib import Path
    import os
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--teacher-username',required=True);args=p.parse_args()
    engine,sessions=database(Settings().database_url)
    try:
        with sessions.begin() as db:seed_content(db,args.teacher_username,Path(os.getenv('STORAGE_ROOT',PROJECT_ROOT/'storage')))
        print('Synthetic content created. Review exam times and schedule them in the teacher UI.')
    finally:engine.dispose()


if __name__=='__main__':main()
