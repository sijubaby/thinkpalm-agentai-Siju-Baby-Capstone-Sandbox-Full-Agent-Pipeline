@echo off
cd /d "%~dp0.."
echo.
echo ========================================
echo  Maritime QA Agent
echo  URL: http://127.0.0.1:8770
echo ========================================
echo.
echo Installing/updating package...
".venv\Scripts\python.exe" -m pip install -e . -q
".venv\Scripts\python.exe" -m pip install "openai>=1.30,<1.55" "httpx>=0.23,<0.28" --only-binary=:all: -q
echo.
echo Starting server (keep this window open)...
".venv\Scripts\python.exe" -m maritime_qa.api
pause
