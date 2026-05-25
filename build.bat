@echo off
setlocal

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

pyinstaller --onefile --noconsole --icon=assets/icon.ico --name RepoBell app/main.py

echo Build completed. Executable is available in dist\RepoBell.exe
endlocal
