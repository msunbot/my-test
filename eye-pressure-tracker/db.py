import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "readings.db"))


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            pressure_left TEXT,
            pressure_right TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def add_reading(date, time, pressure_left, pressure_right):
    conn = get_connection()
    conn.execute(
        "INSERT INTO readings (date, time, pressure_left, pressure_right) VALUES (?, ?, ?, ?)",
        (date, time, pressure_left, pressure_right),
    )
    conn.commit()
    conn.close()


def get_all_readings():
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, time, pressure_left, pressure_right FROM readings ORDER BY date, time"
    ).fetchall()
    conn.close()
    return rows
