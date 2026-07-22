@echo off
setlocal
cd /d "%~dp0\..\.."
where py >nul 2>nul
if %errorlevel%==0 (
  start "MapNG Local Agent" py -3 tools\mapng-local-agent\server.py
) else (
  start "MapNG Local Agent" python tools\mapng-local-agent\server.py
)
timeout /t 2 >nul
start "" http://127.0.0.1:8765/beamng-viewer/
endlocal
