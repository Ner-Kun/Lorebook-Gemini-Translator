@echo off
chcp 65001 > nul
SETLOCAL EnableDelayedExpansion
set "LAUNCHER_VERSION=2"

set "PY_FILE_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/Lorebook_Gemini_Translator.py"
set "ICON_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/icon.ico"
set "REQUIREMENTS_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/requirements.txt"

set "BASE_DIR=%~dp0"
set "VENV_DIR=%BASE_DIR%venv"
set "PYTHON_IN_VENV=%VENV_DIR%\Scripts\python.exe"

TITLE Lorebook Gemini Translator Launcher v%LAUNCHER_VERSION%

echo ===============================================================
echo =           Lorebook Gemini Translator Launcher               =
echo ===============================================================
echo.

echo [1/4] Checking for Python 3.9+...
py -c "import sys; sys.exit(0) if sys.version_info >= (3, 9) else sys.exit(1)" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.9 or higher is not installed or not found in PATH.
    echo Please install it from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo      ... System Python found.

if not exist "%VENV_DIR%" (
    echo [2/4] Virtual environment not found. Creating it now...
    echo      (This is a one-time setup and may take a moment.)
    py -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
    echo      ... Virtual environment created.
    
    set "PIP=%PYTHON_IN_VENV% -m pip"
    
    echo      ... Downloading library requirements...
    curl -A "Mozilla/5.0" -L -o "%BASE_DIR%requirements.txt" "%REQUIREMENTS_URL%"
    if errorlevel 1 (
        echo ERROR: Failed to download requirements.txt. Please check your internet connection.
        pause
        exit /b 1
    )

    echo      ... Installing all libraries. This may take several minutes...
    %PIP% install -r "%BASE_DIR%requirements.txt" --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install required libraries from requirements.txt.
        pause
        exit /b 1
    )
    del "%BASE_DIR%requirements.txt"
    echo      ... Library installation complete.
) else (
    echo [2/4] Virtual environment found.
)

if not exist "%BASE_DIR%Lorebook_Gemini_Translator.py" (
    echo [3/4] Main script not found. Downloading for first-time setup...
    
    curl -A "Mozilla/5.0" -L -o "%BASE_DIR%Lorebook_Gemini_Translator.py" "%PY_FILE_URL%"
    if errorlevel 1 (
        echo ERROR: Failed to download the main script. Please check your internet connection.
        pause
        exit /b 1
    )

    curl -A "Mozilla/5.0" -L -o "%BASE_DIR%icon.ico" "%ICON_URL%" >nul 2>nul
    
    echo      ... Core files downloaded.
) else (
    echo [3/4] Main application script found.
)

echo [4/4] Starting the application...
echo.
echo ===============================================================
echo.

"%PYTHON_IN_VENV%" "%BASE_DIR%Lorebook_Gemini_Translator.py" %*

echo.
echo ===============================================================
echo The application has closed. This window can be closed now.
echo.
pause