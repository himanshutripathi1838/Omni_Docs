from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryCreate(BaseModel):
    user_id: Optional[int] = None
    document_id: Optional[int] = None
    command: str
    detected_task: str
    output_filename: Optional[str] = None
    status: str = "completed"


class HistoryOut(BaseModel):
    id: int
    command: str
    detected_task: str
    output_filename: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
