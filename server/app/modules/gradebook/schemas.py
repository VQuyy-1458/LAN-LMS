from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Weights(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    attendance: float = Field(ge=0, le=100)
    homework: float = Field(ge=0, le=100)
    midterm: float = Field(ge=0, le=100)
    final: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def valid(self):
        if abs(sum(self.model_dump().values()) - 100) > 1e-6:
            raise ValueError("Tổng trọng số phải bằng 100%")
        return self


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    student_id: str
    component: Literal["attendance", "homework", "midterm", "final"]
    score: float | None = Field(default=None, ge=0, le=10)
    reason: str = Field(min_length=3, max_length=1000)


class Update(BaseModel):
    items: list[Entry] = Field(min_length=1, max_length=2000)


class Publish(BaseModel):
    published: bool
