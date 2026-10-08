from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw"
RNG = np.random.default_rng(42)
N_SAMPLES, N_SUBCARRIERS = 5000, 52

def make_record(label):
    data = RNG.normal(0, 1, (N_SAMPLES, N_SUBCARRIERS))
    if label == "human":
        for start, end, strength in [(1800,2600,2.5),(3500,4300,1.8)]:
            data[start:end] += RNG.normal(0, strength, (end-start,N_SUBCARRIERS))
            data[start:end] += np.sin(np.linspace(0,3*np.pi,N_SUBCARRIERS))
    df = pd.DataFrame(data, columns=[f"csi_{i}" for i in range(N_SUBCARRIERS)])
    df.insert(0, "label", int(label == "human"))
    return df

for label in ("no_human", "human"):
    folder = OUT / label
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"simulated_{label}.csv"
    make_record(label).to_csv(path, index=False)
    print("Wrote", path)
