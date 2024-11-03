import asyncio
from bleak import BleakScanner, BleakClient

# 스마트폰에서 광고하는 장치의 MAC 주소와 서비스 UUID
TARGET_MAC_ADDRESS = "xx:xx:xx:xx:xx:xx"  # 스마트폰의 BLE 주소로 변경
TARGET_SERVICE_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # 전송하고자 하는 서비스 UUID

async def run():
    # 장치 스캔
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

    # 대상 장치 찾기
    device = next((d for d in devices if d.address == TARGET_MAC_ADDRESS), None)
    if device is None:
        print("Target device not found.")
        return

    print("Connecting to", TARGET_MAC_ADDRESS)
    async with BleakClient(device) as client:
        print("Connected to device")

        # 서비스에서 데이터를 수신
        while True:
            data = await client.read_gatt_char(TARGET_SERVICE_UUID)
            print("Received:", data.decode("utf-8"))
            await asyncio.sleep(1)

# 비동기 실행
asyncio.run(run())
