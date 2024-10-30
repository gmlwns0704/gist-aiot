import bluetooth
import time

class bt_transmit:
    def __init__(self, name):
        # Bluetooth 서버 소켓 생성
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)

        port = self.server_sock.getsockname()[1]
        bluetooth.advertise_service(self.server_sock, name,
                                    service_classes=[bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE])

        print("Bluetooth server started, waiting for connection...")
        self.client_sock, self.client_info = self.server_sock.accept()
        print(f"Connected to {self.client_info}")

    def sendData(self, data):
        self.client_sock.send(data)
        
    def close(self):
        self.client_sock.close()
        self.server_sock.close()
        print('disconnected')