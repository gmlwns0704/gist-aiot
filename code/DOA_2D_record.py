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

import noisereduce as nr

from scipy.signal import resample

def read_stream():
    nr_data = nr.reduce_noise(y=stream.read(CHUNK, exception_on_overflow=False), sr=RATE)
    data = np.frombuffer(nr_data, dtype=np.int16).reshape(-1,CHANNELS)
    # data_3d = np.frombuffer(stream2.read(CHUNK*3, exception_on_overflow=False), dtype=np.int16)
    # resampled_data_3d = resample(data_3d, CHUNK).reshape(-1,1).astype(np.int16)
    # # print(data)
    # print(data_3d)
    # print(resampled_data_3d)
    return data

# 설정
FORMAT = pyaudio.paInt16
CHANNELS = 6  # ReSpeaker v2.0은 6개의 채널을 지원합니다
RATE = 16000  # 샘플 레이트
CHUNK = 1024  # 버퍼 크기
RECORD_SECONDS = int(input('record time: '))  # 녹음 시간 (초)
WAVE_OUTPUT_FILENAME_TEMPLATE = "output_channel_{}.wav"
SELECTED_CHANNELS_OUTPUT_FILENAME = "output_selected_channels.wav"
MIN_VOLUME = int(input('MIN_VOLUME: '))
SOUND_OFFSET_RATE=0.3

# PyAudio 객체 생성
p = pyaudio.PyAudio()
# p2 = pyaudio.PyAudio()

# 모델객체 생성
rasp_model = model.Rasp_Model()

# resepeaker찾기
dev=usb.core.find(idVendor=0x2886, idProduct=0x0018)

if not dev:
    print('device not found')
    quit()
Mic_tuning=Tuning(dev)

device_index = None
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    name = dev['name'].encode('utf-8')
    print('{}:{} with {} input channels'.format(i, name, dev['maxInputChannels']))
    if name.find(b'ReSpeaker 4 Mic Array') >= 0 and dev['maxInputChannels'] == 6:
        device_index = i
        break

# 입력 스트림 설정
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=device_index)

# stream2 = p2.open(format=FORMAT,
#                 channels=1,
#                 rate=RATE*3,
#                 input=True,
#                 frames_per_buffer=CHUNK*3)

print("* generating initial frames")
frames = []
test_frames=[]
frame_len=(int(RATE / CHUNK * RECORD_SECONDS))
for _ in range(frame_len):
    data = read_stream()
    frames.append(data)
    test_frames.append(data)

print("* waiting for loud volume")
i=0
while True:
    data=read_stream()
    frames[i]=data
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
            data=read_stream()
            test_frames[j]=data
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

# stream2.stop_stream()
# stream2.close()
# p2.terminate()

audio_data = np.vstack(test_frames)

# 각 채널별로 WAV 파일로 저장
for channel in range(CHANNELS+1):
    channel_data = audio_data[:, channel]
    wave_output_filename = WAVE_OUTPUT_FILENAME_TEMPLATE.format(channel + 1)
    
    with wave.open(wave_output_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(channel_data.tobytes())
    
    print("* 데이터를 저장했습니다:", wave_output_filename)

# 1-4번 채널을 통합하여 하나의 WAV 파일로 저장
selected_channels_data = audio_data[:, 1:5]
with wave.open(SELECTED_CHANNELS_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(4)  # 1-4번 채널을 통합하기 때문에 채널 수는 4
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(selected_channels_data.tobytes())
    print("* 1-4번 채널 데이터를 저장했습니다:", SELECTED_CHANNELS_OUTPUT_FILENAME)