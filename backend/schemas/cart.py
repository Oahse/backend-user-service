from uuid import UUID
from datetime import datetime
from typing import Optional, List
from .products import ProductRead, ProductVariantRead
from pydantic import BaseModel


# ----------- CartItem Schemas -----------

class CartItemBase(BaseModel):
    product_id: UUID
    product_variant_id: UUID
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItemRead(CartItemBase):
    id: UUID
    cart_id: UUID
    created_at: datetime
    updated_at: datetime
    product: Optional[ProductRead] = None  # You can replace with ProductRead if typed
    variant: Optional[ProductVariantRead] = None  # Same here

    class Config:
        from_attributes = True


# ----------- Cart Schemas -----------

class CartBase(BaseModel):
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = None


class CartCreate(CartBase):
    pass


class CartRead(CartBase):
    id: UUID
    items: List[CartItemRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
