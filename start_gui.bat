@echo off
echo Opening arXiv Paper Crawler GUI...

cd /d D:\arxiv-paper-system\frontend\public

echo Starting web browser...
start data-collection.html

echo.
echo If the GUI doesn't work properly, make sure the server is running:
echo 1. Open another terminal
echo 2. Run: start_server.bat
echo 3. Wait for "Application startup complete" message
echo 4. Then refresh the browser page

pause
