import json
import socket
import struct
from ctypes import *
from MvCameraControl_class import *

def int_ip_to_str(ip_int):
    return socket.inet_ntoa(struct.pack('>I', ip_int))

def scan_cameras():
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)

    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ Không tìm thấy camera GigE.")
        return []

    print(f"✅ Tìm thấy {deviceList.nDeviceNum} camera:")
    camera_info = []

    for i in range(deviceList.nDeviceNum):
        device_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if device_info.nTLayerType == MV_GIGE_DEVICE:
            gige_info = device_info.SpecialInfo.stGigEInfo

            ip_str = int_ip_to_str(gige_info.nCurrentIp)
            model = bytes(gige_info.chModelName).decode(errors='ignore').strip('\x00').strip()

            serial = bytes(gige_info.chSerialNumber).decode(errors='ignore').strip('\x00').strip()


            cam_name = f"Cam {i + 1}"  # hoặc tạo tên theo model

            print(f"  📷 {cam_name} | IP: {ip_str} | Model: {model} | Serial: {serial}")

            camera_info.append({
                "name": cam_name,
                "serial": serial,
                "ip": ip_str,
                "model_index": i,
                "trigger_mode": "Off",
                "exposure_time": 5000,
                "gain": 10.0
            })

    return camera_info

def save_config(cameras, output_path="CameraConfig2.json"):
    config = {
        "issave": False,
        "save_path": "F:/predict_flutter/GrabImage",
        "cameras": cameras
    }
    with open(output_path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"✅ Đã lưu cấu hình vào '{output_path}'")

if __name__ == "__main__":
    camera_list = scan_cameras()
    if camera_list:
        save_config(camera_list)
    else:
        print("⚠️ Không có camera nào được lưu.")
