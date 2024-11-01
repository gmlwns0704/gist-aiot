import pyaudio
import audioop
import numpy as np
import wave
import time
import sys
import torch
import threading

import pyroomacoustics as pra
import noisereduce as nr

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
                 input_model=None):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = channels
        self.RATE = sr
        self.CHUNK = chunk
        self.RECORD_SECONDS = record_seconds
        self.MIN_VOLUME=min_volume
        self.SOUND_PRE_OFFSET=sound_pre_offset
            
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
        self.test_frames=[]
        print(self.RATE)
        print(self.CHUNK)
        print(self.RECORD_SECONDS)
        frame_len=int((self.RATE/self.CHUNK)*self.RECORD_SECONDS)
        for i in range(frame_len):
            data = self.STREAM.read(self.CHUNK, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS))
            self.test_frames.append(np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS))

        print("* waiting for loud volume")
        i=0
        while True:
            data=self.STREAM.read(self.CHUNK, exception_on_overflow=False)
            frames[i]=np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS)
            # data, 각 2byte
            volume=audioop.rms(frames[i][:,0].flatten(),2)
            if(volume>self.MIN_VOLUME):
                print('loud sound detected')
                self.angle=self.Mic_tuning.direction
                x=int(frame_len*self.SOUND_PRE_OFFSET)
                if i>x:
                    self.test_frames[:x]=frames[i-x:i]
                else:
                    self.test_frames[:x-i]=frames[frame_len-(x-i):]
                    self.test_frames[x-i:x]=frames[:i]
                for j in range(x,frame_len):
                    data=self.STREAM.read(self.CHUNK, exception_on_overflow=False)
                    self.test_frames[j]=np.frombuffer(data, dtype=np.int16).reshape(-1, self.CHANNELS)
                # 다른 스레드에서 분석시작
                print('record done, start callback function')
                # rawdata 노이즈 제거
                for ch in range(1,5):
                    self.test_frames[:][:][ch]=nr.reduce_noise(y=self.test_frames[:][:][ch], sr=self.RATE)
                th=threading.Thread(target=self.default_callback, args=(self.test_frames,))
                th.start()
                print('thread call done')
            # i++
            i = (i+1)%frame_len
    
    def default_callback(self, input_test_frames):
        #실수화(librosa는 실수값으로 작동)
        #0번채널만 추출
        test_frames_np_float = soundDataToFloat(np.array(input_test_frames)[:,:,0]).flatten()
        #모델에 넣기위한 작업과정
        feat = mfcc.pre_progressing(test_frames_np_float, self.RATE)
        result = self.MODEL.test_by_feat(feat)
        print(result)
        print(self.angle)
        return
    
    def stop(self):
        # 스트림 종료
        self.STREAM.stop_stream()
        self.STREAM.close()
        self.PYAUDIO_INSTANCE.terminate()


class DOA_pra_listener(DOA_2D_listener):
    def __init__(self,
                 channels=6,
                 sr=16000,
                 chunk=1024,
                 record_seconds=3,
                 min_volume=1500,
                 sound_pre_offset=0.3,
                 input_model=None,
                 nfft=256,
                 mic_positions=None,
                 dim=2):
        super().__init__(channels=channels,
                         sr=sr,
                         chunk=chunk,
                         record_seconds=record_seconds,
                         min_volume=min_volume,
                         sound_pre_offset=sound_pre_offset,
                         input_model=input_model)
        self.nfft=nfft
        
        if mic_positions is None:
            if dim == 2:
                self.mic_positions = np.array([
                    [1, 1],
                    [-1, 1],
                    [-1, -1],
                    [1, -1]
                ]).T
            elif dim == 3:
                self.mic_positions = np.array([
                    [1, 1, 0],
                    [-1, 1, 0],
                    [-1, -1, 0],
                    [1, -1, 0]
                ]).T
            else:
                print('wrong dim!')
        
        self.doa=pra.doa.music.MUSIC(self.mic_positions, self.RATE, nfft=self.nfft, c=343, dim=dim)
    
    def default_callback(self, input_test_frames):
        test_frames_np=np.array(input_test_frames)
        print(test_frames_np.shape)
        X = np.array(
            [
                pra.transform.stft.analysis(signal.T.flatten(), self.nfft, self.nfft // 2).T
                for signal in test_frames_np.T[1:5]
            ]
        )
        self.doa.locate_sources(X)
        print(f"Estimated DOA angles: {self.doa.azimuth_recon / np.pi * 180.0} degrees")
        return