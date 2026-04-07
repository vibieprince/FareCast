import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==============================
# CONFIG
# ==============================
API_URL = "https://farecast-ml-api.onrender.com/farecast"

st.set_page_config(page_title="FareCast | Smart Ride Prediction", layout="wide")

st.title("🚀 FareCast - AI-Powered Fare Prediction")
st.markdown("Predict current fares and visualize price trends over the next 2 hours.")

# Initialize session state for data storage
if "api_data" not in st.session_state:
    st.session_state.api_data = None

# ==============================
# INPUT SECTION
# ==============================
with st.sidebar:
    st.header("📍 Trip Parameters")
    distance = st.number_input("Distance (km)", min_value=0.5, value=8.5, step=0.5)
    
    traffic = st.selectbox("Current Traffic", ["NORMAL", "MODERATE", "HEAVY", "LOW"])
    
    pickup_zone = st.selectbox("Pickup Zone Type", 
                              ["RESIDENTIAL", "TRANSIT_HUB", "OFFICE_GOVT", "COMMERCIAL", "HEALTHCARE"])
    
    drop_zone = st.selectbox("Drop Zone Type", 
                            ["RESIDENTIAL", "TRANSIT_HUB", "OFFICE_GOVT", "COMMERCIAL", "HEALTHCARE"])

    st.header("☁️ Environmental Conditions")
    col1, col2 = st.columns(2)
    with col1:
        temp = st.slider("Temp (°C)", 10, 45, 30)
        wind = st.slider("Wind (km/h)", 0, 50, 5)
    with col2:
        hum = st.slider("Humidity (%)", 10, 100, 50)
        weather = st.selectbox("Weather", [0, 1, 2, 3], format_func=lambda x: {0:"Clear", 1:"Mainly Clear", 2:"Partly Cloudy", 3:"Overcast"}[x])

    st.header("🕒 Simulation Settings")
    use_custom_time = st.checkbox("Simulate different time")
    
    if use_custom_time:
        sim_time = st.time_input("Pick Time", datetime.now().time())
        sim_day = st.slider("Day of Week (0=Mon, 6=Sun)", 0, 6, datetime.now().weekday())
        decimal_hour = sim_time.hour + (sim_time.minute / 60)
    else:
        now = datetime.now()
        decimal_hour = now.hour + (now.minute / 60)
        sim_day = now.weekday()

    # The Button triggers the API call and saves it to state
    if st.button("Generate Fare Analysis", use_container_width=True):
        payload = {
            "distance_km": distance, "traffic": traffic, "pickup_zone": pickup_zone,
            "drop_zone": drop_zone, "temperature": temp, "humidity": hum,
            "wind_speed": float(wind), "weather_code": weather,
            "decimal_hour": float(decimal_hour), "day": int(sim_day)
        }

        with st.spinner("Analyzing market patterns..."):
            try:
                res = requests.post(API_URL, json=payload)
                res.raise_for_status()
                st.session_state.api_data = res.json()
            except Exception as e:
                st.error(f"Connection Error: {e}")
                st.session_state.api_data = None

# ==============================
# DISPLAY LOGIC
# ==============================
if st.session_state.api_data:
    data = st.session_state.api_data

    # 1. INSIGHT BANNER
    insight = data.get("insight", {})
    st.info(f"💡 **AI Insight:** {insight.get('message', 'Analyzing data...')}")
    
    col_a, col_b = st.columns(2)
    col_a.metric("Best Time to Book", insight.get("best_time", "Now"))
    col_b.metric("Potential Savings", f"₹{insight.get('savings', 0)}")

    st.divider()

    # 2. CURRENT PRICES
    st.subheader("💰 Live Platform Comparison")
    tabs = st.tabs(["🚲 Bike", "🛺 Auto", "🚗 Car"])

    for i, vehicle in enumerate(["bike", "auto", "car"]):
        with tabs[i]:
            v_data = data.get("current", {}).get(vehicle, {})
            if not v_data:
                st.warning("No data available.")
                continue

            valid_prices = {k: v for k, v in v_data.items() if v and isinstance(v, dict)}
            if not valid_prices:
                st.error("Service unavailable.")
                continue

            cheapest = min(valid_prices, key=lambda x: valid_prices[x].get("price", 9999))
            cols = st.columns(3)
            for j, platform in enumerate(["Uber", "Ola", "Rapido"]):
                p = v_data.get(platform)
                with cols[j]:
                    if p:
                        is_low = " (Cheapest)" if platform == cheapest else ""
                        st.metric(f"{platform}{is_low}", f"₹{p['price']}", f"{p['wait']} min")
                    else:
                        st.write(f"**{platform}**: N/A")

    st.divider()

    # 3. PLATFORM-WISE FORECAST (The Toggle)
    st.subheader("📊 Platform Price Trends")
    
    # Toggle Menu
    view_category = st.radio(
        "Select Vehicle Category to Visualize Trends:", 
        ["Bike", "Auto", "Car"], 
        horizontal=True
    ).lower()

    if "forecast" in data and data["forecast"]:
        forecast_list = []
        for entry in data["forecast"]:
            time_val = entry.get("time")
            v_forecast = entry.get(view_category, {})
            
            row = {"Time": time_val}
            for platform in ["Uber", "Ola", "Rapido"]:
                plat_data = v_forecast.get(platform)
                row[platform] = plat_data["price"] if plat_data else None
            
            forecast_list.append(row)

        df_plot = pd.DataFrame(forecast_list).set_index("Time")
        
        # Display the chart - now it won't disappear on toggle!
        st.line_chart(df_plot)
        st.caption(f"Showing predicted price variations for **{view_category.capitalize()}**.")
    else:
        st.warning("Forecast data not available.")
else:
    st.info("👈 Set your parameters and click 'Generate Fare Analysis' to start.")