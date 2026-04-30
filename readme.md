# 🚗 FareCast – Smart Ride Price & Wait Time Prediction Engine

🚀 **FareCast** is an AI-powered system that predicts **ride fares and waiting times** across multiple platforms (Uber, Ola, Rapido) and vehicle types (Bike, Auto, Car), along with a **future price forecast** to help users book at the cheapest time.

---

## 🎯 Problem Solved

Ride prices fluctuate heavily due to:

* Traffic
* Time of day
* Demand (rush hours)
* Weather conditions

❌ Users don’t know *when* to book
❌ No platform shows **future price trends**

👉 **FareCast solves this by predicting both current and future fares + wait times**

---

## 🧠 What I Built

* 🔮 ML models to predict:

  * Ride fare (per platform + vehicle)
  * Waiting time (per platform + vehicle)
* 📈 2-hour **price forecasting engine**
* ⚡ FastAPI backend deployed on cloud
* 🌐 Frontend (Streamlit / Web UI)
* 🔗 Real-world API integration ready (Maps, Weather)

---

## 🧩 Key Features

* ✅ Platform-wise predictions (Uber / Ola / Rapido)
* ✅ Vehicle-wise predictions (Bike / Auto / Car)
* ✅ Wait time estimation
* ✅ Future forecast (every 15 minutes)
* ✅ Best time recommendation
* ✅ Savings calculation

---

## 📊 Sample Output

### Current Predictions

| Vehicle | Platform | Price (₹) | Wait (min) |
| ------- | -------- | --------- | ---------- |
| Bike    | Ola      | 79        | 1          |
| Bike    | Rapido   | 74        | 2          |
| Bike    | Uber     | 74        | 2          |
| Auto    | Ola      | 149       | 2          |
| Car     | Uber     | 190       | 2          |

---

### Forecast Trend (Next 2 Hours)

| Time  | Bike (₹) | Auto (₹) | Car (₹) |
| ----- | -------- | -------- | ------- |
| 18:30 | 74       | 149      | 181     |
| 19:00 | 76       | 144      | 183     |
| 20:00 | 71       | 140      | 197     |

📉 Insight:

> Best time to book: **20:00**
> Potential savings: **₹3**

---

## 📸 Screenshots (Proof of Work)

### 🔹 API Working (Swagger UI)

![API Working](screenshots/Screenshot%20(349).png)

### 🔹 Prediction Output (JSON Response)

![Prediction output](screenshots/Screenshot%20(350).png)
![Prediction output](screenshots/Screenshot%20(351).png)

### 🔹 Forecast Visualization
![Forecast visualization](screenshots/Group%2012.png)

### 🔹 Frontend UI

*Add your FareCast UI screenshot here*
![Frontend UI](screenshots/Group%209.png)
---

## 🧠 ML Approach

* **Random Forest Classifier**

  * Predicts ride availability

* **Random Forest Regressor**

  * Predicts:

    * Price per KM
    * Waiting time

---

## 📊 Features Used

* Time (Decimal Hour)
* Day / Weekend
* Rush Hour flag
* Distance
* Traffic Level
* Surge Value
* Temperature & Humidity
* Pickup / Drop Zones

---

## ⚙️ Tech Stack

* **Backend**: FastAPI
* **ML**: Scikit-learn
* **Data Processing**: Pandas, NumPy
* **Deployment**: Render
* **Frontend**: Streamlit / Web UI
* **APIs Ready**: Google Maps, Weather APIs

---

## 🚀 Live API
[https://farecast-ml-api.onrender.com/farecast]

---

## 📈 Why This Project Stands Out

* Not just prediction → **decision-making system**
* Combines:

  * Time-series thinking
  * ML regression
  * Real-world ride logic
* Production-ready architecture

---

## 🔮 Future Improvements

* Real-time traffic integration
* Weather API integration
* User-specific personalization
* Deep learning models (LSTM for trends)

---

## 👨‍💻 Author

**Prince Singh**
B.Tech CSE (Data Science)
Aspiring Data Scientist 🚀
