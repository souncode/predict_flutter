# test_trigger.py
import cv2
import numpy as np
from ctypes import *
from MvCameraControl_class import *
from datetime import datetime
import time

# PixelType constants (nếu module đã có thì dùng của module)
PixelType_Gvsp_Mono8        = 0x01080001
PixelType_Gvsp_BayerRG8     = 0x01080009
PixelType_Gvsp_RGB8_Packed  = 0x02180014

def save_bgr(img_bgr, prefix="capture"):
    fname = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    cv2.imwrite(fname, img_bgr)
    print(f"💾 Đã lưu ảnh: {fname}")

def main():
    # 1) Enum thiết bị
    dev_list = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, dev_list)
    if ret != 0 or dev_list.nDeviceNum == 0:
        print("❌ Không tìm thấy camera")
        return
    print(f"🔍 Phát hiện {dev_list.nDeviceNum} camera")

    dev_info = cast(dev_list.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents

    cam = MvCamera()
    if cam.MV_CC_CreateHandle(dev_info) != 0:
        print("❌ CreateHandle fail")
        return

    if cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
        print("❌ OpenDevice fail")
        cam.MV_CC_DestroyHandle()
        return
    print("✅ Đã mở camera")

    # 2) (Tuỳ chọn) Set packet size cho GigE
    if dev_info.nTLayerType == MV_GIGE_DEVICE:
        pkt = cam.MV_CC_GetOptimalPacketSize()
        if int(pkt) > 0:
            cam.MV_CC_SetIntValue("GevSCPSPacketSize", pkt)
            print(f"📦 GevSCPSPacketSize = {pkt}")
        else:
            print("⚠️ Không lấy được Optimal Packet Size")

    # 3) Set PixelFormat (BayerRG8 -> Mono8 -> RGB8_Packed)
    ok_pf = (cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_BayerRG8) == 0 or
             cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_Mono8) == 0 or
             cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_RGB8_Packed) == 0)
    if not ok_pf:
        print("❌ Không set được PixelFormat khả dụng")
        cam.MV_CC_CloseDevice(); cam.MV_CC_DestroyHandle()
        return

    # 4) Trigger mode ON + TriggerSource Software
    cam.MV_CC_SetEnumValue("TriggerMode", 1)   # On
    cam.MV_CC_SetEnumValue("TriggerSource", 7) # Software

    # 5) Lấy PayloadSize để cấp bộ nhớ
    intval = MVCC_INTVALUE()
    memset(byref(intval), 0, sizeof(intval))
    if cam.MV_CC_GetIntValue("PayloadSize", intval) != 0 or intval.nCurValue <= 0:
        print("❌ Không lấy được PayloadSize")
        cam.MV_CC_CloseDevice(); cam.MV_CC_DestroyHandle()
        return
    payload = int(intval.nCurValue)
    print(f"🧰 PayloadSize: {payload} bytes")

    # 6) Start grabbing
    if cam.MV_CC_StartGrabbing() != 0:
        print("❌ StartGrabbing fail")
        cam.MV_CC_CloseDevice(); cam.MV_CC_DestroyHandle()
        return
    print("▶️ Camera đã vào chế độ grabbing")

    time.sleep(0.2)  # nhỏ để camera ổn định

    # 7) Cấp buffer user + struct info
    buf = (c_ubyte * payload)()
    frame_info = MV_FRAME_OUT_INFO_EX()
    memset(byref(frame_info), 0, sizeof(frame_info))

    # Số ảnh muốn chụp
    NUM_SHOTS = 1  # đổi thành 5, 10 nếu muốn
    for i in range(NUM_SHOTS):
        print("📸 Trigger ...")
        cam.MV_CC_SetCommandValue("TriggerSoftware")

        # 8) Lấy 1 frame vào buffer user
        memset(byref(frame_info), 0, sizeof(frame_info))
        ret = cam.MV_CC_GetOneFrameTimeout(byref(buf), payload, frame_info, 1000)  # 1000ms
        if ret != 0:
            print(f"❌ GetOneFrameTimeout fail (ret={ret})")
            continue

        w = frame_info.nWidth
        h = frame_info.nHeight
        pxtype = frame_info.enPixelType
        print(f"ℹ️ Frame {i+1}: {w}x{h}, PixelType=0x{pxtype:x}, SizeUsed={frame_info.nFrameLen}")

        # 9) Decode theo PixelType
        # Lưu ý: frame_info.nFrameLen là dung lượng thực tế SDK dùng trong buf
        size_used = int(frame_info.nFrameLen)
        if size_used <= 0 or size_used > payload:
            # fallback an toàn theo pixel type:
            if pxtype == PixelType_Gvsp_RGB8_Packed:
                size_used = w * h * 3
            else:
                size_used = w * h

        np_flat = np.frombuffer((c_ubyte * size_used).from_buffer(buf), dtype=np.uint8)

        if pxtype == PixelType_Gvsp_RGB8_Packed:
            img = np_flat.reshape((h, w, 3))
            bgr = img  # SDK thường trả RGB8_Packed; nếu màu sai, dùng cvtColor RGB2BGR
        elif pxtype == PixelType_Gvsp_Mono8:
            gray = np_flat.reshape((h, w))
            bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif pxtype == PixelType_Gvsp_BayerRG8:
            bayer = np_flat.reshape((h, w))
            bgr = cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2BGR)
        else:
            # Fallback: thử coi như BayerRG8 khi SDK trả 0
            print(f"⚠️ PixelType lạ (0x{pxtype:x}) → thử decode BayerRG8")
            bayer = np_flat.reshape((h, w))
            bgr = cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2BGR)

        save_bgr(bgr, prefix=f"capture_{i+1}")
        time.sleep(0.05)  # khoảng nghỉ nhỏ giữa các lần chụp

    # 10) Dừng và đóng
    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()
    print("✅ Hoàn tất test")

if __name__ == "__main__":
    main()
