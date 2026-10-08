from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; path=ROOT/'data/raw/human/simulated_human.csv'
df=pd.read_csv(path); cols=[c for c in df.columns if c.startswith('csi_')]
plt.figure(figsize=(12,5))
for c in cols[:10]: plt.plot(df[c],alpha=.5,label=c)
plt.title('Example CSI channels'); plt.xlabel('CSI packet'); plt.ylabel('CSI value'); plt.legend(); plt.tight_layout(); plt.show()
