
# 🚦 Surge Intelligence & Fare Optimization System
## Phase 1 – Problem Framing & Strategic Decisions

---

## 1️⃣ Core Objective

Build an end-to-end predictive system that:

- Estimates **Base Fare**
- Predicts **Surge Multiplier**
- Computes **Final Fare = Base × Surge**
- Simulates pricing for next **2 hours**
- Recommends optimal booking time
- Logs user-reported actual fare for future model refinement

This is a **decision-support pricing intelligence system**, not a ride-hailing app.

---

## 2️⃣ Problem Framing

Develop a predictive pricing intelligence system that models dynamic surge behavior using temporal, geospatial, weather, and demand-supply engineered features. The system forecasts short-term fare trends and provides optimal booking-time recommendations. It includes deployment and monitoring with feedback logging for future retraining.

---

## 3️⃣ Modeling Strategy

### 🔹 Model 1 – Base Fare Estimator (Regression)

Base Fare = f(distance, trip duration, location, time)

Metrics:
- MAE
- RMSE
- R²

---

### 🔹 Model 2 – Surge Multiplier Predictor (Regression)

Surge = f(demand index, supply index, weather, peak hour, zone factors)

Metrics:
- MAE
- RMSE
- High-surge error %
- Stability during peak periods

---

### 🔹 Final Fare

Final Fare = Predicted Base × Predicted Surge

System-level evaluation:
- Final fare % error
- Stability across forecast window

---

## 4️⃣ Data Strategy

- NYC Taxi dataset:
  - Pickup time
  - Dropoff time
  - Distance
  - Location zones
  - Base fare structure

- Engineered Features:
  - Hourly demand density
  - Zone-based demand clusters
  - Supply proxy index
  - Time cyclic features
  - Peak hour indicators

- Weather API integration during deployment.

---

## 5️⃣ Surge Simulation Philosophy

Surge will simulate real-world pricing behavior using:

- Non-linear demand-supply imbalance
- Peak hour weighting
- Rain amplification factor
- Weekend factor
- Airport/business zone impact
- Controlled noise injection

---

## 6️⃣ Forecasting Approach

For next 2 hours:

- Shift time feature
- Recompute demand index
- Recompute surge predictors
- Re-run regression model
- Compare predicted fare trends

Feature-driven dynamic simulation (not ARIMA-based).

---

## 7️⃣ Multi-Factor Contributors

- Peak hour category
- Late night factor
- Weekend indicator
- Rain intensity
- Heavy rain boost
- Airport zone flag
- High-demand zone indicator
- Event simulation toggle
- Demand-supply imbalance
- Randomized noise

---

## 8️⃣ Feedback Loop

User may input actual fare paid.

System logs:
- Input features
- Predicted fare
- Actual fare
- Error %

Used for:
- Periodic evaluation
- Drift detection
- Offline retraining

---

## 9️⃣ Scope Boundaries

- NYC only
- 2-hour forecast window
- No traffic API (simulated proxy)
- No real platform scraping
- No real-time retraining

---

## 🔟 Technical Stack

Data:
- NYC Taxi dataset
- Weather API

ML:
- Linear Regression
- Random Forest
- XGBoost / LightGBM
- SHAP
- MLflow

Deployment:
- FastAPI
- Streamlit
- Docker
- Render

Monitoring:
- Prediction logging
- Drift analysis
- Periodic retraining plan

---

## 🎯 Project Classification

This is:

- Applied Data Science
- Economic modeling
- Demand-supply simulation
- Regression modeling
- Short-term forecasting
- Decision optimization
- Deployment-aware ML system

---

## ⚠️ Risks

- Poor surge simulation logic
- Weak feature engineering
- Scope explosion
- UI distraction before modeling

Mitigation:
- Strict phase discipline
- ML-first approach
- Controlled scope

---

## 📌 Phase 1 Status

✔ Objective defined  
✔ Modeling structure defined  
✔ Dataset chosen  
✔ Forecast window locked  
✔ Simulation philosophy defined  
✔ Monitoring strategy planned  
✔ Scope boundaries set  

Phase 1 Complete.
