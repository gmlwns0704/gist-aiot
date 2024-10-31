import pyaudio
import audioop
import numpy as np
import wave
import time
import sys
import torch

sys.path.append('/home/rasp/venv/')
sys.path.append('/home/rasp/venv/gist-aiot/')

from usb_4_mic_array.tuning import Tuning
import usb.core
import usb.util

import pre_and_model.mfcc as mfcc
import pre_and_model.model as model

# 설정
FORMAT = pyaudio.paInt16
CHANNELS = 6  # ReSpeaker v2.0은 6개의 채널을 지원합니다
RATE = 16000  # 샘플 레이트
CHUNK = 1024  # 버퍼 크기
RECORD_SECONDS = 5  # 녹음 시간 (초)
WAVE_OUTPUT_FILENAME_TEMPLATE = "output_channel_{}.wav"
MIN_VOLUME=int(input('MIN_VOLUME: '))
SOUND_OFFSET_RATE=0.3

# PyAudio 객체 생성
p = pyaudio.PyAudio()

# 모델객체 생성
rasp_model = model.Rasp_Model()

# resepeaker찾기
dev=usb.core.find(idVendor=0x2886, idProduct=0x0018)

if not dev:
    print('device not found')
    quit()
Mic_tuning=Tuning(dev)

# 입력 스트림 설정
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* generating initial frames")
frames = []
test_frames=[]
frame_len=(int(RATE / CHUNK * RECORD_SECONDS))
for _ in range(frame_len):
    data = stream.read(CHUNK)
    frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS))
    test_frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS))

print("* waiting for loud volume")
i=0
while True:
    data=stream.read(CHUNK)
    frames[i]=np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS)
    # data, 각 2byte
    volume=audioop.rms(data,2)
    if(volume>MIN_VOLUME):
        print('sound detected!')
        angle=Mic_tuning.direction
        print('angle:'+str(angle))
        print('i:'+str(i)+'/'+str(frame_len))
        if i>int(frame_len*SOUND_OFFSET_RATE):
            test_frames[:int(frame_len*SOUND_OFFSET_RATE)]=frames[i-int(frame_len*SOUND_OFFSET_RATE):i]
        else:
            test_frames[:i]=frames[:i]
            test_frames[i:int(frame_len*SOUND_OFFSET_RATE)]=frames[int(frame_len*SOUND_OFFSET_RATE)+i:]
        for j in range(int(frame_len*SOUND_OFFSET_RATE),frame_len):
            data=stream.read(CHUNK)
            test_frames[j]=np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS)
        break
    i = i+1
    if(i>=frame_len):
        i=0

print("* recorded")
print(len(test_frames))
print()

# 스트림 종료
stream.stop_stream()
stream.close()
p.terminate()

print(np.array(test_frames).shape)

#실수화(librosa는 실수값으로 작동)
test_frames_np_int = np.array(test_frames[:][0], dtype=np.int16).T
print(test_frames_np_int)
print(test_frames_np_int.shape)
# 2. float32로 변환하고 -1.0 ~ 1.0 범위로 정규화
test_frames_np_float = test_frames_np_int.astype(np.float32) / 32768.0

#모델에 넣기위한 작업과정
feat = mfcc.pre_progressing(test_frames_np_float, RATE)
result = rasp_model.test_by_feat(feat)
print(result)