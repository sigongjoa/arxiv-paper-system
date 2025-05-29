@echo off
echo Starting arXiv Paper Crawler Server...

cd /d D:\arxiv-paper-system

echo Installing dependencies...
pip install fastapi uvicorn requests

echo Starting FastAPI server...
cd backend
python api/main.py

pause
