from tuning import Tuning

import usb.core
import usb.util
import time
import pyaudio
import numpy as np
import wave

FORMAT = pyaudio.paInt16
CHANNELS = 6
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"

dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

if not dev:
    print('dev not found')
    Mic_tuning = Tuning(dev)
    quit()

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* 녹음을 시작합니다")

frames = []

for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(np.frombuffer(data, dtype=np.int16))

print("* 녹음을 종료합니다")

# 스트림 종료
stream.stop_stream()
stream.close()
p.terminate()

# 데이터 배열을 결합
audio_data = np.vstack(frames)

# WAV 파일로 저장
with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(audio_data.tobytes())

print("* 데이터를 저장했습니다:", WAVE_OUTPUT_FILENAME)