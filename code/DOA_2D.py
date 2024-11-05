import pyaudio
import audioop
import numpy as np
import wave
import time
import sys
import torch
import threading
#서로 sr이 다르면 통일해줘야함
from scipy.signal import resample

import pyroomacoustics as pra
import noisereduce as nr

from bt import bt_transmit

sys.path.append('/home/rasp/venv/')
sys.path.append('/home/rasp/venv/gist-aiot/')

from usb_4_mic_array.tuning import Tuning
import usb.core
import usb.util

import pre_and_model.mfcc as mfcc
import pre_and_model.model as model
import gyro

def soundDataToFloat(SD):
    # print(SD)
    # print(SD.shape)
    # print(SD.dtype)
    # Converts integer representation back into librosa-friendly floats, given a numpy array SD
    return np.array([ np.float32((s>>2)/(32768.0)) for s in SD])

class DOA_2D_listener():
    def __init__(self,
                 channels=4,
                 sr=16000,
                 chunk=1024,
                 record_seconds=3,
                 min_volume=1500,
                 sound_pre_offset=0.3,
                 input_model=None,
                 bt_class=None,
                 estimate_rate=0.5):
        self.FORMAT = pyaudio.paInt16
        self.RESP_CHANNELS = 6
        self.RATE = sr
        self.CHUNK = chunk
        self.RECORD_SECONDS = record_seconds
        self.MIN_VOLUME=min_volume
        self.SOUND_PRE_OFFSET=sound_pre_offset
        self.estimate_rate=estimate_rate
        
        self.detected = False
        self.start_detect_callback = False
        self.chunk_count = 0
        self.max_chunk_count = int((self.RATE/self.CHUNK)*self.RECORD_SECONDS)
        self.chunks = np.zeros([self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        self.test_frames = np.zeros([self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        
        self.bt_class = bt_class
        self.bt_buffer = ''
        
        # PyAudio 객체 생성
        self.PYAUDIO_INSTANCE = pyaudio.PyAudio()
        
        # 모델 객체 생성
        if input_model is None:
            self.MODEL = model.Rasp_Model()
        else:
            self.MODEL = input_model
            
        # resepeaker찾기
        # DOAANGLE에 사용
        # self.dev=usb.core.find(idVendor=0x2886, idProduct=0x0018)
        # if not self.dev:
        #     print('device not found')
        #     return None
        # self.Mic_tuning=Tuning(self.dev)
        
        device_index = None
        for i in range(self.PYAUDIO_INSTANCE.get_device_count()):
            dev = self.PYAUDIO_INSTANCE.get_device_info_by_index(i)
            name = dev['name'].encode('utf-8')
            print('{}:{} with {} input channels'.format(i, name, dev['maxInputChannels']))
            if name.find(b'ReSpeaker 4 Mic Array') >= 0 and dev['maxInputChannels'] == self.RESP_CHANNELS:
                device_index = i
                break

        # 입력 스트림 설정
        self.STREAM = self.PYAUDIO_INSTANCE.open(format=self.FORMAT,
                        channels=self.RESP_CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK,
                        input_device_index=device_index,
                        stream_callback=self.non_blocking_callback)
        
        if self.bt_class is not None:
            print('start waiting bt connection')
            self.bt_class.accept()
            print('bt connected')
    
    #0-5채널 전부 읽음
    def read_stream(self):
        data = self.STREAM.read(self.CHUNK, exception_on_overflow=False)
        return np.frombuffer(data, dtype=np.int16).reshape(-1, self.RESP_CHANNELS)
    
    def start_detect(self):
        print("detection started")
        while True:
            x_rot, y_rot = gyro.get_angle()
            if np.abs(x_rot) > 45 or np.abs(y_rot) > 45:
                print('!!!machine tilted too much!!!')
                if self.bt_class is not None:
                    self.bt_class.send('warn:tilt\n')
            if self.start_detect_callback:
                print('detected, start detect callback')
                self.detect_callback(self.test_frames)
                self.start_detect_callback = False
            
            time.sleep(0.5)
        return
    
    # def start_detect(self):
    #     frames = []
    #     self.test_frames=[]
    #     # print(self.RATE)
    #     # print(self.CHUNK)
    #     # print(self.RECORD_SECONDS)
    #     frame_len=int((self.RATE/self.CHUNK)*self.RECORD_SECONDS)
    #     for i in range(frame_len):
    #         frame = self.read_stream()
    #         frames.append(frame)
    #         self.test_frames.append(frame)

    #     print("* waiting for loud volume")
    #     i=0
    #     while True:
    #         frames[i]=self.read_stream()
    #         # data, 각 2byte
    #         volume=audioop.rms(frames[i][:,0].flatten(),2)
    #         if(volume>self.MIN_VOLUME):
    #             print('loud sound detected')
    #             # self.angle=self.Mic_tuning.direction
    #             x=int(frame_len*self.SOUND_PRE_OFFSET)
    #             if i>x:
    #                 self.test_frames[:x]=frames[i-x:i]
    #             else:
    #                 self.test_frames[:x-i]=frames[frame_len-(x-i):]
    #                 self.test_frames[x-i:x]=frames[:i]
    #             for j in range(x,frame_len):
    #                 self.test_frames[j]=self.read_stream()
    #             # 분석시작
    #             print('record done, start callback function')
    #             self.default_callback(self.test_frames)
    #         # i++
    #         i = (i+1)%frame_len
    
    def detect_callback(self, input_test_frames):
        #실수화(librosa는 실수값으로 작동)
        #0번채널만 추출
        test_frames_np_float = soundDataToFloat(np.array(input_test_frames)[:,:,0]).flatten()
        #모델에 넣기위한 작업과정
        feat = mfcc.pre_progressing(test_frames_np_float, self.RATE)
        result = self.MODEL.test_by_feat(feat)
        
        estimated = result.detach().numpy()[0,:]
        print(estimated)
        estimated_class = int(np.argmax(estimated))
        estimated_prob = (estimated+abs(np.min(estimated))[estimated_class])/np.sum(estimated+abs(np.min(estimated)))
        if estimated_prob > self.estimate_rate:
            if self.bt_class is not None:
                print(estimated_prob)
                self.bt_buffer+='class:'+str(estimated_class)+'\n'
                self.bt_class.send(self.bt_buffer)
        else:
            print('maybe nothing')
            print(estimated_prob)
            self.bt_buffer=''
        # print(self.angle)
        return
    
    def non_blocking_callback(self, in_data, frame_count, time_info, status):
        # 녹음 후 청크 저장
        np_data = np.frombuffer(in_data, dtype=np.int16).reshape(-1, self.RESP_CHANNELS)
        
        if self.detected:
            self.test_frames[self.chunk_count,:,0:5] = np_data[:,0:5]
        self.chunks[self.chunk_count,:,0:5] = np_data[:,0:5]
        
        if not self.detected:
            volume=audioop.rms(np_data[:,0].flatten(),2)
            # detected
            if volume>self.MIN_VOLUME:
                print('loud sound detected')
                # chunks에서 이전 값들 test_frames 로 옮김
                x=int(self.max_chunk_count*self.SOUND_PRE_OFFSET)
                i=self.chunk_count
                if i>x:
                    self.test_frames[:x]=self.chunks[i-x:i]
                else:
                    self.test_frames[:x-i]=self.chunks[self.max_chunk_count-(x-i):]
                    self.test_frames[x-i:x]=self.chunks[:i]
                self.detected = True
                # x부터 다음 청크 쓰기 시작
                self.chunk_count=x
                
        # 감지되었다면 test_frames도 같이 업데이트
        self.chunk_count += 1
        
        # 루프사이클
        if (self.chunk_count >= self.max_chunk_count):
            self.chunk_count = 0
            # 감지가 되었고, 녹음이 끝남
            if self.detected:
                self.detected = False
                self.start_detect_callback = True
            return in_data, pyaudio.paContinue
            
        return in_data, pyaudio.paContinue
    
    def stop(self):
        # 스트림 종료
        self.STREAM.stop_stream()
        self.STREAM.close()
        self.PYAUDIO_INSTANCE.terminate()
        return
    
    # # mic_dest의 데이터를 mic_source에 맞춤
    # def sync_mic_max(self, mic_dest, mic_source):
    #     mic_base_max = np.max(np.abs(mic_source))
    #     mic_source_max = np.max(np.abs(mic_dest))
    #     scale_factor = mic_base_max / mic_source_max
    #     mic2_scaled = (mic_dest * scale_factor).astype(np.int16)
    #     return mic2_scaled


class DOA_pra_listener(DOA_2D_listener):
    def __init__(self,
                 channels=6,
                 sr=16000,
                 chunk=1024,
                 record_seconds=3,
                 min_volume=1500,
                 sound_pre_offset=0.3,
                 input_model=None,
                 bt_class=None,
                 nfft=256,
                 mic_positions=None,
                 dim=2,
                 dim3_sr=48000,
                 estimate_rate=0.5):
        super().__init__(channels=channels,
                         sr=sr,
                         chunk=chunk,
                         record_seconds=record_seconds,
                         min_volume=min_volume,
                         sound_pre_offset=sound_pre_offset,
                         input_model=input_model,
                         bt_class=bt_class,
                         estimate_rate=estimate_rate)
        self.nfft=nfft
        self.dim=dim
        self.dim3_sr=dim3_sr
        self.dim3_chunk=int(self.CHUNK*(self.dim3_sr/self.RATE))
        
        self.chunks = np.zeros([self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        self.test_frames = np.zeros([self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        
        # 1=1m, respeaker직경은 70mm=0.07m
        self.mic_positions = np.array([
                    [0, 0.035],
                    [-0.035, 0],
                    [0, -0.035],
                    [0.035, 0]
                ]).T
        if dim == 3:
            # 3D용 보조 마이크 인스턴스
            # 3D 마이크는 sr이 다르므로 다른 크기의 청크로 저장하고 후처리
            self.PYAUDIO_INSTANCE_DIM3 = pyaudio.PyAudio()
            self.STREAM_DIM3 = self.PYAUDIO_INSTANCE.open(format=self.FORMAT,
                        channels=1,
                        rate=self.dim3_sr,
                        input=True,
                        frames_per_buffer=self.dim3_chunk,
                        stream_callback=self.non_blocking_3d_callback)
            
            self.mic_3d_positions = np.array([
                [0.035,0],
                [-0.035,0],
                [0,0.035]
            ]).T
        #https://github.com/LCAV/pyroomacoustics/issues/166 버그를 고치기 위해 직접 설정?
        # num_points = 360  # azimuth에 대한 점의 개수
        # azimuth = np.linspace(0, 2*np.pi, num_points)  # -180도에서 180도까지
        # colatitude = np.linspace(0, np.pi, num_points)  # 0에서 180도까지 (구면 좌표계)
        
        self.doa=pra.doa.music.MUSIC(self.mic_positions,
                                     self.RATE,
                                     nfft=self.nfft,
                                     c=343)
        
        if dim == 3:
            self.doa_3d=pra.doa.music.MUSIC(self.mic_3d_positions,
                                        self.RATE,
                                        nfft=self.nfft,
                                        c=343)
        return
    
    def non_blocking_3d_callback(self, in_data, frame_count, time_info, status):
        # 녹음 후 청크 저장
        np_data = resample(np.frombuffer(in_data, dtype=np.int16), self.CHUNK).reshape(-1,1).astype(np.int16)
        
        # 감지되었다면 test_frames도 같이 업데이트
        if self.detected:
            self.test_frames[self.chunk_count,:,5] = np.squeeze(np_data[:])
        self.chunks[self.chunk_count,:,5] = np.squeeze(np_data[:])
        # 카운트값 변경X, respeaker의 카운트값 따라감
        # self.chunk_count += 1
        
        # 루프사이클
        if (self.chunk_count >= self.max_chunk_count):
            self.chunk_count = 0
            # 감지가 되었고, 녹음이 끝남
            if self.detected:
                self.detected = False
                self.start_detect_callback = True
            return in_data, pyaudio.paContinue
        
        return in_data, pyaudio.paContinue
    
    #0-5채널+6채널(보조마이크) 추가
    #0: respeaker 후처리 오디오
    #1-4: respeaker raw
    #5: respeaker playback ???
    #6: 3d sub mic
    # def read_stream(self):
    #     data = super().read_stream()
    #     if self.dim == 3:
    #         data_3d = np.frombuffer(self.STREAM_DIM3.read(self.dim3_chunk, exception_on_overflow=False), dtype=np.int16)
    #         resampled_data_3d = resample(data_3d, self.CHUNK).reshape(-1,1).astype(np.int16)
    #         # print(data)
    #         # print(data_3d)
    #         # print(resampled_data_3d)
    #         return np.hstack((data, resampled_data_3d))
    #     else:
    #         return data
    
    def detect_callback(self, input_test_frames):
        # print(input_test_frames)
        test_frames_np = np.array(input_test_frames)
        # print(test_frames_np.shape)
        X = np.array(
            [
                pra.transform.stft.analysis(test_frames_np[:,:,ch].flatten(), self.nfft, self.nfft // 2).T
                for ch in [1,2,3,4]
            ]
        )
        print(X.shape)
        # 평면좌표 구하기
        self.doa.locate_sources(X)
        h_angle = self.doa.azimuth_recon
        print(f"Estimated DOA angles: {h_angle / np.pi * 180.0} degrees")
        
        if self.dim == 3:
            # TDOA 방식
            # 데시벨을 인식한 청크
            t = int(len(input_test_frames)*self.SOUND_PRE_OFFSET)
            target_frames_np = np.array(input_test_frames[t-1:t+2])
            
            # respeaker 중 마주보는 2개 + 보조마이크
            volume_timing_x=np.zeros(3, dtype=np.int16)
            volume_timing_y=np.zeros(3, dtype=np.int16)
            for i, ch in enumerate([1,3,5]):
                volume_timing_x[i] = np.argmax(target_frames_np[:,:,ch].flatten()>self.MIN_VOLUME)
            for i, ch in enumerate([2,4,5]):
                volume_timing_y[i] = np.argmax(target_frames_np[:,:,ch].flatten()>self.MIN_VOLUME)
            print(volume_timing_x)
            print(volume_timing_y)
            
            # pra기반 MUSIC방식
            # # 수직각도 DOA, 수직으로 교차하는 두개의 평면 사용
            # X_3D_y = np.array(
            #     [
            #         pra.transform.stft.analysis(test_frames_np[:,:,ch].flatten(), self.nfft, self.nfft // 2).T
            #         for ch in [0,2,4]
            #     ]
            # )
            # X_3D_x = np.array(
            #     [
            #         pra.transform.stft.analysis(test_frames_np[:,:,ch].flatten(), self.nfft, self.nfft // 2).T
            #         for ch in [1,3,4]
            #     ]
            # )
            # print(self.doa_3d.M)
            # print(X_3D_x.shape)
            # print(X_3D_y.shape)
            # self.doa_3d.locate_sources(X_3D_x)
            # v_angle_x = self.doa_3d.azimuth_recon
            # self.doa_3d.locate_sources(X_3D_y)
            # v_angle_y = self.doa_3d.azimuth_recon
            
            # print(f"Estimated DOA v_x angles: {v_angle_x / np.pi * 180.0} degrees")
            # print(f"Estimated DOA v_y angles: {v_angle_y / np.pi * 180.0} degrees")
            
            # # 평면각 반영해서 두 평면의 각 일정비율로 반영, 공식에 대해선 고민해볼것
            # v_angle = ((np.cos(h_angle)**2)*v_angle_x + (np.sin(h_angle)**2)*v_angle_y)
            # print(f"Estimated DOA v angles: {v_angle / np.pi * 180.0} degrees")
            
            # # 자이로값 보정, 값의 덧뺄셈, 위치 등은 추후 수정
            # offset_x, offset_y = gyro.get_angle()
            # # v_angle += ((np.cos(h_angle)**2)*offset_x + (np.sin(h_angle)**2)*offset_y)
        
        # 원본콜백 호출, 모델로 추정
        # print(input_test_frames)
        if self.bt_class is not None:
            self.bt_buffer+='angle:'+str(int(h_angle[0]/np.pi*180.0))+'\n'
        return super().detect_callback(input_test_frames)

class DOA_TDOA_listener(DOA_2D_listener):
    def __init__(self, channels=6,
                 sr=16000,
                 chunk=1024,
                 record_seconds=3,
                 min_volume=1500,
                 sound_pre_offset=0.3,
                 input_model=None):
        super().__init__(channels, sr, chunk, record_seconds, min_volume, sound_pre_offset, input_model)
    
    def detect_callback(self, input_test_frames):
        # 데시벨을 인식한 청크
        t = int(len(input_test_frames)*self.SOUND_PRE_OFFSET)
        target_frames_np = np.array(input_test_frames[t-1:t+2])
        # raw데이터 채널 갯수
        volume_timing=np.zeros(4, dtype=np.int16)
        for ch in range(1,5):
            volume_timing[ch-1] = np.argmax(target_frames_np[:,:,ch].flatten()>self.MIN_VOLUME)
        print(volume_timing)
        return super().detect_callback(input_test_frames)