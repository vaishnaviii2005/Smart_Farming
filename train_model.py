import joblib
import mysql.connector
import numpy as np
from sklearn.linear_model import LinearRegression

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",          # change if you have another username
    password="Burlington_101",  # replace with your MySQL password
    database="smart_farming"   # replace with your DB name
)

cursor = conn.cursor()

# Fetch training data
cursor.execute("SELECT temperature, humidity, soil_moisture, crop_health_index FROM sensor_data")
rows = cursor.fetchall()

# Convert to numpy arrays
X = np.array([row[:3] for row in rows])   # features
y = np.array([row[3] for row in rows])    # target

# Train model
model = LinearRegression()
model.fit(X, y)

# Save trained model
joblib.dump(model, "crop_health_model.pkl")

print("✅ Model trained on MySQL data and saved as crop_health_model.pkl")

# Close connection
cursor.close()
conn.close()
