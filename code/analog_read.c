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


static unsigned char listen_bit=0; //읽어들인 채널을 표시하는 비트테이블
static unsigned char listen_bit_mask=0x0f; //listen_bit검사중 사용
unsigned int ADChandle, min_th;

int main(int argc, char* argv[]){
    if(argc!=2){
        fprintf(stderr, "format: %s [minimum_thresh]\n", argv[0]);
        return -1;
    }

    min_th=atoi(argv[1]);
    //CH_NUM만큼의 1을 가지는 비트마스크 (ex:CH_NUM=3 -> 0000 0111)
    listen_bit_mask=(0x1<<CH_NUM)-1;

    //각종 초기화
    gpioInitialise();
    shm_setting();

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
    float value;
    unsigned char read_ch;
    GPIO_CLOCK_TIME* listen_time; //특정 채널이 값을 읽었을 때 시간
    double angle;
    float sound_buf[SOUND_BUF_SZ]; //소리정보를 보관할 버퍼
    unsigned int maximum=0;
    //채널 갯수만큼 시간메모리 할당
    listen_time=malloc(sizeof(GPIO_CLOCK_TIME)*CH_NUM);
    //루프반복
    for(read_ch=0;;read_ch=(read_ch+1)%CH_NUM){
        //이미 인식한 센서라면 스킵
        if(listen_bit&(0x1<<read_ch))
            continue;
        value=readAnalog(ADChandle, read_ch);
        if(value>maximum){
            maximum=value;
            printf("%d\n",value);
        }
        //임계소리크기 넘김
        if(value>min_th){
            //시간기록
            listen_time[read_ch]=gpioTick();
            //비트마커 표시
            listen_bit|=(0x1<<read_ch);

            printf("channel %d marked, current bit: %u\n", read_ch, listen_bit);
            
            //모든 채널에서 소리를 들었음
            if(!(listen_bit^listen_bit_mask)){
                for(int i=0; i<CH_NUM;i++){
                    printf("time: %u\n", listen_time[i]);
                }
                //각 센서별 시간으로 각도계산
                angle=calc_angle(listen_time);
                printf("angle; %f\n", angle);
                //나머지 센서는 멈추고 해당 센서의 입력만 집중적으로 인식, 버퍼에 기록 시작
                for(int i=0; i<SOUND_BUF_SZ;i++){
                    sound_buf[i]=readAnalog(ADChandle, read_ch)/1024.0f;
                }
                //!!!공유메모리에 덮어쓰기
                //!!!공유메모리 작성이 끝나고 파이썬 프로세스에게 전처리시작을 알릴 방법?
                shm_write(sound_buf, sizeof(sound_buf));
                //listen_bit초기화
                listen_bit=0;
                maximum=0;
            }
        }
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
