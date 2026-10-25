from pydantic import BaseModel, Field, ConfigDict


class SubmissionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam_session_id: int = Field(gt=0)
    language: str
    source_code: str = Field(min_length=1, max_length=262144)
