@echo off
:: SYNC.bat — Double-click to push all changes to GitHub → Vercel
:: No Python needed. Uses PowerShell (built into Windows).
powershell -ExecutionPolicy Bypass -File "%~dp0SYNC.ps1"
