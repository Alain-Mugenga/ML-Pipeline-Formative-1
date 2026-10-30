import csv
from pathlib import Path
from getpass import getpass

import mysql.connector


# STEP 1: Locate the cleaned dataset

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = BASE_DIR / "data" / "cleaned_readings.csv"


# STEP 2: Connect to MySQL

password = getpass("Enter MySQL password for task2_user: ")

connection = mysql.connector.connect(
    host="127.0.0.1",
    user="task2_user",
    password=password,
    database="electricity_task2"
)

cursor = connection.cursor()

print("Connected to MySQL successfully!")


# STEP 3: Import electricity measurements

records_processed = 0

try:

    with open(CSV_FILE, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            # Insert electricity measurements

            cursor.execute(
                """
                INSERT IGNORE INTO power_readings
                (
                    recorded_at,
                    global_active_power,
                    global_reactive_power,
                    voltage,
                    global_intensity
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    row["recorded_at"],
                    row["global_active_power"],
                    row["global_reactive_power"],
                    row["voltage"],
                    row["global_intensity"]
                )
            )

            # Get the corresponding reading ID

            cursor.execute(
                """
                SELECT reading_id
                FROM power_readings
                WHERE recorded_at = %s
                """,
                (row["recorded_at"],)
            )

            reading_id = cursor.fetchone()[0]


            # Prepare the three submeter measurements

            submeter_data = [
                (reading_id, 1, row["sub_metering_1"]),
                (reading_id, 2, row["sub_metering_2"]),
                (reading_id, 3, row["sub_metering_3"])
            ]


            # Insert submeter measurements

            cursor.executemany(
                """
                INSERT IGNORE INTO submeter_readings
                (
                    reading_id,
                    submeter_id,
                    energy_wh
                )
                VALUES (%s, %s, %s)
                """,
                submeter_data
            )

            records_processed += 1

            # Save every 1000 records

            if records_processed % 1000 == 0:

                connection.commit()

                print(f"Processed {records_processed} records...")


    connection.commit()

    print("\nData import completed successfully!")

    print("CSV records processed:", records_processed)


    # Verify power readings

    cursor.execute("SELECT COUNT(*) FROM power_readings")

    power_count = cursor.fetchone()[0]


    # Verify submeter readings

    cursor.execute("SELECT COUNT(*) FROM submeter_readings")

    submeter_count = cursor.fetchone()[0]


    print("Total power readings:", power_count)

    print("Total submeter readings:", submeter_count)


except Exception:

    connection.rollback()

    raise


finally:

    cursor.close()

    connection.close()

    print("MySQL connection closed.")
