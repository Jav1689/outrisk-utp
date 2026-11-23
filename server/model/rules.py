from enum import IntEnum
from math import isfinite

from data.preprocess import RISK_FIELDS


STRENUOUS_ACTIVITIES = {"jogging", "cycling", "sports"}
THUNDERSTORM_CODES = {95, 96, 97, 99}
HEAVY_PRECIPITATION_CODES = {65, 67, 75, 82, 86}
WET_WEATHER_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86}
HEAT_CAUTION_C = 35
STRENUOUS_HEAT_CAUTION_C = 32
HEAT_HAZARD_C = 40
AIR_TEMPERATURE_HAZARD_C = 37


class Risk(IntEnum):
    SAFE = 0
    CAUTION = 1
    HAZARDOUS = 2

    @property
    def label(self):
        return self.name.title()


def assess_conditions(row, *, strenuous=False):
    """Rate the weather alone when AQI is missing, with Caution as the minimum."""
    values = [row.get(field) for field in RISK_FIELDS]
    temperature, feels_like, precipitation, uv, aqi, code = [
        value if value is not None and isfinite(value) else None for value in values
    ]
    missing_air_quality = ["Air quality unavailable"] if aqi is None else []
    hazardous = [
        (code in THUNDERSTORM_CODES, "Thunderstorm"),
        (code in HEAVY_PRECIPITATION_CODES or (precipitation is not None and precipitation >= 10), "Heavy precipitation"),
        (feels_like is not None and feels_like >= HEAT_HAZARD_C, "Severe feels-like heat"),
        (temperature is not None and temperature >= AIR_TEMPERATURE_HAZARD_C, "Very high air temperature"),
        (aqi is not None and aqi > 150, "Unhealthy U.S. AQI"),
        (uv is not None and uv >= 11, "Extreme UV"),
    ]
    severe_factors = [label for matches, label in hazardous if matches]
    if severe_factors:
        return Risk.HAZARDOUS, severe_factors + missing_air_quality
    if None in (temperature, feels_like, precipitation, uv, code):
        return None, []

    heat_threshold = STRENUOUS_HEAT_CAUTION_C if strenuous else HEAT_CAUTION_C
    caution = [
        (temperature >= HEAT_CAUTION_C or feels_like >= heat_threshold, "Heat exposure"),
        (code in {45, 48}, "Fog"),
        (code in WET_WEATHER_CODES or precipitation >= 0.1, "Rain or drizzle"),
        (uv >= 6, "High UV"),
        (aqi is not None and aqi > 100, "U.S. AQI unhealthy for sensitive groups"),
    ]
    factors = missing_air_quality + [label for matches, label in caution if matches]
    return (Risk.CAUTION if factors else Risk.SAFE), factors
