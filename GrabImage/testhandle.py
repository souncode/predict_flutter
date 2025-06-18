import json
from ctypes import *
from MvCameraControl_class import *
import socket
import struct


def decode_model_name(model_bytes):
    return bytes(model_bytes).split(b'\x00')[0].decode(errors='ignore').strip()


def int_ip_to_str(ip_int):
    return socket.inet_ntoa(struct.pack('>I', ip_int))


def list_and_save_camera_config(output_path="CameraConfig.json"):
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ Không tìm thấy camera GIGE nào")
        return

    print(f"✅ Tìm thấy {deviceList.nDeviceNum} camera GIGE:\n")

    camera_configs = []

    for i in range(deviceList.nDeviceNum):
        device_info_ptr = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO))
        device_info = device_info_ptr.contents
        gige_info = cast(pointer(device_info.SpecialInfo.stGigEInfo), POINTER(MV_GIGE_DEVICE_INFO)).contents

        serial = decode_model_name(gige_info.chSerialNumber)
        ip = int_ip_to_str(gige_info.nCurrentIp)
        model = decode_model_name(gige_info.chModelName)

        print(f"🔹 Camera {i + 1}")
        print(f"    Serial Number : {serial}")
        print(f"    IP Address    : {ip}")
        print(f"    Model         : {model}")
        print()

        config = {
            "name": f"Cam {i + 1}",
            "serial": serial,
            "ip": ip,
            "model_index": i,
            "trigger_mode": "Off",
            "exposure_time": 5000,
            "gain": 10.0
        }

        camera_configs.append(config)

    output = {
        "cameras": camera_configs
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"💾 Đã lưu cấu hình vào: {output_path}")


if __name__ == "__main__":
    list_and_save_camera_config()
