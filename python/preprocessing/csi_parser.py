from pathlib import Path
import numpy as np
import pandas as pd

def load_csi_csv(path):
    df = pd.read_csv(Path(path))
    cols = [c for c in df.columns if c.startswith("csi_")]
    if not cols: raise ValueError(f"No csi_* columns found in {path}")
    return df[cols].to_numpy(dtype=np.float32)

def normalize_csi(x):
    return (x - x.mean(axis=0, keepdims=True)) / (x.std(axis=0, keepdims=True) + 1e-8)

def create_windows(data, window_size=50, stride=10):
    return np.asarray([data[i:i+window_size] for i in range(0,len(data)-window_size+1,stride)], dtype=np.float32)
