"""Atomic assignment metadata + multiple handouts."""
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter,Depends,File,Form,UploadFile,Request,Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from ...core.database import get_db
from ...core.security import learning_user,fail
from ...models import Assignments,AssignmentAttachments
from ...services import access,files
from ...services.activity import audit,emit
from .schemas import AssignmentInput
from .service import assignment_view
router=APIRouter()
ALLOWED={".pdf",".doc",".docx",".ppt",".pptx",".txt",".zip"}

async def save_assignment(cid,aid,title,description,due_at,allow_resubmit,uploads,replace_files,request,db,user):
    from pydantic import ValidationError
    try:body=AssignmentInput(title=title,description=description,due_at=due_at,allow_resubmit=allow_resubmit)
    except ValidationError:fail(422,"VALIDATION_ERROR","Thông tin hoặc hạn nộp không hợp lệ")
    if len(uploads)>10:fail(422,"TOO_MANY_FILES","Tối đa 10 file đề bài")
    content=[await files.read_upload(f,20*1024*1024,ALLOWED) for f in uploads]
    if sum(len(data) for _,data in content)>100*1024*1024:fail(413,"FILES_TOO_LARGE","Tổng file tối đa 100 MiB")
    row=db.get(Assignments,aid) if aid else None
    if aid and not row:fail(404,"NOT_FOUND","Không tìm thấy bài tập")
    cid=row.course_id if row else cid
    access.course(db,user,cid,True);teacher=access.teacher(db,user)
    saved=[]
    try:
        if not row:row=Assignments(course_id=cid,created_by=teacher.id);db.add(row)
        row.title=body.title;row.description=body.description;row.due_at=body.due_at.timestamp();row.allow_resubmit=body.allow_resubmit
        db.flush()
        old=list(db.scalars(select(AssignmentAttachments).where(AssignmentAttachments.assignment_id==row.id)))
        if len(old)+len(content)>10 and not replace_files:fail(422,"TOO_MANY_FILES","Mỗi bài tập có tối đa 10 file")
        if replace_files:
            for attachment in old:db.delete(attachment)
            row.attachment_path=None;row.attachment_filename=None
        for name,data in content:
            path=files.save(request.app.state.storage_root,"assignment_handouts",data);saved.append(path)
            db.add(AssignmentAttachments(assignment_id=row.id,original_filename=name,storage_path=path,size_bytes=len(data)))
        audit(db,user.user_id,"update" if aid else "create","assignment",row.id)
        emit(db,"grade.updated",cid,{"assignment_id":row.id})
        db.flush();result=assignment_view(row,db);db.commit();return result
    except BaseException:
        db.rollback()
        for path in saved:(Path(request.app.state.storage_root)/path).unlink(missing_ok=True)
        raise

@router.post("/courses/{cid}/assignments/with-files",status_code=201)
async def create(cid:int,request:Request,title:str=Form(...),description:str=Form(""),due_at:str=Form(...),allow_resubmit:bool=Form(True),files:list[UploadFile]=File(default=[]),db=Depends(get_db),user=Depends(learning_user)):
    return await save_assignment(cid,None,title,description,due_at,allow_resubmit,files,False,request,db,user)

@router.patch("/assignments/{aid}/with-files")
async def update(aid:int,request:Request,title:str=Form(...),description:str=Form(""),due_at:str=Form(...),allow_resubmit:bool=Form(True),replace_files:bool=Form(False),files:list[UploadFile]=File(default=[]),db=Depends(get_db),user=Depends(learning_user)):
    return await save_assignment(None,aid,title,description,due_at,allow_resubmit,files,replace_files,request,db,user)

def accessible(db,user,fid,manage=False):
    file=db.get(AssignmentAttachments,fid)
    assignment=db.get(Assignments,file.assignment_id) if file else None
    if not assignment:fail(404,"NOT_FOUND","Không tìm thấy file đề bài")
    access.course(db,user,assignment.course_id,manage)
    return file

@router.get("/assignment-files/{fid}/download")
def download(fid:int,request:Request,db=Depends(get_db),user=Depends(learning_user)):
    file=accessible(db,user,fid)
    return FileResponse(files.resolve(request.app.state.storage_root,file.storage_path),filename=file.original_filename,media_type="application/octet-stream")

@router.get("/assignment-files/{fid}/preview")
def preview(fid:int,request:Request,entry:str|None=None,db=Depends(get_db),user=Depends(learning_user)):
    from ...services.file_preview import preview
    file=accessible(db,user,fid)
    return preview(files.resolve(request.app.state.storage_root,file.storage_path),file.original_filename,entry)

@router.get("/assignment-files/{fid}/view")
def view(fid:int,request:Request,db=Depends(get_db),user=Depends(learning_user)):
    file=accessible(db,user,fid)
    if Path(file.original_filename).suffix.lower()!=".pdf":fail(422,"PREVIEW_UNSUPPORTED","Chỉ đọc PDF tại đường dẫn này")
    return FileResponse(files.resolve(request.app.state.storage_root,file.storage_path),media_type="application/pdf",headers={"Content-Disposition":"inline","X-Content-Type-Options":"nosniff"})

@router.delete("/assignment-files/{fid}",status_code=204)
def delete(fid:int,db=Depends(get_db),user=Depends(learning_user)):
    file=accessible(db,user,fid,True);db.delete(file);db.commit();return Response(status_code=204)
