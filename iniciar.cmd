@echo off
cd /d "%~dp0"
if not exist ".env" copy ".env.example" ".env" >nul
where py >nul 2>nul
if errorlevel 1 (
    python -c "import requests, argon2" >nul 2>nul
    if errorlevel 1 (
        echo Primero ejecuta: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
    python main.py
) else (
    py -3 -c "import requests, argon2" >nul 2>nul
    if errorlevel 1 (
        echo Primero ejecuta: py -3 -m pip install -r requirements.txt
        pause
        exit /b 1
    )
    py -3 main.py
)
pause
