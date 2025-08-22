import threading
from CameraParams_header import MV_FRAME_OUT
from utils.shared import cams, clients, models, cams_lock, issaveimage, save_path
from datetime import datetime
import base64, cv2, time, os
from ctypes import *
import numpy as np
import asyncio


from fastapi import FastAPI, WebSocket


async def handle_capture_and_send(websocket: WebSocket):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def process_camera_thread(cam_info):
        cam = cam_info["cam"]
        cam_name = cam_info["name"]
        model_index = cam_info["model_index"]
        trigger_mode = cam_info.get("trigger_mode", "off").lower()
        trigger_source = cam_info.get("trigger_source", "software").lower()

        def camera_task():
            # 🧵 Thread ID
            thread_id = threading.get_ident()

            # Trigger software nếu cần
            if trigger_mode == "on" and trigger_source == "software":
                trigger_ret = cam.MV_CC_SetCommandValue("TriggerSoftware")
                if trigger_ret != 0:
                    print(f"⚠️ {cam_name} - TriggerSoftware thất bại: {trigger_ret}")
                    return None

                time.sleep(0.02)  # Đợi ảnh được capture

            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))

            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1500)
            if ret != 0 or not stOutFrame.pBufAddr:
                print(f"❌ {cam_name} - Không lấy được buffer ảnh (ret={ret})")
                return None

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

                # 🏷️ Vẽ thread ID
                cv2.putText(np_img, f"Thread: {thread_id}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                processing_time_ms = round((time.time() - start_time) * 1000, 2)

                _, buffer = cv2.imencode('.jpg', np_img)
                base64_img = base64.b64encode(buffer).decode()

                return {
                    "camera": cam_name,
                    "image": base64_img,
                    "avg_processing": processing_time_ms,
                    "thread_id": thread_id
                }

            except Exception as e:
                print(f"❌ Lỗi xử lý ảnh {cam_name}: {e}")
                return None

            finally:
                cam.MV_CC_FreeImageBuffer(stOutFrame)

        # Gọi hàm blocking trong thread riêng
        return await asyncio.to_thread(camera_task)

    # 🧠 Xử lý nhiều camera song song
    with cams_lock:
        tasks = [process_camera_thread(cam_info) for cam_info in cams]
    results = await asyncio.gather(*tasks)

    total_time = 0
    for result in results:
        if result:
            total_time += result["avg_processing"]
            try:
                await websocket.send_json({
                    "type": "camera_image",
                    "camera": result["camera"],
                    "image": result["image"],
                    "avg_processing": result["avg_processing"]
                })
                print(f"📸 {result['camera']} processed by Thread {result['thread_id']} in {result['avg_processing']}ms")
            except Exception as e:
                print(f"⚠️ Lỗi gửi ảnh: {e}")

    # Tổng kết
    try:
        await websocket.send_json({
            "type": "processing_summary",
            "total_processing": round(total_time, 2),
            "total_cameras": len([r for r in results if r])
        })
        print(f"📊 Tổng thời gian xử lý toàn bộ camera: {round(total_time, 2)}ms")
    except Exception as e:
        print(f"⚠️ Lỗi gửi tổng thời gian xử lý tới client: {e}")


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
