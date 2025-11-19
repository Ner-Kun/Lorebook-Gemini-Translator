@echo off
chcp 65001 > nul
SETLOCAL EnableDelayedExpansion

set "NEW_LAUNCHER_URL=https://raw.githubusercontent.com/Ner-Kun/omni-trans-core/main/run.bat"
set "RELEASES_URL=https://github.com/Ner-Kun/omni-trans-core/releases"
set "BACKUP_FOLDER=backup_version_0.1.0"
set "SETTINGS_FILE=translator_settings.json"

TITLE Lorebook Gemini Translator

:CHOICE_PROMPT
cls
echo.
echo ===================================================================
echo              !! IMPORTANT UPDATE TO VERSION 0.2.0 !!
echo ===================================================================
echo.
echo Hello! A new version of Lorebook Gemini Translator is available.
echo It has been completely rewritten on a new, more powerful
echo architecture called "Omni Trans".
echo.
echo What's new:
echo   - Ability to connect different providers (OpenAI, DeepSeek, etc.) as well as custom connections and local models (using Ollama or LM Studio).
echo   - Many other minor additions to the interface, some QOL improvements, I honestly don't remember them all, but there are many under the hood...
echo.
echo Before updating, please review the changes and the new structure.
echo You can read about it here:
echo.
echo   ==^> %RELEASES_URL% ^<==
echo.
echo -------------------------------------------------------------------
echo Note: The new launcher will try to run in Windows Terminal
echo for a better visual experience. If you have it installed,
echo this old console will flash for a moment and a new, modern
echo window will open. If not, the installation will continue here.
echo -------------------------------------------------------------------
echo.
echo.
echo WHAT SHOULD BE DONE WITH YOUR CURRENT VERSION (0.1.0)?
echo.
echo Your settings (%SETTINGS_FILE%) will be saved and
echo automatically migrated to the new version in any case.
echo.
echo   [1] ARCHIVE the old version.
echo       (Recommended. All old files, including venv, will be
echo        moved into the '%BACKUP_FOLDER%' directory. You can
echo        roll back if something goes wrong.)
echo.
echo   [2] DELETE the old version.
echo       (All old files, except for your settings, will be deleted
echo        to save space.)
echo.
echo   [3] Cancel. I'm not ready to update yet.
echo.

set "choice="
set /p choice="Please enter your choice (1, 2, or 3): "

if "%choice%"=="1" goto :ARCHIVE
if "%choice%"=="2" goto :DELETE
if "%choice%"=="3" goto :CANCEL

echo.
echo [ERROR] Invalid choice. Press any key to try again.
pause > nul
goto :CHOICE_PROMPT


:ARCHIVE
cls
echo.
echo [1] ARCHIVE option selected.
echo Creating a backup of the old version...
echo.
mkdir "%BACKUP_FOLDER%" > nul 2> nul

if exist "%SETTINGS_FILE%" (
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

echo.
echo Backup created in the '%BACKUP_FOLDER%' directory.
echo Settings have been preserved for migration.
echo.
pause
goto :START_MIGRATION


:DELETE
cls
echo.
echo [2] DELETE option selected.
echo Preparing for a clean installation...
echo.

if exist "%SETTINGS_FILE%" (
    echo   - Preserving settings file...
    mkdir "temp_settings" > nul 2> nul
    move "%SETTINGS_FILE%" "temp_settings\" > nul
)

echo   - Deleting old scripts and files...
del /q /f "Lorebook Gemini Translator.py" > nul 2> nul
del /q /f "Lorebook_Gemini_Translator.py" > nul 2> nul
del /q /f "run_translator.bat" > nul 2> nul
del /q /f "icon.ico" > nul 2> nul
del /q /f "version.txt" > nul 2> nul

echo   - Deleting the old virtual environment (this may take a moment)...
if exist "venv" (
    rmdir /s /q "venv"
)

if exist "temp_settings\%SETTINGS_FILE%" (
    echo   - Restoring settings file...
    move "temp_settings\%SETTINGS_FILE%" "." > nul
    rmdir "temp_settings"
)

echo.
echo Old version has been deleted. Settings have been preserved for migration.
echo.
pause
goto :START_MIGRATION


:START_MIGRATION
cls
echo.
echo ===================================================================
echo                      STARTING THE UPDATE PROCESS
echo ===================================================================
echo.
echo The new launcher will now be downloaded...
echo.
curl -L -o "run.bat" "%NEW_LAUNCHER_URL%"
if errorlevel 1 goto :DOWNLOAD_ERROR

echo.
echo Download completed successfully.
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !!                                                               !!
echo !!   This window will now close and a NEW one will open to       !!
echo !!   complete the installation. Please follow the instructions   !!
echo !!   in the new window.                                          !!
echo !!                                                               !!
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.
timeout /t 5 > nul

start "Omni Trans Launcher" "run.bat"

(goto) 2>nul & del "%~f0"

exit /b 0


:CANCEL
cls
echo.
echo Update cancelled as requested.
echo You can run the update later by launching 'run_translator.bat' again.
echo.
pause
exit /b 0


:DOWNLOAD_ERROR
cls
echo.
echo ===================================================================
echo                       !!! CRITICAL ERROR !!!
echo ===================================================================
echo.
echo Failed to download the new launcher.
echo Please check your internet connection.
echo.
echo No files have been changed. You can try again later.
echo.
pause
exit /b 1