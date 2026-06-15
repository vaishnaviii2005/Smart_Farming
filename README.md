# 🌱 Smart Farming System

An AI-powered Smart Farming System that helps farmers monitor crop conditions, predict crop health, and make data-driven agricultural decisions using Machine Learning, IoT simulation, and Database Management Systems.

## 🚀 Project Overview

The Smart Farming System is an intelligent web-based application designed to assist farmers in improving crop productivity through real-time environmental monitoring and predictive analytics.

The system collects environmental parameters such as:

* Temperature
* Humidity
* Soil Moisture

These inputs are analyzed using a Machine Learning model to generate a **Crop Health Index** and provide actionable recommendations such as:

* Irrigation required
* Monitor crop conditions
* Maintain current farming practices

All predictions and recommendations are stored in a MySQL database, allowing farmers to analyze historical trends and make informed decisions.

---

## 🎯 Why This Project Matters

Traditional farming often relies on manual observation and experience. This project introduces:

* AI-driven crop health monitoring
* Data-driven decision making
* Resource optimization
* Sustainable agriculture practices
* Automated farm monitoring

By leveraging technology, farmers can improve crop yield while reducing water and fertilizer wastage.

---

## ✨ Key Features

### 🤖 Machine Learning-Based Crop Health Prediction

* Predicts Crop Health Index using environmental data.
* Uses regression-based machine learning models.
* Generates intelligent recommendations automatically.

### 🌐 Web-Based Dashboard

* User-friendly interface for entering farm conditions.
* Displays prediction results instantly.
* Responsive and easy-to-use design.

### 📊 Interactive Data Visualization

* Historical crop health trends.
* Interactive charts powered by Chart.js.
* Easy analysis of long-term farm performance.

### 🗄 Database Management System Integration

* Stores predictions and recommendations.
* Maintains historical records.
* Supports future analytics and reporting.

### 📡 IoT Simulation

* Simulates real-world IoT sensors.
* Generates live:

  * Temperature
  * Humidity
  * Soil Moisture data
* Sends automated readings to the backend.

---



## 🏗 System Architecture

```text
IoT Simulator
      │
      ▼
Flask Backend API
      │
      ▼
Machine Learning Model
      │
      ▼
MySQL Database
      │
      ▼
Frontend Dashboard
```

## 🛠 Tech Stack

### Frontend

* HTML
* CSS
* JavaScript
* Chart.js

### Backend

* Flask (Python)

### Database

* MySQL

### Machine Learning

* Scikit-learn
* Linear Regression

### IoT Simulation

* Python
* HTTP Requests

---

## 📂 Project Modules

### 1. Frontend Dashboard

Provides a user-friendly interface for:

* Viewing sensor data
* Predicting crop health
* Visualizing trends

### 2. Flask Backend

Handles:

* API requests
* ML model inference
* Recommendation generation
* Database integration

### 3. Machine Learning Engine

Processes:

* Temperature
* Humidity
* Soil Moisture

Outputs:

* Crop Health Index
* Farming Recommendations

### 4. MySQL Database

Stores:

* Farm Records
* Predictions
* Recommendations
* Historical Data

### 5. IoT Simulator

Generates realistic sensor readings and automates data flow into the system.

---

## 📈 Sample Recommendations

| Crop Health Index | Recommendation             |
| ----------------- | -------------------------- |
| Below 40          | Irrigation Required        |
| 40 – 70           | Monitor Conditions         |
| Above 70          | Maintain Current Practices |

---

## 🔄 Workflow

1. IoT Simulator generates sensor values.
2. Data is sent to Flask API.
3. ML model predicts Crop Health Index.
4. Recommendation is generated.
5. Results are stored in MySQL.
6. Dashboard displays predictions and trends.

---

## 🌍 Real-World Impact

This project contributes to:

* Precision Agriculture
* Sustainable Farming
* Water Conservation
* Smart Resource Utilization
* Data-Driven Agriculture

---

## 🚀 Future Enhancements

* Real IoT sensor integration
* Weather API integration
* Crop disease detection using Computer Vision
* AI-powered yield prediction
* Mobile application for farmers
* Multi-language support
* Automated irrigation control system
 
