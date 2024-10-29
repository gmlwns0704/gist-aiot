// linux_master.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

#define SERVER_ADDR "XX:XX:XX:XX:XX:XX"  // 라즈베리 파이 블루투스 주소를 입력하세요
#define BUF_SIZE 1024

int main() {
    struct sockaddr_rc addr = { 0 };
    int sock;
    char buf[BUF_SIZE] = "마스터(클라이언트)에서 보낸 메시지";

    // RFCOMM 소켓 생성
    sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (sock < 0) {
        perror("소켓 생성 실패");
        exit(1);
    }

    // 서버(슬레이브) 주소 설정
    addr.rc_family = AF_BLUETOOTH;
    str2ba(SERVER_ADDR, &addr.rc_bdaddr);  // 서버(라즈베리 파이) 블루투스 주소
    addr.rc_channel = (uint8_t) 1;         // RFCOMM 채널 1

    // 서버로 연결 요청
    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("서버 연결 실패");
        close(sock);
        exit(1);
    }

    printf("슬레이브(라즈베리 파이)에 연결되었습니다.\n");

    // 서버로 메시지 전송 및 응답 수신
    while (1) {
        // 메시지 전송
        write(sock, buf, strlen(buf));
        printf("슬레이브(라즈베리 파이)로 메시지를 전송했습니다: %s\n", buf);

        // 서버로부터 응답 수신
        int bytes_read = read(sock, buf, sizeof(buf));
        if (bytes_read > 0) {
            printf("슬레이브(라즈베리 파이)로부터 받은 메시지: %s\n", buf);
        } else {
            printf("슬레이브와의 연결이 종료되었습니다.\n");
            break;
        }
        sleep(1);
    }

    // 소켓 닫기
    close(sock);
    return 0;
}