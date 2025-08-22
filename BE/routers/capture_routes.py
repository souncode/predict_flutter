from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils.capture_handler import capture_all
import subprocess

capture_router = APIRouter()

@capture_router.get("/scancamera")
def scan_camera():
    try:
        process = subprocess.run(["python", "check_and_save_cameras.py"], capture_output=True, text=True)
        if process.returncode == 0:
            return JSONResponse(content={"status": "success", "output": process.stdout.strip()})
        else:
            return JSONResponse(status_code=500, content={"status": "error", "output": process.stderr.strip()})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "exception", "output": str(e)})

@capture_router.get("/capture")
async def capture_route():
    return await capture_all()
