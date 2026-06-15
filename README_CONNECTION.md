# Smart Farming App - Backend & Frontend Connection

## Overview
Your Smart Farming application now has a connected backend (Flask) and frontend (React) setup.

## Setup Instructions

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt.txt
```

### 2. Install Frontend Dependencies
```bash
npm install
```

### 3. Start the Application

#### Option A: Use the Batch Script (Windows)
Double-click `start_servers.bat` to start both servers automatically.

#### Option B: Manual Start
1. **Start Backend (Terminal 1):**
   ```bash
   python app.py
   ```
   Backend will run on: http://localhost:5000

2. **Start Frontend (Terminal 2):**
   ```bash
   npm run dev
   ```
   Frontend will run on: http://localhost:3000

## What's Connected

### Backend (Flask - Port 5000)
- ✅ CORS enabled for cross-origin requests
- ✅ `/predict` endpoint for crop health predictions
- ✅ `/history/<farm_id>` endpoint for prediction history
- ✅ MySQL database integration

### Frontend (React - Port 3000)
- ✅ Connected to Flask backend via axios
- ✅ Form for inputting temperature, humidity, soil moisture
- ✅ Displays crop health index and recommendations
- ✅ Error handling and loading states
- ✅ Modern UI with Tailwind CSS

## API Endpoints

### POST /predict
Send crop data and get health prediction:
```json
{
  "temperature": 25.5,
  "humidity": 60.0,
  "soil_moisture": 45.0,
  "farm_id": 1
}
```

Response:
```json
{
  "crop_health_index": 75.5,
  "recommendation": "Crop health is good. Maintain current practices."
}
```

### GET /history/<farm_id>
Get prediction history for a farm:
- Example: `GET /history/1`

## Troubleshooting

### Common Issues:
1. **CORS Errors**: Make sure flask-cors is installed (`pip install flask-cors`)
2. **Port Conflicts**: Ensure ports 5000 and 3000 are available
3. **Database Connection**: Verify MySQL is running and credentials are correct in `app.py`
4. **Missing Dependencies**: Run `pip install -r requirements.txt.txt` and `npm install`

### Testing Connection:
1. Open http://localhost:3000 in your browser
2. Fill in the form with sample data
3. Click "Get Crop Health Prediction"
4. You should see the prediction results

## Files Modified:
- `app.py` - Added CORS support
- `src/App.jsx` - Enhanced React frontend with full API integration
- `requirements.txt.txt` - Added flask-cors and mysql-connector-python
