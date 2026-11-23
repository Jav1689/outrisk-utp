import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

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
        response = self.client.get("/api/predict/forecast/UTP?source=sample&activity=jogging")
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
        forecast = self.client.get("/api/predict/forecast/UTP?source=sample&activity=cycling").json()
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

    def test_missing_aqi_cannot_hide_a_forecast_thunderstorm(self):
        row = {"temperature": 25, "apparent_temperature": 28, "precipitation": 0, "weather_code": 3, "uv_index": 1}
        incomplete = predict_risk(app.state.model, {**row, "apparent_temperature": None, "aqi": None})
        storm = predict_risk(app.state.model, {**row, "apparent_temperature": None, "weather_code": 95, "aqi": None})
        self.assertIsNone(incomplete["risk_level"])
        self.assertEqual(storm["risk_level"], "Hazardous")
        self.assertIn("Thunderstorm", storm["factors"])
        self.assertIn("Air quality unavailable", storm["factors"])
        self.assertIsNone(storm["confidence"])

    def test_forecast_and_activity_routes_rate_day_seven_when_aqi_ends_early(self):
        weather = self.client.get("/api/weather/forecast/UTP", params={"source": "sample"}).json()
        first_missing_hour = 5 * 24
        for row in weather["hourly"][first_missing_hour:]:
            row.update(aqi=None, pm25=None)

        with patch.object(app.state.weather, "fetch_all_data", return_value=weather):
            response = self.client.get("/api/predict/forecast/UTP", params={"activity": "walking"})
            self.assertEqual(response.status_code, 200)
            hours = response.json()
            self.assertEqual(len(hours), 168)
            self.assertTrue(any(row["risk_level"] == "Safe" for row in hours[:first_missing_hour]))
            for row in hours[first_missing_hour:]:
                self.assertIn(row["risk_level"], {"Caution", "Hazardous"})
                self.assertIn("Air quality unavailable", row["factors"])
                self.assertIsNone(row["aqi"])
                self.assertIsNone(row["confidence"])
                self.assertIsNone(row["probabilities"])

            last_hour = hours[-1]
            date, time = last_hour["datetime"].split("T")
            self.assertEqual(last_hour["risk_level"], "Caution")
            self.assertEqual(hours[-9]["risk_level"], "Hazardous")  # 3 PM thunderstorm on day seven
            params = {"location": "UTP", "activity": "walking", "date": date, "hour": int(time[:2])}
            prediction = self.client.post("/api/predict/risk", json=params)
            recommendations = self.client.post("/api/recommend/activity", json=params)
            self.assertEqual(prediction.status_code, 200)
            self.assertEqual(recommendations.status_code, 200)
            self.assertEqual(prediction.json()["risk_level"], last_hour["risk_level"])
            self.assertEqual(recommendations.json()["risk_level"], last_hour["risk_level"])
            self.assertTrue(any("Air-quality readings are unavailable" in text for text in recommendations.json()["precautions"]))
            self.assertEqual(recommendations.json()["alternative_times"], [])

    def test_tropical_morning_is_low_risk_but_showers_and_severe_weather_still_count(self):
        row = {
            "temperature": 24, "apparent_temperature": 28, "humidity": 100,
            "precipitation": 0, "weather_code": 3, "uv_index": 0, "aqi": 54,
        }
        cases = [
            ({}, "Safe"),
            ({"precipitation": 0.2, "weather_code": 80}, "Caution"),
            ({"weather_code": 82}, "Hazardous"),
            ({"precipitation": 10}, "Hazardous"),
            ({"apparent_temperature": 40}, "Hazardous"),
            ({"uv_index": 11}, "Hazardous"),
            ({"aqi": 110}, "Caution"),
            ({"aqi": 151}, "Hazardous"),
        ]
        for updates, label in cases:
            with self.subTest(updates=updates):
                result = predict_risk(app.state.model, {**row, **updates}, "sports")
                self.assertEqual(result["risk_level"], label)

    def test_forecast_and_assessment_apply_selected_activity_to_heat(self):
        forecast_url = "/api/predict/forecast/UTP"
        walk = self.client.get(forecast_url, params={"source": "sample", "activity": "walking"}).json()
        sport = self.client.get(forecast_url, params={"source": "sample", "activity": "sports"}).json()
        difference = next(
            (easy, strenuous) for easy, strenuous in zip(walk, sport)
            if easy["risk_level"] == "Safe" and strenuous["risk_level"] == "Caution"
        )
        date, time = difference[0]["datetime"].split("T")
        for activity, forecast_row in zip(("walking", "sports"), difference):
            response = self.client.post("/api/predict/risk", json={
                "location": "UTP", "source": "sample", "activity": activity,
                "date": date, "hour": int(time[:2]),
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["risk_level"], forecast_row["risk_level"])

    def test_air_quality_is_joined_by_timestamp(self):
        hours = ["2026-01-01T00:00", "2026-01-01T01:00", "2026-01-01T02:00"]
        weather = {"hourly": {"time": hours, "temperature_2m": [24, 25, 26]}}
        air = {"hourly": {"time": hours[1:], "us_aqi": [44, 45], "pm2_5": [12, 13]}}
        joined = parse_hourly_to_dataframe(weather, air)
        self.assertTrue(joined["aqi"].isna().iloc[0])
        self.assertEqual(joined["aqi"].iloc[1:].tolist(), [44, 45])


if __name__ == "__main__":
    unittest.main()
