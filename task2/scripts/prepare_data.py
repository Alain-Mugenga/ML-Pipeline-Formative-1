import csv
from datetime import datetime
from pathlib import Path

# Locate the dataset folder
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Original Kaggle dataset
input_file = DATA_DIR / "household_power_consumption.txt"

# Prepared dataset
output_file = DATA_DIR / "cleaned_readings.csv"

# Number of valid records for initial database testing
MAX_ROWS = 10000

# Original measurement columns
measurement_columns = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

# Output columns
output_columns = [
    "recorded_at",
    "global_active_power",
    "global_reactive_power",
    "voltage",
    "global_intensity",
    "sub_metering_1",
    "sub_metering_2",
    "sub_metering_3"
]

valid_rows = 0
missing_rows = 0

# Read the original dataset
with open(input_file, "r", encoding="utf-8") as infile:

    reader = csv.DictReader(infile, delimiter=";")

    # Create the cleaned CSV file
    with open(output_file, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)
        writer.writerow(output_columns)

        for row in reader:

            try:
                # Combine Date and Time
                timestamp = datetime.strptime(
                    row["Date"] + " " + row["Time"],
                    "%d/%m/%Y %H:%M:%S"
                )

                # Convert measurements to numeric values
                measurements = [
                    float(row[column])
                    for column in measurement_columns
                ]

            except (ValueError, TypeError, KeyError):
                missing_rows += 1
                continue

            # Write the valid record
            writer.writerow([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                *measurements
            ])

            valid_rows += 1

            if valid_rows >= MAX_ROWS:
                break

print("Data preparation completed successfully!")
print("Valid records:", valid_rows)
print("Invalid/missing records skipped:", missing_rows)
print("Output file:", output_file)
