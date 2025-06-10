@echo off
title Quick Test - System Validation
color 0D

cd /d "%~dp0"
cd ..

echo ================================================================
echo              Quick System Validation (Under 1 minute)
echo ================================================================
echo.
echo Current Directory: %CD%
echo Start Time: %DATE% %TIME%
echo.

REM Activate Python virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat >nul 2>&1
    echo [SUCCESS] Virtual environment activated
) else (
    echo [INFO] Using system Python
)

REM Quick validation checks
echo ================================================================
echo [1/4] Checking directory structure...
if exist "backend" (
    echo   - backend directory exists
) else (
    echo   X backend directory missing
    goto :error
)

if exist "test" (
    echo   - test directory exists
) else (
    echo   X test directory missing
    goto :error
)

echo.
echo [2/4] Testing module imports...
python -c "
try:
    import sys, os
    sys.path.insert(0, 'backend')
    from agents.lm_studio_client import LMStudioClient
    from agents.multi_platform_analysis_agent import MultiPlatformAnalysisAgent
    from automation.pdf_generator import PdfGenerator
    from utils.notion import NotionLogger
    print('  - All core modules imported successfully')
except Exception as e:
    print(f'  X Module import failed: {e}')
    exit(1)
"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Module import failed
    goto :error
)

echo.
echo [3/4] Testing crawler initialization...
python -c "
try:
    import sys, os
    sys.path.insert(0, 'backend')
    from api.crawling.arxiv_crawler import ArxivCrawler
    crawler = ArxivCrawler()
    print('  - ArXiv crawler initialized successfully')
except Exception as e:
    print(f'  X Crawler initialization failed: {e}')
    exit(1)
"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Crawler initialization failed
    goto :error
)

echo.
echo [4/4] Checking output directories...
if not exist "backend\output" (
    mkdir "backend\output" >nul 2>&1
    echo   - output directory created
) else (
    echo   - output directory exists
)

if not exist "backend\output\pdfs" (
    mkdir "backend\output\pdfs" >nul 2>&1
    echo   - pdfs directory created
) else (
    echo   - pdfs directory exists
)

echo.
echo ================================================================
echo [SUCCESS] All validations passed - System ready to run
color 0A
echo ================================================================
echo End Time: %DATE% %TIME%
echo.
echo You can now run other tests:
echo   - run_simple_test.bat (Simple test)
echo   - run_integrated_test.bat (Integrated test)
echo   - run_all_tests.bat (Full menu)
echo.
echo Press any key to exit...
pause >nul
goto :end

:error
color 0C
echo.
echo ================================================================
echo [FAILED] Validation failed - Check system setup
echo ================================================================
echo.
echo Troubleshooting:
echo 1. Check if Python is installed
echo 2. Check if required packages are installed
echo 3. Check if paths are correctly set
echo.
echo Press any key to exit...
pause >nul

:end
