from datetime import datetime

import mysql.connector
from fastapi import APIRouter, HTTPException, Query, Response

from database import get_mysql_connection
from models import Reading, ReadingCreate

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

DUPLICATE_ENTRY = 1062  # MySQL error code for a UNIQUE violation


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


def fetch_reading(cursor, reading_id: int):
    """Return one reading as a flat row, or None if the id does not exist."""
    cursor.execute(
        SELECT_READING + " WHERE p.reading_id = %s GROUP BY p.reading_id",
        (reading_id,),
    )
    return cursor.fetchone()


def submeter_rows(reading_id: int, reading: ReadingCreate):
    """The 3 (reading_id, submeter_id, energy_wh) rows for submeter_readings."""
    s = reading.submeters
    return [
        (reading_id, 1, s.sub_metering_1),
        (reading_id, 2, s.sub_metering_2),
        (reading_id, 3, s.sub_metering_3),
    ]


# --- Time-series endpoints (fixed paths: keep these above /readings/{reading_id}) ---


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


# --- CRUD endpoints ---


@router.get("/readings", response_model=list[Reading])
def list_readings(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """A page of readings, oldest first."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            SELECT_READING
            + " GROUP BY p.reading_id ORDER BY p.recorded_at ASC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [row_to_reading(row) for row in rows]


@router.get("/readings/{reading_id}", response_model=Reading)
def get_reading(reading_id: int):
    """One reading by its id."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        row = fetch_reading(cursor, reading_id)
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")
    return row_to_reading(row)


@router.post("/readings", response_model=Reading, status_code=201)
def create_reading(reading: ReadingCreate):
    """Create a reading: one power_readings row plus 3 submeter_readings rows."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO power_readings
                (recorded_at, global_active_power, global_reactive_power,
                 voltage, global_intensity)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                reading.recorded_at,
                reading.global_active_power,
                reading.global_reactive_power,
                reading.voltage,
                reading.global_intensity,
            ),
        )
        new_id = cursor.lastrowid
        cursor.executemany(
            """
            INSERT INTO submeter_readings (reading_id, submeter_id, energy_wh)
            VALUES (%s, %s, %s)
            """,
            submeter_rows(new_id, reading),
        )
        conn.commit()
        row = fetch_reading(cursor, new_id)
    except mysql.connector.IntegrityError as error:
        conn.rollback()
        if error.errno == DUPLICATE_ENTRY:
            raise HTTPException(
                status_code=409,
                detail="A reading with this recorded_at already exists",
            )
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return row_to_reading(row)


@router.put("/readings/{reading_id}", response_model=Reading)
def update_reading(reading_id: int, reading: ReadingCreate):
    """Replace a reading completely (same body as POST)."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        if fetch_reading(cursor, reading_id) is None:
            raise HTTPException(status_code=404, detail="Reading not found")

        cursor.execute(
            """
            UPDATE power_readings
            SET recorded_at = %s,
                global_active_power = %s,
                global_reactive_power = %s,
                voltage = %s,
                global_intensity = %s
            WHERE reading_id = %s
            """,
            (
                reading.recorded_at,
                reading.global_active_power,
                reading.global_reactive_power,
                reading.voltage,
                reading.global_intensity,
                reading_id,
            ),
        )
        for _, submeter_id, energy_wh in submeter_rows(reading_id, reading):
            cursor.execute(
                """
                UPDATE submeter_readings
                SET energy_wh = %s
                WHERE reading_id = %s AND submeter_id = %s
                """,
                (energy_wh, reading_id, submeter_id),
            )
        conn.commit()
        row = fetch_reading(cursor, reading_id)
    except mysql.connector.IntegrityError as error:
        conn.rollback()
        if error.errno == DUPLICATE_ENTRY:
            raise HTTPException(
                status_code=409,
                detail="Another reading already has this recorded_at",
            )
        raise
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return row_to_reading(row)


@router.delete("/readings/{reading_id}", status_code=204)
def delete_reading(reading_id: int):
    """Delete a reading. ON DELETE CASCADE removes its submeter_readings rows."""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM power_readings WHERE reading_id = %s", (reading_id,)
        )
        conn.commit()
        deleted = cursor.rowcount
    finally:
        conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Reading not found")
    return Response(status_code=204)