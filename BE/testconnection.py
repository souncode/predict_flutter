from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import numpy as np
import cv2
import os

from ctypes import *
from MvCameraControl_class import *  # SDK của camera bạn

app = FastAPI()

# Giả sử bạn đã tạo danh sách camera từ trước
cams = []  # Gán camera object (MvCamera) sau khi mở

def int_ip_to_str(ip_int):
    return socket.inet_ntoa(struct.pack('>I', ip_int))

def test_connect():
    # 1. Khởi tạo danh sách thiết bị
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ Không tìm thấy camera GigE.")
        return

    print(f"✅ Phát hiện {deviceList.nDeviceNum} camera:")

    # 2. Lặp qua từng thiết bị và in thông tin
    for i in range(deviceList.nDeviceNum):
        device_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if device_info.nTLayerType == MV_GIGE_DEVICE:
            gige_info = device_info.SpecialInfo.stGigEInfo
            print(f"  📷 Camera {i + 1}: IP = {bytes(gige_info.nCurrentIp).decode(errors='ignore')}, "
                  f"Model = {bytes(gige_info.chModelName).decode(errors='ignore')}")

    # 3. Mở kết nối camera đầu tiên
    cam = MvCamera()
    ret = cam.MV_CC_CreateHandle(deviceList.pDeviceInfo[0])
    if ret != 0:
        print("❌ Tạo handle thất bại.")
        return

    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print("❌ Không mở được camera.")
        return

    print("✅ Camera kết nối thành công.")
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()


@app.get("/capture")
def capture_all():
    test_connect()
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for idx, cam in enumerate(cams):
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
        if ret == 0 and stOutFrame.pBufAddr:
            width = stOutFrame.stFrameInfo.nWidth
            height = stOutFrame.stFrameInfo.nHeight
            buf_len = stOutFrame.stFrameInfo.nFrameLen

            # Tạo buffer ảnh từ SDK
            buf_type = (c_ubyte * buf_len)
            buf = buf_type.from_address(addressof(stOutFrame.pBufAddr.contents))
            np_img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))  # RGB24

            filename = f"cam{idx+1}_{timestamp}.jpg"
            cv2.imwrite(filename, np_img)

            cam.MV_CC_FreeImageBuffer(stOutFrame)

            results.append(filename)
        else:
            results.append(None)

    return JSONResponse(content={"images": results})

@app.get("/countcame")
def testconn():
    test_connect()
  