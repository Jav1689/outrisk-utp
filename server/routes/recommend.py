from datetime import datetime

from fastapi import APIRouter, Request

from data.fetch_weather import TIMEZONE
from model.rules import HEAT_CAUTION_C, STRENUOUS_ACTIVITIES, STRENUOUS_HEAT_CAUTION_C, THUNDERSTORM_CODES, WET_WEATHER_CODES
from routes.predict import PredictionRequest, assess_activity


router = APIRouter()
ADVICE = {
    "jogging": ("Choose your usual route and bring water.", "Shorten your route and slow your pace.", "Postpone your run or use an indoor track."),
    "cycling": ("Check your route and wear a helmet.", "Reduce speed and allow extra braking distance.", "Postpone the ride or cycle indoors."),
    "walking": ("Choose a familiar route with shade.", "Keep the walk short and stay close to shelter.", "Delay the walk or choose an indoor route."),
    "sports": ("Schedule breaks and keep water available.", "Reduce intensity and plan extra breaks.", "Move the session indoors or reschedule."),
    "commuting": ("Allow time for the outdoor leg of your trip.", "Allow extra time and use sheltered paths if available.", "Delay the outdoor leg if possible or use covered transport."),
}
LEVELS = ("Safe", "Caution", "Hazardous")
ALTERNATIVES = {
    "jogging": ["Indoor track", "Treadmill"],
    "cycling": ["Stationary bike", "Indoor gym"],
    "walking": ["Indoor walk", "Covered walkway when conditions allow"],
    "sports": ["Indoor court", "Indoor gym"],
    "commuting": ["Campus shuttle", "Covered transport"],
}


def generate_recommendations(activity, risk_level, weather_data):
    precautions = ["Check local weather alerts before heading out."]
    heat_threshold = STRENUOUS_HEAT_CAUTION_C if activity in STRENUOUS_ACTIVITIES else HEAT_CAUTION_C
    if (weather_data.get("temperature") or 0) >= HEAT_CAUTION_C or (weather_data.get("apparent_temperature") or 0) >= heat_threshold:
        precautions.append("Choose a cooler hour, bring water and take breaks in the shade.")
    uv = weather_data.get("uv_index") or 0
    if uv >= 8:
        precautions.append("Choose a shaded or indoor option and avoid midday sun.")
    elif uv >= 3:
        precautions.append("Use sun protection and plan a shaded route.")
    if weather_data.get("weather_code") in THUNDERSTORM_CODES:
        precautions.append("Seek shelter in a substantial building or enclosed vehicle during thunder.")
    elif (weather_data.get("precipitation") or 0) > 0 or weather_data.get("weather_code") in WET_WEATHER_CODES:
        precautions.append("Watch for slippery surfaces and reduced visibility.")
    aqi = weather_data.get("aqi")
    if aqi is None:
        precautions.append("Air-quality readings are unavailable for this hour. Check local air quality before heading out.")
    elif aqi > 150:
        precautions.append("Reschedule prolonged or strenuous outdoor activity until air quality improves.")
    elif aqi > 50:
        precautions.append("If you are sensitive to air pollution, check air-quality guidance before strenuous activity.")
    return {
        "advice": ADVICE[activity][LEVELS.index(risk_level)],
        "precautions": precautions,
        "alternative_activities": ALTERNATIVES[activity] if risk_level != "Safe" else [],
    }


@router.post("/activity")
async def activity_recommendations(request: Request, selection: PredictionRequest):
    result, day = await assess_activity(request, selection)
    now = datetime.now(TIMEZONE).replace(tzinfo=None)
    candidates = [
        row for row in day
        if row["risk_level"] == "Safe" and row["datetime"] != result["datetime"]
        and datetime.fromisoformat(row["datetime"]) > now
    ]
    candidates.sort(key=lambda row: (abs(int(row["datetime"][11:13]) - selection.hour), row["datetime"]))
    alternatives = [
        {"datetime": row["datetime"], "hour": int(row["datetime"][11:13]), "risk_level": row["risk_level"],
         "note": f'Feels like {row["apparent_temperature"]:.0f} °C · US AQI {row["aqi"]:.0f}'}
        for row in candidates[:3]
    ]
    return {
        "risk_level": result["risk_level"], "activity": selection.activity, "source": selection.source,
        **generate_recommendations(selection.activity, result["risk_level"], result),
        "alternative_times": alternatives,
    }
