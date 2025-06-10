@echo off
title Integrated Platform Test
color 0A

cd /d "%~dp0"
cd ..

echo ================================================================
echo    Integrated Platform Test (Crawling + AI + PDF + Logging)
echo ================================================================
echo.
echo Current Directory: %CD%
echo Test Start Time: %DATE% %TIME%
echo.

REM Activate Python virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [SUCCESS] Virtual environment activated
    echo.
) else (
    echo [INFO] No virtual environment, using system Python
    echo.
)

REM Check required directories
if not exist "backend" (
    echo [ERROR] backend directory not found
    goto :error
)

if not exist "test\integrated_platform_test.py" (
    echo [ERROR] Test file not found
    goto :error
)

REM Run integrated test
echo [START] Running integrated platform test...
echo ================================================================
python test\integrated_platform_test.py
set TEST_RESULT=%ERRORLEVEL%

echo.
echo ================================================================
if %TEST_RESULT% EQU 0 (
    echo [SUCCESS] Test completed successfully
    color 0A
) else (
    echo [ERROR] Test failed with code: %TEST_RESULT%
    color 0C
)
echo Test End Time: %DATE% %TIME%
echo ================================================================
echo.
echo Press any key to exit...
pause >nul
goto :end

:error
color 0C
echo.
echo ================================================================
echo [FATAL ERROR] Cannot run test
echo ================================================================
echo Press any key to exit...
pause >nul

:end
