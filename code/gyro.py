import smbus  # I2C 통신을 위한 모듈
import time   # 시간 계산을 위한 모듈

# MPU6050 I2C 주소
MPU6050_ADDR = 0x68

# MPU6050 레지스터 주소
PWR_MGMT_1 = 0x6B
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

# I2C 초기화
bus = smbus.SMBus(1)  # 라즈베리파이에서 I2C 버스 1번 사용

# MPU6050 초기화
bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)  # 장치 웨이크업

# 자이로 값을 읽는 함수
def read_gyro():
    def read_word_2c(adr):
        high = bus.read_byte_data(MPU6050_ADDR, adr)
        low = bus.read_byte_data(MPU6050_ADDR, adr+1)
        val = (high << 8) + low
        if val >= 0x8000:  # 음수 처리
            val = -((65535 - val) + 1)
        return val
    
    # 자이로스코프 값 읽기 (각축 X, Y, Z)
    gyro_x = read_word_2c(GYRO_XOUT_H)
    gyro_y = read_word_2c(GYRO_YOUT_H)
    gyro_z = read_word_2c(GYRO_ZOUT_H)
    
    # 감도 조정 (기본 감도는 131)
    gyro_x = gyro_x / 131.0
    gyro_y = gyro_y / 131.0
    gyro_z = gyro_z / 131.0
    
    return gyro_x, gyro_y, gyro_z

# 각도 계산을 위한 초기값 설정
prev_time = time.time()
angle_x = 0
angle_y = 0

# 각도 계산 함수
def calculate_angle():
    global angle_x, angle_y, prev_time
    
    # 현재 시간과 시간 차이 계산
    curr_time = time.time()
    dt = curr_time - prev_time
    prev_time = curr_time
    
    # 자이로스코프 데이터 읽기
    gyro_x, gyro_y, gyro_z = read_gyro()
    
    # 각속도를 시간 차에 곱해 누적하여 각도 계산
    angle_x += gyro_x * dt  # Roll
    angle_y += gyro_y * dt  # Pitch
    
    return angle_x, angle_y

# 메인 루프
try:
    while True:
        angle_x, angle_y = calculate_angle()
        print(f"Roll: {angle_x:.2f}, Pitch: {angle_y:.2f}")
        time.sleep(0.1)  # 0.1초마다 업데이트
except KeyboardInterrupt:
    print("프로그램 종료")
