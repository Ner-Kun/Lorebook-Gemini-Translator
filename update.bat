@echo off
chcp 65001 > nul
SETLOCAL EnableDelayedExpansion

set "APP_NAME=Lorebook Gemini Translator"
set "UPDATER_VERSION=0.1.0"

set "PY_FILE_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/Lorebook_Gemini_Translator.py"

set "LAUNCHER_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/run_translator.bat"

set "REQUIREMENTS=PySide6 google-genai google-api-core pyqtdarktheme-fork rich packaging"

set "OBSOLETE_PACKAGES=google.generativeai"

set "BASE_DIR=%~dp0"
set "VENV_DIR=%BASE_DIR%venv"
set "PYTHON_IN_VENV=%VENV_DIR%\Scripts\python.exe"
set "PIP_IN_VENV=%PYTHON_IN_VENV% -m pip"

for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "C_RESET=%ESC%[0m"
set "C_RED=%ESC%[91m"
set "C_GREEN=%ESC%[92m"
set "C_YELLOW=%ESC%[93m"
set "C_CYAN=%ESC%[96m"
set "C_MAGENTA=%ESC%[95m"

cls
TITLE !APP_NAME! Updater v%UPDATER_VERSION%

echo.!C_MAGENTA!===============================================================!C_RESET!
echo.!C_MAGENTA!=              !APP_NAME! Updater v%UPDATER_VERSION%          =!C_RESET!
echo.!C_MAGENTA!===============================================================!C_RESET!
echo.
echo !C_YELLOW!The update will begin in 3 seconds... Please do not close this window.!C_RESET!
timeout /t 3 > nul
echo.

call :log_step "1/4" "Checking for virtual environment..."
if not exist "%PYTHON_IN_VENV%" (
    call :log_error "Virtual environment not found at: %VENV_DIR%" "Please run the main launcher (run_translator.bat) first to create it."
    goto fatal_error
)
call :log_ok "Virtual environment found."
echo.


call :log_step "2/4" "Updating libraries..."

if defined OBSOLETE_PACKAGES (
    call :log_info "Cleaning up obsolete packages..."
    for %%p in (%OBSOLETE_PACKAGES%) do (
        %PIP_IN_VENV% show %%p >nul 2>nul
        if not errorlevel 1 (
            echo      - Removing '%%p'...
            %PIP_IN_VENV% uninstall -y %%p --quiet
        )
    )
    call :log_ok "Cleanup complete."
    echo.
)

call :log_info "Installing and updating core libraries..."
call :log_info "(This may take a few minutes)"

for %%p in (%REQUIREMENTS%) do (
    call :log_install_header "%%p"
    %PIP_IN_VENV% install --upgrade "%%p"
    if errorlevel 1 (
        call :log_error "Failed to update library '%%p'." "Please check your internet connection."
        goto fatal_error
    )
)
call :log_ok "All libraries are up-to-date."
echo.


call :log_step "3/4" "Updating application files..."

call :log_info "Backing up and downloading new 'Lorebook_Gemini_Translator.py'..."
ren "%BASE_DIR%Lorebook_Gemini_Translator.py" "Lorebook_Gemini_Translator.py.bak" >nul 2>nul
curl --silent --show-error -A "Mozilla/5.0" -L -o "%BASE_DIR%Lorebook_Gemini_Translator.py" "%PY_FILE_URL%"
if errorlevel 1 (
    call :log_error "Failed to download the main script." "Restoring from backup..."
    ren "%BASE_DIR%Lorebook_Gemini_Translator.py.bak" "Lorebook_Gemini_Translator.py" >nul 2>nul
    goto fatal_error
)
call :log_ok "Main script updated successfully."
echo.

call :log_info "Backing up and downloading new 'run_translator.bat'..."
ren "%BASE_DIR%run_translator.bat" "run_translator.bat.bak" >nul 2>nul
curl --silent --show-error -A "Mozilla/5.0" -L -o "%BASE_DIR%run_translator.bat" "%LAUNCHER_URL%"
if errorlevel 1 (
    call :log_error "Failed to update the launcher." "Restoring from backup..."
    ren "%BASE_DIR%run_translator.bat.bak" "run_translator.bat" >nul 2>nul
    goto fatal_error
)
call :log_ok "Launcher updated successfully."
echo.

del "%BASE_DIR%Lorebook Gemini Translator.py" 2>nul

call :log_step "4/4" "Finalizing update..."
call :log_info "Relaunching the application..."
echo.
echo.!C_MAGENTA!===============================================================!C_RESET!
echo.

start "Lorebook Gemini Translator" "%BASE_DIR%run_translator.bat"

(goto) 2>nul & del "%~f0"

exit /b 0

:log_step
echo %C_CYAN%[%~1] %~2%C_RESET%
goto :eof

:log_info
echo      %C_YELLOW%[INFO]%C_RESET% %~1
if not "%~2"=="" echo      %~2
goto :eof

:log_ok
echo      %C_GREEN%[OK]%C_RESET% %~1
goto :eof

:log_error
echo.
echo %C_RED%[ERROR] %~1%C_RESET%
if not "%~2"=="" echo         %~2
goto :eof

:log_install_header
echo.
echo %C_CYAN%--- Updating %~1 ---%C_RESET%
goto :eof

:fatal_error
echo.
echo.!C_RED!===============================================================!C_RESET!
echo.!C_RED!=                 A critical error occurred.                  =!C_RESET!
echo.!C_RED!===============================================================!C_RESET!
echo.
echo !C_YELLOW!The update cannot continue. Please read the error message above.!C_RESET!
echo.
pause
exit /b 1