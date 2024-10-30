import numpy as np
from pyroomacoustics.doa import MUSIC
from pyroomacoustics.beamforming import Beamformer

class DOA:
    def __init__(self):
        mic_position = np.array([
            [0,0,0],
            [1,0,0],
            [1,1,0],
            [0,1,0],
            [0.5,0.5,0.5]
        ])
        self.music_instance=MUSIC(L=mic_position,
                    fs=16000,
                    nfft=256 #값 수정 고려? 커질수록 정확하고 느려짐?
                    num_src=1, #근원지 갯수
                    dim=3
                    )

    def get_direction(self,audio_data):
        # X (numpy array) – Set of signals in the frequency (RFFT) domain for current frame. Size should be M x F x S, where M should correspond to the number of microphones, F to nfft/2+1, and S to the number of snapshots (user-defined). It is recommended to have S >> M.
        self.music_instance.locate_sources(audio_data)