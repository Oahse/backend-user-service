from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import List
from uuid import UUID

router = APIRouter(prefix="/ws/inventory", tags=["Inventory WebSocket"])

inventory_subscribers: List[WebSocket] = []

@router.websocket("/")
async def inventory_ws(websocket: WebSocket):
    await websocket.accept()
    inventory_subscribers.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Optional keep-alive
    except WebSocketDisconnect:
        inventory_subscribers.remove(websocket)

# Broadcast to all connected clients when inventory changes

# Broadcast to all connected clients when inventory changes
async def broadcast_inventory_update(product_id: str,inventory_id:str, new_stock: int):
    for ws in inventory_subscribers:
        try:
            await ws.send_json({
                "event": "inventory-update",
                "product_id": product_id,
                'inventory_id': inventory_id,
                "stock": new_stock
            })
        except Exception:
            inventory_subscribers.remove(ws)