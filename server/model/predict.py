import joblib
import numpy as np
import pandas as pd

from data.preprocess import MODEL_FEATURES, prepare_model_input
from model.rules import Risk, assess_conditions
from model.train import MODEL_PATH, MODEL_VERSION


def load_model():
    if not MODEL_PATH.is_file():
        raise RuntimeError("Run python -m model.train from server/ before starting the API.")
    artifact = joblib.load(MODEL_PATH)
    if artifact["version"] != MODEL_VERSION:
        raise RuntimeError("Retrain the model with python -m model.train.")
    return artifact["model"]


def predict_hourly(model, rows):
    frame = pd.DataFrame(rows, columns=MODEL_FEATURES)
    usable = frame.notna().all(axis=1)
    predictions = {
        index: {"risk_level": None, "confidence": None, "probabilities": None, "factors": []}
        for index in frame.index[~usable]
    }
    if usable.any():
        probabilities = model.predict_proba(prepare_model_input(frame.loc[usable]))
        for index, chances in zip(frame.index[usable], probabilities):
            row = rows[index]
            model_risk = Risk(int(model.classes_[np.argmax(chances)]))
            threshold_risk, factors = assess_conditions(row)
            level = max(model_risk, threshold_risk)
            scores = {Risk(int(key)).label: round(float(value) * 100, 1)
                      for key, value in zip(model.classes_, chances)}
            predictions[index] = {
                "risk_level": level.label,
                "confidence": scores[level.label],
                "probabilities": scores,
                "factors": factors,
            }
    return [{**row, **predictions[index]} for index, row in enumerate(rows)]


def predict_risk(model, row):
    return predict_hourly(model, [row])[0]
