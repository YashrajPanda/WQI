import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import requests

# Backend API URL (update if backend is on a different host/port)
API_URL = "http://localhost:8000/data"

# Create a simple river map centered on India (Ganges River)
def make_river_map(fecal_value):
    # Center map on India, near the Ganges River (Varanasi coordinates: 25.3176, 82.9739)
    m = folium.Map(location=[25.3176, 82.9739], zoom_start=6, tiles='CartoDB positron')
    
    # Simulated Ganges River path (simplified coordinates)
    river_path = [
        [25.3176, 82.9739],  # Varanasi
        [25.4248, 81.8491],  # Allahabad (Prayagraj)
        [25.4582, 80.3319]   # Kanpur
    ]
    color = 'green' if fecal_value < 400 else 'yellow' if fecal_value < 800 else 'red'
    folium.PolyLine(river_path, color=color, weight=8, popup=f'Pollution: {color.capitalize()}').add_to(m)
    folium.Marker(
        location=[25.3176, 82.9739],  # Marker at Varanasi
        popup=f'Fecal Coliform: {fecal_value:.1f} CFU/100mL',
        icon=folium.Icon(color=color)
    ).add_to(m)
    return m

# Check for alerts
def check_alerts(forecast_data, threshold):
    alerts = []
    if any(forecast_data['forecast_fecal'] > threshold):
        alerts.append(f"Warning: Forecasted fecal coliform above {threshold} CFU/100mL.")
    if any(forecast_data['forecast_fecal'] > 800):
        alerts.append("Critical: High pollution risk detected. Take action.")
    return alerts

# Streamlit dashboard configuration
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# Sidebar for threshold input
with st.sidebar:
    st.header("Settings")
    threshold = st.number_input("Set Alert Threshold (CFU/100mL)", min_value=0.0, value=400.0, step=10.0)
    st.header("About")
    st.write("Dashboard for monitoring river water quality in India.")

# Fetch data from backend
try:
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    
    historical_data = pd.DataFrame(data["historical_data"]).set_index('date')
    historical_data.index = pd.to_datetime(historical_data.index)
    
    forecast_data = pd.DataFrame(data["forecast_data"]).set_index('date')
    forecast_data.index = pd.to_datetime(forecast_data.index)
    
    # Decode base64 satellite image
    import base64
    import io
    from matplotlib.image import imread
    satellite_image_base64 = data["satellite_image_base64"]
    satellite_image = imread(io.BytesIO(base64.b64decode(satellite_image_base64)))
    
    latest_fecal = data["latest_fecal"]
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching data from backend: {e}")
    st.stop()

# Main title
st.title("River Water Quality Dashboard - India")

# Tabs for navigation
tab1, tab2 = st.tabs(["Overview", "Details"])

# Tab 1: Overview with map and satellite image
with tab1:
    st.header("Current River Status")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ganges River Map")
        river_map = make_river_map(latest_fecal)
        folium_static(river_map, width=500, height=300)
    with col2:
        st.subheader("Satellite View")
        st.image(satellite_image, caption="Green: Low | Yellow: Medium | Red: High Pollution", width=300)

# Tab 2: Data and Alerts
with tab2:
    st.header("Water Quality Data")
    
    # Show latest measurements
    st.subheader("Current Measurements")
    latest_data = historical_data.iloc[-1]
    latest_date = historical_data.index[-1].date()
    st.write(f"Date: {latest_date}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("pH", f"{latest_data['pH']:.1f}")
    with col2:
        st.metric("Dissolved Oxygen (mg/L)", f"{latest_data['DO']:.1f}")
    with col3:
        st.metric("Fecal Coliform (CFU/100mL)", f"{latest_data['fecal_coliform']:.1f}")

    # Show forecast and trend
    st.subheader("3-Day Forecast")
    st.dataframe(forecast_data.style.format({"forecast_fecal": "{:.1f}"}))

    st.subheader("Trend")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(historical_data.index[-7:], historical_data['fecal_coliform'].iloc[-7:], label="Recent Data", color="blue")
    ax.plot(forecast_data.index, forecast_data['forecast_fecal'], label="Forecast", color="orange", linestyle="--")
    ax.axhline(y=threshold, color="gray", linestyle=":", label=f"Threshold ({threshold})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Fecal Coliform (CFU/100mL)")
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=30)
    plt.tight_layout()
    st.pyplot(fig)

    # Alerts
    st.subheader("Alerts")
    alerts = check_alerts(forecast_data, threshold)
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No alerts. Water quality is within safe limits.")

# Footer
st.markdown("---")
st.caption("Water Quality Dashboard | Simulated Data")