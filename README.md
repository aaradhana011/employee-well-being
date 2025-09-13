# 🟢 Employee Wellbeing & Productivity Tracker

A minimal Flask + SQLite app where employees submit a quick survey and a dashboard shows average metrics and an Overall **Wellbeing Score**.

## Features
- Survey fields: **Stress**, **Workload**, **Job Satisfaction** (1–10)
- Stores data in a local **SQLite** DB (`wellbeing.db`)
- Dashboard shows:
  - Avg Stress
  - Avg Workload
  - Avg Job Satisfaction
  - Overall Wellbeing Score (0–100, weighted: Stress 40%, Workload 20%, Satisfaction 40%)
- Trend chart for the last 30 submissions
- Clean UI with Bootstrap; charts via Chart.js (CDN)

## Quickstart
```bash
# 1) Create a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Initialize DB (auto-creates on first run too)
python app.py  # first run will create tables
# or:
# flask --app app.py init-db

# 4) Run
python app.py
# Open http://localhost:5000
```

## How the score is computed
```
wellbeing = (
  ((10 - avg_stress) * 0.4) +
  ((10 - avg_workload) * 0.2) +
  (avg_satisfaction * 0.4)
) * 10  # => 0..100
```
- Lower **stress**/**workload** improve score, higher **satisfaction** improves score.

## Notes
- Ensure internet access for Bootstrap/Chart.js CDNs, or swap to local files.
- To change the weights, edit `compute_metrics()` in `app.py`.
- To export responses, call `GET /api/responses`.
