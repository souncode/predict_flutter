from fastapi import FastAPI, WebSocket
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

from MvCameraControl_class import *

app = FastAPI()

model_paths = ["models/model1.pt", "models/model2.pt", "models/model3.pt"]
models = [YOLO(p) for p in model_paths]

cams = []
cams_lock = Lock()
clients = set()
print(f"🔌 Số lượng client WebSocket đang kết nối: {len(clients)}")
camera_configs = []
issaveimage = False
save_path = "images"
def load_camera_config():
  
    global camera_configs,issaveimage, save_path
    with open("CameraConfig.json", "r") as f:
        data = json.load(f)
        camera_configs = data["cameras"]
        issaveimage = data.get("issaveimage", False)
        save_path = data.get("save_path", "images")
        

def decode_model_name(model_bytes):
    return bytes(model_bytes).split(b'\x00')[0].decode(errors='ignore').strip()

def init_all_cameras_from_config():
    global cams
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ Không tìm thấy camera")
        return

    print(f"✅ Tìm thấy {deviceList.nDeviceNum} camera")
    cams.clear()

    for cfg in camera_configs:
        serial_target = cfg["serial"].encode()
        found = False

        for i in range(deviceList.nDeviceNum):
            device_info_ptr = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO))
            device_info = device_info_ptr.contents
            serial = decode_model_name(device_info.SpecialInfo.stGigEInfo.chSerialNumber).encode()

            if serial == serial_target:
                found = True
                cam = MvCamera()

                if cam.MV_CC_CreateHandle(device_info) != 0:
                    print(f"❌ Lỗi tạo handle cho {cfg['name']}")
                    break

                if cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
                    print(f"❌ Lỗi mở {cfg['name']}")
                    cam.MV_CC_DestroyHandle()
                    break

                # Set config
                if cfg["trigger_mode"].lower() == "off":
                    cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
                else:
                    cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)

                cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_RGB8_Packed)
                cam.MV_CC_SetFloatValue("ExposureTime", cfg["exposure_time"])
                cam.MV_CC_SetFloatValue("Gain", cfg["gain"])

                if cam.MV_CC_StartGrabbing() != 0:
                    print(f"❌ Không thể bắt đầu grabbing {cfg['name']}")
                    cam.MV_CC_CloseDevice()
                    cam.MV_CC_DestroyHandle()
                    break

                cams.append({
                    "cam": cam,
                    "model_index": cfg["model_index"],
                    "name": cfg["name"]
                })

                print(f"✅ Đã kết nối {cfg['name']}")
                break

        if not found:
            print(f"⚠️ Không tìm thấy camera serial {cfg['serial']}")

    print(f"\n📦 Tổng số camera kết nối: {len(cams)}")

@app.on_event("startup")
def startup_event():
    load_camera_config()
    with cams_lock:
        init_all_cameras_from_config()

@app.websocket("/ws/image")
async def websocket_image(websocket: WebSocket):
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    clients.add(websocket)
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
async def handle_capture_and_send(websocket: WebSocket):
    with cams_lock:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for cam_info in cams:
            cam = cam_info["cam"]
            cam_name = cam_info["name"]

            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))

            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if ret == 0 and stOutFrame.pBufAddr:
                try:
                    width = stOutFrame.stFrameInfo.nWidth
                    height = stOutFrame.stFrameInfo.nHeight
                    buf_len = stOutFrame.stFrameInfo.nFrameLen

                    buf_type = (c_ubyte * buf_len)
                    buf = buf_type.from_address(addressof(stOutFrame.pBufAddr.contents))
                    np_img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))

                    _, buffer = cv2.imencode('.jpg', np_img)
                    base64_img = base64.b64encode(buffer).decode()

                    await websocket.send_json({
                        "camera": cam_name,
                        "image": base64_img
                    })

                    print(f"✅ Sent image from {cam_name} to {websocket.client.host}:{websocket.client.port}")

                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)

@app.get("/capture")
async def capture_all():
    try:
        with cams_lock:
            if not cams:
                return JSONResponse(status_code=500, content={"error": "Không có camera nào đang hoạt động"})

            results = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for idx, cam_info in enumerate(cams):
                cam = cam_info["cam"]
                model_index = cam_info["model_index"]
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
                    np_img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))

                    _, buffer = cv2.imencode('.jpg', np_img)
                    base64_img = base64.b64encode(buffer).decode()

                    data = {
                        "camera": cam_name,
                        "image": base64_img
                    }

                    # Gửi ảnh qua WebSocket
                    for ws in list(clients):
                        try:
                            await asyncio.wait_for(ws.send_json(data), timeout=1.0)
                            print(f"📤 Gửi ảnh từ {cam_name} đến {getattr(ws.client, 'host', 'unknown')}:{getattr(ws.client, 'port', 'unknown')}")
                        except Exception as e:
                            print(f"⚠️ Lỗi gửi ảnh đến WebSocket client: {e}")
                            clients.Wdiscard(ws)

                    # Lưu ảnh
                    if issaveimage:
                        os.makedirs(save_path, exist_ok=True)
                        filename = os.path.join(save_path, f"{cam_name}_{timestamp}.jpg")
                        cv2.imwrite(filename, np_img)
                        print(f"✅ Ảnh từ {cam_name} đã lưu tại {filename}")
                    else:
                        filename = None
                    print(f"✅ Ảnh từ {cam_name} đã lưu và gửi WebSocket")

                    results.append(filename)

                except Exception as e:
                    print(f"❌ Lỗi xử lý ảnh {cam_name}: {e}")
                    results.append(None)

                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)

            return JSONResponse(content={"images": results})

    except Exception as e:
        print(f"🔥 Lỗi trong /capture: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
