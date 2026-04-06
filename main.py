from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import pickle
import numpy as np

app = FastAPI()

# ==============================
# LOAD MODELS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

models = {}

for v in ['bike', 'auto', 'car']:
    models[f'clf_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'clf_{v}.pkl'), 'rb'))
    models[f'reg_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'reg_{v}.pkl'), 'rb'))
    models[f'wait_{v}'] = pickle.load(open(os.path.join(BASE_DIR, f'wait_{v}.pkl'), 'rb'))  # ✅ NEW

# Load mappings
with open(os.path.join(BASE_DIR, 'traffic_map.json')) as f:
    traffic_map = json.load(f)

with open(os.path.join(BASE_DIR, 'zone_map.json')) as f:
    zone_map = json.load(f)

# ==============================
# FEATURE ORDER
# ==============================
FEATURES = [
    'DecimalHour', 'Day', 'Weekend', 'Rushhour',
    'DistanceKm', 'Traffic_Enc', 'SurgeValue',
    'PickupTemperature', 'PickupHumidity',
    'Pickup_Enc', 'Drop_Enc'
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
        'Traffic_Enc': encode_safe(traffic_map, req.traffic),
        'SurgeValue': 1,
        'PickupTemperature': req.temperature,
        'PickupHumidity': req.humidity,
        'Pickup_Enc': encode_safe(zone_map, req.pickup_zone),
        'Drop_Enc': encode_safe(zone_map, req.drop_zone)
    }

# ==============================
# PLATFORM MODIFIERS
# ==============================
PLATFORM_MULTIPLIERS = {
    "Uber": 1.05,
    "Ola": 1.00,
    "Rapido": 0.95
}

WAIT_ADJUSTMENT = {
    "Uber": +1,
    "Ola": +2,
    "Rapido": -1
}

# ==============================
# CORE PREDICTION
# ==============================
def predict_all(features, distance, noise_factor=0.02):
    df = pd.DataFrame([features])[FEATURES]
    result = {}

    for v in ['bike', 'auto', 'car']:

        is_available = models[f'clf_{v}'].predict(df)[0]

        if is_available == 0:
            result[v] = None
            continue

        # Base predictions
        rate = models[f'reg_{v}'].predict(df)[0]
        wait = models[f'wait_{v}'].predict(df)[0]

        # Add slight noise
        rate = rate * (1 + np.random.uniform(-noise_factor, noise_factor))
        wait = max(1, wait * (1 + np.random.uniform(-0.1, 0.1)))

        base_price = max(rate, 0) * distance

        result[v] = {}

        for platform in ["Uber", "Ola", "Rapido"]:
            result[v][platform] = {
                "price": int(base_price * PLATFORM_MULTIPLIERS[platform]),
                "wait": int(max(1, wait + WAIT_ADJUSTMENT[platform]))
            }

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
    current_data = predict_all(current_features, req.distance_km, noise_factor=0.01)

    # FORECAST
    forecast = []
    min_price = float('inf')
    best_time = ""

    for i in range(9):
        future_time = (decimal_hour + i * 0.25) % 24
        f_features = build_features(req, future_time)

        # Dynamic changes
        f_features['SurgeValue'] = 1 + (i * 0.03)
        if i > 4:
            f_features['Traffic_Enc'] = min(f_features['Traffic_Enc'] + 1, 3)

        future_data = predict_all(f_features, req.distance_km, noise_factor=0.03)

        entry = {
            "time": (now + timedelta(minutes=i*15)).strftime("%H:%M"),
            "bike": future_data['bike'],
            "auto": future_data['auto'],
            "car": future_data['car']
        }

        # Find min price
        valid_prices = []
        for v in ['bike', 'auto', 'car']:
            if entry[v]:
                for p in entry[v].values():
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