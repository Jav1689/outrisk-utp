import logging

import joblib
import pandas as pd

from data.preprocess import RISK_FIELDS, prepare_model_input
from model.rules import STRENUOUS_ACTIVITIES, Risk, assess_conditions
from model.train import MODEL_PATH, MODEL_VERSION


logger = logging.getLogger(__name__)


def load_model():
    if not MODEL_PATH.is_file():
        logger.warning("Model scores are unavailable. Run python -m model.train from server/ to enable them.")
        return None
    artifact = joblib.load(MODEL_PATH)
    if artifact["version"] != MODEL_VERSION:
        logger.warning("Ignoring an older risk model. Run python -m model.train from server/ to update it.")
        return None
    return artifact["model"]


def predict_hourly(model, rows, activity=None):
    strenuous = activity in STRENUOUS_ACTIVITIES
    predictions = []
    for row in rows:
        level, factors = assess_conditions(row, strenuous=strenuous)
        predictions.append({
            **row, "risk_level": level.label if level is not None else None,
            "confidence": None, "probabilities": None, "factors": factors,
        })
    if model is None or not predictions:
        return predictions

    frame = pd.DataFrame(rows, columns=RISK_FIELDS, dtype=float)
    usable = (frame.abs() < float("inf")).all(axis=1)
    if usable.any():
        features = frame.loc[usable].assign(strenuous=int(strenuous))
        probabilities = model.predict_proba(prepare_model_input(features))
        for index, chances in zip(frame.index[usable], probabilities):
            scores = {Risk(int(key)).label: round(float(value) * 100, 1)
                      for key, value in zip(model.classes_, chances)}
            predictions[index]["confidence"] = scores[predictions[index]["risk_level"]]
            predictions[index]["probabilities"] = scores
    return predictions


def predict_risk(model, row, activity=None):
    return predict_hourly(model, [row], activity)[0]
