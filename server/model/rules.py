from enum import IntEnum


class Risk(IntEnum):
    SAFE = 0
    CAUTION = 1
    HAZARDOUS = 2

    @property
    def label(self):
        return self.name.title()


def assess_conditions(row):
    """Return the project's threshold class plus the factors that increased risk."""
    temperature, humidity, precipitation, uv, aqi, code = (
        row[name] for name in ("temperature", "humidity", "precipitation", "uv_index", "aqi", "weather_code")
    )
    hazardous = [
        (temperature < 18 or temperature > 36, "Extreme temperature"),
        (humidity > 85, "Very high humidity"),
        (precipitation > 5, "Heavy precipitation"),
        (uv > 8, "Very high UV"),
        (aqi > 100, "Elevated US AQI"),
        (code >= 71, "Thunderstorm" if code >= 95 else "Adverse weather"),
    ]
    caution = [
        (temperature < 22 or temperature > 32, "Temperature outside the comfortable range"),
        (humidity > 70, "High humidity"),
        (precipitation > 0, "Precipitation"),
        (uv > 5, "Elevated UV"),
        (aqi > 50, "Moderate US AQI"),
        (code in {45, 48} or 51 <= code <= 67, "Fog, drizzle or rain"),
    ]
    severe_factors = [label for matches, label in hazardous if matches]
    if severe_factors:
        return Risk.HAZARDOUS, severe_factors
    moderate_factors = [label for matches, label in caution if matches]
    level = Risk.CAUTION if len(moderate_factors) >= 2 else Risk.SAFE
    return level, moderate_factors
