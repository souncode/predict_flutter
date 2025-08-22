from fastapi import FastAPI, WebSocket
import threading
import asyncio
from fastapi.responses import JSONResponse
from datetime import datetime
from ctypes import *
import numpy as np
import cv2
import os
import json
import asyncio
from threading import Lock
import base64
from ultralytics import YOLO
import subprocess
import time
import psutil
import logging
import platform
import ctypes
from ctypes import cdll, c_ubyte, byref
from MvCameraControl_class import *
import threading
import asyncio

app = FastAPI()


PixelType_Gvsp_Mono8        = 0x01080001
PixelType_Gvsp_BayerRG8     = 0x01080009
PixelType_Gvsp_RGB8_Packed  = 0x02180014

model_paths = ["models/model1.pt", "models/model2.pt", "models/model3.pt","models/model3.pt","models/model3.pt","models/model3.pt"]
models = [YOLO(p) for p in model_paths]

cams = []
cams_lock = Lock()
clients = set()
print(f"🔌 Số lượng client WebSocket đang kết nối: {len(clients)}")
camera_configs = []
issaveimage = False
CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

if platform.system() == "Windows":
    libc = cdll.msvcrt
else:
    libc = cdll.LoadLibrary("libc.so.6")

async def send_system_status():
    while True:
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage('/').percent
        cam_count = len(cams)
        ram = psutil.virtual_memory().percent
        try:
            for ws in list(clients):
                await ws.send_json({
                    "type": "system_status",
                    "cpu": cpu,
                    "storage": disk,
                    "ram": ram, 
                    "system_ok": True, 
                    "active": cam_count,
                    "total": len(camera_configs), # 
                })
        except Exception as e:
            clients.discard(ws)
        await asyncio.sleep(5)

def load_camera_config():
  
    global camera_configs,issaveimage, save_path
    with open("CameraConfig.json", "r") as f:
        data = json.load(f)
        camera_configs = data["cameras"]
        issaveimage = data.get("issave", False)
        save_path = data.get("save_path", "images")
        


def decode_model_name(model_bytes):
    return bytes(model_bytes).split(b'\x00')[0].decode(errors='ignore').strip()



def load_config(path="CameraConfig.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def find_device_by_serial_or_ip(dev_list, target_serial=None, target_ip=None):
    for i in range(dev_list.nDeviceNum):
        dev_info = cast(dev_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        serial, ip = None, None

        if dev_info.nTLayerType == MV_GIGE_DEVICE:
            raw = bytes(dev_info.SpecialInfo.stGigEInfo.chSerialNumber)
            serial = raw.decode("utf-8", errors="ignore").strip("\x00")
            nip1 = (dev_info.SpecialInfo.stGigEInfo.nCurrentIp >> 24) & 0xFF
            nip2 = (dev_info.SpecialInfo.stGigEInfo.nCurrentIp >> 16) & 0xFF
            nip3 = (dev_info.SpecialInfo.stGigEInfo.nCurrentIp >> 8) & 0xFF
            nip4 = dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xFF
            ip = f"{nip1}.{nip2}.{nip3}.{nip4}"
        elif dev_info.nTLayerType == MV_USB_DEVICE:
            raw = bytes(dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber)
            serial = raw.decode("utf-8", errors="ignore").strip("\x00")

        print(f"🔎 Camera {i+1}: serial={serial}, ip={ip}")
        if (target_serial and serial == target_serial) or (target_ip and ip == target_ip):
            return dev_info
    return None

def init_all_cameras_from_config(config_path="CameraConfig.json"):
    global cams
    cams.clear()

    config = load_config(config_path)
    dev_list = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, dev_list)
    if ret != 0 or dev_list.nDeviceNum == 0:
        print("❌ Không tìm thấy camera nào")
        return []

    for cam_cfg in config["cameras"]:
        dev_info = find_device_by_serial_or_ip(
            dev_list,
            target_serial=cam_cfg.get("serial"),
            target_ip=cam_cfg.get("ip")
        )
        if dev_info is None:
            print(f"❌ Không tìm thấy {cam_cfg['name']}")
            continue

        cam = MvCamera()
        if cam.MV_CC_CreateHandle(dev_info) != 0:
            continue
        if cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
            cam.MV_CC_DestroyHandle()
            continue

        # GIGE optimize
        if dev_info.nTLayerType == MV_GIGE_DEVICE:
            pkt = cam.MV_CC_GetOptimalPacketSize()
            if int(pkt) > 0:
                cam.MV_CC_SetIntValue("GevSCPSPacketSize", pkt)

        cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_BayerRG8)
        cam.MV_CC_SetEnumValue("TriggerMode", 1)
        cam.MV_CC_SetEnumValue("TriggerSource", 7)
        cam.MV_CC_SetFloatValue("ExposureTime", float(cam_cfg.get("exposure_time", 5000)))
        cam.MV_CC_SetFloatValue("Gain", float(cam_cfg.get("gain", 10.0)))
        cam.MV_CC_StartGrabbing()

        cams.append({
            "cam": cam,
            "name": cam_cfg["name"],
            "cfg": cam_cfg,
            "dev_info": dev_info
        })

    return cams

def save_bgr(bgr, save_path, prefix, issave=True):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefix}_{ts}.jpg"
    filepath = os.path.join(save_path, filename)
    if issave:
        cv2.imwrite(filepath, bgr)
        print(f"💾 Saved {filepath}")
    return filepath

def capture_image(cam_info, issave=True, save_path=CAPTURE_DIR):
    """
    Chụp ảnh từ MvCamera bằng TriggerSoftware + GetOneFrameTimeout
    """
    try:
        cam = cam_info["cam"]
        name = cam_info["name"]

        # Lấy payload size
        intval = MVCC_INTVALUE()
        memset(byref(intval), 0, sizeof(intval))
        cam.MV_CC_GetIntValue("PayloadSize", intval)
        payload = int(intval.nCurValue)

        buf = (c_ubyte * payload)()
        frame_info = MV_FRAME_OUT_INFO_EX()

        # Trigger phần mềm
        cam.MV_CC_SetCommandValue("TriggerSoftware")
        ret = cam.MV_CC_GetOneFrameTimeout(byref(buf), payload, frame_info, 1000)
        if ret != 0:
            print(f"❌ {name}: GetOneFrameTimeout fail (ret={ret})")
            return None

        # Convert RAW -> BGR
        bgr = decode_frame(buf, frame_info, payload)

        # Save file
        filepath = save_bgr(bgr, save_path, prefix=name, issave=issave)

        # Encode base64 để trả về WS
        _, buffer = cv2.imencode(".jpg", bgr)
        b64 = base64.b64encode(buffer).decode("utf-8")
        return b64

    except Exception as e:
        print(f"⚠️ Lỗi capture {cam_info['name']}: {e}")
        return None

def decode_frame(buf, frame_info, payload):
    w, h, pxtype = frame_info.nWidth, frame_info.nHeight, frame_info.enPixelType
    size_used = frame_info.nFrameLen
    if size_used <= 0 or size_used > payload:
        size_used = w * h * (3 if pxtype == PixelType_Gvsp_RGB8_Packed else 1)
    np_flat = np.frombuffer(buf, dtype=np.uint8, count=size_used)

    if pxtype == PixelType_Gvsp_RGB8_Packed:
        return np_flat.reshape((h, w, 3))
    elif pxtype == PixelType_Gvsp_Mono8:
        gray = np_flat.reshape((h, w))
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    else:
        bayer = np_flat.reshape((h, w))
        return cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2BGR)

@app.on_event("startup")
def startup_event():
    with cams_lock:
        init_all_cameras_from_config()
      
    asyncio.create_task(ping_clients_loop())
    asyncio.create_task(send_system_status())
       

from fastapi import WebSocket, WebSocketDisconnect

import json

@app.websocket("/ws/image")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'capture':
                with cams_lock:
                    if not cams:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "No camera"
                        }))
                        continue

                for cam_info in cams:
                    start_time = time.time()
                    b64 = capture_image(cam_info)
                    processing_time_ms = (time.time() - start_time) * 1000

                    if b64:
                        msg = {
                            "type": "camera_image",
                            "camera": cam_info["name"],
                            "image": str(b64),   # ép chắc chắn là string
                            "avg_processing": float(processing_time_ms)
                        }
                        # 🔑 dùng send_text + json.dumps thay vì send_json
                        await websocket.send_text(json.dumps(msg))

            else:
                await websocket.send_text(json.dumps({
                    "type": "info",
                    "message": f"Server nhận: {data}"
                }))

    except WebSocketDisconnect:
        clients.discard(websocket)
    except Exception as e:
        clients.discard(websocket)
        print(f"⚠️ WS error: {e}")


async def run_in_thread(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)
import ctypes
import cv2
import numpy as np
import base64
from ctypes import byref, c_ubyte


from MvCameraControl_class import *



async def ping_clients_loop():
    while True:
        await asyncio.sleep(10)
        for ws in list(clients):
            try:
                await ws.send_json({"ping": "ping"})
            except Exception as e:
                print(f"⚠️ Client do not response ping → Delete: {e}")
                clients.discard(ws)

@app.get("/scancamera")
def scan_camera():
    try:
        process = subprocess.run(
            ["python", "check_and_save_cameras.py"], 
            capture_output=True,
            text=True
        )

        if process.returncode == 0:
            return JSONResponse(content={
                "status": "success",
                "output": process.stdout.strip()
            })
        else:
            return JSONResponse(status_code=500, content={
                "status": "error",
                "output": process.stderr.strip()
            })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "exception",
            "output": str(e)
        })


@app.get("/capture")
async def capture_all():
    try:
        with cams_lock:
            if not cams:
                return JSONResponse(status_code=500, content={"error": "No active camera found"})

            results = []
            total_time_ms = 0  
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for cam_info in cams:
                cam = cam_info["cam"]
                model_index = 1
                cam_name = cam_info["name"]

                stOutFrame = MV_FRAME_OUT()
                memset(byref(stOutFrame), 0, sizeof(stOutFrame))

                ret = cam.MV_CC_GetImageBuffer(stOutFrame, 500)
                if ret != 0 or not stOutFrame.pBufAddr:
                    print(f"❌ Không lấy được ảnh từ {cam_name}")
                    results.append(None)
                    continue

                try:
                    width = stOutFrame.stFrameInfo.nWidth
                    height = stOutFrame.stFrameInfo.nHeight
                    buf_len = stOutFrame.stFrameInfo.nFrameLen

                    buf_type = (c_ubyte * buf_len)
                    buf = buf_type.from_address(addressof(stOutFrame.pBufAddr.contents))
                    np_img_flat = np.frombuffer(buf, dtype=np.uint8)

                    expected_rgb = width * height * 3
                    expected_gray = width * height

                    if buf_len == expected_rgb:
                        np_img = np_img_flat.reshape((height, width, 3))
                    elif buf_len == expected_gray:
                        gray_img = np_img_flat.reshape((height, width))
                        np_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
                    else:
                        raise ValueError(f"❌ Không xác định được định dạng ảnh từ {cam_name}: buf_len={buf_len}, w={width}, h={height}")

                    start_time = time.time()
                    results_yolo = models[model_index](np_img)[0]
                    for box in results_yolo.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = f"{results_yolo.names[cls]} {conf:.2f}"

                        cv2.rectangle(np_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(np_img, label, (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    processing_time_ms = round((time.time() - start_time) * 1000, 2)
                    total_time_ms += processing_time_ms

                    _, buffer = cv2.imencode('.jpg', np_img)
                    base64_img = base64.b64encode(buffer).decode()

                    data = {
                        "type": "camera_image",
                        "camera": cam_name,
                        "image": base64_img,
                        "avg_processing": processing_time_ms
                    }

                    for ws in list(clients):
                        try:
                            await asyncio.wait_for(ws.send_json(data), timeout=1.0)
                            print(f"📤 Sent from {cam_name} ({processing_time_ms}ms) to {getattr(ws.client, 'host', 'unknown')}:{getattr(ws.client, 'port', 'unknown')}")
                        except Exception as e:
                            print(f"⚠️ Sent to WebSocket client fail: {e}")
                            clients.discard(ws)

                    # 💾 Lưu ảnh nếu bật
                    if issaveimage:
                        os.makedirs(save_path, exist_ok=True)
                        filename = os.path.join(save_path, f"{cam_name}_{timestamp}.jpg")
                        cv2.imwrite(filename, np_img)
                        print(f"✅ Image from {cam_name} saved - {filename}")
                    else:
                        filename = None

                    results.append(filename)

                except Exception as e:
                    print(f"❌ Error when predict {cam_name}: {e}")
                    results.append(None)

                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)

         
            for ws in list(clients):
                try:
                    await asyncio.wait_for(ws.send_json({
                    "type": "processing_summary",
                    "total_processing": round(total_time_ms, 2),
                    "total_cameras": len(cams)   
                }), timeout=1.0)
                    print(f" total_processing camera: {round(total_time_ms, 2)}ms")
                except Exception as e:
                    print(f"⚠️ Error when sent processing time: {e}")
                    clients.discard(ws)

            return JSONResponse(content={"images": results})

    except Exception as e:
        print(f"🔥 Lỗi trong /capture: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ws_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  
    )