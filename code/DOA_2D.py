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

def soundDataToFloat(SD):
    # Converts integer representation back into librosa-friendly floats, given a numpy array SD
    return np.array([ np.float32((s>>2)/(32768.0)) for s in SD])

class DOA_2D_listener():
    def __init__(self,
                 channels=6,
                 sr=16000,
                 chunk=1024,
                 record_seconds=3,
                 min_volume=1500,
                 sound_pre_offset=0.3,
                 detect_callback=None,
                 input_model=None):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = channels
        self.RATE = sr
        self.CHUNK = chunk
        self.RECORD_SECONDS = record_seconds
        self.MIN_VOLUME=min_volume
        self.SOUND_PRE_OFFSET=sound_pre_offset
        if detect_callback is None:
            self.DETECT_CALLBACK=self.default_callback
        else:
            self.DETECT_CALLBACK=detect_callback

        # PyAudio 객체 생성
        self.PYAUDIO_INSTANCE = pyaudio.PyAudio()
        
        # 모델 객체 생성
        if input_model is None:
            self.MODEL = model.Rasp_Model()
        else:
            self.MODEL = input_model
            
        # resepeaker찾기
        # DOAANGLE에 사용
        self.dev=usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if not self.dev:
            print('device not found')
            return None
        self.Mic_tuning=Tuning(self.dev)

        # 입력 스트림 설정
        self.STREAM = self.PYAUDIO_INSTANCE.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
    
    def start_detect(self):
        frames = []
        test_frames=[]
        frame_len=(int(self.RATE / self.CHUNK * self.RECORD_SECONDS))
        for i in range(frame_len):
            data = self.STREAM.read(self.CHUNK, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS))
            test_frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS))

        print("* waiting for loud volume")
        print(np.array(frames).shape)
        i=0
        while True:
            data=self.STREAM.read(self.CHUNK, exception_on_overflow=False)
            frames[i]=np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS)
            # data, 각 2byte
            volume=audioop.rms(data,2)
            if(volume>self.MIN_VOLUME):
                print('loud sound detected')
                angle=self.Mic_tuning.direction
                if i>int(frame_len*self.SOUND_PRE_OFFSET):
                    test_frames[:int(frame_len*self.SOUND_PRE_OFFSET)]=frames[i-int(frame_len*self.SOUND_PRE_OFFSET):i]
                else:
                    test_frames[:i]=frames[:i]
                    test_frames[i:int(frame_len*self.SOUND_PRE_OFFSET)]=frames[int(frame_len*self.SOUND_PRE_OFFSET)+i:]
                for j in range(int(frame_len*self.SOUND_PRE_OFFSET),frame_len):
                    data=self.STREAM.read(self.CHUNK, exception_on_overflow=False)
                    test_frames[j]=np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS)
                print('record done, start callback function')
                self.DETECT_CALLBACK(test_frames, angle)
                i=0
            i = i+1
            if(i>=frame_len):
                i=0
    
    def default_callback(self, test_frames, angle):
        #실수화(librosa는 실수값으로 작동)
        #0번채널만 추출
        test_frames_np_float = soundDataToFloat(np.array(test_frames)[:,:,0]).flatten()
        #모델에 넣기위한 작업과정
        feat = mfcc.pre_progressing(test_frames_np_float, self.RATE)
        result = self.MODEL.test_by_feat(feat)
        print(result)
        print(angle)
        return
    
    def stop(self):
        # 스트림 종료
        self.STREAM.stop_stream()
        self.STREAM.close()
        self.PYAUDIO_INSTANCE.terminate()