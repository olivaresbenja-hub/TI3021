@echo off
cd /d "%~dp0"
if not exist ".env" copy ".env.example" ".env" >nul
where py >nul 2>nul
if errorlevel 1 (
    python main.py
) else (
    py -3 main.py
)
pause
