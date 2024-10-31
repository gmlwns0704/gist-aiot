import numpy as np
from scipy.io.wavfile import read
import pyroomacoustics as pra

# 마이크 배열 설정 (주어진 상대 좌표 사용)
mic_positions = np.array([
    [-1, -1, 0],
    [1, 1, 0],
    [-1, 1, 0],
    [1, -1, 0],
    [0.5, 0.5, 1]
]).T

# 샘플 WAV 파일 읽기 (다중 채널 WAV 파일이어야 합니다)
fs, audio_data = read('input.wav')

# 입력 데이터 형식 변환 (samples, channels) -> (channels, samples)
audio_data = audio_data.T

# MUSIC 알고리즘을 사용하여 DOA 추정
nfft = 256  # FFT 길이
freq_bins = np.array([20, 40, 60])  # 분석할 주파수 빈 (예시)
doa = pra.doa.music.MUSIC(mic_positions, fs, nfft, c=343)

# DOA 계산
doa.locate_sources(audio_data, freq_bins=freq_bins)

# 추정된 방향 (azimuth angles in degrees)
azimuths = doa.azimuth_recon

# 결과 출력
print(f"Estimated DOA angles: {np.degrees(azimuths)} degrees")
