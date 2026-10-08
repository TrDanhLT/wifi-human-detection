from pathlib import Path
import joblib, numpy as np
from sklearn.metrics import classification_report, confusion_matrix
ROOT=Path(__file__).resolve().parents[2]
X=np.load(ROOT/"data/processed/X.npy"); y=np.load(ROOT/"data/processed/y.npy")
F=np.concatenate([X.mean(1),X.std(1),X.min(1),X.max(1)],axis=1)
p=joblib.load(ROOT/"models/random_forest.joblib").predict(F)
print(classification_report(y,p,target_names=["NO HUMAN","HUMAN"])); print(confusion_matrix(y,p))
