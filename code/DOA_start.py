import DOA_2D
import numpy as np
import pyroomacoustics as pra
import sys

from bt import bt_transmit

bt_class = bt_transmit.bt_communicate()

listener = DOA_2D.DOA_pra_listener(
        record_seconds=int(sys.argv[1]),
        sound_pre_offset=float(sys.argv[2]),
        min_volume=int(sys.argv[3]),
        bt_class=bt_class
        )

listener.start_detect()
