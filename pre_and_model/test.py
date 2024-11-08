import mfcc
import model

print('start gen model')
model = model.Rasp_Model()
print('start mfcc')
mfcc.pre_progressing_file('./sample.wav')
print('start model eval')
result = model.test_from_image()
print(10**result)
print('done')