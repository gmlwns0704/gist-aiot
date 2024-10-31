
import torch 
import torchvision 
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from PIL import Image

class ResidualBlock(nn.Module):
    def __init__ (self, filters_in, filters_out ):
        super(ResidualBlock,self).__init__()
        self.conv1 = nn.Conv2d(filters_in, filters_in, kernel_size=1, stride=1, padding=0, bias=False)
        self.bn1 = nn.BatchNorm2d(filters_in)
        self.conv2 = nn.Conv2d(filters_in, filters_in, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(filters_in)
        self.conv3 = nn.Conv2d(filters_in, filters_out, kernel_size=1, stride=1, padding=0, bias=False)
        self.bn3 = nn.BatchNorm2d(filters_out)

        # Shortcut layer
        if filters_in != filters_out:
            self.shortcut = nn.Conv2d(filters_in, filters_out, kernel_size=1, stride=1, padding=0, bias=False)
        else:
            self.shortcut = None

    def forward(self, x):
        shortcut = x

        out = F.relu(self.bn1(self.conv1(x)))
        out = F.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))

        if self.shortcut is not None:
            shortcut = self.shortcut(x)

        out += shortcut
        out = F.relu(out)
        return out
class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        # Initial Conv Layer
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(16)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Residual Blocks
        self.res_block1 = ResidualBlock(16, 32)
        self.res_block2 = ResidualBlock(32, 32)
        self.res_block3 = ResidualBlock(32, 64)
        self.res_block4 = ResidualBlock(64, 64)

        # Global Average Pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        # Fully connected layers
        self.fc1 = nn.Linear(64, 32)
        self.fc2 = nn.Linear(32, 3)

        # Dropout
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        # Initial Conv Layer
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)

        # Residual Blocks with Pooling
        x = self.res_block1(x)
        x = self.pool(x)
        x = self.res_block2(x)
        x = self.res_block3(x)
        x = self.pool(x)
        x = self.res_block4(x)

        # Global Average Pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)  # Flatten

        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)

        return x

class Rasp_Model():
    def __init__(self):    
        # Model instantiation
        self.model = CNNModel()
        self.model.load_state_dict(torch.load('./model_parameter.pth'))
        # # Loss and Optimizer
        # self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        # self.criterion = nn.CrossEntropyLoss()
        return
    
    def test(self, input):
        self.model.eval()
        return self.model(input)
    
    def test_from_image(self):
        img = Image.open('./sample.jpg').convert('L')
        return self.test(img)