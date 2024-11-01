import DOA_2D
import numpy as np
import pyroomacoustics as pra

# def default_callback(self, input_test_frames):
#         #실수화(librosa는 실수값으로 작동)
#         #0번채널만 추출
#         test_frames_np_float = soundDataToFloat(np.array(input_test_frames)[:,:,0]).flatten()
#         #모델에 넣기위한 작업과정
#         feat = mfcc.pre_progressing(test_frames_np_float, self.RATE)
#         result = self.MODEL.test_by_feat(feat)
#         print(result)
#         print(self.angle)
#         return

def pyroom_callback(input_test_frames):
    nfft=256
    frame_shape=input_test_frames.shape
    X = np.array(
        [
            pra.transform.stft.analysis(signal.T.flattn(), nfft, nfft // 2).T
            for signal in input_test_frames.T
        ]
    )
    return

record_seconds=int(input('record seconds(int): ')),
sound_pre_offset=float(input('sound_pre_offset(float): ')),
min_volume=int(input('min_volume(int): '))

listener = DOA_2D.DOA_2D_listener(
    record_seconds=record_seconds,
    sound_pre_offset=sound_pre_offset,
    min_volume=min_volume
)

listener.start_detect()


listener_pyroom = DOA_2D.DOA_2D_listener(
    record_seconds=record_seconds,
    sound_pre_offset=sound_pre_offset,
    min_volume=min_volume,
)