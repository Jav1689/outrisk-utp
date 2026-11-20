# OutRisk UTP project brief

Anandaxing’s [Initial approach, issue #1](https://github.com/Jav1689/outrisk-utp/issues/1) is the project brief.

OutRisk UTP helps students, staff, and residents plan outdoor activities around local weather and air quality at Universiti Teknologi PETRONAS and Seri Iskandar.

- Keep the FastAPI server and React client in `server/` and `client/`.
- Fetch current conditions, seven days of hourly forecasts, and 100 complete historical weather days through Open-Meteo.
- Align weather and air quality by timestamp. Train and evaluate a scikit-learn classifier on synthetic weather labeled according to the issue’s thresholds.
- Provide weather, risk, and activity recommendation endpoints. Display current conditions, a planner, class confidence, recommendations, and expandable hourly forecasts.
- Verify both locations and desktop and mobile layouts. Document setup and deployment.

See [README.md](README.md) for the implemented setup and data behavior.
