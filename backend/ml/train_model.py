from pathlib import Path
import json
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.datasets import make_classification

# Feature definitions used by the prediction module
FEATURES = [
    "Age",
    "Frequency",
    "Medicine_Dose",
    "Previous_Medicine_Missed_Count",
    "Avg_Past_Confirmation_Delay_Minutes",
    "Confirmation_Channel",
]   
TARGET = "Missed_Dose"

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
META_PATH = Path(__file__).resolve().parent / "model_metrics.json"

def train_model():
    """Train a RandomForest model on synthetic data.
    This avoids the heavy pandas dependency and allows the project to run
    in environments without compiled extensions.
    """
    # Generate synthetic data matching the feature schema.
    X, y = make_classification(
        n_samples=2000,
        n_features=len(FEATURES),
        n_informative=4,
        n_redundant=0,
        n_classes=2,
        random_state=42,
        flip_y=0.1,
    )
    # Simulate categorical "Frequency" as values 1, 2, 3
    X = X.astype(float)
    freq = (np.arange(X.shape[0]) % 3) + 1
    X[:, 1] = freq

    # Column indices for numeric and categorical features
    numeric_idx = [0, 2, 3, 4]  # Age, Medicine_Dose, Previous_Medicine_Missed_Count, Avg_Past_Confirmation_Delay_Minutes
    categorical_idx = [1, 5]    # Frequency, Confirmation_Channel

    prep = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), numeric_idx),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_idx),
    ])

    model = Pipeline([
        ("preprocess", prep),
        ("classifier", RandomForestClassifier(n_estimators=160, random_state=42, class_weight="balanced")),
    ])

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)

    metrics = {
        "accuracy": accuracy_score(y_test, predicted),
        "precision": precision_score(y_test, predicted, zero_division=0),
        "recall": recall_score(y_test, predicted, zero_division=0),
        "f1": f1_score(y_test, predicted, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
        "target_distribution": {0: int((y_test == 0).sum()), 1: int((y_test == 1).sum())},
        "features": FEATURES,
    }

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    META_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    print(json.dumps(train_model(), indent=2))
