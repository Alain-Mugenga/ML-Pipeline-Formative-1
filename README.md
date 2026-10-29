# Time Series Pipeline: Household Power Consumption Forecasting

ALU group assignment (Time Series Pipeline). We forecast the next hour of household electricity use, store the data in MySQL and MongoDB, expose it through a REST API, and run a prediction script that ties everything together.

## Problem and dataset

**Goal:** predict `Global_active_power` (kW) for the next hour.

**Dataset:** [Individual Household Electric Power Consumption](https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set/data) (Kaggle / UCI Machine Learning Repository). It has a clear timestamp, a numeric target and several measured variables (reactive power, voltage, current intensity and three sub-meters), which is what the assignment requires. Household load forecasting is a practical problem for demand planning and for spotting wasted energy.

- Raw data: one reading per minute, December 2006 to November 2010
- Modelled at hourly resolution (34,589 hourly rows after cleaning)
- Missing values: short gaps (6 hours or less) are interpolated; longer gaps use the same hour from the previous week

## Team



Nina Cyndy Bwiza: Task 1, EDA, analytical questions, preprocessing, model and experiments 
Alain Christian Mugenga: Task 2, MySQL schema and ERD, MongoDB design, queries 
Nazira Umucyo: Task 3 FastAPI CRUD, latest and date-range endpoints for MySQL and MongoDB 
Sandrine Umugwaneza: Task 4,Forecast script: API fetch, preprocessing, model loading, prediction |

## Repository structure

```
.
├── task1_eda_modeling/   EDA notebook, preprocessing.py, figures, trained model
├── task2/                SQL schema, ERD, MongoDB scripts, query results
├── task3/                FastAPI application (/sql and /mongo endpoints)
├── task4/                Forecast script
├── requirements.txt
└── README.md
```

## How the pieces connect

```
Raw minute data -> MySQL + MongoDB (Task 2) -> REST API (Task 3)
                                                    |
        Task 1 preprocessing + trained model  ->  Task 4 forecast script -> next-hour forecast
```

## Model results (Task 1)

One-step-ahead forecast on a held-out test period (training ends 2009-12-31).

| Experiment | Test RMSE | Test MAE | Test R² |
|---|---|---|---|
| Persistence (previous hour) | 0.619 | 0.408 | 0.372 |
| Ridge (tuned) | 0.518 | 0.369 | 0.560 |
| Random Forest (tuned) | 0.465 | 0.314 | 0.647 |
| **HistGradientBoosting (tuned)** | **0.463** | **0.315** | **0.649** |

The final model uses 30 features: lagged values (1 to 168 hours), moving averages, other sensors from the previous hour and calendar features. The full experiment table is in `task1_eda_modeling/data/experiment_table.csv`.

## Databases (Task 2)

- **MySQL** (`electricity_task2`): 3 tables, `power_readings`, `submeters` and `submeter_readings` (20,000 power readings, 60,000 submeter readings). ERD: `task2/docs/erd.png`.
- **MongoDB** (`electricity_task2`, collection `power_readings`): one document per reading, with the three sub-meter values embedded.
- Each database has three queries (latest reading, date range, average daily power). Results are in `task2/docs/`.

## API (Task 3)

FastAPI application with the same endpoints under `/sql` and `/mongo`:

| Method | Path | What it does |
|---|---|---|
| POST | `/readings` | Add a reading |
| GET | `/readings` | List readings, oldest first |
| GET | `/readings/{id}` | Get one reading |
| PUT | `/readings/{id}` | Update a reading |
| DELETE | `/readings/{id}` | Delete a reading |
| GET | `/readings/latest` | Most recent reading |
| GET | `/readings/range?start=...&end=...` | Readings between two dates |

## Forecast script (Task 4)

`task4/forecast.py` fetches the last 200 hours of minute readings from the API, converts them to hourly data with Task 1's preprocessing, builds the 30 features, loads the trained model and prints the forecast for the next hour. Example output:

```
Fetched 200 hourly rows: 2006-12-22 06:00:00 to 2006-12-30 13:00:00
Forecast for 2006-12-30 14:00:00: 2.185 kW
```

## How to run

Tested with Python 3.14. From the repository root:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

1. **Task 1:** open `task1_eda_modeling/Task1_Time_Series_EDA_and_Modeling.ipynb` and run all cells. The cleaned hourly data is in `task1_eda_modeling/data/hourly_clean.csv`.
2. **Task 2:** see `task2/README.md`. In short: run `pip install -r task2/requirements.txt`, download `household_power_consumption.txt` from Kaggle into `task2/data/`, run `python task2/scripts/prepare_data.py`, create the MySQL database with `task2/sql/schema.sql`, put `MONGO_URI` in `task2/.env`, then run `load_mysql.py` and `load_mongodb.py`.
3. **Task 3:** see `task3/README.md`. Create a `.env` file inside `task3/` with your database settings (never commit it), then start the API:
   ```powershell
   pip install fastapi uvicorn pymongo python-dotenv mysql-connector-python
   cd task3
   python -m uvicorn main:app --reload
   ```
   Interactive docs are at `http://127.0.0.1:8000/docs`.
4. **Task 4:** with the API running, from the repository root:
   ```powershell
   pip install -r task4/requirements.txt
   python task4/forecast.py
   ```
   To use a different API address, set the `API_URL` environment variable (default: `http://127.0.0.1:8000/mongo`). See `task4/README.md`.

## Security

Database credentials live in `.env` files, which are ignored by Git. Never commit them.

## Known limitations

- The databases hold the first 20,000 minute readings (16 to 30 December 2006), so the forecast demo predicts for 30 December 2006.
- The model needs at least 168 hours of history to build all of its features.
- The MySQL endpoints need a local MySQL server. The Task 4 script was tested against the MongoDB (Atlas) endpoints.