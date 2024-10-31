import DOA_2D

listener = DOA_2D.DOA_2D_listener(
    record_seconds=int(input('record seconds(int): ')),
    sound_pre_offset=float(input('sound_pre_offset(float): ')),
    min_volume=int(input('min_volume(int): '))
)

listener.start_detect()