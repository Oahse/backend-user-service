from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from services.currency import CurrencyService
from schemas.currency import CurrencyCreate, CurrencyRead, CurrencyUpdate
from core.utils.response import Response

router = APIRouter(prefix="/api/v1/currencies", tags=["Currencies"])


@router.get("/")
async def get_all_currencies(db: AsyncSession = Depends(get_db)):
    service = CurrencyService(db)
    try:
        currencies = await service.get_all()
        return Response(data=[c.to_dict() for c in currencies])
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


@router.get("/{currency_id}")
async def get_currency_by_id(currency_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CurrencyService(db)
    try:
        currency = await service.get_by_id(currency_id)
        if currency is None:
            return Response(message=f"Currency with id '{currency_id}' not found.", code=404)
        return Response(data=currency.to_dict())
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


@router.post("/")
async def create_currency(currency_in: CurrencyCreate, db: AsyncSession = Depends(get_db)):
    service = CurrencyService(db)
    try:
        currency = await service.create(currency_in)
        return Response(data=currency.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


@router.put("/{currency_id}")
async def update_currency(currency_id: UUID, currency_in: CurrencyUpdate, db: AsyncSession = Depends(get_db)):
    service = CurrencyService(db)
    try:
        updated_currency = await service.update(currency_id, currency_in)
        if updated_currency is None:
            return Response(message=f"Currency with id '{currency_id}' not found.", code=404)
        return Response(data=updated_currency.to_dict())
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


@router.delete("/{currency_id}")
async def delete_currency(currency_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CurrencyService(db)
    try:
        success = await service.delete(currency_id)
        if not success:
            return Response(message=f"Currency with id '{currency_id}' not found.", code=404)
        return Response(message="Currency deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)
