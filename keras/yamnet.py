from torch_vggish_yamnet import yamnet
from torch_vggish_yamnet.input_proc import *
import torch 

embedding_yamnet = yamnet.yamnet(pretrained=True)

audio=torch.randn(1,16000)
converter = WaveformToInput()
in_tensor = converter(audio.float(), 16000)
in_tensor.shape

# 모델 예측
emb_yamnet, _ = embedding_yamnet(in_tensor)  # discard logits
print(emb_yamnet.shape)