import math
from datetime import timedelta

from data.fetch_weather import FORECAST_DAYS, TIMEZONE


def sample_weather(location, now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    offset = 0 if location == "UTP" else 1
    hours = []
    for index in range(FORECAST_DAYS * 24):
        moment = start + timedelta(hours=index)
        day, hour = divmod(index, 24)
        sun = max(0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
        heat = 0.5 + 0.5 * math.cos(math.tau * (hour - 14) / 24)
        storm = (day + offset) % 3 == 0 and 15 <= hour <= 17
        drizzle = (day + offset) % 3 == 1 and 16 <= hour <= 18
        temperature = round(24 + 8.0 * heat + (day % 3) * 0.7 + offset * 0.6, 1)
        hours.append({
            "datetime": moment.isoformat(timespec="minutes")[:16],
            "temperature": temperature,
            "apparent_temperature": round(temperature + 2 + 3 * sun, 1),
            "humidity": round(63 + 13 * (1 - heat) + (16 if storm else 5 if drizzle else 0), 1),
            "precipitation": 6.8 if storm else 1.3 if drizzle else 0,
            "weather_code": 95 if storm else 61 if drizzle else 2,
            "uv_index": round(sun * (8.2 + day % 3 * 0.5) * (0.5 if storm or drizzle else 1), 1),
            "aqi": 34 + (day % 3) * 5 + offset * 4 + hour % 5,
            "pm25": 8 + day % 4 + offset,
        })
    current = {**hours[now.hour], "is_day": int(7 <= now.hour < 19), "precipitation_interval_minutes": 60}
    current["air_quality_datetime"] = current["datetime"]
    return {"location": location, "timezone": TIMEZONE.key, "source": "sample", "current": current, "hourly": hours}
