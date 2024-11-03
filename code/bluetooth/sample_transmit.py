import bluetooth

class bt_communicate:
    def __init__(self):
        #적당히 수정?
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(('',bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        self.port = self.server_sock.getsockname()[1]
        # advertise
        bluetooth.advertise_service(self.server_sock, "rasp_bt", service_id = self.uuid,
                                    service_classes = [self.uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles = [bluetooth.SERIAL_PORT_PROFILE])
        return
    
    def accept(self):
        self.client_sock, self.client_info = self.server_sock.accept()
        return self.client_sock, self.client_info
    
    def send(self, data):
        self.client_sock.send(data)
        return
    
    def disconnect(self):
        self.client_sock.close()
        self.server_sock.close()
 