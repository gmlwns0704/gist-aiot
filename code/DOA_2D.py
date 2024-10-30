import pyaudio
import numpy as np
import wave

# 설정
FORMAT = pyaudio.paInt16
CHANNELS = 6  # ReSpeaker v2.0은 6개의 채널을 지원합니다
RATE = 16000  # 샘플 레이트
CHUNK = 1024  # 버퍼 크기
RECORD_SECONDS = 3  # 녹음 시간 (초)
WAVE_OUTPUT_FILENAME_TEMPLATE = "output_channel_{}.wav"

# PyAudio 객체 생성
p = pyaudio.PyAudio()

# 입력 스트림 설정
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* 녹음을 시작합니다")

frames = []

for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS))

i=0
while True:
    data=stream.read(CHUNK)
    frames[i]=data
    print(data[0])
    i = i+1
    if(i>=int(RATE / CHUNK * RECORD_SECONDS)):
        i=0

print("* 녹음을 종료합니다")

# 스트림 종료
stream.stop_stream()
stream.close()
p.terminate()

# 데이터 배열을 결합
audio_data = np.vstack(frames)
# n채널에서 데이터 가져오기: audio_data[:,n]

# 각 채널별로 WAV 파일로 저장
for channel in range(CHANNELS):
    channel_data = audio_data[:, channel]
    wave_output_filename = WAVE_OUTPUT_FILENAME_TEMPLATE.format(channel + 1)
    
    with wave.open(wave_output_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(channel_data.tobytes())
    
    print("* 데이터를 저장했습니다:", wave_output_filename)
