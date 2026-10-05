@echo off
setlocal
cd /d "%~dp0"
if not exist "update_staged" exit /b 1
timeout /t 2 /nobreak >nul
xcopy /E /Y /I "update_staged\*" "." >nul
rmdir /S /Q "update_staged"
start "" "%~dp0SoulRunner.exe"
exit
