# 전처리
from PIL import Image
import librosa
import numpy as np

def pre_progressing_file(filename, size=[32,32]):
    padding = lambda a, i: a[:, 0:i] if a.shape[1] > i else np.hstack((a, np.zeros((a.shape[0], i-a.shape[1]))))

    if '.wav' not in filename:
        print('not .wav file')
        return
    y, sr = librosa.load(filename, sr=16000)
    print('file loaded')
    
    # 이미지 ndarray
    feat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40, norm='ortho', n_fft=2048, hop_length=512)
    # 패딩된 ndarray
    print('mfcc done')
    # feat = padding(feat, 500)
    feat = np.pad(feat, pad_width = ((0,0), (0,1501)), mode = 'constant')
    np.save('./sample.npy',feat)

    # 해당 이미지 새로 저장
    # img = Image.fromarray(padded_mfcc)
    # img = Image.fromarray(feat)
    # img = img.convert('L')
    # # resize크기 적당히 조절
    # img = img.resize(size)
    # img.save('sample.jpg','JPEG')
    # print('save done')

def pre_progressing(y, sr, size=[32,32]):
    # padding = lambda a, i: a[:, 0:i] if a.shape[1] > i else np.hstack((a, np.zeros((a.shape[0], i-a.shape[1]))))
    # 이미지 ndarray
    feat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40, norm='ortho', n_fft=2048, hop_length=512)
    # 패딩된 ndarray
    print('mfcc done')
    # feat = padding(feat, 500)
    feat = np.pad(feat, pad_width = ((0,0), (0,1501)), mode = 'constant')
    # numpy데이터를 직접쓰는 모델로 수정예정
    # img = Image.fromarray(feat)
    # img = img.convert('L')
    # # resize크기 적당히 조절
    # img = img.resize(size)

    return feat