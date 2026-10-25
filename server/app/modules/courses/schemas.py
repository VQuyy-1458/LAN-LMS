from datetime import date
from pydantic import BaseModel, Field, model_validator

class CourseInput(BaseModel):
    course_code: str = Field(min_length=1,max_length=128)
    name: str = Field(min_length=1,max_length=200)
    description: str = Field(default='',max_length=10000)
    start_date: date | None = None
    end_date: date | None = None
    semester: str = Field(default='1',min_length=1,max_length=32)
    academic_year: str = Field(default='2026-2027',min_length=1,max_length=32)
    @model_validator(mode='after')
    def dates(self):
        if self.start_date and self.end_date and self.end_date<self.start_date: raise ValueError('end_date before start_date')
        return self

class CoursePatch(BaseModel):
    course_code:str|None=Field(default=None,min_length=1,max_length=128)
    name:str|None=Field(default=None,min_length=1,max_length=200)
    description:str|None=Field(default=None,max_length=10000)
    start_date:date|None=None
    end_date:date|None=None
    semester:str|None=Field(default=None,min_length=1,max_length=32)
    academic_year:str|None=Field(default=None,min_length=1,max_length=32)
