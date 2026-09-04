from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SlotOut(BaseModel):
    code: str
    row: int
    col: int
    is_occupied: bool
    plate_code: Optional[str] = None

    class Config:
        from_attributes = True


class LotStatusOut(BaseModel):
    total: int
    free: int
    occupied: int
    slots: List[SlotOut]


class EntryResultOut(BaseModel):
    plate_raw: str
    plate_code: str
    slot_code: str
    guidance: str


class ExitResultOut(BaseModel):
    plate_code: str
    freed: bool


class LogOut(BaseModel):
    plate_raw: str
    plate_code: str
    slot_code: Optional[str] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None

    class Config:
        from_attributes = True
