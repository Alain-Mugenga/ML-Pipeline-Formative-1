# Task 4: Hourly Power Forecast Script

Forecasts the next hour of `Global_active_power` (household electricity use, in kW). The script fetches recent readings from the Task 3 API, preprocesses them with the same code Task 1 used for training, loads the trained model, and prints a forecast.

**Author:** Sandrine Umugwaneza

## How it works

1. **Fetch.** Gets the newest timestamp from `/mongo/readings/latest`, then requests the previous 200 hours of minute readings from `/mongo/readings/range`. The API returns at most 10,000 rows per request, so the script fetches in 5-day chunks.
2. **Preprocess.** Flattens the sub-meter fields, renames columns to match Task 1, adds `Sub_metering_4`, converts to hourly means and fills gaps. It then builds the 30 model features (lags, moving averages, calendar features) using `task1_eda_modeling/preprocessing.py`. Reusing Task 1's code keeps training and prediction identical.
3. **Load the model.** Loads `task1_eda_modeling/models/best_model.joblib` (a tuned HistGradientBoostingRegressor) and checks the feature columns against `feature_columns.json`.
4. **Predict.** Forecasts `Global_active_power` for the hour after the last complete hour.

The model looks back up to 168 hours (one week), so at least 168 hours of history must exist in the database. The script fetches 200 for a safety margin.

## Setup

From the repository root:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r task4/requirements.txt
```

## Run

**1. Start the Task 3 API** (in a separate terminal):

```powershell
cd task3
pip install fastapi uvicorn pymongo python-dotenv mysql-connector-python
python -m uvicorn main:app --reload
```

The API needs a `.env` file inside `task3/` with the MongoDB connection string (ask the Task 3 owner for it; never commit this file):

```
MONGO_URI=<your MongoDB Atlas connection string>
```

**2. Run the forecast** (from the repository root, with the venv active):

```powershell
python task4/forecast.py
```

To use a different API address, set the `API_URL` environment variable (default: `http://127.0.0.1:8000/mongo`).

## Example output

```
Fetched 200 hourly rows: 2006-12-22 06:00:00 to 2006-12-30 13:00:00
Forecast for 2006-12-30 14:00:00: 2.185 kW
```

## Error handling

The script exits with a clear one-line message if:
- the API is unreachable or returns no data
- the built features do not match the model's training columns
- there is not enough history to build all features
- the model file is missing

## Notes and limits

- The database holds the first 20,000 minute readings (16 to 30 December 2006), so "latest" means 30 December 2006, not today.
- The model was trained in Task 1 (test RMSE 0.463, MAE 0.315, R² 0.649).
- The script has only been tested against the `/mongo` endpoints.

## Files

| File | Purpose |
|---|---|
| `forecast.py` | The forecast script |
| `requirements.txt` | Task 4 dependencies (also installs the root requirements) |