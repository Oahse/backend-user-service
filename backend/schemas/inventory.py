from typing import Optional
from pydantic import BaseModel
from uuid import UUID
# ---------- Inventory Schemas ----------

class InventoryBase(BaseModel):
    name: str
    location: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    pass

class InventoryRead(InventoryBase):
    id: UUID

    class Config:
        from_attributes = True
