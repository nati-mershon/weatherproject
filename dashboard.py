import streamlit as st
import requests
import pandas as pd
import time


API_BASE_URL = "http://85.210.59.117:5000"


st.title("🌤 Weather Service Dashboard")

# ✅ **Health Check**
st.header("🔍 Service Health Check")
if st.button("Check Service Availability"):
    health_response = requests.get(f"{API_BASE_URL}/healthz")
    if health_response.status_code == 200:
        st.success(f"✅ Service is running!")
    else:
        st.error(f"❌ Service unavailable!")

# 📊 **Weather Data Display**
st.header("🌡️ Latest Weather Data")
auto_refresh = st.checkbox("🔄 Auto-refresh every 5 seconds", value=True)

def load_weather_data():
    weather_response = requests.get(f"{API_BASE_URL}/weather")
    if weather_response.status_code == 200:
        data = weather_response.json()
        if data:
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])  # Convert to datetime format
            return df
        else:
            st.warning("⚠️ No data available!")
    else:
        st.error(f"❌ Error fetching data! Status code: {weather_response.status_code}")
    return None

weather_data = load_weather_data()
if weather_data is not None:
    st.dataframe(weather_data)

# 🌍 **Fetch Weather Data**
st.header("📥 Fetch Weather Data")

if st.button("📡 Fetch Weather"):
    fetch_response = requests.post(f"{API_BASE_URL}/fetch")
    if fetch_response.status_code == 200:
        st.success("✅ Data is being fetched! Check back in a few seconds.")
    elif fetch_response.status_code == 202:
        st.warning("⏳ Fetch already in progress, please wait...")
    elif fetch_response.status_code == 409:
        st.error("❌ Fetch is already running in the background!")
    else:
        st.error(f"❌ Fetch error! Status code: {fetch_response.status_code}")

# 🗑️ **Delete All Data**
st.header("🗑️ Delete All Data")

if st.button("❌ Delete All Data"):
    delete_response = requests.delete(f"{API_BASE_URL}/clear_data")
    if delete_response.status_code == 200:
        st.success("✅ All data successfully deleted!")
        st.rerun()  # Refresh the app
    else:
        st.error(f"❌ Error deleting data! Status code: {delete_response.status_code}")
