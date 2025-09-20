import torch, torch.nn as nn

class SpecBranch(nn.Sequential):
    def __init__(self, dropout_rate=0.2):
        super().__init__(
            nn.Conv2d(3,16,3,padding=1), nn.BatchNorm2d(16), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(dropout_rate),
            nn.Conv2d(16,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1)), nn.Dropout2d(dropout_rate)
        )
    def forward(self,x):
        x = super().forward(x)
        return x.view(x.size(0), -1)

class DEBranch(nn.Module):
    def __init__(self, dropout_rate=0.2, use_batch_norm=False):
        super().__init__()
        layers = []
        layers.append(nn.Linear(26, 64))
        if use_batch_norm:
            layers.append(nn.BatchNorm1d(64))
        layers.extend([nn.ReLU(), nn.Dropout(dropout_rate)])
        
        layers.append(nn.Linear(64, 64))
        if use_batch_norm:
            layers.append(nn.BatchNorm1d(64))
        layers.extend([nn.ReLU(), nn.Dropout(dropout_rate)])
        
        self.layers = nn.Sequential(*layers)
    def forward(self, x): 
        return self.layers(x)

class TCNHead(nn.Sequential):
    def __init__(self, dropout_rate=0.2):
        super().__init__(
            nn.Conv1d(96,128,3,padding=1), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Conv1d(128,64,3,padding=1), nn.BatchNorm1d(64), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1), nn.Flatten(),
            nn.Dropout(dropout_rate),
            nn.Linear(64,32), nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(32,2)
        )
    def forward(self,x): return super().forward(x.unsqueeze(-1))

class EmotionNet(nn.Module):
    def __init__(self, dropout_rate=0.2, use_batch_norm=False):
        super().__init__()
        self.spec = SpecBranch(dropout_rate)
        self.de   = DEBranch(dropout_rate, use_batch_norm)
        self.head = TCNHead(dropout_rate)
    def forward(self, spec, de):
        f = torch.cat([self.spec(spec), self.de(de)], dim=1)
        return self.head(f)