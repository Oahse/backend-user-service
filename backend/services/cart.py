from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from models.cart import Cart, CartItem
from schemas.cart import CartCreate, CartItemCreate


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, cart_id: UUID) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart)
            .options(
                joinedload(Cart.items)
                .joinedload(CartItem.product_variant),
                joinedload(Cart.items)
                .joinedload(CartItem.product)
            )
            .where(Cart.id == cart_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_or_ip(self, user_id: Optional[UUID], ip_address: Optional[str]) -> Optional[Cart]:
        stmt = select(Cart)

        if user_id:
            stmt = stmt.where(Cart.user_id == user_id)
        elif ip_address:
            stmt = stmt.where(Cart.ip_address == ip_address)
        else:
            return None

        stmt = stmt.options(joinedload(Cart.items))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, cart_in: CartCreate) -> Cart:
        cart = Cart(user_id=cart_in.user_id, ip_address=cart_in.ip_address)
        self.db.add(cart)
        try:
            await self.db.commit()
            await self.db.refresh(cart)
            return cart
        except Exception as e:
            await self.db.rollback()
            raise e

    async def add_item(self, cart_id: UUID, item_in: CartItemCreate) -> CartItem:
        # Check if item already exists in the cart
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_variant_id == item_in.product_variant_id
            )
        )
        existing_item = result.scalar_one_or_none()

        try:
            if existing_item:
                existing_item.quantity += item_in.quantity
                await self.db.commit()
                await self.db.refresh(existing_item)
                return existing_item

            # If item doesn't exist, create a new one
            new_item = CartItem(
                cart_id=cart_id,
                product_id=item_in.product_id,
                product_variant_id=item_in.product_variant_id,
                quantity=item_in.quantity
            )
            self.db.add(new_item)
            await self.db.commit()
            await self.db.refresh(new_item)
            return new_item
        except Exception as e:
            await self.db.rollback()
            raise e

    async def remove_item(self, item_id: UUID) -> bool:
        result = await self.db.execute(select(CartItem).where(CartItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            return False

        try:
            await self.db.delete(item)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e

    async def clear_cart(self, cart_id: UUID) -> None:
        try:
            await self.db.execute(
                CartItem.__table__.delete().where(CartItem.cart_id == cart_id)
            )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_cart(self, cart_id: UUID) -> bool:
        cart = await self.get_by_id(cart_id)
        if not cart:
            return False
        try:
            await self.db.delete(cart)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e
