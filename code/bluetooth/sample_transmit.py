import bluetooth

# 블루투스 서버 소켓 생성 및 초기화
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 1
server_socket.bind(("", port))
server_socket.listen(1)

print("Waiting for connection on RFCOMM channel", port)

# 클라이언트(스마트폰) 연결 대기
client_socket, client_address = server_socket.accept()
print("Accepted connection from", client_address)

try:
    while True:
        # 클라이언트로부터 데이터 수신
        data = client_socket.recv(1024)
        if not data:
            break
        print("Received:", data.decode("utf-8"))

        # 응답 전송
        message = "Received: " + data.decode("utf-8")
        client_socket.send(message)

except OSError:
    pass

print("Disconnected.")
client_socket.close()
server_socket.close()
