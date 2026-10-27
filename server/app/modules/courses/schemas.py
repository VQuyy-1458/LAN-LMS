from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class CourseInput(BaseModel):
    course_code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    start_date: date | None = None
    end_date: date | None = None
    semester: Literal["1", "2", "summer"] = "1"
    academic_year: str = Field(default="2026-2027", min_length=1, max_length=32)

    @model_validator(mode="after")
    def dates(self):
        import re
        if not re.fullmatch(r"\d{4}-\d{4}", self.academic_year) or int(self.academic_year[5:]) != int(self.academic_year[:4])+1:
            raise ValueError("Năm học phải gồm hai năm liên tiếp, ví dụ 2026-2027")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date before start_date")
        return self


class CoursePatch(BaseModel):
    course_code: str | None = Field(default=None, min_length=1, max_length=128)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    start_date: date | None = None
    end_date: date | None = None
    semester: str | None = Field(default=None, min_length=1, max_length=32)
    academic_year: str | None = Field(default=None, min_length=1, max_length=32)
