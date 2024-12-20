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

    def _callback(self, in_data, frame_count, time_info, status):
        return None, pyaudio.paContinue
    
    #4행n열로 raw데이터 읽고 numpy, frames로 리턴
    def readRaw(self, duration):
        frames=[]
        total_data=np.zeros([len(self.raw_channels),self.buffer_size])
        print(total_data.shape)
        for i in range(0, int(self.rate / self.buffer_size * duration)):
            data=np.fromstring(self.stream.read(self.buffer_size, exception_on_overflow = False),dtype='int16')
            for j in self.raw_channels:
                total_data[j-1,:]=data[j::self.channels]
            frames.append(data)
        audio_data=np.vstack(frames)
        return audio_data, frames

    def start(self):
        self.stream.start_stream()
        return

    def stop(self):
        self.stream.stop_stream()
        return

print('start respeaker record test')
respeaker=Respeaker()
respeaker.start()
ret_np, ret_frame = respeaker.readRaw(int(input('duration: ')))
respeaker.stop()

wf = wave.open('sample.wav', 'wb')
wf.setnchannels(4)
wf.setsampwidth(respeaker.pyaudio_instance.get_sample_size(pyaudio.paInt16))
wf.setframerate(respeaker.rate)
wf.writeframes(b''.join(ret_frame))
wf.close()