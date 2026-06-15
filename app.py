from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import mysql.connector

app = Flask(__name__)
CORS(app)  


# Load trained ML model
model = joblib.load("crop_health_model.pkl")

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",         # Change if using remote DB
        user="root",              # Your MySQL username
        password="Burlington_101",# Your MySQL password
        database="smart_farming"
    )

# Home route
@app.route("/")
def home():
    return "Smart Farming Backend is Running!"

# Prediction endpoint
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
        farm_id = int(data.get("farm_id", 1))  # default farm_id = 1 if not provided

        # Make prediction
        features = np.array([[temperature, humidity, soil_moisture]])
        prediction = model.predict(features)[0]

        # Recommendation logic
        if prediction < 40:
            recommendation = "Irrigation needed immediately."
        elif 40 <= prediction < 70:
            recommendation = "Monitor soil and weather, apply fertilizer if needed."
        else:
            recommendation = "Crop health is good. Maintain current practices."

        # Save prediction in MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO predictions (farm_id, crop_health_index, recommendation)
            VALUES (%s, %s, %s)
            """,
            (farm_id, float(prediction), recommendation)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Return response
        return jsonify({
            "crop_health_index": float(prediction),
            "recommendation": recommendation
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# History endpoint
@app.route("/history/<int:farm_id>", methods=["GET"])
def history(farm_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT crop_health_index, recommendation, created_at FROM predictions WHERE farm_id = %s ORDER BY created_at ASC",
            (farm_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app (must be last!)
if __name__ == "__main__":
    app.run(debug=True)
