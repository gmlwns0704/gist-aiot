import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import os

# 서비스와 특성 UUID 설정
GATT_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
GATT_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"

class Application(dbus.service.Object):
    """
    D-Bus GATT Application 설정
    """
    def __init__(self, bus):
        self.path = '/org/bluez/example/service'
        self.bus = bus
        self.service = Service(bus, self.path)
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

class Service(dbus.service.Object):
    """
    GATT Service 정의
    """
    def __init__(self, bus, path):
        self.path = path
        self.bus = bus
        self.characteristics = []
        self.uuid = GATT_SERVICE_UUID
        self.primary = True

        self.characteristics.append(Characteristic(bus, self.path, 0))

    def get_path(self):
        return dbus.ObjectPath(self.path)

class Characteristic(dbus.service.Object):
    """
    GATT Characteristic 설정
    """
    def __init__(self, bus, service_path, index):
        self.path = service_path + '/char' + str(index)
        self.bus = bus
        self.uuid = GATT_CHARACTERISTIC_UUID
        self.service = service_path
        dbus.service.Object.__init__(self, bus, self.path)

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature='', out_signature='ay')
    def ReadValue(self):
        print("Read request received")
        return [dbus.Byte(b) for b in "Hello from Raspberry Pi".encode()]

def main():
    # Bluetooth 초기화
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    app = Application(bus)

    # Bluetooth 광고 설정
    os.system("sudo hciconfig hci0 up")
    os.system("sudo hciconfig hci0 leadv 3")  # Advertising 모드 활성화

    print("GATT server running...")

    # Main loop 실행
    mainloop = GLib.MainLoop()
    mainloop.run()

if __name__ == "__main__":
    main()
