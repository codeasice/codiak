@echo off
REM Codiak React + FastAPI Dev Server
REM Runs FastAPI on :8000 and Vite on :5173 simultaneously.
REM Streamlit continues to run separately on :8501 if started via run.bat.

echo ========================================
echo  Codiak React + FastAPI Dev Server
echo ========================================
echo.
echo  FastAPI  -> http://localhost:8000
echo  React    -> http://localhost:5173
echo  API Docs -> http://localhost:8000/docs
echo.
echo Starting FastAPI backend...
start "Codiak - FastAPI" cmd /k ".\venv\Scripts\activate && uvicorn api.main:app --reload --port 8000"

timeout /t 2 /nobreak > nul

echo Starting React frontend...
start "Codiak - React" cmd /k "cd web && npm run dev"

echo.
echo Both servers starting in separate windows.
echo Press any key to exit this launcher.
pause > nul
