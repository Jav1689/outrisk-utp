from collections.abc import Mapping

import numpy as np
import pandas as pd


WEATHER_FIELDS = {
    "temperature_2m": "temperature",
    "apparent_temperature": "apparent_temperature",
    "relative_humidity_2m": "humidity",
    "precipitation": "precipitation",
    "weather_code": "weather_code",
    "uv_index": "uv_index",
}
AIR_FIELDS = {"us_aqi": "aqi", "pm2_5": "pm25"}
RISK_FIELDS = ("temperature", "apparent_temperature", "precipitation", "uv_index", "aqi", "weather_code")
MODEL_FEATURES = (*RISK_FIELDS, "strenuous")
FEATURE_RANGES = {
    "temperature": (20, 40),
    "apparent_temperature": (20, 50),
    "humidity": (40, 100),
    "precipitation": (0, 50),
    "uv_index": (0, 12),
    "aqi": (0, 300),
    "pm25": (0, 150),
}
PHYSICAL_LIMITS = {
    "temperature": (-10, 60),
    "apparent_temperature": (-20, 70),
    "humidity": (0, 100),
    "precipitation": (0, 500),
    "uv_index": (0, 30),
    "aqi": (0, 500),
    "pm25": (0, 1000),
}


def _parse_series(payload, fields):
    hourly = payload["hourly"]
    index = pd.DatetimeIndex(pd.to_datetime(hourly["time"]), name="datetime")
    data = pd.DataFrame({name: hourly.get(key) for key, name in fields.items()}, index=index)
    return data.loc[~data.index.duplicated(keep="last")].sort_index()


def parse_hourly_to_dataframe(weather, air):
    return _parse_series(weather, WEATHER_FIELDS).join(_parse_series(air, AIR_FIELDS))


def clean_dataframe(frame, *, impute=False):
    """Coerce numeric values and retain missing forecast readings by default."""
    clean = frame.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    clean = clean.loc[~clean.index.duplicated(keep="last")].sort_index().astype("float64")
    for name, (minimum, maximum) in PHYSICAL_LIMITS.items():
        if name in clean:
            clean[name] = clean[name].clip(minimum, maximum)
    if impute:
        numeric = clean.drop(columns="weather_code", errors="ignore")
        clean[numeric.columns] = numeric.fillna(numeric.median())
        if "weather_code" in clean:
            clean["weather_code"] = clean["weather_code"].fillna(0)
    return clean


def normalize_features(frame):
    transformed = frame.copy()
    for name, (minimum, maximum) in FEATURE_RANGES.items():
        if name in transformed:
            transformed[name] = (transformed[name] - minimum) / (maximum - minimum)
    return transformed, FEATURE_RANGES.copy()


def prepare_model_input(data):
    frame = pd.DataFrame([data]) if isinstance(data, Mapping) else data
    scaled, _ = normalize_features(frame.loc[:, list(MODEL_FEATURES)].astype(float))
    return scaled.to_numpy()


def json_records(frame):
    records = frame.rename_axis("datetime").reset_index()
    records["datetime"] = records["datetime"].dt.strftime("%Y-%m-%dT%H:%M")
    return records.astype(object).where(pd.notna(records), None).to_dict("records")
