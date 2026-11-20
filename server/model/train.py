from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from data.preprocess import prepare_model_input
from model.rules import Risk, assess_conditions


MODEL_PATH = Path(__file__).with_name("risk_model.pkl")
MODEL_VERSION = 2


def generate_training_data(n_samples=15_000):
    rng = np.random.default_rng(42)
    pool_size = n_samples * 25
    codes = [0, 1, 2, 3, 45, 51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 97, 99]
    code_weights = np.array([18, 13, 18, 16, 2, 4, 4, 4, 4, 3, 2, 2, 2, 2, 2, 1, 1, 1])
    temperature = rng.uniform(20, 43, pool_size)
    humidity = rng.uniform(48, 100, pool_size)
    samples = pd.DataFrame({
        "temperature": temperature,
        "apparent_temperature": temperature + (humidity - 55) * 0.11 + rng.normal(0, 2.5, pool_size),
        "precipitation": np.where(rng.random(pool_size) < 0.62, 0, rng.exponential(3, pool_size)),
        "uv_index": np.where(rng.random(pool_size) < 0.35, 0, rng.uniform(0, 14, pool_size)),
        "aqi": rng.exponential(42, pool_size).clip(0, 500),
        "weather_code": rng.choice(codes, pool_size, p=code_weights / code_weights.sum()),
        "strenuous": rng.integers(0, 2, pool_size),
    })
    labels = [
        assess_conditions(sample, strenuous=bool(sample["strenuous"]))[0].value
        for sample in samples.to_dict("records")
    ]
    samples["risk_level"] = labels
    groups = []
    for level in Risk:
        count = n_samples // len(Risk) + (level.value < n_samples % len(Risk))
        groups.append(samples.loc[samples.risk_level == level.value].sample(count, random_state=42))
    return pd.concat(groups, ignore_index=True)


def train_model():
    samples = generate_training_data()
    features = prepare_model_input(samples)
    labels = samples["risk_level"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    model = RandomForestClassifier(n_estimators=180, max_depth=19, random_state=42, n_jobs=-1)
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    accuracy = accuracy_score(y_test, predicted)
    print(classification_report(y_test, predicted, target_names=[level.label for level in Risk]))
    print(f"Synthetic test accuracy: {accuracy:.2%}")
    if accuracy <= 0.85:
        raise RuntimeError("The classifier did not meet the project's accuracy target.")
    temporary = MODEL_PATH.with_suffix(".tmp")
    joblib.dump({"version": MODEL_VERSION, "model": model}, temporary, compress=3)
    temporary.replace(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
