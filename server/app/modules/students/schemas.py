from pydantic import BaseModel


class Confirm(BaseModel):
    preview_id: str
