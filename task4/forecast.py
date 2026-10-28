"""Task 4: forecast the next hour of Global_active_power (v1: reads a CSV; API comes later)."""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

# Reuse the team's Task 1 code instead of copying it
ROOT = Path(__file__).resolve().parent.parent
TASK1 = ROOT / "task1_eda_modeling"
sys.path.append(str(TASK1))
from preprocessing import features_for_next_hour, feature_columns

MODEL_PATH = TASK1 / "models" / "best_model.joblib"
FEATURES_PATH = TASK1 / "models" / "feature_columns.json"
DATA_PATH = TASK1 / "data" / "hourly_clean.csv"
HISTORY_HOURS = 200  # model needs 168h of lookback; extra is a safety margin


def load_history():
    """Last HISTORY_HOURS of hourly data. Tomorrow this will fetch from the API."""
    df = pd.read_csv(DATA_PATH, parse_dates=["datetime"], index_col="datetime")
    return df.tail(HISTORY_HOURS)


def main():
    hourly = load_history()

    # Same pipeline as training: builds lags, moving averages, calendar features
    X = features_for_next_hour(hourly)

    # Safety check: columns must match what the model was trained on, in order
    with open(FEATURES_PATH) as f:
        expected = json.load(f)["features"]
    assert list(X.columns) == expected, "Feature mismatch with training"
    assert not X.isna().any().any(), "NaNs in features (not enough history?)"

    model = joblib.load(MODEL_PATH)
    prediction = model.predict(X)[0]

    print(f"Forecast for {X.index[0]}: {prediction:.3f} kW")


if __name__ == "__main__":
    main()