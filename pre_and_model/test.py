import mfcc
import model

print('start gen model')
model = model.Rasp_Model()
print('start mfcc')
mfcc.pre_progressing(input('filename: '))
print('start model eval')
model.test_from_image('sample.jpg')
print('done')