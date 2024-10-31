import numpy as np
from scipy.io.wavfile import read
import pyroomacoustics as pra

# 샘플 WAV 파일 읽기
fs, audio_data = read('output_selected_channels.wav')

# FFT 길이 설정
# nfft = 32

# 주파수 분해능 계산
frequency_resolution = fs / nfft
print(f"주파수 분해능: {frequency_resolution} Hz")
print(audio_data.shape)

# 마이크 배열 설정 (주어진 좌표 사용)
mic_positions = np.array([
    [-1, -1, 0],
    [1, 1, 0],
    [-1, 1, 0],
    [1, -1, 0]
]).T  # (3, M) 형식으로 변환

# MUSIC 알고리즘을 사용하여 DOA 추정
doa = pra.doa.music.MUSIC(mic_positions, fs, c=343)

# 음원 방향 추정 (데이터를 FFT 길이에 맞춰 분할)
# audio_data_chunks = [audio_data[:, i:i+nfft] for i in range(0, audio_data.shape[1], nfft)]
# print(audio_data_chunks)
# print(len(audio_data_chunks))

doa.locate_sources(audio_data.T)
azimuths = doa.azimuth_recon
# doa.azimuth_recon contains the reconstructed location of the source
print("  Recovered azimuth:", doa.azimuth_recon / np.pi * 180.0, "degrees")