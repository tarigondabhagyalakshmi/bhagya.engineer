@echo off
:: setup_task_scheduler.bat
:: Registers "BhagyaWebsite-AutoPush" in Windows Task Scheduler
:: Runs auto_push.py every 30 minutes automatically — no manual step needed.
::
:: HOW TO USE:
::   Right-click this file → "Run as Administrator"

echo.
echo =====================================================
echo  Setting up Windows Task Scheduler auto-push task
echo =====================================================
echo.

set SCRIPT_PATH=C:\Users\DELL\Documents\Claud-Global\bhagya-website-main\auto_push.py
set TASK_NAME=BhagyaWebsite-AutoPush

schtasks /create /tn "%TASK_NAME%" ^
  /tr "python \"%SCRIPT_PATH%\"" ^
  /sc MINUTE /mo 30 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel% == 0 (
    echo.
    echo SUCCESS! Task "%TASK_NAME%" created.
    echo It will run every 30 minutes automatically.
    echo.
    echo To run it NOW manually:
    echo   schtasks /run /tn "%TASK_NAME%"
    echo.
    echo To remove it later:
    echo   schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo ERROR: Could not create task. Make sure you ran as Administrator.
)

echo.
pause
