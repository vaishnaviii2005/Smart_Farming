from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

model = joblib.load('crop_health_model.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    soil_moisture = data.get('soil_moisture')
    
    features = np.array([[temperature, humidity, soil_moisture]])
    prediction = model.predict(features)[0]
    
    return jsonify({'crop_health_index': round(prediction, 2)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    