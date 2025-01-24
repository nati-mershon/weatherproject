import pyodbc
import requests
import logging
import random
import time
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify

from prometheus_flask_exporter import PrometheusMetrics


# 📌 Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Database connection parameters
DB_SERVER = os.getenv("MSSQL_HOST", "sqlserver.default.svc.cluster.local")  # ✅ שינוי לכתובת פנימית
DB_PORT = os.getenv("MSSQL_PORT", "1433")
DB_NAME = os.getenv("MSSQL_DATABASE", "WeatherDB")
DB_USER = os.getenv("MSSQL_USER", "sa")
DB_PASSWORD = os.getenv("SA_PASSWORD", "YourPassword123")

app = Flask(__name__)
fetching_data = False  # 🔹 משתנה למעקב אחרי מצב תהליך העדכון


# הוספת המטריקות לאפליקציה
metrics = PrometheusMetrics(app)


def get_db_connection():
    """ יוצר חיבור ל-SQL Server """
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            f"TrustServerCertificate=yes;",
            timeout=10
        )
        logging.info("✅ Successfully connected to SQL Server!")
        return conn
    except Exception as e:
        logging.error(f"🚨 Error connecting to SQL Server: {e}")
        return None

@app.route("/healthz")
def health_check():
    """ בדיקת מצב השירות """
    return jsonify({"status": "ok", "message": "Weather service is running!"}), 200

@app.route("/weather")
def get_weather_data():
    """ מחזיר נתוני מזג אוויר מהמאגר """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 10 * FROM WeatherData ORDER BY date DESC")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        results = [{"id": row[0], "city_id": row[1], "date": row[2], "min_temp": row[3], "max_temp": row[4]} for row in data]
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"🚨 Error fetching weather data: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route("/status")
def status():
    return jsonify({"fetching": fetching_data}), 200

@app.route("/fetch", methods=["POST"])
def fetch_weather():
    """ מפעיל תהליך רקע להבאת נתוני מזג אוויר """
    global fetching_data
    if fetching_data:
        return jsonify({"message": "Weather data fetch already in progress!"}), 409
    threading.Thread(target=fetch_and_store_weather_data, daemon=True).start()
    return jsonify({"message": "Weather data fetch started!", "status": "ok"}), 200

def fetch_and_store_weather_data():
    """ מביא ושומר נתוני מזג אוויר מ-API חיצוני """
    global fetching_data
    fetching_data = True
    try:
        connection = get_db_connection()
        if not connection:
            logging.error("🚨 Failed to connect to database, aborting fetch process.")
            fetching_data = False
            return
        cursor = connection.cursor()

        CITIES = [
            {"name": "London", "lat": 51.5074, "lon": -0.1278},
            {"name": "New York", "lat": 40.7128, "lon": -74.0060},
            {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
            {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
            {"name": "Sydney", "lat": -33.8688, "lon": 151.2093}
        ]

        selected_city = random.choice(CITIES)
        CITY_NAME, LAT, LON = selected_city["name"], selected_city["lat"], selected_city["lon"]
        logging.info(f"🌍 Fetching weather data for {CITY_NAME} ({LAT}, {LON})")

        today = datetime.today()
        START_DATE = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        END_DATE = today.strftime('%Y-%m-%d')

        URL = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={START_DATE}&end_date={END_DATE}&daily=temperature_2m_min,temperature_2m_max,precipitation_sum&timezone=auto"
        response = requests.get(URL)
        data = response.json()

        if "daily" not in data:
            logging.error(f"❌ API response is missing 'daily' data! Full response: {data}")
            return

        logging.info("📥 Inserting data into WeatherData table...")

        cursor.execute("SELECT id FROM Cities WHERE name = ?", CITY_NAME)
        city_row = cursor.fetchone()
        if city_row:
            city_id = city_row[0]
        else:
            cursor.execute("INSERT INTO Cities (name, latitude, longitude) VALUES (?, ?, ?)", CITY_NAME, LAT, LON)
            cursor.execute("SELECT id FROM Cities WHERE name = ?", CITY_NAME)
            city_id = cursor.fetchone()[0]
        connection.commit()

        for i, date in enumerate(data['daily']['time']):
            min_temp = data['daily']['temperature_2m_min'][i] or 0.0
            max_temp = data['daily']['temperature_2m_max'][i] or 0.0
            precipitation = data['daily']['precipitation_sum'][i] or 0.0

            cursor.execute("SELECT COUNT(*) FROM WeatherData WHERE city_id = ? AND date = ?", city_id, date)
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO WeatherData (city_id, date, min_temp, max_temp, precipitation) VALUES (?, ?, ?, ?, ?)",
                    city_id, date, min_temp, max_temp, precipitation
                )
                logging.info(f"✅ Stored {CITY_NAME} data: {date} | Min: {min_temp}°C | Max: {max_temp}°C | Precipitation: {precipitation}mm")

        connection.commit()
    except Exception as e:
        logging.error(f"🚨 Error during weather data fetch: {e}")
    finally:
        fetching_data = False
        cursor.close()
        connection.close()
        logging.info("🔌 Connection closed. Data fetch completed!")

if __name__ == "__main__":
    logging.info("🚀 Weather Service Started! Running Flask server...")
    app.run(host="0.0.0.0", port=5000)
