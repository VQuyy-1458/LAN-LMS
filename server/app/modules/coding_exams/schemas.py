from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict


class ExamInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    title: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    ends_at: datetime
    grade_component: Literal["midterm", "final"]
    score_ladder: list[float] = Field(
        default_factory=lambda: [0, 5, 7, 8, 9, 10], min_length=2, max_length=21
    )

    @model_validator(mode="after")
    def valid(self):
        if (
            not self.starts_at.tzinfo
            or not self.ends_at.tzinfo
            or self.ends_at <= self.starts_at
        ):
            raise ValueError("Thời gian cần múi giờ và kết thúc sau bắt đầu")
        if (
            self.score_ladder[0] != 0
            or self.score_ladder[-1] != 10
            or any(
                a > b or a < 0 or b > 10
                for a, b in zip(self.score_ladder, self.score_ladder[1:])
            )
        ):
            raise ValueError("Bảng điểm phải tăng dần từ 0 đến 10")
        return self


class ProblemInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=50000)
    languages: list[Literal["c", "cpp", "java"]] = Field(
        default_factory=lambda: ["c", "cpp", "java"], min_length=1, max_length=3
    )
    io_mode: Literal["stdio", "file"] = "stdio"
    input_filename: str | None = None
    output_filename: str | None = None
    time_limit_ms: int = Field(default=2000, ge=100, le=10000)
    memory_limit_mib: int = Field(default=256, ge=64, le=1024)
    max_score: float = Field(default=100, gt=0, le=10000)
    comparator: Literal["exact", "normalized"] = "normalized"

    @model_validator(mode="after")
    def valid(self):
        if self.io_mode == "file":
            for name in (self.input_filename, self.output_filename):
                if (
                    not name
                    or len(name) > 100
                    or any(c in name for c in "/\\:")
                    or name in (".", "..", "stdout", "stderr")
                ):
                    raise ValueError("Tên file phải là basename hợp lệ")
            if self.input_filename == self.output_filename:
                raise ValueError("Input/output cần tên khác nhau")
        return self
