import DOA_2D
import numpy as np
import pyroomacoustics as pra
import sys

from bt import bt_transmit

bt_class = bt_transmit.bt_communicate()

listener = DOA_2D.DOA_pra_listener(
        record_seconds=float(sys.argv[1]),
        sound_pre_offset=float(sys.argv[2]),
        volume_gap_rate=float(sys.argv[3]),
        bt_class=bt_class,
        estimate_rate=float(sys.argv[4]),
        multi_frames_num=int(sys.argv[5])
        )

listener.start_detect()
