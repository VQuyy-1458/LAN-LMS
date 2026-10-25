from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: int
    course_id: int
    title: str
    original_filename: str
    size_bytes: int
    uploaded_at: str
