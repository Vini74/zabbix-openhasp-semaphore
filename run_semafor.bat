@echo off
REM Wrapper script for running semafor.py with environment variables on Windows

REM Set the working directory to the script's directory
cd /d "%~dp0"

REM Load environment variables from .env file
if exist .env (
    for /f "tokens=*" %%i in (.env) do set %%i
)

REM Run the Python script
python semafor.py