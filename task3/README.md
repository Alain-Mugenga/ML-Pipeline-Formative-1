# Task 3: Electricity Readings API

This API gives access to the household electricity readings stored in Task 2. It works with both databases, MySQL and MongoDB, using the same endpoints and returning the same JSON, so the client doesn't need to know which database it is talking to.

## Files

- `main.py` starts the app and has two health checks.
- `database.py` connects to MySQL and MongoDB.
- `models.py` defines what a reading looks like and validates input.
- `routes_sql.py` has the MySQL endpoints, under `/sql`.
- `routes_mongo.py` has the MongoDB endpoints, under `/mongo`.

## Setup

Install the packages:

```
python -m pip install fastapi uvicorn mysql-connector-python pymongo python-dotenv
```

Create a `.env` file in the `task3` folder with your own database details:

```
MYSQL_HOST=127.0.0.1
MYSQL_USER=task2_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=electricity_task2
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
```

The `.env` file is ignored by Git, so passwords are never pushed. The databases must already contain the Task 2 data. For MongoDB, it can be loaded with `python task2/scripts/load_mongodb.py`.

## Running

```
cd task3
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to see and test every endpoint. To check that both databases are connected, open `/health/mysql` and `/health/mongo`.

## Endpoints

Each endpoint exists twice: once under `/sql` and once under `/mongo`.

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/readings` | Adds a new reading |
| GET | `/readings` | Lists readings, oldest first |
| GET | `/readings/{id}` | Gets one reading |
| PUT | `/readings/{id}` | Updates a reading |
| DELETE | `/readings/{id}` | Deletes a reading |
| GET | `/readings/latest` | Gets the most recent reading |
| GET | `/readings/range?start=...&end=...` | Gets readings between two dates |

For example, `/mongo/readings/latest` or `/sql/readings/range?start=2006-12-16T17:24:00&end=2006-12-16T18:00:00`.

A reading looks like this:

```json
{
  "recorded_at": "2006-12-16T17:24:00",
  "global_active_power": 4.216,
  "global_reactive_power": 0.418,
  "voltage": 234.84,
  "global_intensity": 18.4,
  "submeters": {
    "sub_metering_1": 0,
    "sub_metering_2": 1,
    "sub_metering_3": 17
  }
}
```

The API adds an `id` when it returns a reading. In MySQL the id is a number, and in MongoDB it is a text id such as `6ae36498d86576ad6ff614b5`.

## How the two databases differ

In MySQL, a reading is split across two tables: the main values in `power_readings` and the three submeter values in `submeter_readings`. The API joins them and returns them as one object. In MongoDB, each reading is a single document with the submeters already inside it, so no joining is needed.

## Data

The data is 20,000 minute-by-minute readings from the household electric power consumption dataset, covering 16 to 30 December 2006.