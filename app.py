import logging
import base64
from PySide6 import QtWidgets, QtGui, QtCore
from logging import Logger
from omni_trans_core import settings
from omni_trans_core.localization_manager import loc_man, translate
from omni_trans_core.core import CoreApp
from omni_trans_core.prompt_formatter import DefaultPromptFormatter
from .data_handler import LorebookDataHandler
from .export_manager import export_lorebook
from .tabs.editor_tab import EditorTab
from .tabs.translation_tab import TranslationTab
from .constants import (
    APP_NAME,
    APP_VERSION,
    LOG_PREFIX,
    APP_VERSION_URL,
    SYSTEM_PROMPT,
    CONTEXT_INSTRUCTIONS,
    USER_PROMPT,
    REGEN_PROMPT,
)


logger: Logger = logging.getLogger(name=f"{LOG_PREFIX}_APP")


class LGTApp(CoreApp):

    ICON_BASE64_DATA = """"""

    def __init__(self) -> None:
        LGT_HEADERS: dict[str, dict[str, str]] = {
            "openrouter": {
                "HTTP-Referer": "https://github.com/Ner-Kun/Lorebook-Gemini-Translator",
                "X-Title": APP_NAME,
            }
        }
        settings.PROVIDER_CUSTOM_HEADERS.update(LGT_HEADERS)

        data_handler = LorebookDataHandler()
        prompt_formatter = DefaultPromptFormatter(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            regen_prompt=REGEN_PROMPT,
            context_instructions=CONTEXT_INSTRUCTIONS,
        )

        super().__init__(
            data_handler=data_handler,
            tabs=[],
            prompt_formatter=prompt_formatter,
            app_name=APP_NAME,
            app_version_url=APP_VERSION_URL,
            app_version=APP_VERSION,
        )

        self._setup_ui()
        self._connect_tab_signals()
        self._load_icon()
        self._show_wip_dialog()

    def _setup_ui(self) -> None:
        export_action = QtGui.QAction(self)
        loc_man.register(export_action, "text", "action.export")
        loc_man.register(export_action, "toolTip", "action.export.tooltip")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(lambda: export_lorebook(self))
        export_action.setEnabled(False)
        self.file_menu.insertAction(self.settings_action, export_action)
        self.data_handler.data_loaded.connect(lambda: export_action.setEnabled(True))

        self.editor_tab = EditorTab(main_window=self, data_handler=self.data_handler)
        self.translation_tab = TranslationTab(
            main_window=self, data_handler=self.data_handler
        )

        self.user_tabs.extend([self.editor_tab, self.translation_tab])
        self.load_user_tabs()
        self.tab_widget.setCurrentIndex(1)

    def _connect_tab_signals(self) -> None:
        self.editor_tab.search_term_changed.connect(
            self.translation_tab.table_widget.search_input.setText
        )
        self.translation_tab.table_widget.search_input.textChanged.connect(
            self.editor_tab.editor_search_input.setText
        )

    def _load_icon(self) -> None:
        if self.ICON_BASE64_DATA:
            try:
                icon_bytes = base64.b64decode(self.ICON_BASE64_DATA)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(icon_bytes)
                app_icon = QtGui.QIcon(pixmap)
                self.setWindowIcon(app_icon)
                logger.debug("Application icon set successfully from embedded data.")
            except Exception as e_icon:
                logger.error(
                    f"Failed to load application icon from embedded data: {e_icon}"
                )

    def _show_wip_dialog(self) -> None:
        if settings.current_settings.get("ux_show_wip_on_startup", False):
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle(translate("dialog.wip.title"))
            msg_box.setTextFormat(QtCore.Qt.RichText)
            msg_box.setText(translate("dialog.wip.text.startup"))
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            checkbox = QtWidgets.QCheckBox(
                translate("dialog.wip.checkbox_dont_show_again")
            )
            msg_box.setCheckBox(checkbox)
            msg_box.exec()
            if checkbox.isChecked():
                settings.current_settings["ux_show_wip_on_startup"] = False
                settings.save_settings()
