from pathlib import Path
import sys, numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"python"))
from preprocessing.csi_parser import load_csi_csv, normalize_csi, create_windows
RAW, OUT = ROOT/"data/raw", ROOT/"data/processed"
OUT.mkdir(parents=True, exist_ok=True)
Xs, ys = [], []
for name, label in [("no_human",0),("human",1)]:
    for path in sorted((RAW/name).glob("*.csv")):
        x = create_windows(normalize_csi(load_csi_csv(path)))
        if len(x): Xs.append(x); ys.append(np.full(len(x),label,dtype=np.int64))
if not Xs: raise RuntimeError("No CSI CSV files found. Run collector/simulator.py first.")
X, y = np.concatenate(Xs), np.concatenate(ys)
np.save(OUT/"X.npy",X); np.save(OUT/"y.npy",y)
print("X:",X.shape,"y:",y.shape)
