import os
import librosa
from pickle import TRUE
from PIL import Image
import numpy as np
import time

import mmap
import ctypes
import numpy as np
from ctypes import c_char, c_longlong, Structure

"""
pre_progressing python code
"""
padding = lambda a, i: a[:, 0:i] if a.shape[1] > i else np.hstack((a, np.zeros((a.shape[0], i-a.shape[1]))))

def pre_progressing(sound):
    print(time.time())
    # 공유메모리에서 가져오기
    # 공유 메모리에서 데이터 읽기
    # buf 데이터를 numpy 배열로 변환
    y = np.frombuffer(mmap_file[8:], dtype=np.uint8)
    # 정수 데이터 접근
    sr = mmap_file[:8]
    print(time.time())
    # 이미지 ndarray
    mfcc = librosa.feature.mfcc(y=wav, sr=sr, n_mfcc=100, n_fft=400, hop_length=160)
    # 패딩된 ndarray
    # 리사이즈 할거면 패딩 필요없음?
    print(time.time())
    padded_mfcc = padding(mfcc, 500)
    print(time.time())

    # 해당 이미지 새로 저장
    # img = Image.fromarray(padded_mfcc)
    img = Image.fromarray(mfcc)
    img = img.convert('RGB')
    # resize크기 적당히 조절
    img = img.resize([32,32])
    print(time.time())
    img.save('image.jpg','JPEG')
    print(time.time())

# 공유 메모리 열기
shm_fd = open("/dev/shm/sound_raw", "rb")
mmap_file = mmap.mmap(shm_fd.fileno(), ctypes.sizeof(Data), access=mmap.ACCESS_READ)

pre_progressing('sample.wav')