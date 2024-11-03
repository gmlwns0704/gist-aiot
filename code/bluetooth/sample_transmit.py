import bluetooth

server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)

print("Waiting for connection...")
client_socket, address = server_socket.accept()
print("Accepted connection from ", address)

while True:
    data = client_socket.recv(1024)
    if not data:
        break
    print("Received: ", data.decode())
    client_socket.sendall(data)

client_socket.close()
server_socket.close()
