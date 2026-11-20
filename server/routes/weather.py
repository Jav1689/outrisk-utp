from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from data.fetch_weather import LOCATIONS


router = APIRouter()
Source = Literal["live", "sample"]


def validate_location(location):
    if location not in LOCATIONS:
        raise HTTPException(400, "Choose UTP or Seri Iskandar.")
    return location


@router.get("/current/{location}")
async def current_weather(request: Request, location: str, source: Source = "live"):
    data = await request.app.state.weather.fetch_all_data(validate_location(location), source)
    return {key: value for key, value in data.items() if key != "hourly"}


@router.get("/forecast/{location}")
async def forecast_weather(request: Request, location: str, source: Source = "live"):
    data = await request.app.state.weather.fetch_all_data(validate_location(location), source)
    return {key: value for key, value in data.items() if key != "current"}


@router.get("/historical/{location}")
async def historical_weather(request: Request, location: str):
    return await request.app.state.weather.historical(validate_location(location))
