@echo off
cd /d "%~dp0"
title WallpaperRenamer — Setup

echo.
echo  =========================================
echo   WallpaperRenamer — First Time Setup
echo  =========================================
echo.

:: Find a real Python (skip Microsoft Store stubs)
set PYTHON=

:: Check known real locations first
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
if exist "C:\Python314\python.exe" (
    set PYTHON=C:\Python314\python.exe
    goto found
)
if exist "C:\Python312\python.exe" (
    set PYTHON=C:\Python312\python.exe
    goto found
)

:: Try py launcher (usually reliable)
where py >nul 2>&1
if %errorlevel%==0 (
    py -c "import sys; exit(0)" >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON=py
        goto found
    )
)

echo  ERROR: Could not find a working Python installation.
echo  Install Python from https://python.org
echo  and check "Add Python to PATH" during install.
echo.
pause
exit /b 1

:found
echo  Using Python: %PYTHON%
echo.

echo  [1/3] Installing Pillow...
"%PYTHON%" -m pip install Pillow -q
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install Pillow.
    pause
    exit /b 1
)
echo       Done.

echo.
echo  [2/3] Installing llama-cpp-python (pre-built CPU wheel)...
"%PYTHON%" -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -q
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install llama-cpp-python.
    pause
    exit /b 1
)
echo       Done.

echo.
echo  [3/3] Installing EasyOCR...
"%PYTHON%" -m pip install easyocr -q
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install EasyOCR.
    pause
    exit /b 1
)
echo       Done.

echo.
echo  =========================================
echo   Setup complete! You can now run run.bat
echo  =========================================
echo.
pause
