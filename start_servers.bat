@echo off
echo Starting Smart Farming Application with Database...
echo.

echo Setting up database...
python setup_database.py

echo.
echo Starting Flask Backend with Database on port 5000...
start cmd /k "cd /d %~dp0 && python app_database.py"

timeout /t 3 /nobreak >nul

echo Starting React Frontend on port 3000...
start cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo Both servers are starting with database integration...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo Database: MySQL smart_farming
echo.
echo Press any key to exit...
pause >nul
