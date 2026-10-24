"""TV1: API 1.1 shared response and pagination contracts."""
from datetime import datetime, timezone
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar('T')


class ErrorItem(BaseModel):
    field: str | None = None
    row: int | None = None
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str
    request_id: str
    errors: list[ErrorItem] = Field(default_factory=list)


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


class Pagination:
    def __init__(self, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self):
        return (self.page - 1) * self.page_size

    def response(self, items, total):
        return Page(items=items, page=self.page, page_size=self.page_size, total=total)


def utc_iso(value: datetime) -> str:
    """Reject ambiguous naive times instead of silently assuming a local timezone."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Datetime must include a timezone')
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
