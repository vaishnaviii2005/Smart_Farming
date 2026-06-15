"""
Simple IoT Sensor Simulator

Sends periodic sensor readings to the backend /ingest-sensor endpoint.
Run: python iot_simulator.py
Stop: Ctrl+C
"""

import random
import time
import requests

BACKEND_URL = "http://localhost:5000/ingest-sensor"

def generate_sensor_value(base: float, jitter: float, min_v: float, max_v: float) -> float:
    value = base + random.uniform(-jitter, jitter)
    return max(min_v, min(max_v, round(value, 2)))

def main():
    print("🌡️ IoT Sensor Simulator started. Sending data to /ingest-sensor ...")
    while True:
        try:
            temperature = generate_sensor_value(26.0, 4.0, 15.0, 38.0)
            humidity = generate_sensor_value(55.0, 15.0, 25.0, 90.0)
            soil_moisture = generate_sensor_value(48.0, 20.0, 15.0, 85.0)

            payload = {
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_moisture,
                "farm_id": 1,
            }
            resp = requests.post(BACKEND_URL, json=payload, timeout=5)
            if resp.ok:
                data = resp.json().get('prediction', {})
                print(f"✅ Sent: {payload} | Health: {data.get('crop_health_index')} | {data.get('prediction_method')}")
            else:
                print(f"❌ Backend error: {resp.status_code} {resp.text}")
        except KeyboardInterrupt:
            print("\n👋 Stopping simulator.")
            break
        except Exception as e:
            print(f"❌ Error sending data: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()


