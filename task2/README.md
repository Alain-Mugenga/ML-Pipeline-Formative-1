# Task 2: Database Design and Implementation

## 1. Dataset Description

**Dataset:** Individual Household Electric Power Consumption

**Source:** Kaggle / UCI Machine Learning Repository

**Dataset link:** https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set/data

The dataset contains minute-level household electricity consumption measurements recorded between December 2006 and November 2010.

The measurements include global active power, global reactive power, voltage, global intensity, and three submeter readings.

The database implementation uses 20,000 valid minute-level electricity readings selected from the original Kaggle dataset.

The records cover the period from 16 December 2006 at 17:24 to 30 December 2006 at 14:47.

Database verification identified two timestamp gaps containing a total of four missing minutes.

The data preparation script confirmed that four incomplete source records were skipped when generating the 20,000 valid readings.

The same prepared dataset was imported into MySQL and MongoDB to allow consistent querying and comparison.

## 2. MySQL Relational Database Design

**Database name:** `electricity_task2`

The relational database consists of three tables.

### Table 1: power_readings

Stores the general electricity measurements.

Fields:

* `reading_id` — Primary key
* `recorded_at` — Unique measurement timestamp
* `global_active_power` — Active power in kW
* `global_reactive_power` — Reactive power in kW
* `voltage` — Voltage in volts
* `global_intensity` — Electrical current in amperes

### Table 2: submeters

Stores information about the three household electricity circuits.

Fields:

* `submeter_id` — Primary key
* `submeter_name` — Name of the electricity circuit

The three submeters are:

1. Kitchen
2. Laundry
3. Water heater and air conditioning

### Table 3: submeter_readings

Stores the measurements from each submeter.

Fields:

* `reading_id` — Foreign key referencing power_readings
* `submeter_id` — Foreign key referencing submeters
* `energy_wh` — Submeter measurement in watt-hours

The combination of `reading_id` and `submeter_id` forms the composite primary key.

### Database Relationships

The database contains two one-to-many relationships:

* One power reading can have multiple submeter readings.
* One submeter can be associated with multiple measurements.

The `submeter_readings` table connects the other two tables.

### Entity Relationship Diagram

See `docs/erd.png`.

### SQL Implementation

SQL schema: `sql/schema.sql`

Data import script: `scripts/load_mysql.py`

SQL queries: `sql/queries.sql`

### MySQL Implementation Results

The database was successfully populated with:

* 20,000 power readings
* 3 submeter types
* 60,000 submeter readings

A JOIN query confirmed that the relationships between all three tables work correctly.

## 3. MongoDB Collection Design

**Database name:** `electricity_task2`

**Collection name:** `power_readings`

MongoDB stores electricity measurements as documents.

Each document contains the measurement timestamp, general electricity readings, and embedded submeter values.

### Sample MongoDB Document

```json
{
  "recorded_at": "2006-12-16T17:24:00Z",
  "global_active_power": 4.216,
  "global_reactive_power": 0.418,
  "voltage": 234.84,
  "global_intensity": 18.4,
  "submeters": {
    "sub_metering_1": 0.0,
    "sub_metering_2": 1.0,
    "sub_metering_3": 17.0
  }
}
```

This is a JSON representation of the document. The actual MongoDB database stores the timestamp as a BSON Date and automatically assigns an `_id`.

### MongoDB Design Explanation

Unlike MySQL, which distributes measurements across related tables, MongoDB stores all measurements for a timestamp in one document.

The three submeter values are embedded inside the `submeters` object.

This structure enables electricity measurements to be retrieved without joining multiple tables.

A unique index on `recorded_at` prevents duplicate timestamps.

### MongoDB Implementation

Data import script: `scripts/load_mongodb.py`

MongoDB query script: `scripts/queries_mongodb.py`

The MongoDB collection was successfully populated with 20,000 electricity consumption documents.

## 4. Database Queries

Three analytical queries were implemented in both MySQL and MongoDB. An additional hourly aggregation query was implemented in MySQL to demonstrate time-series analysis.

### Query 1: Latest Electricity Reading

Retrieves the most recent electricity measurement.

### Query 2: Electricity Readings by Date Range

Retrieves measurements recorded within a specified time interval.

### Query 3: Average Daily Active Power

Groups electricity measurements by date and calculates the average global active power in kW.

### Query 4: Hourly Average Active Power (MySQL)

Calculates the average global active power for each hourly interval using MySQL's DATE_FORMAT(), AVG(), and GROUP BY functions.

This query demonstrates hourly aggregation of minute-level electricity measurements, which is relevant to the project's time-series forecasting pipeline.

The actual results are saved in docs/mysql_results.txt.

### Query Results

MySQL results: `docs/mysql_results.txt`

MongoDB results: `docs/mongodb_results.txt`

The queries were executed successfully, and the results were consistent across both databases.

## 5. MySQL and MongoDB Comparison

| Feature         | MySQL                    | MongoDB                         |
| --------------- | ------------------------ | ------------------------------- |
| Database model  | Relational               | Document-oriented               |
| Data structure  | Three related tables     | One collection                  |
| Record storage  | Rows                     | Documents                       |
| Relationships   | Primary and foreign keys | Embedded fields                 |
| Query approach  | SQL                      | MongoDB queries and aggregation |
| Timestamp field | DATETIME                 | BSON Date                       |
| Data imported   | 20,000 power readings    | 20,000 documents                |

Both databases support the required time-series retrieval and aggregation operations.

## 6. Implementation Instructions

### Python Dependencies

Install the dependencies using:

```bash
python -m pip install -r task2/requirements.txt
```

### Dataset Preparation

Download the original dataset from Kaggle and place `household_power_consumption.txt` inside `task2/data/`.

Run:

```bash
python task2/scripts/prepare_data.py
```

### MySQL

Create the database using the SQL schema:

```bash
sudo mysql < task2/sql/schema.sql
```

Configure an authorized MySQL database user with the required permissions.

Import the prepared dataset:

```bash
python task2/scripts/load_mysql.py
```

Execute the SQL queries:

```bash
mysql -h 127.0.0.1 -u task2_user -p electricity_task2 < task2/sql/queries.sql
```

### MongoDB

Configure a MongoDB Atlas connection string in `task2/.env`:

```env
MONGO_URI=YOUR_MONGODB_CONNECTION_STRING
```

Import the prepared dataset:

```bash
python task2/scripts/load_mongodb.py
```

Execute the MongoDB queries:

```bash
python task2/scripts/queries_mongodb.py
```

Database passwords and connection strings must not be committed to GitHub.

## 7. Integration With Other Tasks


### Task 1: Data Preprocessing and Forecasting

Task 1's forecasting model uses hourly electricity consumption data with a historical lookback window of 168 hours (7 days).

The Task 2 databases store 20,000 valid minute-level electricity consumption readings. These can be aggregated into hourly measurements to provide the historical data required by the forecasting model.

A MySQL hourly aggregation query has been implemented to demonstrate the transformation of minute-level readings into hourly averages.

The prediction pipeline must apply the same preprocessing and feature transformations used during Task 1's model training.

### Task 3: API Implementation

Task 3 can use the MySQL tables and MongoDB collection to implement CRUD operations and time-series retrieval endpoints.

MySQL database: `electricity_task2`

MySQL main table: `power_readings`

MySQL primary key: `reading_id`

MongoDB database: `electricity_task2`

MongoDB collection: `power_readings`

MongoDB document identifier: `_id`

Common timestamp field: `recorded_at`

Task 3 can recreate the local MySQL database using the provided schema and import scripts or use an authorized shared database connection.

MongoDB Atlas access requires appropriate database credentials and network authorization.

### Task 4: Prediction Script

Task 4 can use the API developed in Task 3 to retrieve electricity measurements for forecasting.

Important fields include:

* `recorded_at`
* `global_active_power`
* `global_reactive_power`
* `voltage`
* `global_intensity`

Task 1's forecasting model requires 168 hourly observations. Task 4 must retrieve sufficient historical readings through Task 3's API and preprocess them into the same hourly format and feature structure used during model training.

## 8. Implementation Scope

## 8. Implementation Scope

The database implementation uses 20,000 valid minute-level electricity readings from the Kaggle Individual Household Electric Power Consumption dataset.

The data preparation process skipped four incomplete records. The resulting database covers 16 December 2006 at 17:24 to 30 December 2006 at 14:47, with two timestamp gaps containing four missing minutes.

MySQL contains 20,000 power readings and 60,000 associated submeter readings. MongoDB contains 20,000 electricity documents.

Both databases support latest-record retrieval, date-range filtering, and daily average power calculations. MySQL additionally implements an hourly average power query.

The longest uninterrupted historical period contains 12,883 consecutive minute-level readings (214.72 hours), from 21 December 2006 at 11:25 to 30 December 2006 at 10:07.

Task 1's forecasting model requires 168 hourly observations (7 days). Task 4 has confirmed that its prediction script runs successfully.

MongoDB stores timestamps as UTC according to the project's storage convention, while MySQL uses DATETIME.

Both databases contain equivalent electricity measurements, and their analytical query results have been verified to match.
