@echo off
setlocal

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [1/2] Building RepoBell.exe with PyInstaller...
pyinstaller --onefile --noconsole --icon=assets/icon.ico --add-data "assets;assets" --name RepoBell app/main.py
if errorlevel 1 (
  echo PyInstaller build failed.
  exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
  echo Inno Setup compiler not found.
  echo Install Inno Setup 6: https://jrsoftware.org/isdl.php
  exit /b 1
)

echo [2/2] Building installer via Inno Setup...
"%ISCC%" "installer\RepoBell.iss"
if errorlevel 1 (
  echo Inno Setup compilation failed.
  exit /b 1
)

echo Done.
echo EXE: dist\RepoBell.exe
echo Installer: installer\output\RepoBellSetup.exe
endlocal
