import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base  # Assuming this is your declarative base
from models.products import Product, ProductVariant


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "ip_address": self.ip_address,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Cart ID={self.id} UserID={self.user_id} IP={self.ip_address}>"


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "cart_id": str(self.cart_id),
            "product_id": str(self.product_id),
            "product_variant_id": str(self.product_variant_id),
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "product": self.product.to_dict() if self.product else None,
            "variant": self.product_variant.to_dict() if self.product_variant else None,
        }

    def __repr__(self):
        return (
            f"<CartItem ID={self.id} CartID={self.cart_id} "
            f"ProductVariantID={self.product_variant_id} Quantity={self.quantity}>"
        )
