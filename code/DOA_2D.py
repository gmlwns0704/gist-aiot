import pyaudio
import audioop
import numpy as np
import time
import sys
import threading
import time

import pyroomacoustics as pra
# import noisereduce as nr

from bt import bt_transmit

sys.path.append('/home/rasp/venv/')
sys.path.append('/home/rasp/venv/gist-aiot/')

import pre_and_model.mfcc as mfcc
import pre_and_model.model as model
# import gyro

# mfcc를 위해 실수형으로 교체
# https://www.kaggle.com/discussions/general/213391
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
                 volume_gap_rate=1.3,
                 sound_pre_offset=0.3,
                 input_model=None,
                 bt_class=None,
                 estimate_rate=0.5,
                 multi_frames_num=3):
        self.FORMAT = pyaudio.paInt16
        self.RESP_CHANNELS = 6
        self.RATE = sr
        self.CHUNK = chunk
        self.RECORD_SECONDS = record_seconds
        self.volume_gap_rate=volume_gap_rate
        self.SOUND_PRE_OFFSET=sound_pre_offset
        self.estimate_rate=estimate_rate
        
        print('setting detect values')
        self.detected = False
        self.start_detect_callback = False
        
        print('setting chunks values')
        self.chunk_count = 0
        self.max_chunk_count = int((self.RATE/self.CHUNK)*self.RECORD_SECONDS)
        self.chunks = np.zeros([self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        print(self.max_chunk_count)
        print(self.chunks.shape)
        
        self.filter = np.zeros((5, self.CHUNK), dtype=np.int16)
        
        print('setting multi frames')
        self.multi_frames_num = multi_frames_num
        self.multi_frames = np.zeros([self.multi_frames_num, self.max_chunk_count, self.CHUNK, 5], dtype=np.int16)
        # 0 준비안됨, 1준비됨, 2작동중, 3완료됨, 4녹음중
        self.multi_frames_check = np.zeros([self.multi_frames_num], dtype=np.int8)
        self.multi_frames_angle = np.zeros([self.multi_frames_num])
        self.multi_frames_reult_class = np.zeros([self.multi_frames_num], dtype=np.int32)
        self.multi_frames_reult_value = np.zeros([self.multi_frames_num])
        self.multi_frames_range = np.zeros([self.multi_frames_num],dtype=np.int32)
        print(self.multi_frames_num)
        print(self.multi_frames.shape)
        print(self.multi_frames_check)
        
        print('setting mean volume')
        self.mean_volume = 0
        
        # 소리 녹음 시작이후 최소딜레이
        self.record_delay = 0
        
        print('setting vt values')
        self.bt_class = bt_class
        self.bt_buffer = ''
        
        window_size = 5
        self.window = np.ones(window_size)/window_size
        
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
    
    def threading_detect_callback(self, i):
        # print('thread ['+str(i)+'] started')
        while True:
            self.events[i].wait()
            self.multi_frames_reult_class[i], self.multi_frames_reult_value[i] = self.detect_callback(self.multi_frames[i], i)
            # print('thread callback done '+str(i))
            self.multi_frames_check[i]=3
            self.events[i].clear()         
    
    def start_detect(self):
        print("detection started")
        print('multithread ready')
        # 타겟클래스
        target_class = [1,8]
        # 멀티스레드
        self.events = []
        self.threads = []
        for i in range(self.multi_frames_num): 
            self.events.append(threading.Event())
            self.threads.append(threading.Thread(target=self.threading_detect_callback, args=(i,)))
            self.threads[i].start()
        
        while True:
            for i in range(self.multi_frames_num):
                # print(self.multi_frames_check[i])
                # 버퍼가 준비됐으므로 스레드 실행
                if self.multi_frames_check[i] == 1:
                    # 스레드 작동중
                    self.multi_frames_check[i] = 2
                    # print('start thread ['+str(i)+']')
                    self.events[i].set()
                elif self.multi_frames_check[i] == 3:
                    print(self.multi_frames_angle[i])
                    print(self.multi_frames_reult_class[i])
                    print(self.multi_frames_reult_value[i])
                    if self.bt_class is not None:
                        if self.multi_frames_reult_value[i] > self.estimate_rate and self.multi_frames_reult_class[i] in target_class:
                            self.bt_buffer += 'angle:'+str(self.multi_frames_angle[i])+'\n'
                            self.bt_buffer += 'class:'+str(self.multi_frames_reult_class[i])+'\n'
                            print(self.bt_buffer)
                            self.bt_class.send(self.bt_buffer)
                            self.bt_buffer=''
                    self.multi_frames_check[i] = 0
            
            time.sleep(0.1)
            # print(self.multi_frames_check)
            # print(self.multi_frames_range)
        return
    
    
    def detect_callback(self, input_test_frames, i):
        # print('detect callback called')
        input_test_frames_ch0 = input_test_frames[:,:,0].copy()
        feat = mfcc.pre_progressing(input_test_frames_ch0, self.RATE)
        result = self.MODEL.test_by_feat(feat)
        
        estimated = np.exp(result.detach().numpy()[0,:])
        # print(estimated)
        # print(np.sum(estimated))
        estimated_class = int(np.argmax(estimated))
    
        # print(self.angle)
        return estimated_class, estimated[estimated_class]
    
    def non_blocking_callback(self, in_data, frame_count, time_info, status):
        # 녹음 후 청크 저장
        raw_np_data = np.frombuffer(in_data, dtype=np.int16).reshape(-1, self.RESP_CHANNELS)
        # 이동평균필터 노이즈제거
        np_data = raw_np_data.copy()
        for i in [1,2,3,4]:
            np_data[:,i] = np.convolve(raw_np_data[:,i], self.window, mode='same')
        #데이터 읽음
        self.chunks[self.chunk_count,:,0:5] = np_data[:,0:5]
        
        # 한바퀴 돌았음
        for j in range(self.multi_frames_num):
            if self.multi_frames_check[j] == 4 and self.multi_frames_range[j] == self.chunk_count:
                # print('thread '+str(j)+' record done')
                self.multi_frames[j,:self.chunk_count,:,0:5] = self.chunks[self.max_chunk_count-self.chunk_count:,:,0:5]
                self.multi_frames[j,self.chunk_count:,:,0:5] = self.chunks[:self.max_chunk_count-self.chunk_count,:,0:5]
                self.multi_frames_check[j] = 1
        
        # weighted= waveform_analysis.A_weight(np_data, self.RATE)
        # volume=audioop.rms(weighted.flatten(),2)
        volume=audioop.rms(np_data[1].flatten(),2)
        self.mean_volume += (volume-self.mean_volume)*0.1
        # print(str(volume)+'/'+str(self.mean_volume))
        # detected
        if self.record_delay <= 0:
            if volume>self.mean_volume*self.volume_gap_rate:
                # print('sound detected!')
                x=int(self.max_chunk_count*self.SOUND_PRE_OFFSET)
                # 이용가능 스레드 탐색
                for j in range(self.multi_frames_num):
                    if self.multi_frames_check[j] == 0:
                        # print('found thread '+str(j))
                        if self.chunk_count >= x:
                            self.multi_frames_range[j] = self.chunk_count-x
                        else:
                            self.multi_frames_range[j] = self.max_chunk_count-x+self.chunk_count
                        # 녹음중 표시
                        self.record_delay = int(0.2*self.max_chunk_count)
                        self.multi_frames_check[j] = 4
                        break
        else:
            self.record_delay -= 1
        # 루프
        self.chunk_count = (self.chunk_count+1)%self.max_chunk_count
        
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
                 volume_gap_rate=1.3,
                 sound_pre_offset=0.3,
                 input_model=None,
                 bt_class=None,
                 nfft=256,
                 mic_positions=None,
                 dim=2,
                 dim3_sr=48000,
                 estimate_rate=0.5,
                 multi_frames_num=3):
        super().__init__(channels=channels,
                         sr=sr,
                         chunk=chunk,
                         record_seconds=record_seconds,
                         volume_gap_rate=volume_gap_rate,
                         sound_pre_offset=sound_pre_offset,
                         input_model=input_model,
                         bt_class=bt_class,
                         estimate_rate=estimate_rate,
                         multi_frames_num=multi_frames_num)
        self.nfft=nfft
        self.dim=dim
        self.dim3_sr=dim3_sr
        self.dim3_chunk=int(self.CHUNK*(self.dim3_sr/self.RATE))
        
        # print(self.multi_frames_check)
        
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
        
        self.doa=pra.doa.music.MUSIC(self.mic_positions,
                                     self.RATE,
                                     nfft=self.nfft,
                                     c=343)
        
        if dim == 3:
            print('dims 3 is not supported!')
            quit()
            # self.doa_3d=pra.doa.music.MUSIC(self.mic_3d_positions,
            #                             self.RATE,
            #                             nfft=self.nfft,
            #                             c=343)
        return
    
    def detect_callback(self, input_test_frames, i):
        # print(input_test_frames)
        test_frames_np = np.array(input_test_frames)
        # print(test_frames_np.shape)
        X = np.array(
            [
                pra.transform.stft.analysis(test_frames_np[:,:,ch].flatten(), self.nfft, self.nfft // 2).T
                for ch in [1,2,3,4]
            ]
        )
        # print(X.shape)
        # 평면좌표 구하기
        self.doa.locate_sources(X)
        h_angle = self.doa.azimuth_recon
        # print(f"Estimated DOA angles: {h_angle / np.pi * 180.0} degrees")
        
        if self.dim == 3:
            print('dim 3 is not supported for now!')
            exit()
        
        self.multi_frames_angle[i] = 360-int(h_angle[0]/np.pi*180.0)
        return super().detect_callback(input_test_frames, i)

# class DOA_TDOA_listener(DOA_2D_listener):
#     def __init__(self, channels=6,
#                  sr=16000,
#                  chunk=1024,
#                  record_seconds=3,
#                  min_volume=1500,
#                  sound_pre_offset=0.3,
#                  input_model=None):
#         super().__init__(channels, sr, chunk, record_seconds, min_volume, sound_pre_offset, input_model)
    
#     def detect_callback(self, input_test_frames):
#         # 데시벨을 인식한 청크
#         t = int(len(input_test_frames)*self.SOUND_PRE_OFFSET)
#         target_frames_np = np.array(input_test_frames[t-1:t+2])
#         # raw데이터 채널 갯수
#         volume_timing=np.zeros(4, dtype=np.int16)
#         for ch in range(1,5):
#             volume_timing[ch-1] = np.argmax(target_frames_np[:,:,ch].flatten()>self.volume_gap_rate)
#         print(volume_timing)
#         return super().detect_callback(input_test_frames)