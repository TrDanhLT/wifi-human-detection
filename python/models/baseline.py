from sklearn.ensemble import RandomForestClassifier

def build_random_forest():
    return RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced")
