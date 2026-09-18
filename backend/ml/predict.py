from pathlib import Path



import joblib
from pathlib import Path

# Path to the trained model and preprocessing pipeline
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"

# Default thresholds for risk levels (percentage)
RISK_THRESHOLDS = {
    "Low": 30,
    "Moderate": 60,
    "High": 100,
}

def _load_model():
    """Load the trained model pipeline. Return None if not available."""
    if not MODEL_PATH.is_file():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None

def predict_risk(features: dict) -> dict:
    """Predict missed-dose risk with a safe fallback when no trained model exists."""
    model = _load_model()
    if model is None:
        missed_days = float(features.get('same_time_missed_days', features.get('previous_missed_doses', 0)) or 0)
        risk_score = min(1.0, max(0.0, 0.18 + (missed_days * 0.15) + (float(features.get('previous_missed_doses', 0)) * 0.08)))
        if risk_score >= 0.6:
            risk = 'High'
            prediction = 'Likely to miss'
            recommendation = 'You have missed this medicine at the same time for 4-5 days. Do not miss the next dose. Set a 30-minute reminder and ask a caregiver to check in with you.'
        elif risk_score >= 0.35:
            risk = 'Moderate'
            prediction = 'Likely to miss'
            recommendation = 'This pattern suggests missed doses may happen again. Increase reminders before the next scheduled time.'
        else:
            risk = 'Low'
            prediction = 'Likely to take'
            recommendation = 'Continue using your scheduled reminders and keep the next dose visible.'
        return {
            'prediction': prediction,
            'probability': risk_score,
            'risk': risk,
            'recommendation': recommendation,
        }

    key_map = {
        'age': 'Age',
        'medicine_frequency': 'Frequency',
        'medicine_dose': 'Medicine_Dose',
        'previous_missed_doses': 'Previous_Medicine_Missed_Count',
        'avg_past_confirmation_delay_minutes': 'Avg_Past_Confirmation_Delay_Minutes',
        'confirmation_channel': 'Confirmation_Channel',
        'reminder_response_time': 'Avg_Past_Confirmation_Delay_Minutes',
        'reminder_preference': 'Confirmation_Channel',
    }
    mapped = {}
    for train_key in [
        'Age',
        'Frequency',
        'Medicine_Dose',
        'Previous_Medicine_Missed_Count',
        'Avg_Past_Confirmation_Delay_Minutes',
        'Confirmation_Channel',
    ]:
        found = None
        for in_key, val in features.items():
            if in_key.lower() == train_key.lower() or key_map.get(in_key) == train_key:
                found = val
                break
        if train_key in ['Age', 'Frequency', 'Medicine_Dose', 'Previous_Medicine_Missed_Count', 'Avg_Past_Confirmation_Delay_Minutes']:
            mapped[train_key] = float(found) if found is not None else 0.0
        else:
            mapped[train_key] = str(found) if found is not None else 'unknown'
    ordered_features = [
        mapped['Age'],
        mapped['Frequency'],
        mapped['Medicine_Dose'],
        mapped['Previous_Medicine_Missed_Count'],
        mapped['Avg_Past_Confirmation_Delay_Minutes'],
        mapped['Confirmation_Channel'],
    ]
    try:
        prob = model.predict_proba([ordered_features])[0][1]
    except Exception:
        pred = model.predict([ordered_features])[0]
        prob = float(pred)
    prob_percent = prob * 100
    if prob_percent <= RISK_THRESHOLDS['Low']:
        risk = 'Low'
    elif prob_percent <= RISK_THRESHOLDS['Moderate']:
        risk = 'Moderate'
    else:
        risk = 'High'
    if features.get('same_time_missed_days', 0) >= 4 or features.get('missed_streak', 0) >= 4:
        recommendation = 'You have missed this medicine at the same time for 4-5 days. Do not miss the next dose. Set a 30-minute reminder and ask a caregiver to check in with you.'
        prediction = 'Likely to miss'
        risk = 'High'
    else:
        recommendation = 'Consider enabling follow-up reminders and alerting a caregiver.' if risk != 'Low' else 'Continue using your scheduled reminders.'
        prediction = 'Likely to miss' if risk != 'Low' else 'Likely to take'
    return {
        'prediction': prediction,
        'probability': max(0.0, min(1.0, float(prob))),
        'risk': risk,
        'recommendation': recommendation,
    }

