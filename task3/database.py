import os

import mysql.connector
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def get_mysql_connection():
    """Open a new MySQL connection. The caller must close it."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


# MongoDB: one shared client for the whole app
mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["electricity_task2"]
mongo_readings = mongo_db["power_readings"]