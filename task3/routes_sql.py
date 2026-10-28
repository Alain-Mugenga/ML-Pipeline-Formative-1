from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from database import get_mysql_connection
from models import Reading

router = APIRouter(prefix="/sql", tags=["MySQL"])

# One reading = a power_readings row + its 3 submeter_readings rows,
# turned into 3 columns (sub_metering_1..3) with conditional aggregation.
SELECT_READING = """
    SELECT
        p.reading_id,
        p.recorded_at,
        p.global_active_power,
        p.global_reactive_power,
        p.voltage,
        p.global_intensity,
        MAX(CASE WHEN s.submeter_id = 1 THEN s.energy_wh END) AS sub_metering_1,
        MAX(CASE WHEN s.submeter_id = 2 THEN s.energy_wh END) AS sub_metering_2,
        MAX(CASE WHEN s.submeter_id = 3 THEN s.energy_wh END) AS sub_metering_3
    FROM power_readings p
    JOIN submeter_readings s ON s.reading_id = p.reading_id
"""


def row_to_reading(row: dict) -> dict:
    """Turn a flat SQL row into the API's shape (DECIMAL -> float, nested submeters)."""
    return {
        "id": row["reading_id"],
        "recorded_at": row["recorded_at"],
        "global_active_power": float(row["global_active_power"]),
        "global_reactive_power": float(row["global_reactive_power"]),
        "voltage": float(row["voltage"]),
        "global_intensity": float(row["global_intensity"]),
        "submeters": {
            "sub_metering_1": float(row["sub_metering_1"]),
            "sub_metering_2": float(row["sub_metering_2"]),
            "sub_metering_3": float(row["sub_metering_3"]),
        },
    }


@router.get("/readings/latest", response_model=Reading)
def get_latest_reading():
    """The most recent reading, by recorded_at."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            SELECT_READING
            + " GROUP BY p.reading_id ORDER BY p.recorded_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="No readings found")
    return row_to_reading(row)


@router.get("/readings/range", response_model=list[Reading])
def get_readings_by_date_range(
    start: datetime,
    end: datetime,
    limit: int = Query(1000, ge=1, le=10000),
):
    """Readings with start <= recorded_at <= end, oldest first."""
    if start > end:
        raise HTTPException(status_code=400, detail="start must be before end")

    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            SELECT_READING
            + " WHERE p.recorded_at BETWEEN %s AND %s"
            + " GROUP BY p.reading_id ORDER BY p.recorded_at ASC LIMIT %s",
            (start, end, limit),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [row_to_reading(row) for row in rows]