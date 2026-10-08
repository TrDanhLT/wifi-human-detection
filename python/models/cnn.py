import torch.nn as nn

class CSICNN(nn.Module):
    def __init__(self, window_size=50, subcarriers=52):
        super().__init__()
        self.features = nn.Sequential(nn.Conv2d(1,16,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),nn.Conv2d(16,32,3,padding=1),nn.ReLU(),nn.MaxPool2d(2))
        self.classifier = nn.Sequential(nn.Flatten(),nn.Linear(32*(window_size//4)*(subcarriers//4),64),nn.ReLU(),nn.Dropout(.3),nn.Linear(64,1))
    def forward(self,x): return self.classifier(self.features(x))
