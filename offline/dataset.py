import numpy as np, glob
import torch
from torch.utils.data import Dataset

class EEGWindowSet(Dataset):
    def __init__(self, npz_dir):
        self.items = []
        for f in glob.glob(f'{npz_dir}/*.npz'):
            arr = np.load(f)
            n = arr['y'].shape[0]
            self.items += [(f, i) for i in range(n)]
    def __len__(self):
        return len(self.items)
    def __getitem__(self, idx):
        f,i = self.items[idx]
        arr = np.load(f)
        spec = torch.from_numpy(arr['spec'][i])
        de   = torch.from_numpy(arr['de'][i])
        y    = torch.from_numpy(arr['y'][i]).float()
        return spec, de, y
