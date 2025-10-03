from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from core.database import get_db
from services.cart import CartService
from schemas.cart import CartCreate, CartItemCreate
from core.utils.response import Response

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])

# --- Get cart by user_id or IP address ---
@router.get("/")
async def get_cart(
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = CartService(db)
    try:
        res = await service.get_by_user_or_ip(user_id=user_id, ip_address=ip_address)
        if res is None:
            return Response(message="Cart not found", code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Get cart by cart ID ---
@router.get("/{cart_id}")
async def get_cart_by_id(cart_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        res = await service.get_by_id(cart_id)
        if res is None:
            return Response(message=f"Cart with id '{cart_id}' not found", code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Create a new cart ---
@router.post("/")
async def create_cart(cart_in: CartCreate, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        res = await service.create(cart_in)
        return Response(data=res.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Add item to cart ---
@router.post("/{cart_id}/items")
async def add_item_to_cart(cart_id: UUID, item_in: CartItemCreate, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        res = await service.add_item(cart_id, item_in)
        return Response(data=res.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Remove item from cart ---
@router.delete("/items/{item_id}")
async def remove_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        res = await service.remove_item(item_id)
        if not res:
            return Response(message=f"Cart item with id '{item_id}' not found", code=404)
        return Response(message="Cart item deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Clear all items from cart ---
@router.delete("/{cart_id}/clear")
async def clear_cart(cart_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        await service.clear_cart(cart_id)
        return Response(message="Cart cleared successfully")
    except Exception as e:
        return Response(success=False, data=str(e), code=500)


# --- Delete cart entirely ---
@router.delete("/{cart_id}")
async def delete_cart(cart_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CartService(db)
    try:
        res = await service.delete_cart(cart_id)
        if not res:
            return Response(message=f"Cart with id '{cart_id}' not found", code=404)
        return Response(message="Cart deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, data=str(e), code=500)
