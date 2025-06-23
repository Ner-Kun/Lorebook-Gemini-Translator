@echo off
chcp 65001 > nul
SETLOCAL EnableDelayedExpansion

set "LAUNCHER_VERSION=2"
set "APP_NAME=Lorebook Gemini Translator"

set "PY_FILE_URL=https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/Lorebook_Gemini_Translator.py"

set "REQUIREMENTS=PySide6 google-genai google-api-core pyqtdarktheme-fork rich"

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
TITLE !APP_NAME! Launcher v%LAUNCHER_VERSION%

echo.!C_MAGENTA!===============================================================!C_RESET!
echo.!C_MAGENTA!=           !APP_NAME! Launcher v%LAUNCHER_VERSION%            =!C_RESET!
echo.!C_MAGENTA!===============================================================!C_RESET!
echo.


call :log_step "1/4" "Checking system dependencies..."
py -c "import sys; sys.exit(0) if sys.version_info >= (3, 9) else sys.exit(1)" >nul 2>nul
if errorlevel 1 (
    call :log_error "Python 3.9+ was not found or not in PATH." "Install from https://www.python.org/downloads/ and be sure to check 'Add Python to PATH' during setup."
    goto fatal_error
)
call :log_ok "Python found."

where curl >nul 2>nul
if errorlevel 1 (
    call :log_error "The 'curl' utility was not found." "It is required for downloading files and is included in Windows 10+."
    goto fatal_error
)
call :log_ok "curl utility found."
echo.

call :log_step "2/4" "Checking virtual environment..."

if not exist "%VENV_DIR%" (
    call :log_info "Environment not found. Creating a new one..." "(This is a one-time setup and may take a moment)"
    py -m venv "%VENV_DIR%" >nul
    if errorlevel 1 (
        call :log_error "Failed to create the virtual environment."
        goto fatal_error
    )
    call :log_ok "Virtual environment created successfully."
    
    echo.
    call :log_info "Upgrading pip to the latest version..."
    %PIP_IN_VENV% install --upgrade pip --quiet
    if errorlevel 1 (
        call :log_error "Failed to upgrade pip."
        goto fatal_error
    )
    call :log_ok "Pip has been updated."
    
    echo.
    call :log_info "Installing required libraries. This may take several minutes..."
    
    for %%p in (%REQUIREMENTS%) do (
        call :log_install_header "%%p"
        %PIP_IN_VENV% install "%%p"
        if errorlevel 1 (
            call :log_error "Failed to install the library '%%p'." "Please check your internet connection or try running as administrator."
            goto fatal_error
        )
    )
    
    call :log_ok "All libraries installed successfully."

) else (
    call :log_ok "Virtual environment found."
)
echo.

call :log_step "3/4" "Checking application files..."

if not exist "%BASE_DIR%Lorebook_Gemini_Translator.py" (
    call :log_info "Main script not found. Downloading..."
    curl --silent --show-error -A "Mozilla/5.0" -L -o "%BASE_DIR%Lorebook_Gemini_Translator.py" "%PY_FILE_URL%"
    if errorlevel 1 (
        call :log_error "Failed to download the main script. Please check your internet connection."
        goto fatal_error
    )
    call :log_ok "Main script downloaded successfully."
    echo.

    call :log_ok "Core application files downloaded."
) else (
    call :log_ok "Application files found."
)
echo.

call :log_step "4/4" "Starting the application..."
echo.
echo.!C_MAGENTA!===============================================================!C_RESET!
echo.

"%PYTHON_IN_VENV%" "%BASE_DIR%Lorebook_Gemini_Translator.py" %*

echo.
echo.!C_MAGENTA!===============================================================!C_RESET!
echo.
echo !C_GREEN!The application has been closed. You can now close this window.!C_RESET!
echo.
goto end_script


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
echo %C_CYAN%--- Installing %~1 ---%C_RESET%
goto :eof

:fatal_error
echo.
echo.!C_RED!===============================================================!C_RESET!
echo.!C_RED!=                 A critical error occurred.                  =!C_RESET!
echo.!C_RED!===============================================================!C_RESET!
echo.
echo !C_YELLOW!The launcher cannot continue. Please read the error message above.!C_RESET!
echo.
pause
exit /b 1

:end_script
pause
exit /b 0