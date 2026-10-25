import hashlib
import json
import time
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from ...core.database import get_db,User
from ...core.security import learning_user,hasher,fail
from ...models import CsvImportPreviews,Classes,Students,CourseEnrollments
from ...services import access,idempotency
from ...services.files import read_upload
from .service import inspect_rows
router=APIRouter(prefix='/api',tags=['csv'])

class Confirm(BaseModel):
    preview_id:str

@router.post('/courses/{course_id}/students/import-preview')
async def preview(course_id:int,file:UploadFile=File(...),db=Depends(get_db),user=Depends(learning_user)):
    _,content=await read_upload(file,2*1024*1024,{'.csv'})
    access.course(db,user,course_id,True);teacher=access.teacher(db,user)
    rows,errors,new,existing=inspect_rows(db,content)
    identifier=uuid.uuid4().hex;expires=time.time()+900
    db.add(CsvImportPreviews(preview_id=identifier,course_id=course_id,teacher_id=teacher.id,
        payload_json=content.decode('utf-8-sig',errors='replace'),content_hash=hashlib.sha256(content).hexdigest(),can_confirm=not errors,expires_at=expires))
    db.commit()
    from datetime import datetime,timezone
    return dict(preview_id=identifier,expires_at=datetime.fromtimestamp(expires,timezone.utc).isoformat(),
        total_rows=len(rows)+len(errors),valid_rows=len(rows),new_accounts=new,existing_accounts=existing,can_confirm=not errors,errors=errors,conflicts=[])

@router.post('/courses/{course_id}/students/import-confirm')
def confirm(course_id:int,body:Confirm,request:Request,key:str|None=Header(None,alias='Idempotency-Key'),db=Depends(get_db),user=Depends(learning_user)):
    def authorize(): access.course(db,user,course_id,True)
    def operation():
        teacher=access.teacher(db,user)
        p=db.scalar(select(CsvImportPreviews).where(CsvImportPreviews.preview_id==body.preview_id,CsvImportPreviews.course_id==course_id,CsvImportPreviews.teacher_id==teacher.id))
        if not p or not p.can_confirm or p.expires_at<=time.time() or p.confirmed_at:
            fail(409,'PREVIEW_STALE','Preview không hợp lệ, cần xem trước lại')
        rows,errors,_,_=inspect_rows(db,p.payload_json.encode('utf-8'))
        if errors: fail(409,'PREVIEW_STALE','Dữ liệu đã thay đổi; cần preview lại')
        result=dict(preview_id=p.preview_id,total_rows=len(rows),created_accounts=0,existing_accounts=0,new_enrollments=0,existing_enrollments=0,failed_rows=0)
        for row in rows:
            account=db.scalar(select(User).where(User.username==row['student_id']))
            if not account:
                account=User(username=row['student_id'],password_hash=hasher.hash(row['date_of_birth']),role='student',must_change_password=True)
                db.add(account);db.flush();result['created_accounts']+=1
                cls=db.scalar(select(Classes).where(Classes.class_code==row['class_name']))
                if not cls:
                    cls=Classes(class_code=row['class_name'],class_name=row['class_name']);db.add(cls);db.flush()
                s=Students(user_id=account.id,student_code=row['student_id'],full_name=row['full_name'],date_of_birth=row['date_of_birth'],email=row['email'] or None,class_id=cls.id)
                db.add(s);db.flush()
            else:
                result['existing_accounts']+=1
                s=db.scalar(select(Students).where(Students.user_id==account.id))
            enrollment=db.scalar(select(CourseEnrollments).where(CourseEnrollments.course_id==course_id,CourseEnrollments.student_id==s.id))
            if not enrollment:
                db.add(CourseEnrollments(course_id=course_id,student_id=s.id,status='active'));result['new_enrollments']+=1
            else:
                if enrollment.status!='active': enrollment.status='active'
                result['existing_enrollments']+=1
        p.confirmed_at=time.time()
        return result
    result,status=idempotency.run(db,user,'POST',request.url.path,key,idempotency.request_hash(body.model_dump()),operation,authorize=authorize)
    return JSONResponse(result,status_code=status)
