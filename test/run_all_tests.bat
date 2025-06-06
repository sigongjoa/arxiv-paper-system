@echo off
title Complete Test Suite
color 0E

cd /d "%~dp0"
cd ..

echo ================================================================
echo               Complete Test Suite
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

REM Test menu
:menu
echo ================================================================
echo                    Test Menu
echo ================================================================
echo.
echo  1. Simple Crawler Test (3 papers only)
echo  2. Integrated Platform Test (Crawling + AI + PDF)
echo  3. Platform-specific Crawler Test
echo  4. Run All Tests Sequentially
echo  0. Exit
echo.
set /p choice="Choose option (0-4): "

if "%choice%"=="1" goto :simple_test
if "%choice%"=="2" goto :integrated_test
if "%choice%"=="3" goto :platform_test
if "%choice%"=="4" goto :all_tests
if "%choice%"=="0" goto :end

echo [ERROR] Invalid choice.
echo.
goto :menu

:simple_test
echo.
echo [1] Starting Simple Crawler Test...
echo ================================================================
python test\simple_test.py
echo.
echo Simple test completed. Returning to menu...
pause
goto :menu

:integrated_test
echo.
echo [2] Starting Integrated Platform Test...
echo ================================================================
python test\integrated_platform_test.py
echo.
echo Integrated test completed. Returning to menu...
pause
goto :menu

:platform_test
echo.
echo [3] Starting Platform-specific Crawler Test...
echo ================================================================
if exist "test\platform_crawler_test.py" (
    python test\platform_crawler_test.py
) else (
    echo [ERROR] platform_crawler_test.py file not found.
)
echo.
echo Platform test completed. Returning to menu...
pause
goto :menu

:all_tests
echo.
echo [4] Starting All Tests Sequentially...
echo ================================================================
echo.

echo ### 1/3: Simple Crawler Test ###
python test\simple_test.py
echo.

echo ### 2/3: Platform-specific Crawler Test ###
if exist "test\platform_crawler_test.py" (
    python test\platform_crawler_test.py
) else (
    echo [SKIP] platform_crawler_test.py file not found.
)
echo.

echo ### 3/3: Integrated Platform Test ###
python test\integrated_platform_test.py
echo.

echo ================================================================
echo [SUCCESS] All tests completed
echo End Time: %DATE% %TIME%
echo ================================================================
echo.
echo Returning to menu...
pause
goto :menu

:end
echo.
echo ================================================================
echo                 Exiting Test Tool
echo ================================================================
echo Exit Time: %DATE% %TIME%
echo.
pause >nul
