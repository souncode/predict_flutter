from fastapi import APIRouter, WebSocket
from utils.shared import clients
from utils.capture_handler import handle_capture_and_send

websocket_router = APIRouter()

@websocket_router.websocket("/ws/image")
async def websocket_image(websocket: WebSocket):
    await websocket.accept()
    for ws in list(clients):
        if ws.client.host == websocket.client.host and ws.client.port == websocket.client.port:
            clients.discard(ws)

    clients.add(websocket)
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    print(f"🟢 WebSocket client connected: {client_info} (Total: {len(clients)})")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"📨 Received from client: {message}")
            if message == "capture":
                await handle_capture_and_send(websocket)
    except Exception as e:
        print(f"🔴 WebSocket client disconnected: {client_info} ({e})")
    finally:
        clients.discard(websocket)
        print(f"🟡 Client removed: {client_info} (Remaining: {len(clients)})")
