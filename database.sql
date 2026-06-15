CREATE DATABASE IF NOT EXISTS smart_farming;
USE smart_farming;

CREATE TABLE Farmer (
    FarmerID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    ContactNumber VARCHAR(15),
    Email VARCHAR(100),
    Address TEXT,
    FarmSize FLOAT
);

CREATE TABLE Farm (
    FarmID INT PRIMARY KEY AUTO_INCREMENT,
    FarmerID INT,
    Location VARCHAR(100),
    SoilType VARCHAR(50),
    IrrigationType VARCHAR(50),
    Area FLOAT,
    FOREIGN KEY (FarmerID) REFERENCES Farmer(FarmerID)
);

CREATE TABLE Crop (
    CropID INT PRIMARY KEY AUTO_INCREMENT,
    CropName VARCHAR(100),
    CropType VARCHAR(50),
    GrowthDuration INT,
    IdealTemperature FLOAT,
    IdealSoilMoisture FLOAT
);

CREATE TABLE Planting (
    PlantingID INT PRIMARY KEY AUTO_INCREMENT,
    FarmID INT,
    CropID INT,
    PlantingDate DATE,
    ExpectedHarvestDate DATE,
    Status VARCHAR(20),
    FOREIGN KEY (FarmID) REFERENCES Farm(FarmID),
    FOREIGN KEY (CropID) REFERENCES Crop(CropID)
);

CREATE TABLE SoilSensorData (
    SensorID INT PRIMARY KEY AUTO_INCREMENT,
    FarmID INT,
    MoistureLevel FLOAT,
    Temperature FLOAT,
    pHLevel FLOAT,
    RecordedDateTime DATETIME,
    FOREIGN KEY (FarmID) REFERENCES Farm(FarmID)
);

CREATE TABLE MarketPrice (
    PriceID INT PRIMARY KEY AUTO_INCREMENT,
    CropID INT,
    Date DATE,
    PricePerKg FLOAT,
    FOREIGN KEY (CropID) REFERENCES Crop(CropID)
);
