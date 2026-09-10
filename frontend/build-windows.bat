@echo off
echo ================================================
echo    DataPOS - Ndertimi i Aplikacionit Windows
echo ================================================
echo.

echo [1/4] Duke instaluar varesit...
call yarn install
if errorlevel 1 (
    echo GABIM: Instalimi i varesive deshtoi!
    pause
    exit /b 1
)

echo.
echo [2/4] Duke ndertuar aplikacionin React...
call yarn build
if errorlevel 1 (
    echo GABIM: Ndertimi i React deshtoi!
    pause
    exit /b 1
)

echo.
echo [3/4] Duke kopjuar file-at e Electron...
copy /Y electron.js build\electron.js
copy /Y preload.js build\preload.js
copy /Y offline.html build\offline.html

echo.
echo [4/4] Duke krijuar file-in .exe...
call npx electron-builder --win

if errorlevel 1 (
    echo.
    echo GABIM: Ndertimi i Electron deshtoi!
    pause
    exit /b 1
)

echo.
echo ================================================
echo    SUKSES! Aplikacioni u krijua!
echo ================================================
echo.
echo File-i .exe ndodhet ne:
echo %cd%\dist\DataPOS Setup 1.0.0.exe
echo.
echo Hapni folder-in dist per ta gjetur.
echo.
pause
