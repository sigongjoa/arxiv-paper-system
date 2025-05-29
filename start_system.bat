@echo off
echo Starting arXiv Paper Management System...

cd /d D:\arxiv-paper-system

echo Starting backend server...
start "Backend" cmd /c "cd backend && python api/main.py"

timeout /t 3 >nul

echo Opening main interface...
start "" "frontend\public\data-collection.html"

echo System started successfully!
echo.
echo Available interfaces:
echo - Main: frontend\public\data-collection.html
echo - Search: frontend\public\arxiv-search.html  
echo - Results: frontend\public\arxiv-results.html
echo - Summaries: frontend\public\paper-summary.html
echo - Backend API: http://localhost:8000
echo.
echo Press any key to stop the system...
pause >nul

taskkill /f /im python.exe 2>nul
echo System stopped.
