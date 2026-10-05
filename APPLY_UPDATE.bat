@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LOG=%~dp0update.log"
echo [%date% %time%] SoulRunner update started>"%LOG%"

if not exist "update_staged\SoulRunner.exe" (
  echo [%date% %time%] ERROR: staged SoulRunner.exe missing>>"%LOG%"
  exit /b 1
)

rem Preserve the user's proven recorded route. Releases must never replace it.
if exist "town_route.json" copy /Y "town_route.json" "%TEMP%\SoulRunner-town_route.json" >nul
if exist "config.json" copy /Y "config.json" "%TEMP%\SoulRunner-config.json" >nul

rem The launcher has requested shutdown. Wait until Windows releases SoulRunner.exe.
set /a tries=0
:wait_for_exit
set /a tries+=1
2>nul (>>"SoulRunner.exe" echo.) && goto unlocked
if %tries% GEQ 30 goto locked_error
timeout /t 1 /nobreak >nul
goto wait_for_exit

:unlocked
echo [%date% %time%] Executable unlocked; installing update>>"%LOG%"
copy /Y "update_staged\SoulRunner.exe" "SoulRunner.exe" >>"%LOG%" 2>&1
if errorlevel 1 goto copy_error

rem Copy any additional update files, but restore user-owned route/config afterward.
for /R "update_staged" %%F in (*) do (
  if /I not "%%~nxF"=="SoulRunner.exe" (
    set "REL=%%F"
  )
)
xcopy /E /Y /I "update_staged\*" "." >>"%LOG%" 2>&1
if errorlevel 1 goto copy_error

if exist "%TEMP%\SoulRunner-town_route.json" (
  copy /Y "%TEMP%\SoulRunner-town_route.json" "town_route.json" >nul
  del /Q "%TEMP%\SoulRunner-town_route.json" >nul 2>&1
)
if exist "%TEMP%\SoulRunner-config.json" (
  copy /Y "%TEMP%\SoulRunner-config.json" "config.json" >nul
  del /Q "%TEMP%\SoulRunner-config.json" >nul 2>&1
)

rmdir /S /Q "update_staged"
echo [%date% %time%] Update completed successfully>>"%LOG%"
start "" "%~dp0SoulRunner.exe" --updated
exit /b 0

:locked_error
echo [%date% %time%] ERROR: SoulRunner.exe remained locked for 30 seconds>>"%LOG%"
start "SoulRunner Update Error" notepad.exe "%LOG%"
exit /b 2

:copy_error
echo [%date% %time%] ERROR: Could not replace SoulRunner files>>"%LOG%"
start "SoulRunner Update Error" notepad.exe "%LOG%"
exit /b 3
