import os
import sys
import logging
import qdarktheme
from PySide6 import QtWidgets
from rich.traceback import install as install_rich_tracebacks
from omni_trans_core import settings
from omni_trans_core.localization_manager import loc_man
from omni_trans_core.utils import ui_loader_manager
from omni_trans_core.logger import LoggerManager
from lgt_app.app import LGTApp
from pathlib import Path


def main() -> None:
    _ = install_rich_tracebacks(show_locals=True)

    project_root = str(Path(__file__).parent.parent.resolve())

    sys.path.insert(0, project_root)

    settings.initialize_app_paths(project_root_path=project_root)
    settings.load_settings()

    logger_manager = LoggerManager(settings.current_settings)
    logger_manager.configure_logging()
    logger = logging.getLogger(f"{settings.LOG_PREFIX}_RUN")

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    assert isinstance(app, QtWidgets.QApplication)

    app_i18n_path = Path(__file__).parent / "i18n_app"
    if app_i18n_path.is_dir():
        loc_man.add_translation_directory(str(app_i18n_path))
        loc_man.set_language(loc_man._current_language)

    try:
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
        logger.debug("Applied qdarktheme (dark).")
        custom_stylesheet = """
            QToolTip { color: #e0e0e0; background-color: #3c3c3c; border: 1px solid #555555; padding: 5px; border-radius: 4px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding-left: 10px; padding-right: 10px; }
        """
        app.setStyleSheet(app.styleSheet() + custom_stylesheet)
        logger.debug("Applied custom stylesheets.")
    except Exception as e_theme:
        logger.warning(
            f"pyqtdarktheme not found or failed: {e_theme}. Using default OS theme."
        )

    main_window = LGTApp()
    main_window.showMaximized()
    ui_loader_manager.log_summary()
    main_window.log_initialization_complete()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
