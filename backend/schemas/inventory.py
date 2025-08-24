from typing import Optional
from pydantic import BaseModel, UUID4, Field
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


class InventoryProductCreate(BaseModel):
    inventory_id: UUID4
    product_id: UUID4
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True

class InventoryProductUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)

    class Config:
        from_attributes = True
