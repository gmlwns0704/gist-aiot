import pyaudio
import wave
import numpy as np

p = pyaudio.PyAudio()

p.open(rate=int(input('rate: ')),
       channels=int(input('channels: ')),
       format=pyaudio.paInt16,
       input=True)