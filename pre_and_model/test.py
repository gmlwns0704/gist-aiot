import mfcc
import model
import numpy as np

print('start gen model')
model = model.Rasp_Model()
print('start mfcc')
mfcc.pre_progressing_file('./sample.wav')
print('start model eval')
result = model.test_from_image().detach().numpy()
print(np.exp(result))
print('done')