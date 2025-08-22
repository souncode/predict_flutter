# main.py
from fastapi import FastAPI
from routers.websocket_routes import websocket_router
from routers.capture_routes import capture_router
from utils.camera_initializer import load_camera_config, init_all_cameras_from_config
from utils.system_status import send_system_status, ping_clients_loop
import asyncio
from utils.shared import cams_lock

app = FastAPI()

@app.on_event("startup")
def startup_event():
    load_camera_config()
    with cams_lock:
        init_all_cameras_from_config()
    asyncio.create_task(send_system_status())
    asyncio.create_task(ping_clients_loop())

app.include_router(websocket_router)
app.include_router(capture_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
