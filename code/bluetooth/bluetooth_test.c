// raspberry_slave.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

#define BUF_SIZE 1024

int main() {
    struct sockaddr_rc loc_addr = { 0 }, rem_addr = { 0 };
    char buf[BUF_SIZE] = { 0 };
    int server_sock, client_sock;
    socklen_t opt = sizeof(rem_addr);

    // RFCOMM 소켓 생성
    server_sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (server_sock < 0) {
        perror("소켓 생성 실패");
        exit(1);
    }

    // 서버 주소 설정
    loc_addr.rc_family = AF_BLUETOOTH;
    loc_addr.rc_bdaddr = *BDADDR_ANY;  // 모든 장치에서의 연결 허용
    loc_addr.rc_channel = (uint8_t) 1; // RFCOMM 채널 1

    // 소켓 바인딩
    if (bind(server_sock, (struct sockaddr *)&loc_addr, sizeof(loc_addr)) < 0) {
        perror("소켓 바인딩 실패");
        close(server_sock);
        exit(1);
    }

    // 연결 대기 (클라이언트가 마스터로 연결을 요청할 때까지)
    if (listen(server_sock, 1) < 0) {
        perror("연결 대기 실패");
        close(server_sock);
        exit(1);
    }

    printf("클라이언트의 연결 요청을 기다리는 중...\n");

    // 클라이언트 연결 수락
    client_sock = accept(server_sock, (struct sockaddr *)&rem_addr, &opt);
    if (client_sock < 0) {
        perror("클라이언트 연결 수락 실패");
        close(server_sock);
        exit(1);
    }

    ba2str(&rem_addr.rc_bdaddr, buf);
    printf("클라이언트가 연결되었습니다. 주소: %s\n", buf);
    memset(buf, 0, sizeof(buf));

    // 클라이언트로부터 메시지 수신 및 응답 전송
    while (1) {
        int bytes_read = read(client_sock, buf, sizeof(buf));
        if (bytes_read > 0) {
            printf("클라이언트로부터 받은 메시지: %s\n", buf);

            // 응답 메시지 전송
            char response[] = "슬레이브(라즈베리 파이)에서 보낸 메시지";
            write(client_sock, response, sizeof(response));
        } else {
            printf("클라이언트 연결이 종료되었습니다.\n");
            break;
        }
    }

    // 소켓 닫기
    close(client_sock);
    close(server_sock);
    return 0;
}