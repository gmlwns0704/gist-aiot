import pyaudio
import wave
import numpy as np
# https://github.com/respeaker/usb_4_mic_array/tree/master/test

class Respeaker():
    def __init__(self, rate=16000, frames_size=None, buffer_size=1024):
        self.rate = rate
        self.frames_size = frames_size if frames_size else rate / 100
        # Channel 0: processed audio for ASR
        # Channel 1: mic1 raw data
        # Channel 2: mic2 raw data
        # Channel 3: mic3 raw data
        # Channel 4: mic4 raw data
        # Channel 5: merged playback
        self.channels = 6
        self.raw_channels=[1,2,3,4]
        self.buffer_size=buffer_size
        self.pyaudio_instance = pyaudio.PyAudio()

        #디바이스 찾기
        device_index = None
        for i in range(self.pyaudio_instance.get_device_count()):
            dev = self.pyaudio_instance.get_device_info_by_index(i)
            name = dev['name'].encode('utf-8')
            print('{}:{} with {} input channels'.format(i, name, dev['maxInputChannels']))
            if name.find(b'ReSpeaker 4 Mic Array') >= 0 and dev['maxInputChannels'] == self.channels:
                device_index = i
                break

        if device_index is None:
            raise ValueError('Can not find an input device with {} channel(s)'.format(self.channels))

        self.stream = self.pyaudio_instance.open(
            start=False,
            format=pyaudio.paInt16,
            input_device_index=device_index,
            channels=self.channels,
            rate=int(self.rate),
            frames_per_buffer=int(self.frames_size),
            # stream_callback=self._callback,
            input=True
        )
    
    #4행n열로 raw데이터 읽고 numpy로 리턴
    def readRaw(self, duration):
        frames=[]
        data=np.array([self.raw_channels,self.buffer_size])
        for i in range(0, int(self.rate / self.buffer_size * duration)):
            total_data=self.stream.read(self.buffer_size)
            for j in self.raw_channels:
                data[j,:]=total_data[j::self.channels]
            frames.append(data)
        audio_data=np.vstack(frames)
        return audio_data

    def start(self):
        self.stream.start_stream()
        return

    def stop(self):
        self.stream.stop_stream()
        return

respeaker=Respeaker()
print(respeaker.readRaw(10))