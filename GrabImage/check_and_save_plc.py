import snap7
from snap7.util import *
import socket
import json

def check_plc(ip, rack=0, slot=1, timeout=2000):
    client = snap7.client.Client()
    client.set_connection_params(ip, rack, slot)
    try:
        client.connect(ip, rack, slot)
        if client.get_connected():
            order_code = client.get_cpu_info().ModuleTypeName
            serial_number = client.get_cpu_info().SerialNumber
            firmware = client.get_cpu_info().ASName
            client.disconnect()
            return {
                "ip": ip,
                "rack": rack,
                "slot": slot,
                "order_code": order_code,
                "serial_number": serial_number,
                "firmware": firmware
            }
    except:
        return None

def scan_network(subnet="192.168.1.", start=1, end=254):
    found_devices = []
    for i in range(start, end+1):
        ip = f"{subnet}{i}"
        result = check_plc(ip)
        if result:
            print(f"✅ Found PLC at {ip}")
            found_devices.append(result)
    return found_devices

def save_config(plcs, filename="plc_config.json"):
    with open(filename, "w") as f:
        json.dump(plcs, f, indent=4)
    print(f"📁 Saved PLC configuration to {filename}")

if __name__ == "__main__":
    devices = scan_network("192.168.1.", 1, 50)
    if devices:
        save_config(devices)
    else:
        print("❌ No PLC found in this range.")
