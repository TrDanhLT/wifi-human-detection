from pathlib import Path
import argparse, joblib, numpy as np, pandas as pd, sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"python"))
from preprocessing.csi_parser import normalize_csi, create_windows
ap=argparse.ArgumentParser(); ap.add_argument("--csv",required=True); a=ap.parse_args()
df=pd.read_csv(a.csv); cols=[c for c in df.columns if c.startswith("csi_")]
w=create_windows(normalize_csi(df[cols].to_numpy(dtype=np.float32)))
F=np.concatenate([w.mean(1),w.std(1),w.min(1),w.max(1)],axis=1)
p=joblib.load(ROOT/"models/random_forest.joblib").predict_proba(F)[:,1]
for i,v in enumerate(p): print(f"Window {i:04d}: {'HUMAN' if v>=.5 else 'NO HUMAN'} | probability={v:.3f}")
