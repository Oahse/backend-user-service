from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

class NotificationCreate(BaseModel):
    to_user_id: UUID
    body: str
    token: str
    data: Optional[Dict[str, Any]] = None
    title: Optional[str] = None

class TelegramNotificationCreate(BaseModel):
    chat_id: int
    text: Optional[str] = None
    photo_path: Optional[str] = None
    document_path: Optional[str] = None
    photo_caption: Optional[str] = None
    document_caption: Optional[str] = None

