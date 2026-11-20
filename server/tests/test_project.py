import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from data.fetch_weather import TIMEZONE
from data.preprocess import parse_hourly_to_dataframe
from main import app
from model.predict import predict_risk


class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        cls.today = datetime.now(TIMEZONE).date()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_sample_forecast_matches_assessment_and_precautions(self):
        response = self.client.get("/api/predict/forecast/UTP?source=sample")
        self.assertEqual(response.status_code, 200)
        forecast = response.json()
        self.assertEqual(len(forecast), 168)
        self.assertEqual(forecast[15]["risk_level"], "Hazardous")
        for location in ("UTP", "Seri Iskandar"):
            with self.subTest(location=location):
                params = {
                    "location": location, "activity": "jogging", "date": self.today.isoformat(),
                    "hour": 15, "source": "sample",
                }
                prediction = self.client.post("/api/predict/risk", json=params)
                recs = self.client.post("/api/recommend/activity", json=params)
                self.assertEqual(prediction.status_code, 200)
                self.assertEqual(recs.status_code, 200)
                self.assertEqual(prediction.json()["risk_level"], recs.json()["risk_level"])
                self.assertTrue(recs.json()["precautions"])
        self.assertIn("Thunderstorm", forecast[15]["factors"])

    def test_recommended_times_match_lower_risk_hours_on_the_selected_date(self):
        tomorrow = (self.today + timedelta(days=1)).isoformat()
        params = {"location": "UTP", "activity": "cycling", "date": tomorrow, "hour": 17, "source": "sample"}
        response = self.client.post("/api/recommend/activity", json=params)
        self.assertEqual(response.status_code, 200)
        times = response.json()["alternative_times"]
        self.assertTrue(times)
        forecast = self.client.get("/api/predict/forecast/UTP?source=sample").json()
        risks = {row["datetime"]: row["risk_level"] for row in forecast}
        for option in times:
            self.assertEqual(option["datetime"][:10], tomorrow)
            self.assertEqual(risks[option["datetime"]], "Safe")
            self.assertNotEqual(option["hour"], params["hour"])

    def test_validation_rejects_a_noninteger_hour_and_dates_outside_the_forecast(self):
        params = {"location": "UTP", "activity": "walking", "date": self.today.isoformat(), "hour": 10, "source": "sample"}
        for invalid in ({"hour": True}, {"hour": 24}, {"date": (self.today + timedelta(days=7)).isoformat()}):
            with self.subTest(invalid=invalid):
                response = self.client.post("/api/predict/risk", json={**params, **invalid})
                self.assertEqual(response.status_code, 422)

    def test_missing_aqi_is_unavailable_and_severe_weather_cannot_be_downgraded(self):
        row = {"temperature": 25, "humidity": 65, "precipitation": 0, "weather_code": 95, "uv_index": 1}
        missing = predict_risk(app.state.model, {**row, "aqi": None})
        complete = predict_risk(app.state.model, {**row, "aqi": 35})
        self.assertIsNone(missing["risk_level"])
        self.assertEqual(complete["risk_level"], "Hazardous")

    def test_air_quality_is_joined_by_timestamp(self):
        hours = ["2026-01-01T00:00", "2026-01-01T01:00", "2026-01-01T02:00"]
        weather = {"hourly": {"time": hours, "temperature_2m": [24, 25, 26]}}
        air = {"hourly": {"time": hours[1:], "us_aqi": [44, 45], "pm2_5": [12, 13]}}
        joined = parse_hourly_to_dataframe(weather, air)
        self.assertTrue(joined["aqi"].isna().iloc[0])
        self.assertEqual(joined["aqi"].iloc[1:].tolist(), [44, 45])


if __name__ == "__main__":
    unittest.main()
