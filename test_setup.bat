@echo off
echo Testing arXiv Server Connection...

cd /d D:\arxiv-paper-system

echo.
echo Testing imports...
python -c "from arxiv_crawler import ArxivCrawler; from database import PaperDatabase; from categories import ALL_CATEGORIES; print('All imports successful!')"

if %errorlevel% neq 0 (
    echo ERROR: Import failed. Check dependencies.
    pause
    exit /b 1
)

echo.
echo Testing database creation...
python -c "from database import PaperDatabase; db = PaperDatabase(); print(f'Database initialized with {db.get_total_count()} papers')"

if %errorlevel% neq 0 (
    echo ERROR: Database test failed.
    pause
    exit /b 1
)

echo.
echo All tests passed! You can now start the server.
pause
