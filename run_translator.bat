@echo off
cd /d "%~dp0"

set "VENV_DIR=venv"
set "SCRIPT_NAME=Lorebook Gemini Translator Dev.py"

where python >nul 2>nul
if errorlevel 1 (
    echo Error: Python not found in PATH. Please install Python 3.9+
    pause
    exit /b 1
)

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo.
    echo Activating environment for the first time to install bootstrap dependencies...
    call "%VENV_DIR%\Scripts\activate.bat"
    
    echo Installing core libraries (PySide6, requests)...
    python -m pip install --upgrade pip setuptools
    pip install PySide6 requests
    if errorlevel 1 (
        echo Core dependency installation failed. Check your internet connection.
        pause
        exit /b 1
    )
    
    echo Core libraries installed.
    call "%VENV_DIR%\Scripts\deactivate.bat"
)

if not exist "%SCRIPT_NAME%" (
    echo Downloading the application for the first time...
    set "SCRIPT_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/Lorebook%%20Gemini%%20Translator.py"
    curl -L -o "%SCRIPT_NAME%" "%SCRIPT_URL%"
    if errorlevel 1 (
        echo Failed to download the application. Check your internet connection.
        pause
        exit /b 1
    )
)

echo.
echo Launching the application...
call "%VENV_DIR%\Scripts\activate.bat"

echo -------------------------------------------------------------------
python "%SCRIPT_NAME%"
echo -------------------------------------------------------------------

call "%VENV_DIR%\Scripts\deactivate.bat"
pause