from torch_vggish_yamnet import yamnet
from torch_vggish_yamnet.input_proc import *
import torch 

model = yamnet.yamnet(pretrained=True)
print(model)
model.eval()
audio=torch.randn(1,16000)

# 모델 예측
with torch.no_grad():
    predictions = model(audio) # 예측 결과 출력 print(predictions)