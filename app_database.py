from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import logging
import os
import json
import threading
try:
    import paho.mqtt.client as mqtt  # type: ignore
    MQTT_AVAILABLE = True
except Exception:
    MQTT_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the actual trained ML model
try:
    model = joblib.load("crop_health_model.pkl")
    logger.info("✅ ML Model loaded successfully!")
    model_available = True
except Exception as e:
    logger.warning(f"⚠️ Could not load ML model: {e}")
    model_available = False

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Burlington_101',
    'database': 'smart_farming',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logger.info("✅ Database connection established")
            return connection
    except Error as e:
        logger.error(f"❌ Error connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """Execute a database query safely"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            raise Exception("Could not connect to database")
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.lastrowid if cursor.lastrowid else True
            
        return result
    except Error as e:
        logger.error(f"Database error: {e}")
        if connection:
            connection.rollback()
        raise Exception(f"Database operation failed: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        # Create predictions table if it doesn't exist
        create_predictions_table = """
        CREATE TABLE IF NOT EXISTS predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            farm_id INT NOT NULL,
            temperature FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            soil_moisture FLOAT NOT NULL,
            crop_health_index FLOAT NOT NULL,
            recommendation TEXT NOT NULL,
            prediction_method VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_farm_id (farm_id),
            INDEX idx_created_at (created_at)
        )
        """
        execute_query(create_predictions_table)
        logger.info("✅ Predictions table ready")

        # Create sensor_data table if it doesn't exist (used by live IoT)
        create_sensor_table = """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            farm_id INT NOT NULL,
            temperature FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            soil_moisture FLOAT NOT NULL,
            crop_health_index FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_farm_id (farm_id),
            INDEX idx_created_at (created_at)
        )
        """
        execute_query(create_sensor_table)
        # Backwards-safe ALTERs in case table exists without farm_id
        try:
            execute_query("ALTER TABLE sensor_data ADD COLUMN IF NOT EXISTS farm_id INT NOT NULL DEFAULT 1")
            execute_query("CREATE INDEX IF NOT EXISTS idx_farm_id ON sensor_data (farm_id)")
        except Exception as _:
            pass
        logger.info("✅ Sensor data table ready")
        
        # Insert some sample data if table is empty
        check_count = "SELECT COUNT(*) as count FROM predictions"
        result = execute_query(check_count, fetch=True)
        
        if result[0]['count'] == 0:
            logger.info("📊 Inserting sample data...")
            sample_data = [
                (1, 25.5, 60.0, 45.0, 75.2, "Crop health is good. Maintain current practices.", "ML Model"),
                (1, 28.0, 65.0, 50.0, 78.5, "Crop health is good. Maintain current practices.", "ML Model"),
                (1, 22.0, 55.0, 40.0, 68.3, "Monitor soil and weather, apply fertilizer if needed.", "ML Model"),
                (1, 30.0, 70.0, 55.0, 82.1, "Crop health is excellent.", "ML Model"),
                (1, 26.0, 58.0, 48.0, 76.8, "Crop health is good. Maintain current practices.", "ML Model")
            ]
            
            insert_sample = """
            INSERT INTO predictions (farm_id, temperature, humidity, soil_moisture, 
                                   crop_health_index, recommendation, prediction_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for data in sample_data:
                execute_query(insert_sample, data)
            logger.info("✅ Sample data inserted")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

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

def compute_prediction_values(temperature: float, humidity: float, soil_moisture: float):
    """Compute prediction and related metadata using ML model or fallback."""
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
    return float(prediction), prediction_method, recommendation, health_status

# Initialize database on startup
try:
    init_database()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")

# Home route
@app.route("/")
def home():
    try:
        # Test database connection
        connection = get_db_connection()
        db_status = "Connected" if connection else "Disconnected"
        if connection:
            connection.close()
    except:
        db_status = "Error"
    
    return jsonify({
        "message": "Smart Farming Backend with Database is Running!",
        "model_status": "Available" if model_available else "Using fallback algorithm",
        "database_status": db_status,
        "version": "3.0"
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

        prediction, prediction_method, recommendation, health_status = compute_prediction_values(
            temperature, humidity, soil_moisture
        )

        # Store prediction in database
        try:
            insert_query = """
            INSERT INTO predictions (farm_id, temperature, humidity, soil_moisture, 
                                   crop_health_index, recommendation, prediction_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            prediction_id = execute_query(insert_query, (
                farm_id, temperature, humidity, soil_moisture, 
                prediction, recommendation, prediction_method
            ))
            logger.info(f"✅ Prediction stored in database with ID: {prediction_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store prediction in database: {e}")

        # Return enhanced response
        return jsonify({
            "crop_health_index": round(float(prediction), 2),
            "recommendation": recommendation,
            "health_status": health_status,
            "prediction_method": prediction_method,
            "timestamp": datetime.now().isoformat(),
            "prediction_id": prediction_id if 'prediction_id' in locals() else None,
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
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

# IoT ingestion endpoint: accepts raw sensor readings and stores both sensor and prediction
@app.route("/ingest-sensor", methods=["POST"])
def ingest_sensor():
    try:
        data = request.get_json() or {}
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
        farm_id = int(data.get("farm_id", 1))

        # Compute prediction first
        prediction, prediction_method, recommendation, health_status = compute_prediction_values(
            temperature, humidity, soil_moisture
        )

        # Store raw sensor reading with computed health
        try:
            insert_sensor = (
                "INSERT INTO sensor_data (farm_id, temperature, humidity, soil_moisture, crop_health_index) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            execute_query(insert_sensor, (farm_id, temperature, humidity, soil_moisture, prediction))
        except Exception as e:
            logger.error(f"❌ Failed to store sensor data: {e}")
        prediction_id = None
        try:
            insert_prediction = """
            INSERT INTO predictions (farm_id, temperature, humidity, soil_moisture, 
                                   crop_health_index, recommendation, prediction_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            prediction_id = execute_query(insert_prediction, (
                farm_id, temperature, humidity, soil_moisture,
                prediction, recommendation, prediction_method
            ))
        except Exception as e:
            logger.error(f"❌ Failed to store prediction from sensor ingestion: {e}")

        return jsonify({
            "message": "Sensor data ingested",
            "prediction": {
                "crop_health_index": round(float(prediction), 2),
                "recommendation": recommendation,
                "health_status": health_status,
                "prediction_method": prediction_method,
                "timestamp": datetime.now().isoformat(),
                "prediction_id": prediction_id,
                "input_data": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "soil_moisture": soil_moisture,
                    "farm_id": farm_id
                }
            }
        })
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        return jsonify({"error": str(e)}), 400

# Latest sensor reading
@app.route("/latest-sensor/<int:farm_id>", methods=["GET"])
def latest_sensor(farm_id):
    try:
        query = (
            "SELECT temperature, humidity, soil_moisture, created_at FROM sensor_data "
            "WHERE farm_id = %s ORDER BY id DESC LIMIT 1"
        )
        rows = execute_query(query, (farm_id,), fetch=True)
        if not rows:
            return jsonify({"message": "No sensor data yet"}), 404
        row = rows[0]
        return jsonify({
            "temperature": float(row["temperature"]),
            "humidity": float(row["humidity"]),
            "soil_moisture": float(row["soil_moisture"]),
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
        })
    except Exception as e:
        logger.error(f"Latest sensor error: {e}")
        return jsonify({"error": str(e)}), 500

# Latest prediction for a farm, formatted like /predict response so UI can reuse it
@app.route("/latest-prediction/<int:farm_id>", methods=["GET"])
def latest_prediction(farm_id):
    try:
        query = (
            "SELECT temperature, humidity, soil_moisture, crop_health_index, recommendation, "
            "prediction_method, created_at FROM predictions WHERE farm_id = %s ORDER BY created_at DESC LIMIT 1"
        )
        rows = execute_query(query, (farm_id,), fetch=True)
        if not rows:
            return jsonify({"message": "No predictions yet"}), 404
        rec = rows[0]
        health_status = get_health_status(float(rec['crop_health_index']))
        return jsonify({
            "crop_health_index": round(float(rec['crop_health_index']), 2),
            "recommendation": rec['recommendation'],
            "health_status": health_status,
            "prediction_method": rec['prediction_method'],
            "timestamp": rec['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
            "prediction_id": None,
            "input_data": {
                "temperature": float(rec['temperature']),
                "humidity": float(rec['humidity']),
                "soil_moisture": float(rec['soil_moisture']),
                "farm_id": farm_id
            },
            "insights": {
                "temperature_optimal": 20 <= float(rec['temperature']) <= 30,
                "humidity_optimal": 40 <= float(rec['humidity']) <= 80,
                "soil_moisture_optimal": 30 <= float(rec['soil_moisture']) <= 70
            }
        })
    except Exception as e:
        logger.error(f"Latest prediction error: {e}")
        return jsonify({"error": str(e)}), 500

# History endpoint with real database data
@app.route("/history/<int:farm_id>", methods=["GET"])
def history(farm_id):
    try:
        query = """
        SELECT temperature, humidity, soil_moisture, crop_health_index, 
               recommendation, prediction_method, created_at
        FROM predictions 
        WHERE farm_id = %s 
        ORDER BY created_at DESC 
        LIMIT 50
        """
        history_data = execute_query(query, (farm_id,), fetch=True)
        
        # Format the data for frontend
        formatted_history = []
        for record in history_data:
            formatted_history.append({
                "temperature": float(record['temperature']),
                "humidity": float(record['humidity']),
                "soil_moisture": float(record['soil_moisture']),
                "crop_health_index": float(record['crop_health_index']),
                "recommendation": record['recommendation'],
                "prediction_method": record['prediction_method'],
                "created_at": record['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            })
        
        logger.info(f"✅ Retrieved {len(formatted_history)} history records for farm {farm_id}")
        return jsonify(formatted_history)
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({"error": str(e)}), 500

# Analytics endpoint with real database data
@app.route("/analytics/<int:farm_id>", methods=["GET"])
def analytics(farm_id):
    try:
        # Get analytics from real database
        avg_query = "SELECT AVG(crop_health_index) as avg_health FROM predictions WHERE farm_id = %s"
        min_query = "SELECT MIN(crop_health_index) as min_health FROM predictions WHERE farm_id = %s"
        max_query = "SELECT MAX(crop_health_index) as max_health FROM predictions WHERE farm_id = %s"
        count_query = "SELECT COUNT(*) as total_predictions FROM predictions WHERE farm_id = %s"
        
        avg_result = execute_query(avg_query, (farm_id,), fetch=True)
        min_result = execute_query(min_query, (farm_id,), fetch=True)
        max_result = execute_query(max_query, (farm_id,), fetch=True)
        count_result = execute_query(count_query, (farm_id,), fetch=True)
        
        # Calculate trend (compare recent vs older predictions)
        trend_query = """
        SELECT 
            AVG(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN crop_health_index END) as recent_avg,
            AVG(CASE WHEN created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN crop_health_index END) as older_avg
        FROM predictions 
        WHERE farm_id = %s
        """
        trend_result = execute_query(trend_query, (farm_id,), fetch=True)
        
        recent_avg = trend_result[0]['recent_avg'] or 0
        older_avg = trend_result[0]['older_avg'] or 0
        
        if recent_avg > older_avg + 2:
            trend = "improving"
        elif recent_avg < older_avg - 2:
            trend = "declining"
        else:
            trend = "stable"
        
        analytics_data = {
            "average_health": round(float(avg_result[0]['avg_health'] or 0), 2),
            "trend": trend,
            "peak_health": round(float(max_result[0]['max_health'] or 0), 2),
            "lowest_health": round(float(min_result[0]['min_health'] or 0), 2),
            "total_predictions": int(count_result[0]['total_predictions']),
            "recent_avg": round(float(recent_avg), 2),
            "older_avg": round(float(older_avg), 2)
        }
        
        logger.info(f"✅ Generated analytics for farm {farm_id}")
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({"error": str(e)}), 500

# Database status endpoint
@app.route("/db-status", methods=["GET"])
def db_status():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return jsonify({
                "status": "connected",
                "mysql_version": version[0],
                "database": DB_CONFIG['database']
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Run the app
if __name__ == "__main__":
    # Optional MQTT ingestion
    def start_mqtt_listener():
        if not MQTT_AVAILABLE:
            logger.info("MQTT not available. Skipping MQTT listener.")
            return
        broker = os.getenv("MQTT_BROKER")
        if not broker:
            logger.info("MQTT_BROKER not set. Skipping MQTT listener.")
            return
        port = int(os.getenv("MQTT_PORT", "1883"))
        topic = os.getenv("MQTT_TOPIC", "smart_farming/sensors")

        def on_connect(client, userdata, flags, reason_code, properties=None):  # paho-mqtt v2 signature
            logger.info(f"✅ MQTT connected to {broker}:{port}, subscribing to {topic}")
            client.subscribe(topic)

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
                temperature = float(payload["temperature"])
                humidity = float(payload["humidity"])
                soil_moisture = float(payload["soil_moisture"])
                farm_id = int(payload.get("farm_id", 1))

                # Reuse HTTP ingestion logic
                prediction, prediction_method, recommendation, health_status = compute_prediction_values(
                    temperature, humidity, soil_moisture
                )
                try:
                    insert_sensor = (
                        "INSERT INTO sensor_data (temperature, humidity, soil_moisture, crop_health_index) "
                        "VALUES (%s, %s, %s, %s)"
                    )
                    execute_query(insert_sensor, (temperature, humidity, soil_moisture, prediction))
                    insert_prediction = (
                        "INSERT INTO predictions (farm_id, temperature, humidity, soil_moisture, crop_health_index, recommendation, prediction_method) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    )
                    execute_query(insert_prediction, (
                        farm_id, temperature, humidity, soil_moisture,
                        prediction, recommendation, prediction_method
                    ))
                except Exception as e:
                    logger.error(f"❌ MQTT ingestion DB error: {e}")
            except Exception as e:
                logger.error(f"❌ MQTT message error: {e}")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        logger.info("🚀 MQTT listener started")

    # Start MQTT listener in background if configured
    try:
        threading.Thread(target=start_mqtt_listener, daemon=True).start()
    except Exception as e:
        logger.error(f"Failed to start MQTT listener: {e}")

    logger.info("🚀 Starting Smart Farming Backend with Database Integration")
    app.run(debug=True, port=5000)
