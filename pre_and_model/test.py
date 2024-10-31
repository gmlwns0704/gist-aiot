import mfcc
import model

model = model.Rasp_Model()
mfcc.pre_progressing(input('filename: '))
model.test_from_image('sample.jpg')