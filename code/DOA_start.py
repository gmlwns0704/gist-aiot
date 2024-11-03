import DOA_2D
import numpy as np
import pyroomacoustics as pra
import sys

listener = DOA_2D.DOA_pra_listener(
        record_seconds=int(sys.argv[1]),
        sound_pre_offset=float(sys.argv[2]),
        min_volume=int(sys.argv[3])
        )

listener.start_detect()
