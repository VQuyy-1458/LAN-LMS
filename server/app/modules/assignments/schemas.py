from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AssignmentInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20000)
    due_at: datetime
    allow_resubmit: bool = True

    @field_validator("due_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone required")
        return value


class GradeInput(BaseModel):
    score: float = Field(ge=0, le=10, allow_inf_nan=False)
    feedback: str = Field(default="", max_length=10000)


class AssignmentPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    due_at: datetime | None = None
    allow_resubmit: bool | None = None
