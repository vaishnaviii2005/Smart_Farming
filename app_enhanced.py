from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the actual trained ML model
try:
    model = joblib.load("crop_health_model.pkl")
    print("✅ ML Model loaded successfully!")
    model_available = True
except Exception as e:
    print(f"⚠️ Could not load ML model: {e}")
    model_available = False

# In-memory stores for live IoT mode
# latest_sensor_by_farm: { farm_id: { temperature, humidity, soil_moisture, timestamp } }
# latest_prediction_by_farm: { farm_id: { crop_health_index, recommendation, health_status, prediction_method, timestamp, input_data } }
latest_sensor_by_farm = {}
latest_prediction_by_farm = {}

# Simple prediction function as fallback
def simple_crop_health_prediction(temperature, humidity, soil_moisture):
    """Fallback prediction when ML model is not available"""
    temp_score = max(0, 100 - abs(temperature - 25) * 4)
    humidity_score = max(0, 100 - abs(humidity - 60) * 2)
    soil_score = max(0, 100 - abs(soil_moisture - 50) * 2)
    health_index = (temp_score * 0.4 + humidity_score * 0.3 + soil_score * 0.3)
    return min(100, max(0, health_index))

def get_recommendation(health_index):
    """Get recommendation based on health index"""
    if health_index < 30:
        return "🚨 Critical: Immediate irrigation and environmental adjustment required!"
    elif health_index < 50:
        return "⚠️ Poor: Increase irrigation frequency and check soil nutrients."
    elif health_index < 70:
        return "🟡 Fair: Monitor conditions closely, consider fertilizer application."
    elif health_index < 85:
        return "✅ Good: Crop health is satisfactory, maintain current practices."
    else:
        return "🌟 Excellent: Optimal conditions, continue current management."

def get_health_status(health_index):
    """Get health status with color coding"""
    if health_index < 30:
        return {"status": "Critical", "color": "red"}
    elif health_index < 50:
        return {"status": "Poor", "color": "orange"}
    elif health_index < 70:
        return {"status": "Fair", "color": "yellow"}
    elif health_index < 85:
        return {"status": "Good", "color": "green"}
    else:
        return {"status": "Excellent", "color": "emerald"}

# Home route
@app.route("/")
def home():
    return jsonify({
        "message": "Smart Farming Backend is Running!",
        "model_status": "Available" if model_available else "Using fallback algorithm",
        "version": "2.0"
    })

# Prediction endpoint
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
        farm_id = int(data.get("farm_id", 1))

        # Make prediction using ML model if available, otherwise use simple algorithm
        if model_available:
            features = np.array([[temperature, humidity, soil_moisture]])
            prediction = model.predict(features)[0]
            # Ensure prediction is within reasonable bounds
            prediction = max(0, min(100, prediction))
            prediction_method = "ML Model"
        else:
            prediction = simple_crop_health_prediction(temperature, humidity, soil_moisture)
            prediction_method = "Fallback Algorithm"

        recommendation = get_recommendation(prediction)
        health_status = get_health_status(prediction)

        # Return enhanced response
        return jsonify({
            "crop_health_index": round(float(prediction), 2),
            "recommendation": recommendation,
            "health_status": health_status,
            "prediction_method": prediction_method,
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_moisture,
                "farm_id": farm_id
            },
            "insights": {
                "temperature_optimal": 20 <= temperature <= 30,
                "humidity_optimal": 40 <= humidity <= 80,
                "soil_moisture_optimal": 30 <= soil_moisture <= 70
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# IoT sensor ingest endpoint for live mode
@app.route("/ingest-sensor", methods=["POST"])
def ingest_sensor():
    try:
        data = request.get_json()
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
        farm_id = int(data.get("farm_id", 1))

        # Save latest sensor reading
        sensor_payload = {
            "temperature": temperature,
            "humidity": humidity,
            "soil_moisture": soil_moisture,
            "timestamp": datetime.now().isoformat(),
            "farm_id": farm_id,
        }
        latest_sensor_by_farm[farm_id] = sensor_payload

        # Compute prediction (mirror logic from /predict)
        if model_available:
            features = np.array([[temperature, humidity, soil_moisture]])
            prediction = model.predict(features)[0]
            prediction = max(0, min(100, prediction))
            prediction_method = "ML Model"
        else:
            prediction = simple_crop_health_prediction(temperature, humidity, soil_moisture)
            prediction_method = "Fallback Algorithm"

        recommendation = get_recommendation(prediction)
        health_status = get_health_status(prediction)

        prediction_payload = {
            "crop_health_index": round(float(prediction), 2),
            "recommendation": recommendation,
            "health_status": health_status,
            "prediction_method": prediction_method,
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_moisture,
                "farm_id": farm_id,
            },
        }
        latest_prediction_by_farm[farm_id] = prediction_payload

        return jsonify({
            "sensor": sensor_payload,
            "prediction": prediction_payload,
            "message": "Sensor ingested and prediction computed",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Latest sensor endpoint
@app.route("/latest-sensor/<int:farm_id>", methods=["GET"])
def latest_sensor(farm_id):
    try:
        data = latest_sensor_by_farm.get(farm_id)
        if not data:
            return jsonify({"error": "No sensor data available"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Latest prediction endpoint
@app.route("/latest-prediction/<int:farm_id>", methods=["GET"])
def latest_prediction(farm_id):
    try:
        data = latest_prediction_by_farm.get(farm_id)
        if not data:
            return jsonify({"error": "No prediction available"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# History endpoint with enhanced mock data
@app.route("/history/<int:farm_id>", methods=["GET"])
def history(farm_id):
    try:
        # Generate realistic mock history data
        history_data = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(20):
            date = base_date + timedelta(days=i*1.5)
            # Generate realistic health index with some variation
            base_health = 70 + random.uniform(-20, 20)
            health_index = max(0, min(100, base_health))
            
            history_data.append({
                "crop_health_index": round(health_index, 2),
                "recommendation": get_recommendation(health_index),
                "created_at": date.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": round(random.uniform(15, 35), 1),
                "humidity": round(random.uniform(30, 90), 1),
                "soil_moisture": round(random.uniform(20, 80), 1)
            })
        
        return jsonify(history_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Analytics endpoint
@app.route("/analytics/<int:farm_id>", methods=["GET"])
def analytics(farm_id):
    try:
        # Mock analytics data
        analytics_data = {
            "average_health": round(random.uniform(65, 85), 2),
            "trend": "improving" if random.random() > 0.5 else "stable",
            "peak_health": round(random.uniform(80, 95), 2),
            "lowest_health": round(random.uniform(30, 60), 2),
            "total_predictions": random.randint(50, 200),
            "recommendation_frequency": {
                "irrigation": random.randint(5, 15),
                "fertilizer": random.randint(3, 10),
                "monitoring": random.randint(8, 20)
            }
        }
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
