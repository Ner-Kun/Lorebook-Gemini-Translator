import logging
from PySide6 import QtWidgets, QtCore
from omni_trans_core.ui.dialogs import AnimatedDialog
from omni_trans_core.localization_manager import loc_man, translate
from omni_trans_core import settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni_trans_core.core import CoreApp

logger = logging.getLogger(f"{settings.LOG_PREFIX}_APP_UI.dialogs")

class ExportSettingsDialog(AnimatedDialog):
    def __init__(self, main_window: "CoreApp", default_lore_name: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.all_entries = (
            self.main_window.data_handler.data.get("entries", {})
            if self.main_window.data_handler.data
            else {})
        self.src_lang = settings.current_settings.get("selected_source_language", "")
        self.available_target_langs = settings.current_settings.get( "target_languages", [] )
        self.current_selected_target_lang = settings.current_settings.get( "selected_target_language", "" )
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.setMinimumSize(500, 500)
        main_layout = QtWidgets.QVBoxLayout(self)
        name_group_box = QtWidgets.QGroupBox()
        name_layout = QtWidgets.QHBoxLayout(name_group_box)
        self.loreNameEdit = QtWidgets.QLineEdit(default_lore_name)
        name_layout.addWidget(self.loreNameEdit)
        main_layout.addWidget(name_group_box)
        lang_group_box = QtWidgets.QGroupBox()
        lang_group_box_layout = QtWidgets.QVBoxLayout(lang_group_box)
        lang_scroll_area = QtWidgets.QScrollArea()
        lang_scroll_area.setWidgetResizable(True)
        lang_scroll_area.setMinimumHeight(150)
        lang_widget_container = QtWidgets.QWidget()
        self.lang_grid_layout = QtWidgets.QGridLayout(lang_widget_container)
        lang_scroll_area.setWidget(lang_widget_container)
        lang_group_box_layout.addWidget(lang_scroll_area)
        main_layout.addWidget(lang_group_box)
        self.lang_checkboxes = {}
        if not self.available_target_langs:
            no_langs_label = QtWidgets.QLabel()
            loc_man.register(no_langs_label, "text", "dialog.export.no_languages")
            no_langs_label.setStyleSheet("color: orange;")
            self.lang_grid_layout.addWidget(no_langs_label, 0, 0)
        else:
            select_buttons_layout = QtWidgets.QHBoxLayout()
            select_all_button = QtWidgets.QPushButton()
            deselect_all_button = QtWidgets.QPushButton()
            select_buttons_layout.addWidget(select_all_button)
            select_buttons_layout.addWidget(deselect_all_button)
            select_buttons_layout.addStretch()
            self.lang_grid_layout.addLayout(select_buttons_layout, 0, 0, 1, 2)
            sorted_langs = sorted(self.available_target_langs)
            row, col = 1, 0
            for lang_name in sorted_langs:
                checkbox = QtWidgets.QCheckBox(lang_name)
                if lang_name == self.current_selected_target_lang:
                    checkbox.setChecked(True)
                self.lang_checkboxes[lang_name] = checkbox
                self.lang_grid_layout.addWidget(checkbox, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1
            self.lang_grid_layout.setRowStretch(row + 1, 1)
            loc_man.register(select_all_button, "text", "dialog.export.select_all")
            select_all_button.clicked.connect(self.select_all_langs)
            loc_man.register(deselect_all_button, "text", "dialog.export.deselect_all")
            deselect_all_button.clicked.connect(self.deselect_all_langs)
        options_group = QtWidgets.QGroupBox()
        options_layout = QtWidgets.QVBoxLayout(options_group)
        self.includeOriginalsCheck = QtWidgets.QCheckBox()
        self.includeOriginalsCheck.setChecked(True)
        options_layout.addWidget(self.includeOriginalsCheck)
        missing_trans_group = QtWidgets.QGroupBox()
        missing_trans_layout = QtWidgets.QVBoxLayout(missing_trans_group)
        self.leaveOriginalRadio = QtWidgets.QRadioButton()
        self.leaveOriginalRadio.setChecked(True)
        self.skipKeyRadio = QtWidgets.QRadioButton()
        missing_trans_layout.addWidget(self.leaveOriginalRadio)
        missing_trans_layout.addWidget(self.skipKeyRadio)
        options_layout.addWidget(missing_trans_group)
        main_layout.addWidget(options_group)
        stats_group = QtWidgets.QGroupBox()
        stats_layout = QtWidgets.QVBoxLayout(stats_group)
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        main_layout.addWidget(stats_group, stretch=1)
        self.buttonBox = QtWidgets.QDialogButtonBox( QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)
        for checkbox in self.lang_checkboxes.values():
            checkbox.stateChanged.connect(self.update_stats)
        self.includeOriginalsCheck.stateChanged.connect(self.update_stats)
        self.leaveOriginalRadio.toggled.connect(self.update_stats)
        self.retranslate_ui()
        self.update_stats()

    def retranslate_ui(self):
        loc_man.register(self, "windowTitle", "dialog.export.title")
        self.findChild(QtWidgets.QGroupBox).setTitle( translate("dialog.export.group.name"))
        self.findChildren(QtWidgets.QGroupBox)[1].setTitle( translate("dialog.export.group.languages"))
        self.findChildren(QtWidgets.QGroupBox)[2].setTitle( translate("dialog.export.group.options"))
        loc_man.register( self.includeOriginalsCheck, "text", "dialog.export.check.include_originals")
        loc_man.register( self.includeOriginalsCheck, "toolTip", "dialog.export.check.include_originals.tooltip",)
        self.findChildren(QtWidgets.QGroupBox)[3].setTitle( translate("dialog.export.group.missing_translation"))
        loc_man.register( self.leaveOriginalRadio, "text", "dialog.export.radio.leave_original")
        loc_man.register(self.skipKeyRadio, "text", "dialog.export.radio.skip_key")
        self.findChildren(QtWidgets.QGroupBox)[4].setTitle( translate("dialog.export.group.stats"))
        self.update_stats()

    def update_stats(self):
        self.stats_label.setText(translate("dialog.export.stats.calculating"))
        total_entries = len(self.all_entries)
        _, selected_languages, _, _ = self.get_export_settings()
        total_original_keys = sum(
            len(entry.get("key", [])) for entry in self.all_entries.values())
        if not selected_languages:
            stats_text = translate(
                "dialog.export.stats.no_languages_selected",
                num_entries=total_entries,
                num_keys=total_original_keys,)
            self.stats_label.setText(stats_text)
            return
        translations_found_per_lang = {lang: 0 for lang in selected_languages}
        for entry in self.all_entries.values():
            original_keys = entry.get("key", [])
            if not original_keys:
                continue
            for key_text in original_keys:
                for lang in selected_languages:
                    if self.main_window.cache_manager.get_from_cache( key_text, self.src_lang, lang ):
                        translations_found_per_lang[lang] += 1
        total_translations_found = sum(translations_found_per_lang.values())
        stats_text = translate(
            "dialog.export.stats.template",
            num_entries=total_entries,
            num_translations=total_translations_found,)
        warnings = []
        for lang, found_count in translations_found_per_lang.items():
            missing_count = total_original_keys - found_count
            if missing_count > 0:
                warnings.append(
                    translate(
                        "dialog.export.stats.warning_template",
                        num_missing=missing_count,
                        lang_name=lang,
                    )
                )
        if warnings:
            stats_text += (
                f"\n\n{translate('dialog.export.stats.warnings_header')}\n"
                + "\n".join(warnings))
        self.stats_label.setText(stats_text)

    def select_all_langs(self):
        for checkbox in self.lang_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_langs(self):
        for checkbox in self.lang_checkboxes.values():
            checkbox.setChecked(False)

    def accept_settings(self):
        if self.lang_checkboxes and not any( cb.isChecked() for cb in self.lang_checkboxes.values() ):
            reply = QtWidgets.QMessageBox.question(
                self,
                translate("dialog.export.prompt.no_languages_selected.title"),
                translate("dialog.export.prompt.no_languages_selected.text"),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
        self.accept()

    def get_export_settings(self):
        lore_name = self.loreNameEdit.text().strip()
        selected_target_languages = [
            lang for lang, cb in self.lang_checkboxes.items() if cb.isChecked()]
        include_originals = self.includeOriginalsCheck.isChecked()
        missing_translation_rule = (
            "leave" if self.leaveOriginalRadio.isChecked() else "skip")
        return (
            lore_name,
            selected_target_languages,
            include_originals,
            missing_translation_rule,)
