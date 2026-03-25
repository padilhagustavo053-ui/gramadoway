@echo off
cd /d "%~dp0"
echo API Gramadoway em http://localhost:8000/docs
python -m uvicorn api_app:app --host 0.0.0.0 --port 8000
pause
