import io,zipfile
from datetime import datetime,timedelta,timezone
from sqlalchemy import select,func
from test_day25 import context
from test_completion import prepare_exam
from server.app.models import Assignments,CalendarEvents,AssignmentAttachments

def future(days=1):return (datetime.now(timezone.utc)+timedelta(days=days)).isoformat()

def test_finalized_course_rejects_all_mutations_but_keeps_reads(context):
    app,c,cid=context
    items=[{'student_id':'s','component':k,'score':8} for k in ['attendance','homework','midterm','final']]
    assert c['t'].patch(f'/api/courses/{cid}/grades',json={'items':items}).status_code==200
    assert c['t'].post(f'/api/courses/{cid}/gradebook/publish',json={'published':True}).status_code==200
    assert c['t'].get(f'/api/courses/{cid}').json()['status']=='finalized'
    for method,path,body in [
        ('PATCH',f'/api/courses/{cid}',{'name':'Changed'}),
        ('PATCH',f'/api/courses/{cid}/grades',{'items':items}),
        ('POST',f'/api/courses/{cid}/assignments',{'title':'New','due_at':future()}),
        ('POST',f'/api/courses/{cid}/attendance-sessions',{}),
        ('POST',f'/api/courses/{cid}/gradebook/publish',{'published':False}),
        ('DELETE',f'/api/courses/{cid}',None)]:
        response=c['t'].request(method,path,json=body)
        assert response.status_code==423,(path,response.text)
    assert c['t'].get(f'/api/courses/{cid}/students').status_code==200
    assert c['t'].get(f'/api/courses/{cid}/gradebook/export-csv').status_code==200
    assert c['s'].get(f'/api/courses/{cid}/gradebook').json()['items'][0]['total_score']==8

def test_closed_attendance_cannot_correct_or_reissue(context):
    app,c,cid=context
    event=c['t'].post(f'/api/courses/{cid}/events',json={'title':'Buổi 1','starts_at':future(),'ends_at':future(2)}).json()
    session=c['t'].post(f'/api/courses/{cid}/attendance-sessions',json={'event_id':event['id']}).json()
    assert c['t'].patch(f"/api/attendance-sessions/{session['id']}",json={'status':'closed'}).status_code==200
    assert c['t'].patch(f"/api/attendance-sessions/{session['id']}/records",json={'student_id':'s','status':'present','reason':'checked'}).status_code==409
    assert c['t'].post(f'/api/courses/{cid}/attendance-sessions',json={'event_id':event['id']}).status_code==409
    assert c['t'].get(f"/api/attendance-sessions/{session['id']}/roster").json()['items'][0]['status']=='absent'
    assert c['t'].get(f'/api/courses/{cid}/events').json()['items'][0]['attendance_state']=='closed'

def test_submitted_exam_cannot_reopen_and_teacher_can_delete(context):
    app,c,cid=context
    eid,pids,sid=prepare_exam(app,c,cid)
    assert c['s'].post(f'/api/exam-sessions/{sid}/finish').status_code==200
    assert c['s'].get(f'/api/coding-exams/{eid}').json()['can_open'] is False
    assert c['s'].get(f'/api/coding-exams/{eid}/problems').status_code==409
    assert c['s'].post(f'/api/coding-exams/{eid}/sessions/start').status_code==409
    assert c['t'].get(f'/api/coding-exams/{eid}/problems').status_code==200
    assert c['other'].delete(f'/api/coding-exams/{eid}').status_code==403
    assert c['t'].delete(f'/api/coding-exams/{eid}').status_code==204
    assert c['t'].get(f'/api/coding-exams/{eid}').status_code==404
    assert c['t'].get(f'/api/courses/{cid}/coding-exams').json()['total']==0
    # Deleting a final releases its unique component slot without deleting history.
    assert c['t'].post(f'/api/courses/{cid}/coding-exams',json={'title':'Final mới','starts_at':future(),'ends_at':future(2),'grade_component':'final','score_ladder':[0,10]}).status_code==201

def test_derived_calendar_and_ten_record_pages(context):
    app,c,cid=context
    for i in range(13):
        response=c['t'].post(f'/api/courses/{cid}/assignments',json={'title':f'BT {i}','due_at':future()})
        assert response.status_code==201
    page=c['t'].get(f'/api/courses/{cid}/assignments?page_size=100').json()
    assert page['page_size']==10 and len(page['items'])==10 and page['total']==13
    assert len(c['t'].get(f'/api/courses/{cid}/assignments?page=2').json()['items'])==3
    aid=page['items'][0]['id']
    assert c['t'].patch(f'/api/assignments/{aid}',json={'due_at':future(3)}).status_code==200
    events=c['t'].get(f'/api/courses/{cid}/events').json()
    assert events['total']==13 and len(events['items'])==10
    assert c['t'].post(f'/api/courses/{cid}/events',json={'title':'Fake exam','event_type':'exam','starts_at':future(),'ends_at':future(2)}).status_code==422
    assert c['t'].delete(f'/api/assignments/{aid}').status_code==204
    assert c['t'].get(f'/api/courses/{cid}/events').json()['total']==12
    assert c['t'].get(f'/api/assignments/{aid}').status_code==404

def test_multiple_handouts_create_and_replace_atomically(context):
    app,c,cid=context
    data={'title':'Đề nhiều file','description':'Nội dung','due_at':future(),'allow_resubmit':'true'}
    path=f'/api/courses/{cid}/assignments/with-files'
    bad=c['t'].post(path,data=data,files=[('files',('de.txt',b'one')),('files',('bad.exe',b'bad'))])
    assert bad.status_code==400
    assert c['t'].get(f'/api/courses/{cid}/assignments').json()['total']==0
    created=c['t'].post(path,data=data,files=[('files',('de.txt',b'one')),('files',('rubric.txt',b'two'))])
    assert created.status_code==201,created.text
    row=created.json();assert len(row['attachments'])==2
    fid=row['attachments'][0]['id']
    assert c['s'].get(f'/api/assignment-files/{fid}/preview').json()['text']=='one'
    assert c['outsider'].get(f'/api/assignment-files/{fid}/preview').status_code==403
    update=c['t'].patch(f"/api/assignments/{row['id']}/with-files",data={**data,'title':'Đề đã sửa','replace_files':'true'},files=[('files',('new.txt',b'new'))])
    assert update.status_code==200,update.text
    assert len(update.json()['attachments'])==1
    assert c['t'].get(f'/api/assignment-files/{fid}/download').status_code==404

def test_standardized_academic_fields_and_course_delete(context):
    app,c,cid=context
    for term,year,status in [('3','2026-2027',422),('summer','2026/2027',422),('2','2026-2029',422),('summer','2026-2027',201)]:
        response=c['t'].post('/api/courses',json={'course_code':'TERM','name':'Học kỳ','semester':term,'academic_year':year})
        assert response.status_code==status,response.text
    assert c['other'].delete(f'/api/courses/{cid}').status_code==403
    assert c['t'].delete(f'/api/courses/{cid}').status_code==204
    assert c['s'].get(f'/api/courses/{cid}').status_code==404
    assert c['s'].get('/api/courses').json()['total']==0

def test_midterm_average_updates_as_each_exam_finishes(context):
    from test_completion import submit
    from server.app.models import CodingExams
    from judge import job_queue
    from judge.runners.container import Result
    app,c,cid=context
    eid,pids,sid=prepare_exam(app,c,cid)
    assert submit(c,pids[0],sid).status_code==202
    job_queue.complete(app.state.sessions,job_queue.claim(app.state.sessions,'test'),Result('Accepted',100,100),1,1)
    c['s'].post(f'/api/exam-sessions/{sid}/finish')
    with app.state.sessions.begin() as db:db.get(CodingExams,eid).grade_component='midterm'
    next_eid,_,next_sid=prepare_exam(app,c,cid)
    with app.state.sessions.begin() as db:db.get(CodingExams,next_eid).grade_component='midterm'
    assert c['s'].get(f'/api/courses/{cid}/gradebook').json()['items'][0]['midterm_score']==10
    c['s'].post(f'/api/exam-sessions/{next_sid}/finish')
    assert c['s'].get(f'/api/courses/{cid}/gradebook').json()['items'][0]['midterm_score']==5
