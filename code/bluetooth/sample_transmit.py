import bluetooth
 
#######################################################
# Scan
#######################################################
 
target_name = "iot_test"   # target device name
target_address = None
port = 1         # RFCOMM port
 
nearby_devices = bluetooth.discover_devices()
 
# scanning for target device
for bdaddr in nearby_devices:
    print(bluetooth.lookup_name( bdaddr ))
    if target_name == bluetooth.lookup_name( bdaddr ):
        target_address = bdaddr
        break
 
if target_address is not None:
    print('device found. target address %s' % target_address)
else:
    print('could not find target bluetooth device nearby')
 
#######################################################
# Connect
#######################################################
 
# establishing a bluetooth connection
try:
    sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
    sock.connect((target_address, port))
 
    while True:         
        try:
            recv_data = sock.recv(1024)
            print(recv_data)
            sock.send(recv_data)
        except KeyboardInterrupt:
            print("disconnected")
            sock.close()
            print("all done")
except bluetooth.btcommon.BluetoothError as err:
    print('An error occurred : %s ' % err)
    pass