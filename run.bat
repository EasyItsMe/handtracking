@echo off
echo ===================================================
echo   Menjalankan AR Hand Tracking Filter...
echo ===================================================
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    py -3.12 main.py
)
pause
