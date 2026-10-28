"""
preprocessing.py
----------------
Reusable preprocessing for the Household Power Consumption time-series project.

Used by:
  * Task 1 notebook (EDA + modelling)
  * Task 4 forecast script (same pipeline => no train/serve mismatch)

Pipeline:  raw minute data -> add Sub_metering_4 -> hourly mean -> fill gaps -> feature table
"""
import numpy as np
import pandas as pd

TARGET = "Global_active_power"
SUB_METERS = ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3", "Sub_metering_4"]
EXOG_COLS = ["Global_reactive_power", "Voltage", "Global_intensity"] + SUB_METERS
TARGET_LAGS = [1, 2, 3, 6, 12, 24, 48, 168]   # 1h, 2h, 3h, 6h, 12h, 1 day, 2 days, 1 week
ROLL_WINDOWS = [3, 6, 24, 168]                 # hours


def load_raw(path):
    """Read the UCI text file; '?' marks missing values; build a DatetimeIndex."""
    df = pd.read_csv(path, sep=";", na_values=["?"], low_memory=False)
    df.index = pd.to_datetime(df.pop("Date") + " " + df.pop("Time"), format="%d/%m/%Y %H:%M:%S")
    df.index.name = "datetime"
    return df.astype("float64").sort_index()


def add_unmetered(df):
    """Sub_metering_4 = active energy (Wh/min) NOT captured by sub-meters 1-3."""
    df = df.copy()
    metered = df[["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]].sum(axis=1, skipna=False)
    df["Sub_metering_4"] = df[TARGET] * 1000 / 60 - metered
    return df


def to_hourly(df):
    """Aggregate minute data to hourly means (NaNs are ignored inside each hour)."""
    return df.resample("60min").mean()


def fill_missing_hourly(hourly, short_gap=6, season=168):
    """
    Gap-aware imputation on the hourly table.
      * gaps <= `short_gap` hours  -> time-based linear interpolation
      * longer gaps                -> same hour one week earlier (fallback: one week later)
    """
    h = hourly.copy()
    gap = h.isna().any(axis=1)
    run_id = (gap != gap.shift()).cumsum()
    run_len = gap.groupby(run_id).transform("sum")
    short = gap & (run_len <= short_gap)

    interp = h.interpolate(method="time", limit_area="inside")
    h.loc[short] = interp.loc[short]

    h = h.fillna(h.shift(season))      # same hour, previous week
    h = h.fillna(h.shift(-season))     # same hour, next week (only used at the very start)
    return h.ffill().bfill()           # safety net, should be a no-op


def build_features(hourly):
    """
    Supervised table for one-step-ahead forecasting: predict Global_active_power at hour t
    using ONLY information available up to hour t-1 (every feature is shifted >= 1).
    """
    y = hourly[TARGET]
    out = pd.DataFrame(index=hourly.index)
    out[TARGET] = y

    for L in TARGET_LAGS:                                   # lagged features
        out[f"lag_{L}"] = y.shift(L)
    for w in ROLL_WINDOWS:                                  # moving averages (of the PAST w hours)
        out[f"roll_mean_{w}"] = y.shift(1).rolling(w).mean()
    out["roll_std_24"] = y.shift(1).rolling(24).std()

    for c in EXOG_COLS:                                     # other sensors, previous hour
        out[f"{c}_lag1"] = hourly[c].shift(1)

    idx = out.index                                         # calendar features (known in advance)
    out["hour"] = idx.hour
    out["dayofweek"] = idx.dayofweek
    out["month"] = idx.month
    out["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    out["hour_sin"], out["hour_cos"] = np.sin(2 * np.pi * idx.hour / 24), np.cos(2 * np.pi * idx.hour / 24)
    out["dow_sin"], out["dow_cos"] = np.sin(2 * np.pi * idx.dayofweek / 7), np.cos(2 * np.pi * idx.dayofweek / 7)
    out["month_sin"], out["month_cos"] = np.sin(2 * np.pi * idx.month / 12), np.cos(2 * np.pi * idx.month / 12)
    return out


def feature_columns():
    """Names of the model inputs (everything except the target)."""
    cols = [f"lag_{L}" for L in TARGET_LAGS] + [f"roll_mean_{w}" for w in ROLL_WINDOWS] + ["roll_std_24"]
    cols += [f"{c}_lag1" for c in EXOG_COLS]
    cols += ["hour", "dayofweek", "month", "is_weekend", "hour_sin", "hour_cos",
             "dow_sin", "dow_cos", "month_sin", "month_cos"]
    return cols


def features_for_next_hour(hourly):
    """Task 4 helper: feature row for the hour AFTER the last hour in `hourly`."""
    next_ts = hourly.index[-1] + pd.Timedelta(hours=1)
    ext = hourly.reindex(hourly.index.append(pd.DatetimeIndex([next_ts])))
    return build_features(ext).iloc[[-1]][feature_columns()]
