@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing project requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Starting Around the Globe Quiz...
streamlit run app.py
pause
