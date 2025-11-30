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

    ICON_BASE64_DATA = """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"""

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
