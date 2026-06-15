#!/usr/bin/env python3
"""
Database Setup Script for Smart Farming Application
Run this script to set up the MySQL database and tables
"""

import mysql.connector
from mysql.connector import Error
import sys

def create_database():
    """Create the smart_farming database"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Burlington_101'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS smart_farming")
            print("✅ Database 'smart_farming' created successfully")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create the necessary tables"""
    try:
        # Connect to the smart_farming database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Burlington_101',
            database='smart_farming'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create predictions table
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
            cursor.execute(create_predictions_table)
            print("✅ Predictions table created successfully")
            
            # Create sensor_data table (from your existing schema)
            create_sensor_table = """
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                soil_moisture FLOAT NOT NULL,
                crop_health_index FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_sensor_table)
            print("✅ Sensor data table created successfully")
            
            # Insert sample data into sensor_data table
            sample_data = [
                (22, 55, 30, 68),
                (24, 60, 35, 72),
                (26, 58, 40, 75),
                (28, 62, 45, 80),
                (30, 65, 50, 85),
                (32, 70, 55, 88),
                (34, 72, 60, 90),
                (36, 75, 65, 92),
                (25, 55, 38, 74),
                (27, 60, 42, 77)
            ]
            
            insert_query = """
            INSERT IGNORE INTO sensor_data (temperature, humidity, soil_moisture, crop_health_index)
            VALUES (%s, %s, %s, %s)
            """
            cursor.executemany(insert_query, sample_data)
            print("✅ Sample sensor data inserted")
            
            connection.commit()
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

def test_connection():
    """Test the database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Burlington_101',
            database='smart_farming'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            print(f"✅ Database connection successful - {count} predictions in database")
            
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            count = cursor.fetchone()[0]
            print(f"✅ {count} sensor data records available")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🌱 Smart Farming Database Setup")
    print("=" * 40)
    
    print("\n1. Creating database...")
    if not create_database():
        print("❌ Database creation failed. Please check your MySQL credentials.")
        sys.exit(1)
    
    print("\n2. Creating tables...")
    if not create_tables():
        print("❌ Table creation failed.")
        sys.exit(1)
    
    print("\n3. Testing connection...")
    if not test_connection():
        print("❌ Connection test failed.")
        sys.exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYou can now run the backend with: python app_database.py")
    print("Frontend: npm run dev")
    print("Visit: http://localhost:3000")

if __name__ == "__main__":
    main()
