from pathlib import Path
import pandas as pd

FEATURES = [
    "Age", "Frequency", "Medicine_Dose", "Previous_Medicine_Missed_Count",
    "Avg_Past_Confirmation_Delay_Minutes", "Confirmation_Channel"
]
TARGET = "Missed_Dose"


def load_dataset(path: str | Path) -> pd.DataFrame:
    frame = pd.read_excel(path)
    # Basic numeric cleaning
    frame["Age"] = pd.to_numeric(frame["Age"], errors="coerce").fillna(frame["Age"].median())
    frame["Previous_Medicine_Missed_Count"] = pd.to_numeric(frame["Previous_Medicine_Missed_Count"], errors="coerce").fillna(0)
    frame["Avg_Past_Confirmation_Delay_Minutes"] = pd.to_numeric(frame["Avg_Past_Confirmation_Delay_Minutes"], errors="coerce").fillna(0)
    # Convert dosage to numeric (extract number)
    frame["Medicine_Dose"] = (
        frame["Medicine_Dose"].astype(str)
        .str.extract(r"(\d+(?:\.\d+)?)", expand=False)
        .astype(float)
        .fillna(0)
    )
    # Frequency may be textual like "Once daily"; extract numeric frequency if present, otherwise default 1
    frame["Frequency"] = (
        frame["Frequency"].astype(str)
        .str.extract(r"(\d+)", expand=False)
        .astype(float)
        .fillna(1)
    )
    # Map Missed_Dose Yes/No to binary
    if frame[TARGET].dtype == object:
        frame[TARGET] = frame[TARGET].str.strip().str.lower().map({"yes": 1, "no": 0}).fillna(0).astype(int)
    else:
        frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce").fillna(0).astype(int)
    return frame
