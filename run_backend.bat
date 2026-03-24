@echo off
REM Codiak FastAPI Backend
echo Starting FastAPI backend on http://localhost:8000 ...
echo API Docs: http://localhost:8000/docs
.\venv\Scripts\activate && uvicorn api.main:app --reload --port 8000
