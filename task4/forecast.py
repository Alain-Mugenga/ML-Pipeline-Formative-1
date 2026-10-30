"""Task 4: forecast the next hour of Global_active_power using data from the Task 3 API."""
import json
import os
import sys
from pathlib import Path

import joblib
import pandas as pd
import requests

# Reuse the team's Task 1 code instead of copying it
ROOT = Path(__file__).resolve().parent.parent
TASK1 = ROOT / "task1_eda_modeling"
sys.path.append(str(TASK1))
from preprocessing import (add_unmetered, to_hourly, fill_missing_hourly,
                           features_for_next_hour)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/mongo")
MODEL_PATH = TASK1 / "models" / "best_model.joblib"
FEATURES_PATH = TASK1 / "models" / "feature_columns.json"
HISTORY_HOURS = 200               # model needs 168h of lookback; extra is a margin
CHUNK = pd.Timedelta(days=5)      # 7,200 minutes, under the API's 10,000-row cap

# API column names -> names that preprocessing.py expects
RENAME = {
    "global_active_power": "Global_active_power",
    "global_reactive_power": "Global_reactive_power",
    "voltage": "Voltage",
    "global_intensity": "Global_intensity",
    "sub_metering_1": "Sub_metering_1",
    "sub_metering_2": "Sub_metering_2",
    "sub_metering_3": "Sub_metering_3",
}


def fetch_latest_time():
    """Timestamp of the newest reading in the database."""
    r = requests.get(f"{API_URL}/readings/latest", timeout=30)
    r.raise_for_status()
    return pd.Timestamp(r.json()["recorded_at"])


def fetch_range(start, end):
    """All minute readings from start to end, fetched in chunks."""
    rows = []
    t = start
    while t <= end:
        chunk_end = min(t + CHUNK, end)
        r = requests.get(
            f"{API_URL}/readings/range",
            params={"start": t.isoformat(), "end": chunk_end.isoformat(), "limit": 10000},
            timeout=60,
        )
        r.raise_for_status()
        rows += r.json()
        t = chunk_end + pd.Timedelta(minutes=1)   # avoids fetching the boundary row twice
    return rows


def api_to_hourly(rows):
    """API minute rows -> the same hourly table Task 1 trained on."""
    df = pd.DataFrame(rows)
    subs = pd.DataFrame(df["submeters"].tolist(), index=df.index)   # one column per sub-meter
    df = pd.concat([df.drop(columns=["id", "submeters"]), subs], axis=1)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df = (df.drop_duplicates("recorded_at")
            .set_index("recorded_at").sort_index()
            .rename(columns=RENAME))
    df = add_unmetered(df)                   # Sub_metering_4 is not in the API
    return fill_missing_hourly(to_hourly(df))


def load_history():
    """The last HISTORY_HOURS complete hours, fetched from the API."""
    end = fetch_latest_time().floor("h") - pd.Timedelta(minutes=1)   # end of last full hour
    start = end - pd.Timedelta(hours=HISTORY_HOURS) + pd.Timedelta(minutes=1)
    rows = fetch_range(start, end)
    if not rows:
        raise RuntimeError("API returned no readings for the requested window")
    return api_to_hourly(rows)


def main():
    try:
        hourly = load_history()
    except (requests.exceptions.RequestException, RuntimeError) as err:
        sys.exit(f"Could not get data from the API at {API_URL}: {err}")
    print(f"Fetched {len(hourly)} hourly rows: {hourly.index[0]} to {hourly.index[-1]}")

    X = features_for_next_hour(hourly)

    with open(FEATURES_PATH) as f:
        expected = json.load(f)["features"]
    if list(X.columns) != expected:
        sys.exit("Feature mismatch: columns differ from the ones the model was trained on")
    if X.isna().any().any():
        sys.exit("Not enough history to build all features (need 168+ hourly rows)")

    try:
        model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        sys.exit(f"Model file not found: {MODEL_PATH}")

    prediction = model.predict(X)[0]
    print(f"Forecast for {X.index[0]}: {prediction:.3f} kW")
    

if __name__ == "__main__":
    main()