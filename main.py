from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import pickle

app = FastAPI()

# ==============================
# LOAD MODELS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

models = {}

for v in ['bike', 'auto', 'car']:
    models[f'clf_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'clf_{v}.pkl'), 'rb'))
    models[f'reg_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'reg_{v}.pkl'), 'rb'))
    models[f'wait_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'wait_{v}.pkl'), 'rb'))

# Load mappings
with open(os.path.join(BASE_DIR, 'traffic_map.json')) as f:
    traffic_map = json.load(f)

with open(os.path.join(BASE_DIR, 'zone_map.json')) as f:
    zone_map = json.load(f)

# 🔥 NEW
with open(os.path.join(BASE_DIR, 'platform_map.json')) as f:
    platform_map = json.load(f)

# ==============================
# FEATURE ORDER (UPDATED)
# ==============================
FEATURES = [
    'DecimalHour', 'Day', 'Weekend', 'Rushhour',
    'DistanceKm', 'Duration',
    'Traffic_Enc', 'SurgeValue',

    'PickupTemperature', 'PickupHumidity',
    'PickupWindSpeed', 'PickupWeatherCode',

    'DropTemperature', 'DropHumidity',
    'DropWindSpeed', 'DropWeatherCode',

    'Pickup_Enc', 'Drop_Enc',

    'Platform_Enc'  # 🔥 NEW
]

# ==============================
# REQUEST MODEL
# ==============================
class RideRequest(BaseModel):
    distance_km: float
    traffic: str
    pickup_zone: str
    drop_zone: str
    temperature: float
    humidity: float

# ==============================
# HELPERS
# ==============================
def encode_safe(mapping, value):
    return mapping.get(value.upper(), 0)

def is_rush(hour):
    return 1 if (7.5 <= hour <= 9.5 or 17 <= hour <= 20) else 0

def build_features(req, decimal_hour):
    return {
        'DecimalHour': decimal_hour,
        'Day': datetime.now().weekday(),
        'Weekend': 1 if datetime.now().weekday() >= 5 else 0,
        'Rushhour': is_rush(decimal_hour),
        'DistanceKm': req.distance_km,
        'Duration': req.distance_km * 3,  # simple proxy
        'Traffic_Enc': encode_safe(traffic_map, req.traffic),
        'SurgeValue': 1,

        'PickupTemperature': req.temperature,
        'PickupHumidity': req.humidity,
        'PickupWindSpeed': 2,
        'PickupWeatherCode': 0,

        'DropTemperature': req.temperature,
        'DropHumidity': req.humidity,
        'DropWindSpeed': 2,
        'DropWeatherCode': 0,

        'Pickup_Enc': encode_safe(zone_map, req.pickup_zone),
        'Drop_Enc': encode_safe(zone_map, req.drop_zone),

        'Platform_Enc': 0  # placeholder (will override)
    }

# ==============================
# CORE PREDICTION (UPDATED)
# ==============================
def predict_all(features, distance):
    result = {}

    for v in ['bike', 'auto', 'car']:

        vehicle_result = {}

        for platform in ["UBER", "OLA", "RAPIDO"]:

            # Inject platform
            features['Platform_Enc'] = platform_map.get(platform, 0)

            df = pd.DataFrame([features])[FEATURES]

            # Availability
            is_available = models[f'clf_{v}'].predict(df)[0]

            if is_available == 0:
                vehicle_result[platform.capitalize()] = None
                continue

            # Predictions
            rate = models[f'reg_{v}'].predict(df)[0]
            wait = models[f'wait_{v}'].predict(df)[0]

            base_price = max(rate, 0) * distance
            wait = max(1, wait)

            vehicle_result[platform.capitalize()] = {
                "price": int(base_price),
                "wait": int(wait)
            }

        result[v] = vehicle_result

    return result

# ==============================
# API ENDPOINT
# ==============================
@app.post("/farecast")
def farecast(req: RideRequest):

    now = datetime.now()
    decimal_hour = now.hour + now.minute / 60

    # CURRENT
    current_features = build_features(req, decimal_hour)
    current_data = predict_all(current_features.copy(), req.distance_km)

    # FORECAST
    forecast = []
    min_price = float('inf')
    best_time = ""

    for i in range(9):
        future_time = (decimal_hour + i * 0.25) % 24
        f_features = build_features(req, future_time)

        # dynamic adjustments
        f_features['SurgeValue'] = 1 + (i * 0.03)
        if i > 4:
            f_features['Traffic_Enc'] = min(f_features['Traffic_Enc'] + 1, 3)

        future_data = predict_all(f_features.copy(), req.distance_km)

        entry = {
            "time": (now + timedelta(minutes=i*15)).strftime("%H:%M"),
            "bike": future_data['bike'],
            "auto": future_data['auto'],
            "car": future_data['car']
        }

        # min price
        valid_prices = []
        for v in ['bike', 'auto', 'car']:
            if entry[v]:
                for p in entry[v].values():
                    if p:
                        valid_prices.append(p['price'])

        if valid_prices:
            min_val = min(valid_prices)
            if min_val < min_price:
                min_price = min_val
                best_time = entry["time"]

        forecast.append(entry)

    # INSIGHT
    valid_current = []
    for v in ['bike', 'auto', 'car']:
        if current_data[v]:
            for p in current_data[v].values():
                if p:
                    valid_current.append(p['price'])

    current_min = min(valid_current) if valid_current else 0
    savings = max(0, current_min - min_price)

    if savings <= 5:
        message = "Prices are stable right now"
    elif savings <= 20:
        message = f"You could save ₹{int(savings)} by waiting a bit"
    else:
        message = f"You could save ₹{int(savings)} by waiting"

    return {
        "current": current_data,
        "forecast": forecast,
        "insight": {
            "best_time": best_time,
            "savings": int(savings),
            "message": message
        }
    }