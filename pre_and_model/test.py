import mfcc
import model

print('start gen model')
model = model.Rasp_Model()
print('start mfcc')
mfcc.pre_progressing('/home/rasp/venv/gist-aiot/output_channel_1.wav')
print('start model eval')
model.test_from_image('sample.jpg')
print('done')