import asyncio
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from time import monotonic
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
from dotenv import load_dotenv
from fastapi import HTTPException

from data.preprocess import AIR_FIELDS, WEATHER_FIELDS, clean_dataframe, json_records, parse_hourly_to_dataframe


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
TIMEZONE = ZoneInfo("Asia/Kuala_Lumpur")
LOCATIONS = {"UTP": (4.3856, 100.9779), "Seri Iskandar": (4.3621, 100.9407)}
FORECAST_DAYS = 7


def _clean_env_url(key: str, default: str) -> str:
    raw = os.getenv(key, default)
    return raw.strip().strip("\"'").rstrip("/")


FORECAST_URL = _clean_env_url("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1")
AIR_URL = _clean_env_url("OPEN_METEO_AIR_QUALITY_URL", "https://air-quality-api.open-meteo.com/v1")
ARCHIVE_URL = _clean_env_url("OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1")
HISTORY_FIELDS = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code")
REQUEST_HEADERS = {"User-Agent": "OutRisk-UTP/1.0"}


async def _request(client: httpx.AsyncClient, url: str, lat: float, lon: float, **variables):
    params = {"latitude": lat, "longitude": lon, "timezone": TIMEZONE.key, **variables}
    last_exc = None

    for attempt in range(3):
        try:
            response = await client.get(url, params=params, headers=REQUEST_HEADERS, timeout=15.0)
            if response.status_code == 429:
                wait_seconds = float(response.headers.get("Retry-After", 1.5 * (attempt + 1)))
                print(f"[Open-Meteo 429] Rate limited on {url}; retrying in {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            body_preview = ""
            if isinstance(exc, httpx.HTTPStatusError):
                body_preview = f" | body={exc.response.text[:200]}"
            print(f"[Open-Meteo Error] attempt={attempt + 1} url={url} error={repr(exc)}{body_preview}")
            if attempt < 2:
                await asyncio.sleep(1.0 * (attempt + 1))

    raise HTTPException(502, "Open-Meteo data is temporarily unavailable. Please try again.") from last_exc


async def fetch_current_and_forecast(client, lat, lon):
    return await _request(
        client, f"{FORECAST_URL}/forecast", lat, lon,
        current=",".join((*WEATHER_FIELDS, "is_day")),
        hourly=",".join(WEATHER_FIELDS), forecast_days=FORECAST_DAYS,
    )


async def fetch_air_quality(client, lat, lon):
    fields = ",".join(AIR_FIELDS)
    return await _request(
        client, f"{AIR_URL}/air-quality", lat, lon,
        current=fields, hourly=fields, forecast_days=FORECAST_DAYS,
    )


async def fetch_historical(client, lat, lon, start_date, end_date):
    return await _request(
        client, f"{ARCHIVE_URL}/archive", lat, lon,
        start_date=start_date.isoformat(), end_date=end_date.isoformat(),
        daily=",".join(HISTORY_FIELDS), models="ecmwf_ifs",
    )


def _current_conditions(weather, air):
    current = weather["current"]
    merged = {name: current.get(key) for key, name in WEATHER_FIELDS.items()}
    merged.update({name: air["current"].get(key) for key, name in AIR_FIELDS.items()})
    return {
        **merged,
        "datetime": current["time"],
        "air_quality_datetime": air["current"]["time"],
        "precipitation_interval_minutes": current.get("interval", 900) // 60,
        "is_day": current.get("is_day"),
    }


class WeatherService:
    def __init__(self, client):
        self.client = client
        self.cache = {}
        self.locks = {(location, kind): asyncio.Lock() for location in LOCATIONS for kind in ("history", "live")}

    async def _cached(self, location, kind, fetch, seconds, day: date):
        key = (location, kind)
        async with self.locks[key]:
            expires, data_day, payload = self.cache.get(key, (0, None, None))
            if monotonic() < expires and day == data_day:
                return payload
            try:
                payload = await fetch(*LOCATIONS[location])
                self.cache[key] = (monotonic() + seconds, day, payload)
                return payload
            except HTTPException:
                if payload is not None:
                    print(f"[Open-Meteo Cache] Refresh failed for {key}; serving stale cached data.")
                    return payload
                raise

    async def fetch_all_data(self, location, source):
        now = datetime.now(TIMEZONE)
        if source == "sample":
            from data.sample import sample_weather
            return sample_weather(location, now)

        async def fetch(lat, lon):
            # Fetch sequentially to stay within Open-Meteo's 1-concurrent-request-per-IP limit
            weather = await fetch_current_and_forecast(self.client, lat, lon)
            await asyncio.sleep(0.25)
            air = await fetch_air_quality(self.client, lat, lon)

            try:
                current = _current_conditions(weather, air)
                hours = json_records(clean_dataframe(parse_hourly_to_dataframe(weather, air)))
                expected_hours = FORECAST_DAYS * 24
                if len(hours) != expected_hours:
                    raise ValueError("Incomplete hourly weather forecast")
            except (KeyError, TypeError, ValueError) as exc:
                raise HTTPException(502, "Open-Meteo returned an incomplete forecast. Please try again.") from exc
            return {"location": location, "timezone": TIMEZONE.key, "source": "live", "current": current, "hourly": hours}

        return await self._cached(location, "live", fetch, 900, now.date())

    async def historical(self, location):
        today = datetime.now(TIMEZONE).date()
        end = today - timedelta(days=1)
        start = end - timedelta(days=99)

        async def fetch(lat, lon):
            payload = await fetch_historical(self.client, lat, lon, start, end)
            try:
                days = pd.DataFrame(payload["daily"])
                if len(days) != 100:
                    raise ValueError("Incomplete historical series")
                records = days.astype(object).where(pd.notna(days), None).to_dict("records")
            except (KeyError, TypeError, ValueError) as exc:
                raise HTTPException(502, "Open-Meteo returned an incomplete weather archive.") from exc
            return {"location": location, "timezone": TIMEZONE.key, "source": "live", "daily": records}

        return await self._cached(location, "history", fetch, 3600, today)