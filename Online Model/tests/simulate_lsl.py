#!/usr/bin/env python3
# online/tests/simulate_lsl.py

import os
import sys
import time

import mne
from pylsl import StreamInfo, StreamOutlet


BASE_DIR = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
RAW_DIR  = os.path.join(BASE_DIR, 'data', 'raw')
if not os.path.isdir(RAW_DIR):
    raise RuntimeError(f"No such directory: {RAW_DIR}")


set_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.set')]
if not set_files:
    raise RuntimeError(f"No .set files found in {RAW_DIR}")
set_path = os.path.join(RAW_DIR, set_files[0])
print(f"[simulate_lsl] Loading {set_path}")


raw = mne.io.read_raw_eeglab(set_path, preload=True, verbose='ERROR')
raw.resample(256)  # 与 online/config/runtime.yaml 中 sampling_rate 保持一致
data = raw.get_data().T          # 转成 (n_times, n_channels)
fs   = int(raw.info['sfreq'])
n_ch = data.shape[1]
print(f"[simulate_lsl] Data shape: {data.shape}, Sampling rate: {fs} Hz")


info   = StreamInfo(name='EEG', type='EEG',
                    channel_count=n_ch,
                    nominal_srate=fs,
                    channel_format='float32',
                    source_id='simulate_raw')
outlet = StreamOutlet(info)
print(f"[simulate_lsl] Streaming on LSL stream 'EEG' ({n_ch} channels) at {fs} Hz")


interval = 1.0 / fs
for sample in data:
    outlet.push_sample(sample.tolist())
    time.sleep(interval)

print("[simulate_lsl] Finished streaming all samples.")
