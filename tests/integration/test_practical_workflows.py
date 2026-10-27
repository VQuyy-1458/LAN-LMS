import csv
import io
import zipfile
from datetime import datetime,timedelta,timezone
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_day25 import context,ORIGIN
from test_completion import prepare_exam,submit
from server.app.models import Students,AssignmentGrades
from judge import job_queue
from judge.runners.container import Result

def test_tabs_select_independent_httponly_sessions_and_logout(context):
    app,clients,cid=context
    with TestClient(app) as browser:
        tabs=['a'*32,'b'*32]
        for tab,name in zip(tabs,['t','s']):
            response=browser.post('/api/auth/login',headers={**ORIGIN,'X-Session-Tab':tab},json={'username':name,'password':'password-123'})
            assert response.status_code==200
            assert 'HttpOnly' in response.headers['set-cookie']
        for tab,name in zip(tabs,['t','s']):
            assert browser.get('/api/auth/me',headers={'X-Session-Tab':tab}).json()['username']==name
            assert browser.get(f'/api/auth/me?session_tab={tab}').json()['username']==name
        csrf=browser.get('/api/auth/csrf',headers={'X-Session-Tab':tabs[0]}).json()['csrf_token']
        assert browser.post('/api/auth/logout',headers={**ORIGIN,'X-Session-Tab':tabs[0],'X-CSRF-Token':csrf}).status_code==204
        assert browser.get('/api/auth/me',headers={'X-Session-Tab':tabs[0]}).status_code==401
        assert browser.get('/api/auth/me',headers={'X-Session-Tab':tabs[1]}).json()['username']=='s'
        assert browser.get('/api/auth/me',headers={'X-Session-Tab':'invalid'}).status_code==400

def test_editable_homework_matrix_and_live_grade_csv_are_atomic(context):
    app,c,cid=context
    now=datetime.now(timezone.utc)
    aids=[c['t'].post(f'/api/courses/{cid}/assignments',json={'title':f'BT{i}','due_at':(now+timedelta(days=1)).isoformat()}).json()['id'] for i in range(2)]
    path=f'/api/courses/{cid}/assignments/progress'
    assert c['s'].patch(path,json={'items':[{'student_id':'s','assignment_id':aids[0],'score':8}]}).status_code==403
    assert c['t'].patch(path,json={'items':[{'student_id':'s','assignment_id':a,'score':score} for a,score in zip(aids,[8,6])]}).status_code==200
    assert c['t'].get(path).json()['items'][0]['average']==7
    assert c['s'].get(path).json()['items'][0]['scores'][str(aids[0])]==8
    book=f'/api/courses/{cid}/gradebook'
    assert c['s'].get(book).json()['items'][0]['homework_score']==7
    before=c['t'].get(book+'/export-csv');assert before.status_code==200
    rows=list(csv.DictReader(io.StringIO(before.content.decode('utf-8-sig'))));assert rows[0]['final_score']==''
    payload=b'student_id,midterm_score,final_score\ns,7,8\n'
    assert c['t'].post(book+'/import-csv',files={'file':('grades.csv',payload)}).status_code==200
    assert c['s'].get(book).json()['items'][0]['final_score']==8
    invalid=b'student_id,final_score\ns,1\noutsider,9\n'
    assert c['t'].post(book+'/import-csv',files={'file':('grades.csv',invalid)}).status_code==404
    assert c['s'].get(book).json()['items'][0]['final_score']==8
    assert c['t'].post(book+'/import-csv',files={'file':('grades.csv',b'student_id,final_score\ns,nan\n')}).status_code==422
    assert c['t'].patch(f'/api/courses/{cid}/grades',json={'items':[{'student_id':'s','component':'final','score':9}]}).status_code==200
    assert c['s'].get(book).json()['items'][0]['final_score']==9

def test_previews_do_not_expose_other_students_or_execute_zip(context):
    app,c,cid=context
    aid=c['t'].post(f'/api/courses/{cid}/assignments',json={'title':'Source','due_at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}).json()['id']
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('src/main.cpp','int main(){}');z.writestr('page.html','<script>alert(1)</script>')
    row=c['s'].post(f'/api/assignments/{aid}/submissions',files={'file':('answer.zip',archive.getvalue())},headers={'Idempotency-Key':'preview'}).json()
    path=f"/api/assignment-submissions/{row['id']}/preview"
    assert c['t'].get(path).json()['kind']=='archive'
    assert c['t'].get(path+'?entry=src/main.cpp').json()['text']=='int main(){}'
    assert c['t'].get(path+'?entry=page.html').status_code==422
    assert c['outsider'].get(path).status_code==403

def test_attendance_starts_at_ten_and_subtracts_one_per_absence(context):
    app,c,cid=context
    book=f'/api/courses/{cid}/gradebook'
    assert c['s'].get(book).json()['items'][0]['attendance_score']==10
    for index in range(3):
        session=c['t'].post(f'/api/courses/{cid}/attendance-sessions',json={}).json()
        if index==0:
            assert c['s'].post(f"/api/attendance-sessions/{session['id']}/check-in",json={'token':session['token']}).status_code==201
        assert c['t'].patch(f"/api/attendance-sessions/{session['id']}",json={'status':'closed'}).status_code==200
    assert c['s'].get(book).json()['items'][0]['attendance_score']==8

def test_active_exam_early_finish_and_csv_follow_completed_judge(context):
    app,c,cid=context
    eid,pids,sid=prepare_exam(app,c,cid)
    assert c['s'].get('/api/my/active-exam').json()=={'exam_id':eid,'session_id':sid}
    assert c['s'].get(f'/api/coding-exams/{eid}/export-csv').status_code==403
    assert submit(c,pids[0],sid).status_code==202
    assert c['s'].post(f'/api/exam-sessions/{sid}/finish').status_code==200
    assert c['s'].get('/api/my/active-exam').json() is None
    path=f'/api/coding-exams/{eid}/export-csv'
    row=list(csv.DictReader(io.StringIO(c['t'].get(path).content.decode('utf-8-sig'))))[0]
    assert row['score']==''
    claim=job_queue.claim(app.state.sessions,'test');job_queue.complete(app.state.sessions,claim,Result('Accepted',100,100),1,1)
    row=list(csv.DictReader(io.StringIO(c['t'].get(path).content.decode('utf-8-sig'))))[0]
    assert float(row['score'])==10 and row['accepted_count']=='1'
    assert c['s'].get(f'/api/courses/{cid}/gradebook').json()['items'][0]['final_score']==10
