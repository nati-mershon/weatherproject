import pyodbc
import requests
import logging
import random
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

# 📌 Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Database connection parameters
DB_SERVER = os.getenv("MSSQL_HOST", "sqlserver.default.svc.cluster.local")
DB_PORT = os.getenv("MSSQL_PORT", "1433")
DB_NAME = os.getenv("MSSQL_DATABASE", "WeatherDB")
DB_USER = os.getenv("MSSQL_USER", "sa")
DB_PASSWORD = os.getenv("SA_PASSWORD", "YourPassword123")

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# 🔹 משתנים גלובליים למעקב
fetching_data = False  
fetch_thread = None  

# 🔹 רשימת 20 ערים מפורסמות עם קואורדינטות
CITIES = [
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"name": "Dubai", "lat": 25.276987, "lon": 55.296249},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"name": "Toronto", "lat": 43.651070, "lon": -79.347015},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Barcelona", "lat": 41.3851, "lon": 2.1734},
    {"name": "Amsterdam", "lat": 52.3676, "lon": 4.9041},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780}
]

def get_db_connection():
    """יוצר חיבור ל-SQL Server"""
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
    """מחזיר נתוני מזג אוויר ממסד הנתונים בפורמט JSON"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        query = """
            SELECT 
                w.id,
                c.name AS city,
                w.date,
                w.min_temp AS "Min Temperature (°C)",
                w.max_temp AS "Max Temperature (°C)",
                w.precipitation AS "Precipitation (mm)"
            FROM WeatherData w
            JOIN Cities c ON w.city_id = c.id
            ORDER BY w.date DESC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        results = [dict(zip(column_names, row)) for row in data]

        cursor.close()
        conn.close()
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"🚨 Error fetching weather data: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route("/clear_data", methods=["DELETE"])
def clear_weather_data():
    """ מוחק את כל הנתונים מה-DB """
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = connection.cursor()

        cursor.execute("DELETE FROM WeatherData;")
        cursor.execute("DELETE FROM Cities;")
        connection.commit()

        cursor.close()
        connection.close()
        logging.info("🗑️ All weather data has been cleared from the database!")
        return jsonify({"message": "✅ כל הנתונים נמחקו בהצלחה!"}), 200
    except Exception as e:
        logging.error(f"🚨 Error clearing data: {e}")
        return jsonify({"error": "❌ כשל במחיקת הנתונים"}), 500



@app.route("/fetch", methods=["POST"])
def fetch_weather():
    """מפעיל תהליך רקע להבאת נתוני מזג אוויר"""
    global fetching_data, fetch_thread
    if fetching_data:
        return jsonify({"message": "Weather data fetch already in progress!"}), 409

    fetching_data = True
    fetch_thread = threading.Thread(target=fetch_and_store_weather_data, daemon=True)
    fetch_thread.start()

    return jsonify({"message": "Weather data fetch started!", "status": "ok"}), 200

def fetch_and_store_weather_data():
    """מביא ושומר נתוני מזג אוויר מ-API חיצוני"""
    global fetching_data
    fetching_data = True
    try:
        connection = get_db_connection()
        if not connection:
            logging.error("🚨 Failed to connect to database, aborting fetch process.")
            fetching_data = False
            return
        cursor = connection.cursor()

        # 🔹 בחירת עיר רנדומלית
        selected_city = random.choice(CITIES)
        CITY_NAME, LAT, LON = selected_city["name"], selected_city["lat"], selected_city["lon"]
        logging.info(f"🌍 Fetching weather data for {CITY_NAME} ({LAT}, {LON})")

        today = datetime.today()
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        URL = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_min,temperature_2m_max,precipitation_sum&timezone=auto"
        
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        data = response.json()

        cursor.execute("SELECT id FROM Cities WHERE name = ?", CITY_NAME)
        city_row = cursor.fetchone()
        if not city_row:
            cursor.execute("INSERT INTO Cities (name, latitude, longitude) VALUES (?, ?, ?)", CITY_NAME, LAT, LON)
            connection.commit()
            cursor.execute("SELECT id FROM Cities WHERE name = ?", CITY_NAME)
            city_row = cursor.fetchone()

        city_id = city_row[0]

        for i, date in enumerate(data['daily']['time']):
            cursor.execute("SELECT COUNT(*) FROM WeatherData WHERE city_id = ? AND date = ?", city_id, date)
            if cursor.fetchone()[0] == 0:  # הוספת הנתון רק אם לא קיים
                cursor.execute("INSERT INTO WeatherData (city_id, date, min_temp, max_temp, precipitation) VALUES (?, ?, ?, ?, ?)",
                               city_id, date, data['daily']['temperature_2m_min'][i], data['daily']['temperature_2m_max'][i], data['daily']['precipitation_sum'][i])


        connection.commit()
    finally:
        fetching_data = False
        cursor.close()
        connection.close()

if __name__ == "__main__":
    logging.info("🚀 Weather Service Started! Running Flask server...")
    app.run(host="0.0.0.0", port=5000)
