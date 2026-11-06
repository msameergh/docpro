@echo off
cd /d "%~dp0"
echo Starting Docpro... your browser will open shortly.
echo Close this window to stop the app.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
