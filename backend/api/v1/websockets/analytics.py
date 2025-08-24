# ws/admin_dashboard.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(prefix="/ws/admin-dashboard", tags=["Orders-WebSockets"])

# List of connected admin dashboard clients
admin_clients: List[WebSocket] = []

@router.websocket("/")
async def admin_dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    admin_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Optional keep-alive
    except WebSocketDisconnect:
        admin_clients.remove(websocket)

# Broadcast helper
async def broadcast_to_admins(payload: dict):
    for client in admin_clients:
        await client.send_json(payload)


# When a new order is placed
# async def notify_new_order(order_id: str, total: float):
#     await broadcast_to_admins({
#         "type": "new_order",
#         "order_id": order_id,
#         "total": total,
#     })

# When a new user visits (traffic)
async def notify_new_visitor(session_id: str):
    await broadcast_to_admins({
        "type": "new_visitor",
        "session_id": session_id,
    })

# When a cart is abandoned
async def notify_cart_abandonment(user_id: str, cart_value: float):
    await broadcast_to_admins({
        "type": "cart_abandoned",
        "user_id": user_id,
        "cart_value": cart_value,
    })
