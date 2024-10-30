# https://github.com/zhiim/doa_py
import numpy as np
from doa import doa

# 샘플 레이트 설정
fs = 16000

# 마이크 배열 설정
mic_positions = np.array([
    [-1, -1, 0],
    [1, 1, 0],
    [1, -1, 0],
    [-1, 1, 0]
]).T

# 오디오 파일 읽기
from scipy.io.wavfile import read
fs, audio_data = read('sample.wav')

# DOA 분석 (MUSIC 알고리즘 사용)
doa_obj = doa.Doa(mic_positions, fs, nfft=1024)
doa_obj.locate_sources(audio_data)
azimuths = doa_obj.azimuth

print(f"Estimated DOA Azimuths: {azimuths}")