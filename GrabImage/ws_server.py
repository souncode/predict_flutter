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
import subprocess
import time
import psutil

from MvCameraControl_class import *

app = FastAPI()


model_paths = ["models/model1.pt", "models/model2.pt", "models/model3.pt","models/model3.pt","models/model3.pt","models/model3.pt"]
models = [YOLO(p) for p in model_paths]

cams = []
cams_lock = Lock()
clients = set()
print(f"🔌 Số lượng client WebSocket đang kết nối: {len(clients)}")
camera_configs = []
issaveimage = False
save_path = "images"


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
                    "cameras": cam_count,
                    "system_ok": True  # Hoặc logic kiểm tra khác
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
    asyncio.create_task(ping_clients_loop())
    asyncio.create_task(send_system_status())
       

@app.websocket("/ws/image")
async def websocket_image(websocket: WebSocket):
    await websocket.accept()
    for ws in list(clients):
        if ws.client.host == websocket.client.host and ws.client.port == websocket.client.port:
            clients.discard(ws)

    clients.add(websocket)
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
            model_index = cam_info["model_index"]

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

                    # ✅ Chạy YOLO
                    results_yolo = models[model_index](np_img)[0]

                    # ✅ Vẽ bounding box
                    for box in results_yolo.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = f"{results_yolo.names[cls]} {conf:.2f}"

                        cv2.rectangle(np_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(np_img, label, (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # ✅ Gửi ảnh đã vẽ
                    _, buffer = cv2.imencode('.jpg', np_img)
                    base64_img = base64.b64encode(buffer).decode()

                    await websocket.send_json({
                        "camera": cam_name,
                        "image": base64_img,
                        "avg_processing": processing_ms
                    })

                    print(f"✅ Sent image from {cam_name} to {websocket.client.host}:{websocket.client.port}")

                except Exception as e:
                    print(f"❌ Lỗi xử lý ảnh {cam_name}: {e}")

                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)
async def handle_capture_and_send(websocket: WebSocket):
    with cams_lock:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_time_ms = 0  # ✅ Tổng thời gian xử lý toàn bộ camera

        for cam_info in cams:
            cam = cam_info["cam"]
            cam_name = cam_info["name"]
            model_index = cam_info["model_index"]

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
                    start_time = time.time()
                    results_yolo = models[model_index](np_img)[0]

                    # 🖍️ Vẽ bounding box
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

                    await websocket.send_json({
                        "type": "camera_image",
                        "camera": cam_name,
                        "image": base64_img,
                        "avg_processing": processing_time_ms
                    })

                    print(f"✅ Sent image from {cam_name} ({processing_time_ms}ms) to {websocket.client.host}:{websocket.client.port}")

                except Exception as e:
                    print(f"❌ Lỗi xử lý ảnh {cam_name}: {e}")

                finally:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)

        try:
            await websocket.send_json({
                "type": "processing_summary",
                "total_processing": round(total_time_ms, 2),
                "total_cameras": len(cams)
            })
            print(f"📊 Tổng thời gian xử lý toàn bộ camera: {round(total_time_ms, 2)}ms")
        except Exception as e:
            print(f"⚠️ Lỗi gửi tổng thời gian xử lý tới client: {e}")

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