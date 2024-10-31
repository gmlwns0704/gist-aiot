import numpy as np
from scipy.io.wavfile import read
import pyroomacoustics as pra

# 샘플 WAV 파일 읽기
fs, audio_data = read('output_selected_channels.wav')

# FFT 길이 설정
nfft = 256

chunk_size=4096

# 주파수 분해능 계산
# frequency_resolution = fs / nfft
# print(f"주파수 분해능: {frequency_resolution} Hz")
print(audio_data.shape)

# 마이크 배열 설정 (주어진 좌표 사용)
mic_positions = np.array([
    [-1, -1, 0],
    [1, 1, 0],
    [-1, 1, 0],
    [1, -1, 0]
]).T  # (3, M) 형식으로 변환

# 청크 단위로 오디오 데이터를 분할
audio_data_chunks = [audio_data[i:i+chunk_size, :] for i in range(0, audio_data.shape[0], chunk_size)]
print(f"총 청크 수: {len(audio_data_chunks)}")

# MUSIC 알고리즘을 사용하여 DOA 추정
doa = pra.doa.music.MUSIC(mic_positions, fs, nfft=nfft, c=343)

# S 값을 설정 (총 청크 수에서 적절한 값으로 설정)
S = min(len(audio_data_chunks), 100)
print(f"사용할 스냅샷 수(S): {S}")

# 분할된 청크 확인 및 DOA 추정
for i, chunk in enumerate(audio_data_chunks):
    print(f"Chunk {i+1}: shape {chunk.shape}")
    if chunk.shape[0] < nfft:
        continue  # 청크의 크기가 FFT 길이보다 작은 경우 건너뜀
    X = np.array(
        [
            pra.transform.stft.analysis(signal, nfft, nfft // 2).T
            for signal in chunk.T
        ]
    )
    print(X.shape)
    doa.locate_sources(X)
    azimuth = doa.azimuth_recon

    if azimuth is not None:
        print(f"Estimated DOA angles: {azimuth*np.pi/180} degrees")
    else:
        print("DOA estimation failed.")