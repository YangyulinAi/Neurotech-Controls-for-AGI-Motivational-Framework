import argparse
import os
import json

import mne
import numpy as np
from scipy.signal import cheby2, sosfiltfilt, stft


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--inp', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--sfreq', type=int, default=128)
    p.add_argument('--win', type=float, default=5.0)
    p.add_argument('--stride', type=float, default=2.5)
    return p.parse_args()


def bandpass(data, fs, low=0.5, high=45, order=4):
    nyq = 0.5 * fs
    sos = cheby2(order, 20, [low / nyq, high / nyq], btype='bandpass', output='sos')
    return sosfiltfilt(sos, data, axis=-1)


def extract_feats(window, fs):
    # Spectrogram branch
    _, _, Z = stft(window, fs, nperseg=fs // 2, noverlap=fs // 4)
    spec = np.log1p(np.abs(Z))  # (C, F, T)
    spec = spec.mean(axis=0)  # collapse channel → (F, T)
    spec = spec[:224, :224]  # crop/resize
    spec3 = np.stack([spec] * 3, axis=0).astype('float32')  # (3, H, W)

    # Differential Entropy branch
    bands = [(1, 4), (4, 8), (8, 13), (13, 30), (30, 45)]
    de = []
    for low, high in bands:
        bp = bandpass(window, fs, low, high)
        var = np.var(bp, axis=-1) + 1e-6
        de.append(0.5 * np.log(2 * np.pi * np.e * var))
    # de: list of length 5, each an array of length C; collapse by mean
    de = np.array(de)  # shape (5, C)
    de_vec = de.mean(axis=1)  # (5,)

    # Frontal Alpha Asymmetry (FAA)
    # adjust these channel indices to your montage:
    idx_af7, idx_af8 = 0, 1
    left_a = np.var(bandpass(window[idx_af7], fs, 8, 13))
    right_a = np.var(bandpass(window[idx_af8], fs, 8, 13))
    faa = np.log(left_a + 1e-6) - np.log(right_a + 1e-6)

    de_vec = np.concatenate([de_vec, [faa]]).astype('float32')  # (6,)
    # repeat or pad to length 26 if needed; here we tile:
    de_vec = np.tile(de_vec, 5)[:26]

    return spec3, de_vec


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    mp = os.path.join(args.inp, 'subject2_labels.json')
    label_map = json.load(open(mp))

    win = int(args.sfreq * args.win)
    step = int(args.sfreq * args.stride)

    for fname in os.listdir(args.inp):
        if not fname.endswith('.set'): continue
        key = os.path.splitext(fname)[0]
        v, a = label_map[key]['valence'], label_map[key]['arousal']

        raw = mne.io.read_raw_eeglab(os.path.join(args.inp, fname), preload=True, verbose='ERROR')
        raw.resample(args.sfreq)
        data = bandpass(raw.get_data(), args.sfreq)  # (C, N)

        specs, des, ys = [], [], []
        for i in range(0, data.shape[1] - win + 1, step):
            w = data[:, i:i + win]
            spec3, de26 = extract_feats(w, args.sfreq)
            specs.append(spec3)
            des.append(de26)
            ys.append((v, a))

        specs = np.stack(specs, axis=0)  # (n,3,H,W)
        des = np.stack(des, axis=0)  # (n,26)
        ys = np.array(ys, dtype='float32')  # (n,2)

        np.savez(os.path.join(args.out, key + '.npz'),
                 spec=specs, de=des, y=ys)
        print(f"{key}: {specs.shape[0]} windows")


if __name__ == '__main__':
    main()
