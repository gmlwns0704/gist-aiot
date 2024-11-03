import pyaudio

p = pyaudio.PyAudio()

# 연결된 오디오 장치 정보를 확인
for i in range(p.get_device_count()):
    dev_info = p.get_device_info_by_index(i)
    print(f"Device {i}: {dev_info['name']}")
    print(f"  - Default Sample Rate: {dev_info['defaultSampleRate']}")
    print(f"  - Max Input Channels: {dev_info['maxInputChannels']}")
    print(f"  - Supported Formats: Likely paInt16")  # pyaudio는 일반적으로 paInt16 사용
p.terminate()