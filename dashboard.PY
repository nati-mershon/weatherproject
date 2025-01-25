import streamlit as st
import requests
import pandas as pd
import time

# 📌 כתובת השרת – עדכן לפי הכתובת החיצונית של השירות!
API_BASE_URL = "http://4.234.52.245:5000"

# 🎯 כותרת
st.title("🌤 Weather Service Dashboard")

# ✅ **בדיקת Health**
st.header("🔍 Service Health Check")
if st.button("בדוק את זמינות השירות"):
    health_response = requests.get(f"{API_BASE_URL}/healthz")
    if health_response.status_code == 200:
        st.success(f"✅ השירות פעיל! {health_response.json()}")
    else:
        st.error(f"❌ שירות לא זמין! קוד: {health_response.status_code}")

# 📊 **תצוגת נתוני מזג אוויר (רענון אוטומטי)**
st.header("🌡️ נתוני מזג אוויר אחרונים")

# הוספת אפשרות לשליטה ברענון אוטומטי
auto_refresh = st.checkbox("🔄 רענון אוטומטי כל 5 שניות", value=True)

def load_weather_data():
    weather_response = requests.get(f"{API_BASE_URL}/weather")
    if weather_response.status_code == 200:
        data = weather_response.json()
        if data:
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])  # המרת תאריך לפורמט נוח
            return df
        else:
            st.warning("⚠️ אין כרגע נתונים זמינים!")
    else:
        st.error(f"❌ שגיאה בשליפת הנתונים! קוד: {weather_response.status_code}")
    return None

weather_data = load_weather_data()
if weather_data is not None:
    st.dataframe(weather_data)

# 🌍 **הפעלת Fetch ומעקב אחרי מצב התהליך**
st.header("📥 הוסף עיר ושלוף נתונים")

if st.button("📡 Fetch מזג אוויר"):
    fetch_response = requests.post(f"{API_BASE_URL}/fetch")
    if fetch_response.status_code == 200:
        st.success("✅ הנתונים נאספים כעת! בדוק בעוד כמה שניות.")
    elif fetch_response.status_code == 202:
        st.warning("⏳ Fetch כבר מתבצע, אנא המתן...")
    elif fetch_response.status_code == 409:
        st.error("❌ Fetch כבר רץ ברקע! אנא המתן...")
    else:
        st.error(f"❌ שגיאה בעת Fetch! קוד: {fetch_response.status_code}")

# 🗑️ **כפתור מחיקת כל הנתונים**
st.header("🗑️ מחיקת כל הנתונים")

if st.button("❌ מחק את כל הנתונים"):
    delete_response = requests.delete(f"{API_BASE_URL}/clear_data")
    if delete_response.status_code == 200:
        st.success("✅ כל הנתונים נמחקו בהצלחה!")
        st.rerun()  # ✅ שימוש בפונקציה העדכנית
    else:
        st.error(f"❌ שגיאה במחיקת הנתונים! קוד: {delete_response.status_code}")
