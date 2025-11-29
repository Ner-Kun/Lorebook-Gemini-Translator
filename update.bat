@echo off
chcp 65001 > nul
SETLOCAL EnableDelayedExpansion

set "NEW_BAT_URL=https://raw.githubusercontent.com/Ner-Kun/omni-trans-core/main/run.bat"
set "NEW_PS1_URL=https://raw.githubusercontent.com/Ner-Kun/omni-trans-core/main/run.ps1"
set "RELEASES_URL=https://github.com/Ner-Kun/omni-trans-core/releases"
set "BACKUP_FOLDER=backup_version_0.1.0"
set "SETTINGS_FILE=translator_settings.json"

TITLE Lorebook Gemini Translator - Migration Assistant

:CHOICE_PROMPT
cls
echo ===================================================================
echo              !! IMPORTANT UPDATE TO VERSION 0.2.0 !!
echo ===================================================================
echo Hello! A new version of Lorebook Gemini Translator is available.
echo It has been completely rewritten on a new, more powerful
echo architecture called "Omni Trans".
echo.
echo Before updating, please review the changes and the new structure.
if defined RELEASES_URL (
    echo You can read about it here:
    echo   ==^> %RELEASES_URL% ^<==
) else (
    echo Release URL information is temporarily unavailable.
)
echo.
echo Note: The new launcher will try to run in Windows Terminal
echo for a better visual experience. If you have it installed,
echo this old console will flash for a moment and a new, modern
echo window will open. If not, the installation will continue here.
echo.
echo WHAT SHOULD BE DONE WITH YOUR CURRENT VERSION (0.1.0)?
echo Your settings (%SETTINGS_FILE%) will be saved and
echo automatically migrated to the new version in any case.
echo   [1] ARCHIVE the old version.
echo       (Recommended. All old files, including venv, will be
echo        moved into the '%BACKUP_FOLDER%' directory. You can
echo        roll back if something goes wrong.)
echo   [2] DELETE the old version.
echo       (All old files, except for your settings, will be deleted
echo        to save space.)
echo   [3] Cancel. I'm not ready to update yet.
set /p "choice=Please enter your choice (1, 2, or 3): "
if "%choice%"=="1" goto :ARCHIVE
if "%choice%"=="2" goto :DELETE
if "%choice%"=="3" goto :CANCEL
echo [ERROR] Invalid choice. Press any key to try again.
pause > nul
goto :CHOICE_PROMPT

:ARCHIVE
cls
echo [1] ARCHIVE option selected.
echo Creating a backup of the old version...
mkdir "%BACKUP_FOLDER%" > nul 2> nul
if exist "%SETTINGS_FILE%" (
    echo   - Preserving settings file...
    copy "%SETTINGS_FILE%" "%BACKUP_FOLDER%\" > nul
)
echo   - Moving scripts...
move "Lorebook Gemini Translator.py" "%BACKUP_FOLDER%\" > nul 2> nul
move "Lorebook_Gemini_Translator.py" "%BACKUP_FOLDER%\" > nul 2> nul
move "run_translator.bat" "%BACKUP_FOLDER%\" > nul 2> nul
echo   - Moving the old virtual environment (this may take a moment)...
if exist "venv" (
    move "venv" "%BACKUP_FOLDER%\" > nul 2> nul
)
echo Backup created in the '%BACKUP_FOLDER%' directory.
echo Settings have been preserved for migration.
pause
goto :START_MIGRATION

:DELETE
cls
echo [2] DELETE option selected.
echo Preparing for a clean installation...
if exist "%SETTINGS_FILE%" (
    echo   - Preserving settings file...
    mkdir "temp_settings" > nul 2> nul
    move "%SETTINGS_FILE%" "temp_settings\" > nul
)
echo   - Deleting old scripts and files...
del /q /f "Lorebook Gemini Translator.py" > nul 2> nul
del /q /f "Lorebook_Gemini_Translator.py" > nul 2> nul
del /q /f "run_translator.bat" > nul 2> nul
echo   - Deleting the old virtual environment (this may take a moment)...
if exist "venv" (
    rmdir /s /q "venv" > nul
)
if exist "temp_settings\%SETTINGS_FILE%" (
    echo   - Restoring settings file...
    move "temp_settings\%SETTINGS_FILE%" "." > nul
    rmdir "temp_settings" > nul
)
echo Old version has been deleted. Settings have been preserved for migration.
pause
goto :START_MIGRATION

:START_MIGRATION
cls
echo ===================================================================
echo                      STARTING THE UPDATE PROCESS
echo ===================================================================
echo The new launcher will now be downloaded...

where curl >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: curl command not found. Please install curl or ensure it's in PATH.
    pause
    exit /b 1
)

echo   - Downloading run.bat...
curl -L -o "run.bat.temp" "%NEW_BAT_URL%"
if errorlevel 1 (
    echo [ERROR] Failed to download run.bat
    del "run.bat.temp" > nul 2>&1
    goto :DOWNLOAD_ERROR
)

echo   - Downloading run.ps1...
curl -L -o "run.ps1.temp" "%NEW_PS1_URL%"
if errorlevel 1 (
    echo [ERROR] Failed to download run.ps1
    del "run.ps1.temp" > nul 2>&1
    goto :DOWNLOAD_ERROR
)

if not exist "run.bat.temp" (
    echo [ERROR] run.bat.temp was not created
    goto :DOWNLOAD_ERROR
)
if not exist "run.ps1.temp" (
    echo [ERROR] run.ps1.temp was not created
    goto :DOWNLOAD_ERROR
)

move /y "run.bat.temp" "run.bat" > nul
move /y "run.ps1.temp" "run.ps1" > nul

echo Download completed successfully.
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !!                                                               !!
echo !!   This window will now close and a NEW one will open to       !!
echo !!   complete the installation. Please follow the instructions   !!
echo !!   in the new window.                                          !!
echo !!                                                               !!
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
timeout /t 3 > nul

start "Omni Trans Launcher" cmd.exe /c "call run.bat & timeout /t 2 > nul & del \"%~f0\" > nul 2>&1"
exit

:CANCEL
cls
echo Update cancelled as requested.
echo You can run the update later by launching 'run_translator.bat' again.
pause
exit /b 0

:DOWNLOAD_ERROR
cls
echo ===================================================================
echo                       !!! CRITICAL ERROR !!!
echo ===================================================================
echo Failed to download the new launcher files.
echo Please check your internet connection.
echo No files have been changed. You can try again later.
pause
exit /b 1