# 전처리
from PIL import Image
import librosa
import numpy as np
def pre_progressing(filename, size=[32,32]):
    padding = lambda a, i: a[:, 0:i] if a.shape[1] > i else np.hstack((a, np.zeros((a.shape[0], i-a.shape[1]))))

    if '.wav' not in filename:
        print('not .wav file')
        return
    y, sr = librosa.load(filename, sr=16000)
    # 이미지 ndarray
    feat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=100, n_fft=400, hop_length=160)
    # 패딩된 ndarray
    feat = padding(feat, 500)

    # 해당 이미지 새로 저장
    # img = Image.fromarray(padded_mfcc)
    img = Image.fromarray(feat)
    img = img.convert('L')
    # resize크기 적당히 조절
    img = img.resize(size)
    img.save('sample.jpg','JPEG')
