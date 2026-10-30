# TASK 2: MongoDB Database Implementation
# Dataset: Individual Household Electric Power Consumption

import csv
import os

from pathlib import Path
from datetime import datetime, timezone
from pprint import pprint

from dotenv import load_dotenv
from pymongo import MongoClient, ReplaceOne, ASCENDING


# STEP 1: LOCATE PROJECT FILES

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = BASE_DIR / "data" / "cleaned_readings.csv"

load_dotenv(BASE_DIR / ".env")


# STEP 2: CONNECT TO MONGODB ATLAS

mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ValueError("MONGO_URI not found in .env")

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=15000
)

try:
    # Verify connection
    client.admin.command("ping")

    print("Connected to MongoDB Atlas successfully!")


    # STEP 3: CREATE DATABASE AND COLLECTION

    db = client["electricity_task2"]

    collection = db["power_readings"]

    # Prevent duplicate timestamps
    collection.create_index(
        [("recorded_at", ASCENDING)],
        unique=True
    )

    print("Database: electricity_task2")
    print("Collection: power_readings")


    # STEP 4: IMPORT ELECTRICITY DATA

    operations = []

    records_processed = 0

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            # Convert timestamp into MongoDB Date.
            # UTC is used as the team's storage convention.
            recorded_at = datetime.strptime(
                row["recorded_at"],
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)


            # Create MongoDB document
            document = {

                "recorded_at": recorded_at,

                "global_active_power":
                    float(row["global_active_power"]),

                "global_reactive_power":
                    float(row["global_reactive_power"]),

                "voltage":
                    float(row["voltage"]),

                "global_intensity":
                    float(row["global_intensity"]),

                "submeters": {

                    "sub_metering_1":
                        float(row["sub_metering_1"]),

                    "sub_metering_2":
                        float(row["sub_metering_2"]),

                    "sub_metering_3":
                        float(row["sub_metering_3"])

                }
            }


            # Insert or update the document
            operations.append(

                ReplaceOne(
                    {"recorded_at": recorded_at},
                    document,
                    upsert=True
                )

            )

            records_processed += 1


            # Import in batches of 500
            if len(operations) == 500:

                collection.bulk_write(operations)

                operations.clear()

                print(
                    f"Processed {records_processed} records..."
                )


        # Import any remaining records
        if operations:

            collection.bulk_write(operations)


    # STEP 5: VERIFY IMPORTED RECORDS

    total_records = collection.count_documents({})

    print("\nMongoDB data import completed!")

    print("CSV records processed:", records_processed)

    print("Total MongoDB documents:", total_records)


    # Display one sample document
    print("\nSample MongoDB document:")

    sample = collection.find_one(
        {},
        sort=[("recorded_at", ASCENDING)]
    )

    pprint(sample)

finally:

    client.close()

    print("\nMongoDB connection closed.")
