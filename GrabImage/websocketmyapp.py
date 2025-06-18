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
camera_configs = []

def load_camera_config():
    global camera_configs
    with open("CameraConfig.json", "r") as f:
        data = json.load(f)
        camera_configs = data["cameras"]

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
            await asyncio.sleep(1)
    except Exception as e:
        print(f"🔴 WebSocket client disconnected: {client_info} ({e})")
    finally:
        clients.discard(websocket)
        print(f"🟡 Client removed: {client_info} (Remaining: {len(clients)})")


@app.get("/capture")
async def capture_all():
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
            if ret == 0 and stOutFrame.pBufAddr:
                try:
                    width = stOutFrame.stFrameInfo.nWidth
                    height = stOutFrame.stFrameInfo.nHeight
                    buf_len = stOutFrame.stFrameInfo.nFrameLen

                    buf_type = (c_ubyte * buf_len)
                    buf = buf_type.from_address(addressof(stOutFrame.pBufAddr.contents))
                    np_img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))

                    # Encode ảnh sang base64
                    _, buffer = cv2.imencode('.jpg', np_img)
                    base64_img = base64.b64encode(buffer).decode()

                    data = {
                        "camera": cam_name,
                        "image": base64_img
                    }

                    # Gửi ảnh qua WebSocket
                    for ws in list(clients):
                        try:
                            await ws.send_json(data)
                            print(f"📤 Gửi ảnh từ {cam_name} đến {ws.client.host}:{ws.client.port}")
                        except Exception as e:
                            print(f"⚠️ Lỗi gửi ảnh đến {ws.client.host}:{ws.client.port} — {e}")
                            clients.remove(ws)

                    # Lưu ảnh
                    filename = f"{cam_name}_{timestamp}.jpg"
                    cv2.imwrite(filename, np_img)
                    print(f"✅ Ảnh từ {cam_name} đã lưu và gửi WebSocket")

                    results.append(filename)

                except Exception as e:
                    print(f"❌ Lỗi xử lý ảnh {cam_name}: {e}")
                    results.append(None)
                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)
            else:
                print(f"❌ Lỗi lấy buffer {cam_name}: mã lỗi {hex(ret)}")
                results.append(None)

        return JSONResponse(content={"images": results})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "websocketmyapp:app",
        host="0.0.0.0",
        port=8000,
        reload=True  
    )