from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

import uuid

from models.products import Product, Inventory, InventoryProduct
from schemas.inventory import InventoryCreate, InventoryProductCreate, InventoryProductUpdate
# from api.v1.websockets.inventory import broadcast_inventory_update  # WebSocket broadcast


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Inventory]:
        try:
            query = select(Inventory).options(
                selectinload(Inventory.inventory_products).selectinload(InventoryProduct.product)
            )
            filters = []

            if name:
                filters.append(Inventory.name.ilike(f"%{name}%"))
            if location:
                filters.append(Inventory.location.ilike(f"%{location}%"))

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            raise RuntimeError("Failed to fetch inventories") from e

    async def get_by_id(self, inventory_id: UUID) -> Optional[Inventory]:
        result = await self.db.execute(
            select(Inventory)
            .options(
                selectinload(Inventory.inventory_products).selectinload(InventoryProduct.product)
            )
            .where(Inventory.id == inventory_id)
        )
        return result.scalar_one_or_none()

    async def create(self, inventory_in: InventoryCreate) -> Inventory:
        inventory = Inventory(
            name=inventory_in.name,
            location=inventory_in.location
        )
        self.db.add(inventory)
        try:
            await self.db.commit()
            await self.db.refresh(inventory)
            # Re-fetch inventory with related data eagerly loaded
            inventory = await self.get_by_id(inventory.id)
            return inventory
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(self, inventory_id: UUID, inventory_in: InventoryCreate) -> Optional[Inventory]:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            return None

        inventory.name = inventory_in.name
        inventory.location = inventory_in.location

        try:
            await self.db.commit()
            await self.db.refresh(inventory)
            return inventory
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, inventory_id: UUID) -> bool:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            return False

        try:
            await self.db.delete(inventory)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e


class InventoryProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        inventory_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[InventoryProduct]:
        try:
            query = select(InventoryProduct)
            if inventory_id:
                query = query.where(InventoryProduct.inventory_id == inventory_id)
            if product_id:
                query = query.where(InventoryProduct.product_id == product_id)

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RuntimeError("Failed to fetch inventory products") from e

    async def get_by_id(self, id: UUID) -> Optional[InventoryProduct]:
        result = await self.db.execute(select(InventoryProduct).where(InventoryProduct.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: InventoryProductCreate) -> InventoryProduct:
        new_item = InventoryProduct(
            inventory_id=data.inventory_id,
            product_id=data.product_id,
            quantity=data.quantity,
            low_stock_threshold=data.low_stock_threshold
        )
        self.db.add(new_item)
        try:
            await self.db.commit()
            await self.db.refresh(new_item)
            # Broadcast stock update via websocket
            # await broadcast_inventory_update(
            #     str(data.product_id), str(data.inventory_id), data.quantity
            # )  # noqa
            return new_item
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(self, id: UUID, data: InventoryProductUpdate) -> Optional[InventoryProduct]:
        item = await self.get_by_id(id)
        if not item:
            return None

        if data.quantity is not None:
            item.quantity = data.quantity
        if data.low_stock_threshold is not None:
            item.low_stock_threshold = data.low_stock_threshold

        try:
            await self.db.commit()
            await self.db.refresh(item)
            # Broadcast stock update via websocket
            # await broadcast_inventory_update(
            #     str(item.product_id), str(item.inventory_id), item.quantity
            # )  # noqa
            return item
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, id: UUID) -> bool:
        item = await self.get_by_id(id)
        if not item:
            return False

        try:
            await self.db.delete(item)
            await self.db.commit()
            # Broadcast stock update with quantity 0 since deleted
            # await broadcast_inventory_update(
            #     str(item.product_id), str(item.inventory_id), 0
            # )  # noqa
            return True
        except Exception as e:
            await self.db.rollback()
            raise e
