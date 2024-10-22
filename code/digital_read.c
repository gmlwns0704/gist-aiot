#include<pigpio.h>
#include<stdio.h>
#include<stdlib.h>

int main() {
    // pigpio 초기화
    if (gpioInitialise() < 0) {
        printf("pigpio 초기화 실패\n");
        return 1;
    }

    // 소리 센서 핀을 입력 모드로 설정
    gpioSetMode(17, PI_INPUT);
    gpioSetMode(18, PI_INPUT);
    gpioSetMode(22, PI_INPUT);
    gpioSetMode(23, PI_INPUT);

    // 무한 루프를 통해 소리 센서의 신호를 읽음
    while (1) {
        // 디지털 신호 읽기 (HIGH 또는 LOW)
        int sound_detected[4];
        sound_detected[0]=gpioRead(17);
        sound_detected[1]=gpioRead(18);
        sound_detected[2]=gpioRead(22);
        sound_detected[3]=gpioRead(23);
        for(int i=0;i<4;i++){
            printf("%d ", sound_detected[i]);
        }
        printf("\n");

        gpioDelay(500000);  // 0.5초 대기 (500,000 마이크로초)
    }

    // pigpio 종료
    gpioTerminate();

    return 0;
}