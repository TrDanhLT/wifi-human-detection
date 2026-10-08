from pathlib import Path
import sys, joblib, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"python"))
from models.baseline import build_random_forest
X=np.load(ROOT/"data/processed/X.npy"); y=np.load(ROOT/"data/processed/y.npy")
F=np.concatenate([X.mean(1),X.std(1),X.min(1),X.max(1)],axis=1)
Xtr,Xte,ytr,yte=train_test_split(F,y,test_size=.2,random_state=42,stratify=y)
m=build_random_forest(); m.fit(Xtr,ytr); p=m.predict(Xte)
print("Accuracy:",accuracy_score(yte,p)); print(classification_report(yte,p,target_names=["NO HUMAN","HUMAN"]))
(ROOT/"models").mkdir(exist_ok=True); joblib.dump(m,ROOT/"models/random_forest.joblib")
