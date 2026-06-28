@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
call :check_python python
if defined PYTHON_CMD goto run_app
call :check_python py -3
if defined PYTHON_CMD goto run_app

echo ProMentum needs Python 3.10 or newer.
echo.
echo What to do:
echo   1. Go to https://www.python.org/downloads/windows/
echo   2. Download and install Python.
echo   3. Tick "Add python.exe to PATH" during install.
echo   4. Double-click START_ProMentum_WINDOWS.bat again.
echo.
echo Nothing has been installed or changed by ProMentum.
echo.
pause
exit /b 1

:run_app
if defined PROMENTUM_HOME goto launch
if defined IDEA_COLLIDER_HOME (
  set "PROMENTUM_HOME=%IDEA_COLLIDER_HOME%"
  goto launch
)
if exist "D:\" (
  set "PROMENTUM_HOME=D:\ProMentumData"
  md "%PROMENTUM_HOME%" >nul 2>nul
  if errorlevel 1 (
    set "PROMENTUM_HOME=%CD%\promentum_data"
  )
) else (
  set "PROMENTUM_HOME=%CD%\promentum_data"
)

:launch
set "IDEA_COLLIDER_HOME=%PROMENTUM_HOME%"
echo Starting ProMentum with %PYTHON_CMD% ...
echo Data folder: %PROMENTUM_HOME%
echo Your browser should open in a moment.
echo.
%PYTHON_CMD% -m idea_collider_app.app
pause
exit /b 0

:check_python
%* -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=%*"
exit /b 0
