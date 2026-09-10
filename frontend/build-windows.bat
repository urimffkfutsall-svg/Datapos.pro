@echo off
REM ==========================================================
REM  DataPOS - Ndertimi i setup.exe per Windows (build i paster)
REM ==========================================================
setlocal
cd /d "%~dp0"

echo.
echo [1/5] Mbyllja e proceseve DataPOS / electron qe bllokojne skedaret...
taskkill /F /IM DataPOS.exe /T >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
taskkill /F /IM app-builder.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Fshirja e dosjes dist...
if exist dist (
  rmdir /s /q dist
)
if exist dist (
  echo.
  echo GABIM: dosja "dist" nuk mund te fshihet - eshte ende e hapur.
  echo   - Mbyll aplikacionin DataPOS nese eshte i hapur
  echo   - Mbyll dritaret e File Explorer brenda dosjes dist
  echo   - Ose rinis kompjuterin dhe provo perseri
  pause
  exit /b 1
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
call npx electron-builder --win nsis --x64
if errorlevel 1 goto :error

echo.
echo ==========================================================
echo  GATI! Instaluesi ndodhet ne:  dist\DataPOS-Setup-1.0.0.exe
echo ==========================================================
explorer dist
pause
exit /b 0

:error
echo.
echo GABIM gjate ndertimit. Shiko mesazhet me lart.
pause
exit /b 1
