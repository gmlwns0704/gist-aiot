import mfcc
import model

print('start gen model')
model = model.Rasp_Model()
print('start mfcc')
mfcc.pre_progressing_file('/home/rasp/venv/gist-aiot/code/output_channel_1.wav')
print('start model eval')
print(model.test_from_image())
print('done')