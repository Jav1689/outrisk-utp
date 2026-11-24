import asyncio
import unittest
from datetime import datetime, timedelta
from email.utils import format_datetime
from unittest.mock import patch

import httpx
from fastapi import HTTPException

from data.fetch_weather import TIMEZONE, WeatherService, _retry_after


def weather_response():
    start = datetime.now(TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    times = [(start + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M") for hour in range(168)]
    readings = {
        "temperature_2m": 25, "apparent_temperature": 28, "relative_humidity_2m": 88,
        "precipitation": 0, "weather_code": 2, "uv_index": 0,
    }
    return httpx.Response(200, json={
        "current": {"time": times[0], **readings},
        "hourly": {"time": times, **{key: [value] * len(times) for key, value in readings.items()}},
    })


class WeatherServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit_returns_promptly_and_backs_off_across_locations(self):
        calls = []

        def upstream(request):
            calls.append(request.url.path)
            return httpx.Response(429, headers={"Retry-After": "120"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            service = WeatherService(client)
            yesterday = datetime.now(TIMEZONE).date() - timedelta(days=1)
            service.cache[("UTP", "weather")] = (0, yesterday, weather_response().json())
            for location in ("UTP", "UTP", "Seri Iskandar"):
                with self.assertRaises(HTTPException) as raised:
                    await asyncio.wait_for(service.fetch_all_data(location, "live"), timeout=1)
                self.assertEqual(raised.exception.status_code, 503)
                self.assertGreaterEqual(int(raised.exception.headers["Retry-After"]), 119)
        self.assertEqual(calls, ["/v1/forecast"])

    async def test_air_quality_failure_still_returns_live_weather(self):
        calls = []

        def upstream(request):
            calls.append(request.url.path)
            if request.url.path.endswith("/air-quality"):
                return httpx.Response(429, headers={"Retry-After": "120"})
            return weather_response()

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            service = WeatherService(client)
            for _ in range(2):
                result = await service.fetch_all_data("UTP", "live")
                self.assertEqual(result["source"], "live")
                self.assertEqual(result["current"]["temperature"], 25)
                self.assertIsNone(result["current"]["aqi"])
                self.assertIsNone(result["current"]["air_quality_datetime"])
                self.assertEqual(len(result["hourly"]), 168)
                self.assertTrue(all(row["aqi"] is None for row in result["hourly"]))
        self.assertEqual(calls, ["/v1/forecast", "/v1/air-quality"])

    async def test_slow_weather_request_hits_deadline_and_does_not_repeat_immediately(self):
        calls = []

        async def upstream(request):
            calls.append(request.url.path)
            await asyncio.sleep(3)
            return weather_response()

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            service = WeatherService(client)
            with patch("data.fetch_weather.UPSTREAM_TIMEOUT", 0.01):
                for _ in range(2):
                    with self.assertRaises(HTTPException) as raised:
                        await asyncio.wait_for(service.fetch_all_data("UTP", "live"), timeout=1)
                    self.assertEqual(raised.exception.status_code, 504)
        self.assertEqual(calls, ["/v1/forecast"])

    def test_retry_after_accepts_http_dates_and_handles_invalid_values(self):
        future = format_datetime(datetime.now(TIMEZONE) + timedelta(seconds=120))
        self.assertIn(_retry_after(future), (119, 120))
        self.assertEqual(_retry_after("unavailable"), 60)
