import sys
import os
import subprocess
import requests
import logging

APP_VERSION = "0.0.2"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger('Migration_Script')
logging.basicConfig(level="INFO", format='%(levelname)s: %(message)s')

def check_for_updates(force_update=False):
    UPDATER_URL = "https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/update.bat"

    try:
        update_reason = ""
        if force_update:
            update_reason = "Mandatory application structure upgrade detected."
        if update_reason:
            logger.info("="*60)
            logger.info("!! IMPORTANT MIGRATION !!")
            logger.info(update_reason)
            logger.info("Starting the new updater to finalize the transition...")
            logger.info("Please wait, a new window will open.")
            logger.info("="*60)
            
            updater_path = os.path.join(APP_DIR, "update.bat")
            try:
                update_response = requests.get(UPDATER_URL, timeout=10)
                update_response.raise_for_status()
                with open(updater_path, "wb") as f:
                    f.write(update_response.content)
            except Exception as e:
                logger.error(f"Failed to download the updater script: {e}")
                return

            subprocess.Popen(updater_path, shell=True)
            sys.exit(0)
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not check for updates (network error): {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the update check: {e}")

if __name__ == '__main__':
    check_for_updates(force_update=True)

    logger.info("\nMigration complete. This script will now exit.")
    input("Press Enter to close this window.")