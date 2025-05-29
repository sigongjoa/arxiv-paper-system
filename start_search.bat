@echo off
echo Starting arXiv Search System...

cd /d D:\arxiv-paper-system

echo Starting backend server...
start "Backend" cmd /c "cd backend && python api/main.py"

timeout /t 3 >nul

echo Opening arXiv management interface...
start "" "frontend\public\data-collection.html"

echo System started!
echo - Backend API: http://localhost:8000
echo - Search Interface: frontend\arxiv-search.html
echo.
echo Press any key to stop...
pause >nul

taskkill /f /im python.exe 2>nul
echo System stopped.
