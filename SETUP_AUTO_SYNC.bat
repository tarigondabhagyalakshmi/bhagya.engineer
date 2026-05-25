@echo off
:: SETUP_AUTO_SYNC.bat
:: Run this ONCE (as Administrator) to make Windows auto-sync every 30 minutes.
:: After that, every change you save will be pushed automatically — no manual step needed.
::
:: HOW TO USE:
::   Right-click this file → "Run as administrator"

echo.
echo =====================================================
echo  bhagya.engineer — Auto-Sync Setup
echo =====================================================
echo.
echo This will create a Windows Task that runs SYNC.bat
echo automatically every 30 minutes.
echo.

set SCRIPT_PATH=C:\Users\DELL\Documents\Claud-Global\bhagya-website-main\SYNC.ps1
set TASK_NAME=BhagyaWebsite-AutoSync

schtasks /create /tn "%TASK_NAME%" ^
  /tr "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%SCRIPT_PATH%\"" ^
  /sc MINUTE /mo 30 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel% == 0 (
    echo.
    echo  SUCCESS! Auto-sync task created.
    echo  Your site will push to GitHub every 30 minutes automatically.
    echo.
    echo  To push RIGHT NOW manually:
    echo    Double-click SYNC.bat
    echo.
    echo  To stop auto-sync later:
    echo    schtasks /delete /tn "%TASK_NAME%" /f
    echo.
) else (
    echo.
    echo  ERROR: Could not create task.
    echo  Make sure you right-clicked and chose "Run as administrator".
    echo.
)

pause
