@echo off
REM ==========================================================
REM  DataPOS - Ndertimi i setup.exe per Windows
REM  Dalja: release\DataPOS-Setup-1.0.0.exe
REM ==========================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo [1/5] Mbyllja e proceseve qe bllokojne skedaret...
taskkill /F /IM DataPOS.exe /T >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
taskkill /F /IM app-builder.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Pastrimi i dosjeve te vjetra te daljes...
if exist dist rmdir /s /q dist >nul 2>&1
if exist release rmdir /s /q release >nul 2>&1
REM Nese dosja e vjeter "dist" mbetet e bllokuar, nuk ka problem:
REM ndertimi i ri perdor dosjen "release".
if exist release (
  echo   Paralajmerim: dosja "release" nuk u fshi dot plotesisht.
  set STAMP=%RANDOM%
  echo   Do te perdoret dosja alternative: release-!STAMP!
  set OUTDIR=release-!STAMP!
) else (
  set OUTDIR=release
)

echo.
echo [3/5] Instalimi i vareseve...
call yarn install
if errorlevel 1 goto :error

echo.
echo [4/5] Ndertimi i aplikacionit React...
call yarn build
if errorlevel 1 goto :error

echo.
echo [5/5] Krijimi i instaluesit (setup.exe)...
call npx electron-builder --win nsis --x64 -c.directories.output=!OUTDIR!
if errorlevel 1 goto :error

echo.
echo ==========================================================
echo  GATI! Instaluesi:  !OUTDIR!\DataPOS-Setup-1.0.0.exe
echo ==========================================================
explorer !OUTDIR!
pause
exit /b 0

:error
echo.
echo GABIM gjate ndertimit. Shiko mesazhet me lart.
pause
exit /b 1
