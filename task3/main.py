from fastapi import FastAPI

from database import get_mysql_connection

app = FastAPI(title="Electricity Time-Series API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health/mysql")
def health_mysql():
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM power_readings")
        (count,) = cursor.fetchone()
        return {"mysql": "connected", "power_readings": count}
    finally:
        conn.close()