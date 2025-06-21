@echo off
SETLOCAL EnableDelayedExpansion
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

TITLE Lorebook Gemini Translator Updater

echo ===============================================================
echo =           Lorebook Gemini Translator Updater                =
echo ===============================================================
echo.

set "BASE_DIR=%~dp0"
set "VENV_PY=%BASE_DIR%venv\Scripts\python.exe"
set "PIP=%VENV_PY% -m pip"

set "PY_FILE_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/Lorebook_Gemini_Translator.py"
set "REQUIREMENTS_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/requirements.txt"
set "LAUNCHER_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/run_translator.bat"

set "DEL_LIST=google.generativeai"

echo Starting update... Please wait. This window will close automatically.
timeout /t 3 > nul

echo.
echo [1/4] Verifying environment...
%PIP% --version | findstr /I "venv" >nul
if errorlevel 1 (
    echo ERROR: pip command does not point to the local 'venv'. Update cancelled.
    pause
    exit /b
)
echo      ... Environment OK.
echo.
echo [2/4] Cleaning up obsolete packages...
FOR %%p IN (%DEL_LIST%) DO (
    %PIP% show %%p >nul 2>nul
    if not errorlevel 1 (
        echo      - Removing obsolete package: %%p...
        %PIP% uninstall -y %%p >nul
    )
)
echo      ... Cleanup complete.
echo.
echo [3/4] Updating libraries...
echo      - Downloading new library requirements...
curl -A "Mozilla/5.0" -L -o "requirements.new.txt" "%REQUIREMENTS_URL%" >nul 2>nul
IF errorlevel 1 (
    echo ERROR: Failed to download requirements.txt. Aborting.
    pause
    exit /b
)
echo      - Installing/Updating all required libraries...
%PIP% install -r requirements.new.txt --upgrade --quiet
if errorlevel 1 (
    echo ERROR: Failed to install libraries. Update failed.
    pause
    exit /b
)
del "requirements.new.txt"
echo      ... Libraries are now up-to-date.
echo.
echo [4/4] Updating application files and restarting...
ren "Lorebook_Gemini_Translator.py" "Lorebook_Gemini_Translator.py.bak" >nul 2>nul
curl -A "Mozilla/5.0" -L -o "Lorebook_Gemini_Translator.py" "%PY_FILE_URL%" >nul 2>nul
ren "run_translator.bat" "run_translator.bat.bak" >nul 2>nul
curl -A "Mozilla/5.0" -L -o "run_translator.bat" "%LAUNCHER_URL%" >nul 2>nul
echo.
echo Relaunching application...
if exist "run_translator.bat" (
    start "" "run_translator.bat"
) else (
    echo ERROR: Launcher not found. Please run manually.
    pause
)

DEL "%~f0"