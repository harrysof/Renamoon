@echo off
cd /d "%~dp0"
title WallpaperRenamer

:: Find a real Python (skip Microsoft Store stubs)
set PYTHON=

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe
    goto found
)
if exist "%LOCALAPPDATA%\Programs\Thonny\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Thonny\python.exe
    goto found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto found
)
if exist "C:\Python314\python.exe" set PYTHON=C:\Python314\python.exe && goto found
if exist "C:\Python312\python.exe" set PYTHON=C:\Python312\python.exe && goto found

where py >nul 2>&1
if %errorlevel%==0 (
    py -c "import sys; exit(0)" >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON=py
        goto found
    )
)

echo.
echo  ERROR: Python not found. Please run install_deps.bat first.
echo.
pause
exit /b 1

:found
"%PYTHON%" app.py
