@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; raise SystemExit(sys.version_info < (3,10))"
if errorlevel 1 (
  echo Install Python 3.10 or later from python.org, then run this again.
  pause
  exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Ready. Double-click Start Windows.cmd.
pause
exit /b 0
:failed
echo Setup did not finish. Read the error above before retrying.
pause
exit /b 1
