"""Course finalization is serialized with every learning-data mutation."""
from .. import models as m
from ..core.security import fail
from . import access

def assert_writable_request(db,user,request):
    parts=request.url.path.strip('/').split('/')
    if len(parts)<3 or parts[0]!='api':return
    try: ident=int(parts[2])
    except ValueError:return
    resource=parts[1];course_id=None;row=None
    if resource=='courses':course_id=ident
    elif resource in {'assignments','coding-exams','events','attendance-sessions','materials'}:
        model={'assignments':m.Assignments,'coding-exams':m.CodingExams,'events':m.CalendarEvents,'attendance-sessions':m.AttendanceSessions,'materials':m.CourseMaterials}[resource]
        row=db.get(model,ident)
        if row:course_id=row.course_id
    elif resource in {'assignment-submissions','assignment-files'}:
        row=db.get(m.AssignmentSubmissions if resource=='assignment-submissions' else m.AssignmentAttachments,ident)
        assignment=db.get(m.Assignments,row.assignment_id) if row else None
        if assignment:course_id=assignment.course_id
    elif resource in {'problems','test-cases','exam-sessions'}:
        if resource=='problems':problem=db.get(m.Problems,ident);eid=problem.exam_id if problem else None
        elif resource=='test-cases':
            test=db.get(m.TestCases,ident);problem=db.get(m.Problems,test.problem_id) if test else None;eid=problem.exam_id if problem else None
        else:
            session=db.get(m.ExamSessions,ident);reg=db.get(m.ExamRegistrations,session.registration_id) if session else None;eid=reg.exam_id if reg else None
        exam=db.get(m.CodingExams,eid) if eid else None
        if exam:course_id=exam.course_id
    if course_id is not None:
        course=access.course(db,user,course_id)
        if course.status=='finalized':fail(423,'COURSE_FINALIZED','Khóa học đã tổng kết; chỉ được xem và xuất dữ liệu')
