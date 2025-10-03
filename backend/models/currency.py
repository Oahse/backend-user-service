from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, DateTime
from core.database import Base, CHAR_LENGTH
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(CHAR_LENGTH), index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), index=True)
    symbol: Mapped[str] = mapped_column(String(CHAR_LENGTH), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    def __repr__(self):
        return f"<Currency(code='{self.code}', name='{self.name}', symbol='{self.symbol}')>"