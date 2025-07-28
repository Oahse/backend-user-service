from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.user import Address  # Assuming Address is already defined
from typing import List, Optional


class AddressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_address(
        self,
        user_id: int,
        street: Optional[str],
        city: Optional[str],
        state: Optional[str],
        country: Optional[str],
        post_code: Optional[str],
        kind: str
    ) -> tuple[Optional[Address], Optional[str]]:
        new_address = Address(
            user_id=user_id,
            street=street,
            city=city,
            state=state,
            country=country,
            post_code=post_code,
            kind=kind
        )
        try:
            self.db.add(new_address)
            await self.db.commit()
            await self.db.refresh(new_address)
            return new_address, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return None, f"DB error during create_address: {str(e)}"

    async def get_address_by_id(self, address_id: int) -> tuple[Optional[Address], Optional[str]]:
        try:
            result = await self.db.execute(select(Address).where(Address.id == address_id))
            address = result.scalar_one_or_none()
            return address, None
        except SQLAlchemyError as e:
            return None, f"DB error during get_address_by_id: {str(e)}"

    async def update_address(self, address_id: int, **kwargs) -> tuple[Optional[Address], Optional[str]]:
        address, err = await self.get_address_by_id(address_id)
        if err:
            return None, err
        if not address:
            return None, "Address not found"
        for key, value in kwargs.items():
            if hasattr(address, key) and value is not None:
                setattr(address, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(address)
            return address, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return None, f"DB error during update_address: {str(e)}"

    async def delete_address(self, address_id: int) -> tuple[bool, Optional[str]]:
        address, err = await self.get_address_by_id(address_id)
        if err:
            return False, err
        if not address:
            return False, "Address not found"
        try:
            await self.db.delete(address)
            await self.db.commit()
            return True, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return False, f"DB error during delete_address: {str(e)}"

    async def list_addresses(self, user_id: Optional[int] = None, skip: int = 0, limit: int = 100
                             ) -> tuple[List[Address], Optional[str]]:
        try:
            query = select(Address)
            if user_id:
                query = query.where(Address.user_id == user_id)
            query = query.offset(skip).limit(limit)
            result = await self.db.execute(query)
            addresses = result.scalars().all()
            return addresses, None
        except SQLAlchemyError as e:
            return [], f"DB error during list_addresses: {str(e)}"
