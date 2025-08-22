import json
from utils.shared import camera_configs, issaveimage, save_path
from MvCameraControl_class import *
from utils.camera_helpers import decode_model_name
from utils.shared import cams, models
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CameraConfig.json")

def load_camera_config():
    global camera_configs, issaveimage, save_path
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            print("📁 Đã load cấu hình từ CameraConfig.json:")
            print(json.dumps(data, indent=4, ensure_ascii=False))  # In nội dung đẹp và dễ đọc

            camera_configs = data["cameras"]
            issaveimage = data.get("issave", False)
            save_path = data.get("save_path", "images")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file cấu hình: {CONFIG_PATH}")
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi đọc JSON: {e}")
    except Exception as e:
        print(f"❌ Lỗi khi load config: {e}")

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

                # ⚙️  Trigger Mode
                trigger_mode = cfg.get("trigger_mode", "Off").lower()
                if trigger_mode == "off":
                    cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
                else:
                    cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)

                    # ⚙️ Trigger Source nếu cần
                    trigger_source = cfg.get("trigger_source", "software").lower()
                    if trigger_source == "software":
                        cam.MV_CC_SetEnumValue("TriggerSource", 7)  # 7 = Software
                    elif trigger_source == "hardware":
                        cam.MV_CC_SetEnumValue("TriggerSource", 0)  # 0 = Line0 (tùy hãng)

                # Các thiết lập khác
                cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_RGB8_Packed)
                cam.MV_CC_SetFloatValue("ExposureTime", cfg["exposure_time"])
                cam.MV_CC_SetFloatValue("Gain", cfg["gain"])

                # Bắt đầu grabbing
                if cam.MV_CC_StartGrabbing() != 0:
                    print(f"❌ Không thể bắt đầu grabbing {cfg['name']}")
                    cam.MV_CC_CloseDevice()
                    cam.MV_CC_DestroyHandle()
                    break

                cams.append({
                    "cam": cam,
                    "model_index": cfg["model_index"],
                    "name": cfg["name"],
                    "trigger_mode": trigger_mode,
                    "trigger_source": cfg.get("trigger_source", "software").lower()
                })

                print(f"✅ Đã kết nối {cfg['name']}")
                break

        if not found:
            print(f"⚠️ Không tìm thấy camera serial {cfg['serial']}")

    print(f"\n📦 Tổng số camera kết nối: {len(cams)}")
