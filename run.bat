@echo off
REM ===================================================================
REM  One-click launcher for Windows.
REM
REM  Poker Advisor with a graphical window: enter your cards, board,
REM  pot and stacks, and the Smart Champion engine tells you whether to
REM  raise, call, bet, check or fold.
REM
REM  Double-click this file to run. If Python is not installed it will
REM  try to install it automatically (via winget, or by downloading the
REM  official installer). Unlike a pure-Tkinter app, this one also needs
REM  the "treys" package, so the launcher creates a local virtual
REM  environment (the .venv folder) and installs it there the first time.
REM
REM  To run the terminal version instead of the window:   run.bat cli
REM
REM  This window ALWAYS waits for a key press before closing, so it can
REM  never just flash open and shut: whatever happens, you can read it.
REM ===================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Poker Advisor Launcher

REM Which frontend to run: gui (default) or cli.
set "MODE=%~1"
if not defined MODE set "MODE=gui"
if /i "%MODE%"=="gui" (set "TARGET=gui.py") else if /i "%MODE%"=="cli" (set "TARGET=cli.py") else (
    echo Unknown option "%MODE%". Use:  run.bat        ^(window^)
    echo                          or:  run.bat cli    ^(terminal^)
    goto end
)

REM --- 1. Is a *working* Python already available? -------------------
call :find_python
if defined PYLAUNCH goto have_python

REM --- 2. Not found: try to install it automatically ------------------
echo.
echo Python was not found on this computer.
echo Attempting to install it automatically (this needs an internet
echo connection and may ask for permission)...
echo.

where winget >nul 2>nul
if "!errorlevel!"=="0" (
    echo Installing Python via winget...
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
) else (
    echo winget is not available. Downloading the official installer...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-setup.exe'"
    echo Installing Python ^(this may take a minute^)...
    "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
    del "%TEMP%\python-setup.exe" >nul 2>nul
)

REM --- 3. Look again after the install --------------------------------
call :find_python
if not defined PYLAUNCH (
    echo.
    echo Could not install or locate a working Python automatically.
    echo Please install it manually from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    goto end
)

:have_python
echo Using Python: %PYLAUNCH%
%PYLAUNCH% -c "import sys; print('Python', sys.version.split()[0], 'at', sys.executable)"
echo.

REM --- 4. Create / repair the local virtual environment -------------
REM  This is fully automatic: the user never has to delete anything.
REM  If the .venv is missing, was copied from another computer
REM  (e.g. a Linux/Mac venv with no Windows python.exe), or is simply
REM  broken, we wipe it and build a fresh one - up to two attempts.
set "VENV_PY=.venv\Scripts\python.exe"

REM A .venv that exists but has no Windows python.exe was built on
REM another operating system. Remove it so we can rebuild it here.
if exist ".venv" if not exist "%VENV_PY%" (
    echo Found a virtual environment from another computer; rebuilding it...
    rmdir /s /q ".venv" >nul 2>nul
)

set "VENV_TRIES=0"
:make_venv
set /a VENV_TRIES+=1
if not exist "%VENV_PY%" (
    echo Creating virtual environment in .venv ...
    %PYLAUNCH% -m venv .venv
)

REM Confirm the venv Python actually runs (same 42 trick as above).
set "VENVOK="
if exist "%VENV_PY%" for /f "delims=" %%v in ('"%VENV_PY%" -c "print(42)" 2^>nul') do if "%%v"=="42" set "VENVOK=1"
if defined VENVOK goto venv_ready

if !VENV_TRIES! geq 2 (
    echo.
    echo Could not create a working virtual environment ^(.venv^).
    echo Make sure your Python install includes the "venv" module,
    echo then run this file again.
    goto end
)
echo The virtual environment did not work; rebuilding it from scratch...
rmdir /s /q ".venv" >nul 2>nul
goto make_venv

:venv_ready

REM --- 5. Install requirements only if "treys" is missing ------------
"%VENV_PY%" -c "import treys" >nul 2>nul
if not "!errorlevel!"=="0" (
    echo Installing requirements ^(first run only^)...
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt
    "%VENV_PY%" -c "import treys" >nul 2>nul
    if not "!errorlevel!"=="0" (
        echo.
        echo Could not install the required "treys" package.
        echo Check your internet connection and try again.
        goto end
    )
)

REM --- 6. Tkinter check (only matters for the GUI) -------------------
if /i "%MODE%"=="gui" (
    "%VENV_PY%" -c "import tkinter" >nul 2>nul
    if not "!errorlevel!"=="0" (
        echo Python is installed but Tkinter is missing, so the window
        echo cannot open. Re-run the Python installer and make sure
        echo "tcl/tk and IDLE" is selected, then run this file again.
        echo ^(Or use the terminal version:  run.bat cli^)
        goto end
    )
)

REM --- 7. Run it -----------------------------------------------------
echo Starting Poker Advisor ^(%MODE%^)...
"%VENV_PY%" %TARGET%
set "EXITCODE=!errorlevel!"
echo.
echo Poker Advisor has closed ^(exit code !EXITCODE!^).
if not "!EXITCODE!"=="0" echo If a Python error is shown above, please report it.
goto end

REM ===================================================================
REM  Helper: locate a Python that can actually RUN code, store it in
REM  PYLAUNCH. We don't trust the command merely existing, because
REM  Windows ships a fake "python.exe" App-Execution-Alias stub that
REM  runs nothing. So we make Python PRINT a known value and only
REM  accept it if that value actually comes back: the stub prints
REM  nothing, a real interpreter prints "42".
REM ===================================================================
:find_python
set "PYLAUNCH="
call :verify "py -3"
if defined PYLAUNCH exit /b
call :verify "python"
if defined PYLAUNCH exit /b
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if not defined PYLAUNCH if exist "%%D\python.exe" (
        for /f "delims=" %%v in ('"%%D\python.exe" -c "print(42)" 2^>nul') do (
            if "%%v"=="42" set PYLAUNCH="%%D\python.exe"
        )
    )
)
exit /b

:verify
REM %~1 is a python command. Set PYLAUNCH to it only if it really runs.
set "PYOUT="
for /f "delims=" %%v in ('%~1 -c "print(42)" 2^>nul') do set "PYOUT=%%v"
if "%PYOUT%"=="42" set "PYLAUNCH=%~1"
exit /b

REM ===================================================================
REM  Single place EVERY path lands on (success or failure) so the
REM  window always pauses and never flashes shut.
REM ===================================================================
:end
echo.
pause
exit /b
