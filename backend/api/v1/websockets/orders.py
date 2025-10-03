from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from services.orders import OrderService, UUID
from core.database import get_db  # Make sure this returns AsyncSession
import json

router = APIRouter(prefix="/ws/orders", tags=["Orders-WebSockets"])

# Store active WebSocket connections
connections: Dict[UUID, WebSocket] = {}

# --- Notify Function --- #
async def notify_order_update(user_id: UUID, status: str):
    if user_id in connections:
        await connections[user_id].send_json({"order-status": status})

async def update_order_in_background(order_id: UUID, status: str):
    async with get_db() as db:  # Manual DB session
        service = OrderService(db)
        await service.update_order_status(order_id, status)

# --- WebSocket Routes --- #
@router.websocket("/order-status/{user_id}")
async def order_status_ws(websocket: WebSocket, user_id: UUID):
    await websocket.accept()
    connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # You must send data as JSON string from the client side
            payload = json.loads(data)

            # Extract info from payload
            order_id = UUID(payload.get("order_id"))
            status = payload.get("status")

            # Run background task to update DB
            await update_order_in_background(order_id, status)

            await notify_order_update(user_id, status)
    except WebSocketDisconnect:
        connections.pop(user_id, None)


