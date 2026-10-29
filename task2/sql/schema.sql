-- TASK 2: RELATIONAL DATABASE DESIGN
-- Dataset: Individual Household Electric Power Consumption



-- STEP 1: CREATING DATABASE

CREATE DATABASE IF NOT EXISTS electricity_task2;

USE electricity_task2;



-- TABLE 1: POWER READINGS

CREATE TABLE IF NOT EXISTS power_readings (

    reading_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    recorded_at DATETIME NOT NULL UNIQUE,

    global_active_power DECIMAL(10,3) NOT NULL,

    global_reactive_power DECIMAL(10,3) NOT NULL,

    voltage DECIMAL(10,3) NOT NULL,

    global_intensity DECIMAL(10,3) NOT NULL

);



-- TABLE 2: SUBMETERS


CREATE TABLE IF NOT EXISTS submeters (

    submeter_id TINYINT UNSIGNED PRIMARY KEY,

    submeter_name VARCHAR(100) NOT NULL

);



-- TABLE 3: SUBMETER READINGS


CREATE TABLE IF NOT EXISTS submeter_readings (

    reading_id BIGINT NOT NULL,

    submeter_id TINYINT UNSIGNED NOT NULL,

    energy_wh DECIMAL(10,3) NOT NULL,

    PRIMARY KEY (reading_id, submeter_id),

    FOREIGN KEY (reading_id)
        REFERENCES power_readings(reading_id)
        ON DELETE CASCADE,

    FOREIGN KEY (submeter_id)
        REFERENCES submeters(submeter_id)

);



-- INSERT SUBMETER INFORMATION


INSERT IGNORE INTO submeters
(submeter_id, submeter_name)

VALUES
(1, 'Kitchen'),
(2, 'Laundry'),
(3, 'Water heater and air conditioning');
