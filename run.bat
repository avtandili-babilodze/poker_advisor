@echo off
REM ===================================================================
REM  One-click launcher for Windows.
REM
REM  Double-click this file to run the Poker Advisor window.
REM  If Python is missing it is downloaded and installed automatically,
REM  then a local virtual environment (.venv) is created and the
REM  required libraries are installed - all on the first run only.
REM
REM  To run the terminal version instead of the window:   run.bat cli
REM ===================================================================
cd /d "%~dp0"
title Poker Advisor Launcher

REM Which frontend to run: gui (default) or cli.
set "TARGET=gui.py"
if /i "%~1"=="cli" set "TARGET=cli.py"

echo Checking for Python...
py -3 --version >nul 2>&1
if %errorlevel% equ 0 set "PY_CMD=py -3"
if %errorlevel% equ 0 goto setup_venv

python --version >nul 2>&1
if %errorlevel% equ 0 set "PY_CMD=python"
if %errorlevel% equ 0 goto setup_venv

echo.
echo Python was not found on this computer.
echo Downloading and installing Python automatically...
echo Please wait, this may take a minute or two...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"

echo Installing Python silently in the background...
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
del "%TEMP%\python-installer.exe" >nul 2>&1

REM Because the terminal doesn't instantly know the path updated, we point
REM directly to where it just installed.
set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY_CMD%" set "PY_CMD=python"

:setup_venv
echo.
REM A .venv copied from another computer (e.g. Linux/Mac) has no Windows
REM python.exe; rebuild it so it works here.
if exist .venv if not exist .venv\Scripts\python.exe (
    echo Found a virtual environment from another computer; rebuilding it...
    rmdir /s /q .venv
)

if exist .venv\Scripts\python.exe goto install_libs

echo Creating local virtual environment...
%PY_CMD% -m venv .venv

:install_libs
if exist .venv\installed.txt goto launch

echo Installing required poker libraries...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo done > .venv\installed.txt

:launch
echo Starting Poker Advisor...
.venv\Scripts\python.exe %TARGET%

if %errorlevel% neq 0 goto error
exit /b

:error
echo.
echo The application closed unexpectedly.
pause
exit /b