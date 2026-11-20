from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from data.fetch_weather import FORECAST_DAYS, TIMEZONE
from model.predict import predict_hourly
from routes.weather import Source, validate_location


router = APIRouter()
Activity = Literal["jogging", "cycling", "walking", "sports", "commuting"]


class PredictionRequest(BaseModel):
    location: Literal["UTP", "Seri Iskandar"]
    activity: Activity
    date: date
    hour: int = Field(ge=0, le=23, strict=True)
    source: Source = "live"


async def scored_forecast(request, location, source, activity=None):
    weather = await request.app.state.weather.fetch_all_data(location, source)
    return await run_in_threadpool(predict_hourly, request.app.state.model, weather["hourly"], activity)


async def assess_activity(request, selection):
    today = datetime.now(TIMEZONE).date()
    if not today <= selection.date < today + timedelta(days=FORECAST_DAYS):
        raise HTTPException(422, "Choose a date within the seven-day forecast in Malaysia time.")
    when = datetime.combine(selection.date, time(selection.hour)).isoformat(timespec="minutes")
    forecast = await scored_forecast(request, selection.location, selection.source, selection.activity)
    day = [row for row in forecast if row["datetime"][:10] == selection.date.isoformat()]
    result = next((row for row in day if row["datetime"] == when), None)
    if result is None or result["risk_level"] is None:
        raise HTTPException(503, "Some forecast readings are missing for that hour. Try a different time.")
    return result, day


@router.post("/risk")
async def activity_risk(request: Request, selection: PredictionRequest):
    result, _ = await assess_activity(request, selection)
    return {**selection.model_dump(mode="json"), **result, "timezone": TIMEZONE.key}


@router.get("/forecast/{location}")
async def forecast_risk(request: Request, location: str, source: Source = "live", activity: Activity | None = None):
    return await scored_forecast(request, validate_location(location), source, activity)
