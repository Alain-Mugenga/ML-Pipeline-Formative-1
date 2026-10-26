# TASK 2: MongoDB Time-Series Queries
# Dataset: Individual Household Electric Power Consumption

import os
from pathlib import Path
from datetime import datetime, timezone
from pprint import pprint

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING, ASCENDING


# STEP 1: CONNECT TO MONGODB

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ValueError("MONGO_URI not found in .env")


client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=15000
)

try:
    client.admin.command("ping")

    print("Connected to MongoDB Atlas successfully!")

    db = client["electricity_task2"]

    collection = db["power_readings"]


    # QUERY 1: LATEST ELECTRICITY READING

    print("\n======================================")
    print("QUERY 1: LATEST ELECTRICITY READING")
    print("======================================")

    latest_record = collection.find_one(
        {},
        {"_id": 0},
        sort=[("recorded_at", DESCENDING)]
    )

    pprint(latest_record)


    # QUERY 2: RECORDS WITHIN A DATE RANGE

    print("\n======================================")
    print("QUERY 2: RECORDS BY DATE RANGE")
    print("======================================")

    start_date = datetime(
        2006, 12, 16, 17, 24,
        tzinfo=timezone.utc
    )

    end_date = datetime(
        2006, 12, 16, 18, 0,
        tzinfo=timezone.utc
    )

    date_range_records = collection.find(
        {
            "recorded_at": {
                "$gte": start_date,
                "$lt": end_date
            }
        },
        {"_id": 0}
    ).sort(
        "recorded_at", ASCENDING
    ).limit(5)

    for record in date_range_records:
        pprint(record)



    # QUERY 3: DAILY AVERAGE ACTIVE POWER


    print("\n======================================")
    print("QUERY 3: DAILY AVERAGE ACTIVE POWER")
    print("======================================")

    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$recorded_at",
                        "timezone": "UTC"
                    }
                },
                "average_active_power_kw": {
                    "$avg": "$global_active_power"
                },
                "total_readings": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        },
        {
            "$project": {
                "_id": 0,
                "reading_date": "$_id",
                "average_active_power_kw": {
                    "$round": ["$average_active_power_kw", 3]
                },
                "total_readings": 1
            }
        }
    ]

    daily_averages = collection.aggregate(pipeline)

    for result in daily_averages:
        pprint(result)


    print("\nAll three MongoDB queries completed!")

finally:
    client.close()
    print("MongoDB connection closed.")
