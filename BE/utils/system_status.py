import asyncio
import psutil
from utils.shared import clients, cams, camera_configs

async def send_system_status():
    while True:
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage('/').percent
        cam_count = len(cams)
        ram = psutil.virtual_memory().percent

        for ws in list(clients):
            try:
                await ws.send_json({
                    "type": "system_status",
                    "cpu": cpu,
                    "storage": disk,
                    "ram": ram,
                    "system_ok": True,
                    "active": cam_count,
                    "total": len(camera_configs),
                })
            except Exception:
                clients.discard(ws)
        await asyncio.sleep(5)

async def ping_clients_loop():
    while True:
        await asyncio.sleep(10)
        for ws in list(clients):
            try:
                await ws.send_json({"ping": "ping"})
            except Exception:
                clients.discard(ws)
