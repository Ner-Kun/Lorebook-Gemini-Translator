@echo off
cd /d "%~dp0"

set "SCRIPT_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/main/Lorebook%%20Gemini%%20Translator.py"
set "ICON_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/main/icon.ico"
set "SCRIPT_NAME=Lorebook Gemini Translator.py"
set "ICON_NAME=icon.ico"

where python >nul 2>nul
if errorlevel 1 (
    echo Error: Python not found in PATH. Please install Python 3.9+ or add python.exe to your PATH.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Check write permissions in "%~dp0".
        pause
        exit /b 1
    )
    echo Virtual environment created.

    echo Activating virtual environment and installing dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install PySide6 google-generativeai pyqtdarktheme-fork
    if errorlevel 1 (
        echo Dependency installation failed. Check network connection and PyPI access.
        pause
        exit /b 1
    )
    echo Dependencies installed.
    call venv\Scripts\deactivate.bat
) else (
    echo Virtual environment already exists. Skipping creation.
)

echo Downloading the latest version...
curl -L -o "%SCRIPT_NAME%" "%SCRIPT_URL%"
curl -L -o "%ICON_NAME%" "%ICON_URL%" 2>nul
if errorlevel 1 (
    echo Failed to download %SCRIPT_NAME%. Check URL: %SCRIPT_URL% and internet connection.
    pause
    exit /b 1
)
echo %SCRIPT_NAME% downloaded successfully.


echo Activating virtual environment and launching the application...
call venv\Scripts\activate.bat


echo -------------------------------------------------------------------
echo RUNNING: python "%~dp0%SCRIPT_NAME%"
echo -------------------------------------------------------------------

python "%~dp0%SCRIPT_NAME%"
echo Return code: %errorlevel%

call venv\Scripts\deactivate.bat
pause
