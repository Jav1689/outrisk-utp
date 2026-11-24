import asyncio
import logging
import os
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from functools import partial
from math import ceil
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit
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
UPSTREAM_TIMEOUT = 6
RATE_LIMIT_BACKOFF = 60
FAILURE_BACKOFF = 15
EMPTY_AIR = {"current": {}, "hourly": {"time": []}}
logger = logging.getLogger(__name__)


def _clean_env_url(key: str, default: str) -> str:
    raw = os.getenv(key, "").strip().strip("\"'").strip().rstrip("/")
    return raw or default


FORECAST_URL = _clean_env_url("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1")
AIR_URL = _clean_env_url("OPEN_METEO_AIR_QUALITY_URL", "https://air-quality-api.open-meteo.com/v1")
ARCHIVE_URL = _clean_env_url("OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1")
HISTORY_FIELDS = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code")
REQUEST_HEADERS = {"User-Agent": "OutRisk-UTP/1.0"}


def _retry_after(value):
    if not value:
        return RATE_LIMIT_BACKOFF
    try:
        return max(1, int(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value).astimezone(UTC)
            return max(1, ceil((retry_at - datetime.now(UTC)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            return RATE_LIMIT_BACKOFF


async def _request(client: httpx.AsyncClient, url: str, lat: float, lon: float, **variables):
    params = {"latitude": lat, "longitude": lon, "timezone": TIMEZONE.key, **variables}
    endpoint = urlsplit(url)
    service = f"{endpoint.hostname}{endpoint.path}"
    try:
        async with asyncio.timeout(UPSTREAM_TIMEOUT):
            response = await client.get(url, params=params, headers=REQUEST_HEADERS)
    except (TimeoutError, httpx.TimeoutException) as exc:
        logger.warning("Open-Meteo request to %s timed out", service)
        raise HTTPException(504, "Open-Meteo took too long to respond. Please try again shortly.") from exc
    except httpx.RequestError as exc:
        logger.warning("Open-Meteo request to %s failed (%s)", service, type(exc).__name__)
        raise HTTPException(502, "Could not reach Open-Meteo. Please try again shortly.") from exc

    if not response.is_success:
        logger.warning("Open-Meteo %s returned HTTP %s", service, response.status_code)
        if response.status_code == 429:
            delay = _retry_after(response.headers.get("Retry-After"))
            raise HTTPException(
                503, "Open-Meteo is rate limiting live requests. Please try again later.",
                headers={"Retry-After": str(delay)},
            )
        raise HTTPException(502, "Open-Meteo rejected the live data request. Please try again later.")
    try:
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            raise ValueError("Invalid Open-Meteo response")
        return payload
    except ValueError as exc:
        logger.warning("Open-Meteo %s returned an invalid response", service)
        raise HTTPException(502, "Open-Meteo returned an invalid response. Please try again later.") from exc


def _validate_hourly(payload, fields, *, expected_hours=None):
    current = payload.get("current")
    hourly = payload.get("hourly")
    times = hourly.get("time") if isinstance(hourly, dict) else None
    if (
        not isinstance(current, dict) or not isinstance(current.get("time"), str)
        or not isinstance(times, list) or not times
        or (expected_hours is not None and len(times) != expected_hours)
        or any(values is not None and (not isinstance(values, list) or len(values) != len(times))
               for values in (hourly.get(field) for field in fields))
    ):
        raise HTTPException(502, "Open-Meteo returned incomplete weather or air-quality data.")
    return payload


async def fetch_current_and_forecast(client, lat, lon):
    payload = await _request(
        client, f"{FORECAST_URL}/forecast", lat, lon,
        current=",".join((*WEATHER_FIELDS, "is_day")),
        hourly=",".join(WEATHER_FIELDS), forecast_days=FORECAST_DAYS,
    )
    return _validate_hourly(payload, WEATHER_FIELDS, expected_hours=FORECAST_DAYS * 24)


async def fetch_air_quality(client, lat, lon):
    fields = ",".join(AIR_FIELDS)
    payload = await _request(
        client, f"{AIR_URL}/air-quality", lat, lon,
        current=fields, hourly=fields, forecast_days=FORECAST_DAYS,
    )
    return _validate_hourly(payload, AIR_FIELDS)


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
        "air_quality_datetime": air["current"].get("time"),
        "precipitation_interval_minutes": current.get("interval", 900) // 60,
        "is_day": current.get("is_day"),
    }


class WeatherService:
    def __init__(self, client):
        self.client = client
        self.cache = {}
        self.failures = {}
        self.locks = {(location, kind): asyncio.Lock() for location in LOCATIONS for kind in ("history", "weather", "air")}

    async def _cached(self, location, kind, fetch, seconds, day: date):
        key = (location, kind)
        rate_limit_key = (None, kind)
        async with self.locks[key]:
            expires, data_day, payload = self.cache.get(key, (0, None, None))
            now = monotonic()
            if now < expires and day == data_day:
                return payload
            for failure_key in (rate_limit_key, key):
                failure = self.failures.get(failure_key)
                if failure and now < failure[0]:
                    retry_at, status, detail = failure
                    raise HTTPException(status, detail, headers={"Retry-After": str(ceil(retry_at - now))})

            try:
                payload = await fetch(*LOCATIONS[location])
            except HTTPException as exc:
                if exc.status_code == 503:
                    delay = int(exc.headers["Retry-After"])
                    self.failures[rate_limit_key] = (monotonic() + delay, exc.status_code, exc.detail)
                else:
                    self.failures[key] = (monotonic() + FAILURE_BACKOFF, exc.status_code, exc.detail)
                raise
            self.cache[key] = (monotonic() + seconds, day, payload)
            self.failures.pop(key, None)
            return payload

    async def fetch_all_data(self, location, source):
        now = datetime.now(TIMEZONE)
        if source == "sample":
            from data.sample import sample_weather
            return sample_weather(location, now)

        today = now.date()
        weather = await self._cached(location, "weather", partial(fetch_current_and_forecast, self.client), 900, today)
        try:
            air = await self._cached(location, "air", partial(fetch_air_quality, self.client), 900, today)
        except HTTPException:
            air = EMPTY_AIR

        try:
            current = _current_conditions(weather, air)
            hours = json_records(clean_dataframe(parse_hourly_to_dataframe(weather, air)))
            if len(hours) != FORECAST_DAYS * 24:
                raise ValueError("Incomplete hourly weather forecast")
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(502, "Open-Meteo returned an incomplete forecast. Please try again.") from exc
        return {"location": location, "timezone": TIMEZONE.key, "source": "live", "current": current, "hourly": hours}

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
