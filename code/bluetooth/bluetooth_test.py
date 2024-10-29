import bluetooth

# Bluetooth 서버 설정
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 1  # 사용할 포트 번호
server_socket.bind(("", port))
server_socket.listen(1)

print("스마트폰 연결 대기 중...")
client_socket, address = server_socket.accept()
print(f"스마트폰이 연결되었습니다. 주소: {address}")

try:
    while True:
        # 스마트폰에서 데이터 수신
        data = client_socket.recv(1024)
        print("스마트폰으로부터 받은 메시지:", data.decode())
        
        # 응답 보내기
        response = "라즈베리 파이에서 보낸 메시지입니다."
        client_socket.send(response.encode())
except OSError:
    print("연결이 끊어졌습니다.")
finally:
    client_socket.close()
    server_socket.close()
    print("블루투스 연결이 종료되었습니다.")