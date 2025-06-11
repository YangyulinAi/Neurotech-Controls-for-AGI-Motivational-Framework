import torch, torch.nn as nn

class SpecBranch(nn.Sequential):
    def __init__(self):
        super().__init__(
            nn.Conv2d(3,16,3,padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16,32,3,padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1))
        )
    def forward(self,x):
        x = super().forward(x)
        return x.view(x.size(0), -1)

class DEBranch(nn.Sequential):
    def __init__(self):
        super().__init__(
            nn.Linear(26,64),  # input dim 26 now
            nn.ReLU()
        )
    def forward(self,x): return super().forward(x)

class TCNHead(nn.Sequential):
    def __init__(self):
        super().__init__(
            nn.Conv1d(96,128,3,padding=1), nn.ReLU(),
            nn.Conv1d(128,64,3,padding=1),  nn.ReLU(),
            nn.AdaptiveAvgPool1d(1), nn.Flatten(),
            nn.Linear(64,2)
        )
    def forward(self,x): return super().forward(x.unsqueeze(-1))

class EmotionNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.spec = SpecBranch()
        self.de   = DEBranch()
        self.head = TCNHead()
    def forward(self, spec, de):
        f = torch.cat([self.spec(spec), self.de(de)], dim=1)
        return self.head(f)
