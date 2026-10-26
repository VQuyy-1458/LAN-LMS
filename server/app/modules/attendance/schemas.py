from typing import Literal
from pydantic import BaseModel, Field


class Create(BaseModel):
    title: str = Field(default="Điểm danh", min_length=1, max_length=200)
    duration_seconds: int = Field(default=300, ge=60, le=3600)
    event_id: int | None = Field(default=None, gt=0)


class Close(BaseModel):
    status: Literal["closed"]


class Check(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class Correction(BaseModel):
    student_id: str
    status: Literal["present", "absent", "late"]
    reason: str = Field(min_length=3, max_length=1000)
