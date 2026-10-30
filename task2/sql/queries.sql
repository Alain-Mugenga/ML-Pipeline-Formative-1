
USE electricity_task2;


-- QUERY 1: Retrieve the latest electricity reading

SELECT
    reading_id,
    recorded_at,
    global_active_power,
    global_reactive_power,
    voltage,
    global_intensity
FROM power_readings
ORDER BY recorded_at DESC
LIMIT 1;

-- QUERY 2: Retrieve electricity readings within a date range

SELECT
    recorded_at,
    global_active_power,
    voltage,
    global_intensity
FROM power_readings
WHERE recorded_at >= '2006-12-16 17:24:00'
  AND recorded_at < '2006-12-16 18:00:00'
ORDER BY recorded_at ASC
LIMIT 5;

-- QUERY 3: Calculate average daily active power

SELECT
    DATE(recorded_at) AS reading_date,
    ROUND(AVG(global_active_power), 3) AS average_active_power_kw,
    COUNT(*) AS total_readings
FROM power_readings
GROUP BY DATE(recorded_at)
ORDER BY reading_date ASC;


