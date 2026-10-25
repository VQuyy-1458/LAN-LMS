from .service import view
from .schemas import MaterialResponse
from ...schemas.common import Page
import time
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import CourseMaterials
from ...services import access
from ...services.files import read_upload, save, resolve
from ...schemas.common import Pagination

router = APIRouter(prefix="/api", tags=["materials"])


@router.get("/courses/{course_id}/materials", response_model=Page[MaterialResponse])
def listing(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id)
    q = select(CourseMaterials).where(CourseMaterials.course_id == course_id)
    return p.response(
        [
            view(r)
            for r in db.scalars(
                q.order_by(CourseMaterials.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.post(
    "/courses/{course_id}/materials", status_code=201, response_model=MaterialResponse
)
async def upload(
    course_id: int,
    request: Request,
    title: str = Form(..., min_length=1, max_length=200),
    file: UploadFile = File(...),
    db=Depends(get_db),
    user=Depends(learning_user),
):
    access.course(db, user, course_id, True)
    name, data = await read_upload(
        file, 20 * 1024 * 1024, {".pdf", ".docx", ".pptx", ".txt", ".zip"}
    )
    path = save(request.app.state.storage_root, "course_materials", data)
    try:
        r = CourseMaterials(
            course_id=course_id,
            uploaded_by=user.user_id,
            title=title,
            original_filename=name,
            size_bytes=len(data),
            storage_path=path,
            uploaded_at=time.time(),
        )
        db.add(r)
        db.commit()
        return view(r)
    except BaseException:
        (Path(request.app.state.storage_root) / path).unlink(missing_ok=True)
        raise


@router.get("/materials/{material_id}/download")
def download(
    material_id: int, request: Request, db=Depends(get_db), user=Depends(learning_user)
):
    r = db.get(CourseMaterials, material_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy tài liệu")
    access.course(db, user, r.course_id)
    return FileResponse(
        resolve(request.app.state.storage_root, r.storage_path),
        filename=r.original_filename,
        media_type="application/octet-stream",
    )
