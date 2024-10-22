#include<pigpio.h>
#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#include"const.h"
#include"shm_ctrl.h"

/*
각 센서는 일정 조건이 만족되는 소리가 들어오면 활성화됨
활성화 시 당시의 시간을 기록
4개의 센서가 모두 활성화되면 마지막 센서를 제외한 나머지 센서는 잠시 정지
마지막 센서가 인식한 소리를 기준으로 소리를 분석한다
분석 종료후 다시 첫단계로

데이터의 전달은 공유데이터
C에서 배열형태로 전달하면 파이썬이 ctype라이브러리로 ndarray형태로 전환할 예정
*/

unsigned int readAnalog(unsigned int, unsigned char);
double calc_angle(GPIO_CLOCK_TIME* listen_time);

unsigned int ADChandle, min_th;

int main(int argc, char* argv[]){

    //각종 초기화
    gpioInitialise();
    if(!shm_setting()){
        fprintf(stderr,"E:shared memory setting error\n");
        return -1;
    }

    if ((ADChandle = spiOpen(0, 1000000, 0)) < 0) {
        fprintf(stderr, "SPIOpen Err\n");
        return -1;
    }

    waiting_repeat(ADChandle, min_th);

    if(spiClose(ADChandle)<0){
        fprintf(stderr, "SPIClose Err\n");
        return -1;
    }

    gpioTerminate();

    return 0;
}

void waiting_repeat(unsigned int ADChandle, unsigned int min_th){
    unsigned char read_ch;
    double angle;
    char sound_buf[CH_NUM][SOUND_BUF_SZ]={0}; //소리정보를 보관할 버퍼
    int buf_offset=0;
    //루프반복
    for(read_ch=0;;read_ch=(read_ch+1)%CH_NUM){
        sound_buf[read_ch][buf_offset]=readAnalog(ADChandle, read_ch);
        if(buf_offset==SOUND_BUF_SZ-1 && read_ch==CH_NUM-1){
            shm_write(sound_buf[read_ch], SOUND_BUF_SZ);
            buf_offset=0;
            printf("buffer reset\n");
        }
        if(read_ch==CH_NUM-1)
            buf_offset++;
    }
}

unsigned int readAnalog(unsigned int handle, unsigned char ch){
    // MCP3008 SPI 메시지 전송 (시작 비트, 싱글/디퍼런셜, 채널 번호, 빈 비트)
    unsigned char buf[] = {0x1, (0x8 + ch) << 4, 0x0};
    spiXfer(handle, buf, buf, 3);  // SPI 데이터 전송 및 수신

    // 결과 계산 (MCP3008에서 10비트 데이터 수신)
    return ((buf[1] & 3) << 8) + buf[2];
}

//4개 센서의 도달시간을 측정해서 60분법 각도 계산
double calc_angle(GPIO_CLOCK_TIME* listen_time){
    GPIO_CLOCK_TIME t1, t2;
    double angle;
    t1=listen_time[2]-listen_time[1];
    t2=listen_time[3]-listen_time[0];
    angle=atan2(t1,t2);
    //60분법으로 변경
    angle*=180.0/3.141592;

    return angle;
}
