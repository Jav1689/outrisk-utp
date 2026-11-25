<h1 align="center" />
 <img width="128" height="128" alt="outrisk-icon" src="https://github.com/user-attachments/assets/c4671bdc-e5f3-47d3-864f-a0b837ef56cf" />
 <br/>
 <strong> 
        OutRisk UTP
 </strong>
<br/>
<img src="https://img.shields.io/badge/Front_end-React_19-cyan?logo=react&style=for-the-badge"/>
<img src="https://img.shields.io/badge/FE_Language-Javascript-yellow?logo=javascript&style=for-the-badge"/>
<img src="https://img.shields.io/badge/BE_Language-Python-blue?logo=python&style=for-the-badge"/>
<img src="https://img.shields.io/badge/Back_end-Fast_API-green?logo=fastapi&style=for-the-badge"/>
<img src="https://img.shields.io/badge/Open_source_data-Open_Meteo-purple?style=for-the-badge"/>
<img src="https://img.shields.io/badge/version_1.0.0-333?style=for-the-badge"/>
</h1>

<a href="https://outrisk-utp.netlify.app">Checkout the website</a>

**AI-based outdoor activity risk assessment and recommendation system for Universiti Teknologi PETRONAS (UTP) and Seri Iskandar, Perak.**

TGB2013 Artificial Intelligence · Group 16 · Universiti Teknologi PETRONAS 2026

---

## 📑 Table of contents

1. 🎯 [Problem definition](#-1-problem-definition)
2. 🧰 [Tech stack](#-2-tech-stack)
3. 🖥️ [Client (front-end)](#️-3-client-front-end)
4. ⚙️ [Server (back-end)](#️-4-server-back-end)
5. 🚀 [How to run](#-5-how-to-run)
6. 📖 [How to use](#-6-how-to-use)
7. 👥 [Team](#-7-team)
8. 📄 [License](#-8-license)

---

## 🎯 1. Problem definition

Seri Iskandar is a `tropical` township 🌦️ with `intense sun`, `high humidity`, sudden `storms` and occasional `haze`. Students at UTP and residents regularly `walk`, `jog`, `cycle` and `play sports outdoors`, but:

- **`Heat is a real hazard.`** Between 1 January and 3 May 2026, Malaysia's Ministry of Health recorded 56 heat-related cases and two deaths, with 58% linked to physical activity (Bernama, 2026).
- **`Humidity makes it worse.`** A reading for Seri Iskandar showed 29°C air temperature but a 36°C *feels-like* temperature at 82% humidity.
- **`Poor air quality and UV add risk,`** yet most people do not check them before going outside.
- **`Existing sources cover one hazard each.`** MetMalaysia's heat alerts rely on multi-day maximum temperatures and do not say which *hour* is safe for a given *activity*. There is no unified, hourly, activity-specific view.

**✅ OutRisk UTP closes that gap.** The user picks a location, an activity, a date and an hour. The system rates the hour as **Safe**, **Caution** or **Hazardous**, explains the contributing factors, gives precautions and alternatives, and suggests up to three safer hours on the same day.

It is a **planning aid** 🧭 that works alongside official MetMalaysia warnings. It does not replace them.

---

## 🧰 2. Tech stack

| Layer | Technology |
| --- | --- |
| Front-end | React, pnpm (Node.js 22.12+, pnpm 11) |
| Back-end | Python 3.12, FastAPI, Uvicorn |
| AI model | Random Forest classifier (3 classes: Safe / Caution / Hazardous) |
| Weather data | [Open-Meteo](https://open-meteo.com/) forecast and archive APIs (no API key for non-commercial use) |
| Air-quality data | Open-Meteo air-quality API, backed by [Copernicus Atmosphere Monitoring Service](https://atmosphere.copernicus.eu/) |
| Deployment (prototype) | Netlify (client), Render (API) |

**🌍 Why a web app?** It runs on any OS and browser with no installation, benefits from mature front-end and API ecosystems, and is easy to maintain and scale.

---

## 🖥️ 3. Client (front-end)

The React dashboard in `client/` is designed so users need no training. It talks to the FastAPI server through a small API client in `client/src/`.

### 🏠 Dashboard (overview)

| Label | Module | Purpose |
| --- | --- | --- |
| A | Navigation bar | Jump between the **Overview** and **Forecast** sections |
| B | Location toggle | Switch between **UTP** and **Seri Iskandar** |
| C | Current conditions | Temperature, humidity, UV index, precipitation and air quality for the chosen location |
| D | Plan-an-activity form | Choose activity, date and hour |
| E | Risk assessment | Risk class, confidence and contributing factors returned by the back-end |
| F | Recommendations | Activity-specific precautions, alternative activities and safer hours |

### 📅 7-day forecast

| Label | Module | Purpose |
| --- | --- | --- |
| A | Risk trend chart | Safety level over the seven-day period |
| B | Daily dropdown | Expands to a daily summary and the hourly breakdown |
| C | Hourly rows | All 24 hours with their metrics and risk class |
| D | Next-day dropdown | Same layout for the following day |

### 🧪 Sample mode

If a live request fails, choose **Explore sample weather** to try the full workflow with synthetic conditions.

---

## ⚙️ 4. Server (back-end)

> The back-end is the main focus of this project. This section explains what it does, the concepts behind it and the algorithm.

### ✨ 4.1 Features

- Live current conditions, 168-hour forecast and 100 days of history for UTP and Seri Iskandar
- Hourly risk classification with a confidence score
- Activity-specific rules (strenuous vs. light activities)
- Precautions, alternative activities and up to three safer hours on the same day
- Graceful degradation: rule-based ratings still work if the model file is missing, and weather stays visible if the air-quality feed is down
- Sample-weather mode (`source=sample`) for offline demonstrations
- Offline regression tests

### 🔄 4.2 Processing pipeline

```text
Open-Meteo weather + air quality
        │
        ▼
 1. Ingest        fetch hourly data for the chosen location (Malaysia time)
        │
        ▼
 2. Clean         convert to numbers, clamp to physically possible ranges,
                  keep missing readings as missing (never guess)
        │
        ▼
 3. Rule engine   apply threshold rules → Safe / Caution / Hazardous
                  and list the contributing factors
        │
        ▼
 4. Random Forest estimate class probabilities → confidence score
        │
        ▼
 5. Advice        activity-specific precautions, alternatives, safer hours
        │
        ▼
   JSON → React dashboard
```

### 💡 4.3 Concepts

**🌡️ Feels-like temperature.** Air temperature alone is misleading in a humid tropical climate. OutRisk uses Open-Meteo's feels-like (apparent) temperature, which combines air temperature, humidity, wind and solar radiation. Humidity is still displayed for context but is not a threshold on its own.

**🏃 Activity intensity.** Strenuous activities (jogging, cycling, outdoor sports) generate body heat, so they use a **lower** heat threshold than walking, commuting or the general outlook.

**❓ Missing data.** The weather forecast spans seven days but the air-quality feed can end earlier. A known severe hazard (such as a thunderstorm) is always shown. Hours with incomplete readings and no known severe hazard are marked **unavailable** rather than assumed safe.

### 🚦 4.4 Risk rules

The hourly forecast, activity assessment and alternative-time search all use the same rules.

| Level | Triggers |
| --- | --- |
| 🟡 **Caution** | Feels-like ≥ **35°C** (walking, commuting, general) or ≥ **32°C** (jogging, cycling, outdoor sports) · air temperature ≥ 35°C · rain or drizzle · fog · UV ≥ 6 · U.S. AQI > 100 |
| 🔴 **Hazardous** | Forecast thunderstorm · heavy precipitation code or ≥ 10 mm/hour · feels-like ≥ 40°C or air temperature ≥ 37°C · UV ≥ 11 · U.S. AQI > 150 |
| 🟢 **Safe** | Enough readings to assess, and none of the conditions above |

These thresholds are for **hourly planning**. MET Malaysia issues official warnings with separate criteria (for example, multi-day maximum temperatures for heat waves), and Malaysia's Department of Environment publishes local IPU readings. OutRisk shows Open-Meteo's U.S. AQI.

References: [MET Malaysia warnings](https://www.met.gov.my/en/ramalan/ribut-petir/) · [MET Malaysia heat-wave criteria](https://www.met.gov.my/en/pendidikan/fenomena-cuaca/) · [KKM hot-weather guidance](https://infosihat.moh.gov.my/cuaca-panas.html) · [WHO UV guidance](https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-%28uv%29-index) · [U.S. AQI guidance](https://www.airnow.gov/aqi/aqi-basics/) · [Malaysia IPU readings](https://eqms.doe.gov.my/APIMS/main/)

### 🤖 4.5 The AI model

| Item | Detail |
| --- | --- |
| Algorithm | Random Forest classifier |
| Classes | Safe, Caution, Hazardous |
| Input features | Air temperature, feels-like temperature, precipitation, UV index, weather code, U.S. AQI, plus a flag for whether the activity is strenuous |
| Training data | 15,000 synthetic hourly conditions, balanced across the three classes |
| Labels | Generated from the rules in section 4.4 |
| Split | 80% train / 20% test (3,000 held-out samples) |
| Quality gate | Training fails unless test accuracy exceeds 85% |
| Result | 99.77% test accuracy |

**📊 Why synthetic data?** No labelled record of outdoor-activity outcomes exists for the area, so the model is trained on conditions labelled with the rules from our preliminary study.

**🧠 What the model does, and does not, do.**
- The **rules** decide the displayed risk level and its contributing factors.
- The **model** supplies a confidence score and smooths the decision boundaries.
- The 99.77% score measures how closely the model **reproduces the rules**, not how well it predicts real-world harm. Validating against local observations and independently assessed examples is future work.
- If the model file is unavailable, the API returns rule-based ratings without model scores.

Retrain after changing rules:

```bash
cd server
python -m model.train
```

### 🔍 4.6 Key finding: humidity threshold

The first version rated any hour above 85% relative humidity as Hazardous, including a dry 24°C morning at UTP. Because high humidity is normal in Malaysia, the rules were revised to use feels-like temperature, with a lower caution threshold for strenuous activity. On the same 130 forecast hours per location:

| Location | Hazardous hours (old rules) | Hazardous hours (revised) |
| --- | --- | --- |
| UTP | 108 | 6 |
| Seri Iskandar | 109 | 5 |

Every forecast thunderstorm remained Hazardous.

### 🔌 4.7 API

Use `UTP` or `Seri Iskandar` as the location. Weather routes use ISO timestamps in Malaysia time. Prediction requests take `location`, `activity`, `date` (YYYY-MM-DD) and `hour` (integer 0–23).

| Method | Endpoint | Response |
| --- | --- | --- |
| GET | `/api/health` | API status |
| GET | `/api/weather/current/{location}` | Current weather, UV, US AQI and PM2.5 |
| GET | `/api/weather/forecast/{location}` | 168 hourly weather rows |
| GET | `/api/weather/historical/{location}` | 100 complete calendar days ending yesterday |
| POST | `/api/predict/risk` | Risk class, confidence, probabilities and contributing factors |
| GET | `/api/predict/forecast/{location}` | 168 hourly weather and risk rows, optionally rated for an activity with `?activity=sports` |
| POST | `/api/recommend/activity` | Activity advice, precautions and available alternatives |

Current and forecast endpoints accept `?source=sample`. The two POST endpoints accept `"source": "sample"` in the body. The historical route uses the live archive.

Interactive docs are served at `http://localhost:8000/docs` when the server is running.

### ⚠️ 4.8 Limitations

- Training data are simulated from the rules, so accuracy reflects rule agreement only.
- Advice texts are fixed templates written by the team.
- The air-quality feed can end before the 7-day weather horizon.
- During deployment testing, live requests through Render timed out while the sample endpoint worked. A revision that sets a deadline on upstream requests and keeps weather visible during an air-quality outage was tested locally. The root cause of the hosted timeout is unconfirmed.

### 🗂️ 4.9 Repository layout

```text
outrisk/
├── server/
│   ├── main.py           FastAPI entry point
│   ├── data/             Forecast ingestion and preprocessing
│   ├── model/            Training, thresholds and inference
│   ├── routes/           Weather, prediction and advice endpoints
│   └── tests/            Offline regression checks
├── client/
│   ├── public/           Dashboard imagery
│   └── src/              React dashboard and API client
└── issue.md              Project brief and roadmap
```

---

## 🚀 5. How to run

**📋 Requirements:** Python 3.12, Node.js 22.12 or newer, pnpm 11, and an internet connection (Open-Meteo needs no API key for non-commercial use).

### 🪟 Windows (PowerShell)

Easy way to initialize and to run the app:

```bash
cd client
npm install

# Intialize the project
npm run init:win

# Run the project
npm run app:win
```

Or start the API from the repository root:

```powershell
cd server
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m model.train
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Start the client in a **second** terminal from the repository root:

```powershell
cd client
pnpm install --frozen-lockfile
pnpm dev
```

### 🍎🐧 macOS / Linux

Easy way to initialize and to run the app:

```bash
cd client
npm install

# For initialization
npm run init:unix

# For running the app
npm run app:unix
```

Or start the API from the repository root:

```bash
cd server
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m model.train
./venv/bin/python -m uvicorn main:app --reload --port 8000
```

Start the client in a **second** terminal from the repository root:

```bash
cd client
pnpm install --frozen-lockfile
pnpm dev
```

### 🌐 Open the app

- Dashboard: <http://localhost:5173/>
- API docs: <http://localhost:8000/docs>

### ✅ Tests and production build

```bash
# From server/ after training (use .\venv\Scripts\python.exe on Windows)
./venv/bin/python -m unittest discover -s tests -v

# From client/
pnpm build
```

After `pnpm build`, start FastAPI from `server/` and it serves `client/dist` and the API from the same origin on port 8000. To use custom Open-Meteo endpoints, set the base URLs in `server/.env` as shown in `server/.env.example`.

---

## 📖 6. How to use

1. **Open the dashboard.** The landing page shows the navigation bar and current conditions.
2. **Choose a location.** Toggle between **UTP** and **Seri Iskandar**. Current temperature, humidity, UV, precipitation and air quality update immediately.
3. **Fill in the planner.** Select an activity (walking, commuting, jogging, cycling or outdoor sports), a date and an hour.
4. **Click "Plan an activity".** The back-end returns the risk level (Safe, Caution or Hazardous), a confidence percentage and the factors behind the rating.
5. **Read the recommendations.** You get precautions, alternative activities (for example an indoor track or treadmill) and up to three safer hours that day.
6. **Plan ahead.** Open the **Forecast** section to see the 7-day risk chart, then expand any day to inspect its 24 hourly ratings.
7. **No connection?** Click **Explore sample weather** to try everything with synthetic data.

### 🧮 Example simulations (24 November 2026, UTP)

| Activity | Time | Result |
| --- | --- | --- |
| Jogging | 6:00 AM | 🟢 **Safe** (100% confidence) with a reminder to check local weather alerts |
| Outdoor sports | 9:00 AM | 🟡 **Caution** due to heat exposure, with advice to move to cooler hours, bring water, rest in shade and check air quality |

---

## 👥 7. Team

**TGB2013: Artificial Intelligence, Group 16**
Universiti Teknologi PETRONAS, 2026

| Name | Student ID | Program | Year of study |
| --- | --- | --- | --- |
| Ananda Adiputra | 24006462 | BCS | 2nd Year, 1st Sem |
| Javier Lee | 24006576 | BCS | 2nd Year, 1st Sem |
| Muhammad Akmal Fikri Bin Asma Zaki | 26005849 | BCS | 1st Year, 2nd Sem |
| Muhammad Saqib | 24009307 | BCS | 2nd Year, 1st Sem |

---

## 📄 8. License

This project is released under the [MIT License](LICENSE).

Weather and air-quality data are provided by [Open-Meteo](https://open-meteo.com/) and the Copernicus Atmosphere Monitoring Service under their own terms. Banner photo by [Yogendra Singh on Pexels](https://www.pexels.com/photo/men-playing-soccer-on-field-1375148/), used under the [Pexels License](https://www.pexels.com/license/).

---

### 📚 References

- Bernama. (2026, May 3). *Hot weather: 56 cases, two deaths recorded as of May 3 - MOH.* https://bernama.com/en/news.php?id=2552245
- Bernama. (2026, March 23). *Padang Terap, Kedah records Level Two heatwave - MetMalaysia.* https://bernama.com/en/news.php?id=2536718
- Hahad, O., et al. (2021). Physical activity in polluted air: net benefit or harm to cardiovascular health? *Antioxidants, 10*(11), 1787. https://doi.org/10.3390/antiox10111787
- Marko, T., et al. (2021). Air pollution, physical activity and health: a mapping review of the evidence. *Environment International, 147*, 105954. https://doi.org/10.1016/j.envint.2020.105954
- Thompson, E. J., et al. (2024). The interplay of climate change and physical activity. *American Heart Journal Plus, 47*, 100474. https://doi.org/10.1016/j.ahjo.2024.100474
