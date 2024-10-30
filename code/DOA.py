# https://github.com/zhiim/doa_py
import numpy as np
from scipy.io.wavfile import read

from doa_py import arrays, signals
from doa_py.algorithm import music
from doa_py.plot import plot_spatial_spectrum

# 마이크배열 좌표설정
mic_positions=np.array([
    [-1,-1,0],
    [-1,1,0],
    [1,-1,0],
    [1,1,0]
]).T

elem_x=mic_positions[0,:]
elem_y=mic_positions[1,:]
elem_z=mic_positions[2,:]

ula = arrays.Array(elem_x,elem_y,elem_z)
print(ula._element_position)

# WAV 파일 읽기
fs, audio_data = read('sample.wav')
print(audio_data.shape)

# Simulate the received data
received_data = np.array(audio_data).T

# Calculate the MUSIC spectrum
angle_grids = np.arange(-180, 180, 1)
spectrum = music(
    received_data=received_data,
    num_signal=1,
    array=ula,
    signal_fre=1000,
    angle_grids=angle_grids,
    unit="deg",
)

# Plot the spatial spectrum
plot_spatial_spectrum(
    spectrum=spectrum,
    ground_truth=np.array([0, 30]),
    angle_grids=angle_grids,
    num_signal=2,
)

estimated_angle = angle_grids[np.argmax(spectrum)]  # 신호 1개의 최대값 추출
print(f"Estimated DOA Angle: {estimated_angle:.2f} degrees")