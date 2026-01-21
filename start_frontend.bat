@echo off
echo Starting FactorFlow Frontend...
cd /d "%~dp0"
.venv\Scripts\python.exe -m streamlit run frontend/app.py
pause
