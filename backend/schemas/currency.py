from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str

class CurrencyCreate(CurrencyBase):
    pass

class CurrencyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None

class CurrencyRead(CurrencyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
