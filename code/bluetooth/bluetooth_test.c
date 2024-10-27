#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>

#define BUF_SIZE 1024  // 수신 버퍼 크기

int main(int argc, char **argv) {
    struct sockaddr_rc loc_addr = { 0 }, rem_addr = { 0 };
    char buf[BUF_SIZE] = { 0 };
    int s, client, bytes_read;
    socklen_t opt = sizeof(rem_addr);

    // 블루투스 소켓 생성
    s = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (s < 0) {
        perror("블루투스 소켓 생성 실패");
        exit(1);
    }

    // 서버 주소 설정
    loc_addr.rc_family = AF_BLUETOOTH;
    loc_addr.rc_bdaddr = *BDADDR_ANY;  // 모든 블루투스 장치에서 연결 허용
    loc_addr.rc_channel = (uint8_t) 1; // RFCOMM 채널 1

    // 소켓 바인딩
    if (bind(s, (struct sockaddr *)&loc_addr, sizeof(loc_addr)) < 0) {
        perror("소켓 바인딩 실패");
        close(s);
        exit(1);
    }

    // 연결 대기
    if (listen(s, 1) < 0) {
        perror("연결 대기 실패");
        close(s);
        exit(1);
    }

    printf("스마트폰의 연결을 기다리는 중...\n");

    // 클라이언트(스마트폰) 연결 수락
    client = accept(s, (struct sockaddr *)&rem_addr, &opt);
    if (client < 0) {
        perror("클라이언트 연결 수락 실패");
        close(s);
        exit(1);
    }

    // 연결된 클라이언트 주소 출력
    ba2str(&rem_addr.rc_bdaddr, buf);
    printf("스마트폰이 연결되었습니다. 주소: %s\n", buf);
    memset(buf, 0, sizeof(buf));

    // 메시지 수신 및 송신
    while (1) {
        // 스마트폰에서 데이터 수신
        bytes_read = read(client, buf, sizeof(buf));
        if (bytes_read > 0) {
            printf("스마트폰으로부터 받은 메시지: %s\n", buf);
        } else {
            printf("연결이 종료되었습니다.\n");
            break;
        }

        // 응답 보내기
        char response[] = "라즈베리 파이에서 보낸 메시지입니다.";
        write(client, response, sizeof(response));
    }

    // 소켓 닫기
    close(client);
    close(s);
    return 0;
}