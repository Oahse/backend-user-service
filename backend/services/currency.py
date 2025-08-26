from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from sqlalchemy.exc import NoResultFound
from typing import List, Optional
from uuid import UUID
from models.currency import Currency
from schemas.currency import CurrencyCreate, CurrencyUpdate


class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Currency]:
        result = await self.db.execute(select(Currency))
        return result.scalars().all()

    async def get_by_id(self, currency_id: UUID) -> Optional[Currency]:
        result = await self.db.execute(select(Currency).where(Currency.id == currency_id))
        currency = result.scalars().first()
        return currency

    async def create(self, currency_in: CurrencyCreate) -> Currency:
        currency = Currency(**currency_in.dict())
        self.db.add(currency)
        await self.db.commit()
        await self.db.refresh(currency)
        return currency

    async def update(self, currency_id: UUID, currency_in: CurrencyUpdate) -> Optional[Currency]:
        currency = await self.get_by_id(currency_id)
        if not currency:
            return None
        for field, value in currency_in.dict(exclude_unset=True).items():
            setattr(currency, field, value)
        await self.db.commit()
        await self.db.refresh(currency)
        return currency

    async def delete(self, currency_id: UUID) -> bool:
        currency = await self.get_by_id(currency_id)
        if not currency:
            return False
        await self.db.delete(currency)
        await self.db.commit()
        return True
