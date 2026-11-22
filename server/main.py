from contextlib import asynccontextmanager
from mimetypes import add_type
from pathlib import Path
import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from data.fetch_weather import WeatherService
from model.predict import load_model
from routes import predict, recommend, weather


@asynccontextmanager
async def lifespan(app):
    app.state.model = load_model()
    async with httpx.AsyncClient(timeout=10) as client:
        app.state.weather = WeatherService(client)
        yield


app = FastAPI(title="OutRisk UTP API", version="1.0.0", lifespan=lifespan)
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["Recommendations"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


client_build = Path(__file__).resolve().parents[1] / "client" / "dist"
if (client_build / "index.html").is_file():
    # Windows can assign text/plain to Vite assets through the system MIME registry.
    add_type("text/javascript", ".js")
    add_type("text/css", ".css")
    add_type("image/webp", ".webp")
    app.mount("/", StaticFiles(directory=client_build, html=True), name="dashboard")
