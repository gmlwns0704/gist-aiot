
import torch 
import torchvision 
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.transforms as transforms

import numpy as np

from PIL import Image

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0, bias=False)
        self.bn1 = nn.BatchNorm2d(in_channels)
        
        self.conv2 = nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(in_channels)
        
        self.conv3 = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=False)
        self.bn3 = nn.BatchNorm2d(out_channels)
        
        self.shortcut = None
        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=False)

    def forward(self, x):
        shortcut = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.bn3(self.conv3(x))
        
        if self.shortcut is not None:
            shortcut = self.shortcut(shortcut)
            
        x += shortcut
        return F.relu(x)


class Resnet_block3(nn.Module):
    def __init__(self):
        super(Resnet_block3, self).__init__()
        
        self.conv1 = nn.Conv2d(1, 64, kernel_size=7, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.res_block1 = ResidualBlock(64, 128)
        self.res_block2 = ResidualBlock(128, 128)
        self.res_block3 = ResidualBlock(128,64)

        
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))  # 어떤 입력 크기든 평균 풀링으로 1x1로 변환
        
        self.fc1 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.dropout = nn.Dropout(0.5)
        
        self.fc2 = nn.Linear(32, 10)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        
        x = self.res_block1(x)
        x = self.pool(x)
        
        x = self.res_block2(x)
        x = self.pool(x)
        
        x = self.res_block3(x)
        x = self.pool(x)
        
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)  # Flatten
        
        x = F.relu(self.bn2(self.fc1(x)))
        x = self.dropout(x)
        
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class Rasp_Model():
    def __init__(self):    
        # Model instantiation
        self.model = Resnet_block3()
        self.model.load_state_dict(torch.load('/home/rasp/venv/gist-aiot/pre_and_model/model_parameter.pth', map_location=torch.device('cpu')))
        # # Loss and Optimizer
        # self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        # self.criterion = nn.CrossEntropyLoss()
        # 모델 맞춤형 트랜스포머
        # self.img_transform = transforms.Compose([
        #     transforms.Resize((32, 32)),          # 모델에 맞는 크기로 조정
        #     transforms.Grayscale(num_output_channels=3),  # 3채널로 변환
        #     transforms.ToTensor()
        # ])
        return
    
    def test_by_feat(self, data):
        self.model.eval()
        # numpy를 입력으로 받는 모델에 맞춰 수정
        # input_tensor = self.img_transform(img).unsqueeze(0)
        input_tensor = torch.Tensor(data).unsqueeze(0).unsqueeze(0)
        # print(input_tensor)
        # print(input_tensor.shape)
        return self.model(input_tensor)
    
    def test_from_image(self):
        data = np.load('./sample.npy')
        print(data.shape)
        print('np load done')
        # 이미지를 텐서로 변환
        # input_tensor = torch.Tensor(data).unsqueeze(0).unsqueeze(0)
        # print(input_tensor.shape)
        # print('transform done')
        self.model.eval()
        return self.model(data)