from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json
import os
import pickle
from datetime import datetime, timedelta

app = FastAPI()

ALLOWED_ORIGINS = [
    # Local development — all common Vite ports
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    # Production — Vercel deployments
    "https://farecast.vercel.app",
    "https://farecast-web-app.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# 1. LOAD MODELS & MAPPINGS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load 9 models: (Classification, Fare Regressor, Wait Regressor) x 3 Vehicles
models = {}
for v in ['bike', 'auto', 'car']:
    try:
        models[f'clf_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'clf_{v}.pkl'), 'rb'))
        models[f'reg_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'reg_{v}.pkl'), 'rb'))
        models[f'wait_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'wait_reg_{v}.pkl'), 'rb'))
    except FileNotFoundError as e:
        print(f"Warning: Model file not found - {e}")

# Load all categorical mappings
def load_json(filename):
    with open(os.path.join(BASE_DIR, filename)) as f:
        return json.load(f)

traffic_map = load_json('traffic_map.json')
zone_map = load_json('zone_map.json')
platform_map = load_json('platform_map.json')

# EXACT order used during training (CRITICAL for model.predict)
FEATURES = [
    'Platform_Enc', 'Hour', 'Minute', 'DecimalHour', 'Day', 'Weekend', 'Rushhour', 
    'DistanceKm', 'Duration', 'TrafficLevel_Enc', 'SurgeValue', 
    'PickupTemperature', 'PickupWindSpeed', 'PickupWeatherCode', 'PickupHumidity',
    'DropTemperature', 'DropWindSpeed', 'DropWeatherCode', 'DropHumidity',
    'PickupZone_Enc', 'DropZone_Enc'
]

# ==============================
# 2. DATA MODELS
# ==============================
class RideRequest(BaseModel):
    distance_km: float
    traffic: str
    pickup_zone: str
    drop_zone: str
    temperature: float
    humidity: float
    wind_speed: float = 2.0  # Default if not provided
    weather_code: int = 0    # Default if not provided
    # Optional overrides for simulation
    decimal_hour: float = None 
    day: int = None

# ==============================
# 3. LOGIC HELPERS
# ==============================
def get_rush_status(decimal_hour):
    # Standard Indian Metro Rush Hours
    return 1 if (8.0 <= decimal_hour <= 10.5 or 17.5 <= decimal_hour <= 20.5) else 0

def build_feature_vector(req, platform_code, current_hour):
    """Creates an ordered feature vector matching the model's training data."""
    h = int(current_hour)
    m = int((current_hour % 1) * 60)
    d = req.day if req.day is not None else datetime.now().weekday()
    
    data = {
        'Platform_Enc': platform_code,
        'Hour': h,
        'Minute': m,
        'DecimalHour': current_hour,
        'Day': d,
        'Weekend': 1 if d >= 5 else 0,
        'Rushhour': get_rush_status(current_hour),
        'DistanceKm': req.distance_km,
        'Duration': req.distance_km * 2.5, # Base heuristic for duration
        'TrafficLevel_Enc': traffic_map.get(req.traffic.upper(), 3),
        'SurgeValue': 0,
        'PickupTemperature': req.temperature,
        'PickupWindSpeed': req.wind_speed,
        'PickupWeatherCode': req.weather_code,
        'PickupHumidity': req.humidity,
        'DropTemperature': req.temperature,
        'DropWindSpeed': req.wind_speed,
        'DropWeatherCode': req.weather_code,
        'DropHumidity': req.humidity,
        'PickupZone_Enc': zone_map.get(req.pickup_zone.upper(), 8),
        'DropZone_Enc': zone_map.get(req.drop_zone.upper(), 8)
    }
    # Return as DataFrame to keep feature names and order intact
    return pd.DataFrame([data])[FEATURES]

def predict_platforms(req, hour_val):
    """Predicts prices and waits for all platforms for a given time."""
    results = {"bike": {}, "auto": {}, "car": {}}
    
    for v in ['bike', 'auto', 'car']:
        for platform_name, p_code in platform_map.items():
            features_df = build_feature_vector(req, p_code, hour_val)
            
            # 1. Check Availability
            if models[f'clf_{v}'].predict(features_df)[0] == 0:
                results[v][platform_name.capitalize()] = None
                continue
            
            # 2. Predict Fare & Wait
            rate_km = models[f'reg_{v}'].predict(features_df)[0]
            wait_time = models[f'wait_{v}'].predict(features_df)[0]
            
            results[v][platform_name.capitalize()] = {
                "price": int(max(rate_km, 0) * req.distance_km),
                "wait": int(max(wait_time, 1))
            }
    return results

# ==============================
# 4. API ENDPOINTS
# ==============================
@app.post("/farecast")
async def farecast_endpoint(req: RideRequest):
    # Use provided time or current server time
    if req.decimal_hour is not None:
        start_hour = req.decimal_hour
    else:
        now = datetime.now()
        start_hour = now.hour + (now.minute / 60)

    # A. CURRENT ESTIMATES
    current_data = predict_platforms(req, start_hour)

    # B. 2-HOUR FORECAST (9 steps of 15 mins)
    forecast_list = []
    all_prices = []

    for i in range(9):
        f_hour = (start_hour + (i * 0.25)) % 24
        f_data = predict_platforms(req, f_hour)
        
        # Formatting timestamp for UI
        display_time = (datetime.combine(datetime.today(), datetime.min.time()) + 
                        timedelta(hours=f_hour)).strftime("%H:%M")
        
        forecast_list.append({
            "time": display_time,
            "bike": f_data['bike'],
            "auto": f_data['auto'],
            "car": f_data['car']
        })

        # Track valid prices for "Best Time" logic
        for v in f_data.values():
            for p in v.values():
                if p: all_prices.append(p['price'])

    # C. INSIGHTS GENERATION
    # Compare current cheapest vs global forecast cheapest
    current_cheapest = 0
    valid_current = [p['price'] for v in current_data.values() for p in v.values() if p]
    if valid_current:
        current_cheapest = min(valid_current)
    
    global_cheapest = min(all_prices) if all_prices else current_cheapest
    savings = max(0, current_cheapest - global_cheapest)
    
    # Logic for best time
    best_time = forecast_list[0]['time']
    for entry in forecast_list:
        step_prices = [p['price'] for v in ['bike', 'auto', 'car'] for p in entry[v].values() if p]
        if step_prices and min(step_prices) == global_cheapest:
            best_time = entry['time']
            break

    message = "Prices are stable right now"
    if savings > 20:
        message = f"Smart Move: Wait for {best_time} to save ₹{savings}"
    elif savings > 5:
        message = "Slight price drop expected soon"

    return {
        "current": current_data,
        "forecast": forecast_list,
        "insight": {
            "best_time": best_time,
            "savings": int(savings),
            "message": message
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
