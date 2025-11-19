import logging
from PySide6 import QtWidgets, QtCore
from omni_trans_core.interfaces import (
    AbstractTab,
    TranslatableItem,
    IControlWidgetActions,
)
from omni_trans_core.ui.widgets import (
    RPMStatusWidget,
    GenerationParamsWidget,
    SourceLanguageWidget,
    TargetLanguageWidget,
    DataTableWidget,
    ConnectionSelectionWidget,
    TranslationControlWidget,
)
from omni_trans_core import constants as const
from omni_trans_core import settings
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from omni_trans_core.core import CoreApp
    from ..data_handler import LorebookDataHandler

logger = logging.getLogger(f'{settings.LOG_PREFIX}_APP.translation_tab')

class TranslationTab(AbstractTab, IControlWidgetActions):
    TAB_NAME = "Translation"
    translation_requested = QtCore.Signal(list, bool)
    generation_params_updated = QtCore.Signal(str, dict)
    data_availability_changed = QtCore.Signal(bool)

    def __init__(self, main_window: "CoreApp", data_handler: "LorebookDataHandler"):
        super().__init__(main_window)
        self.main_window = main_window
        self.data_handler = data_handler
        self.table_data = []
        self.data_availability_changed.emit(False)
        self.init_ui()
        self._connect_signals()
        self.connection_widget.update_connections()
    
    def init_ui(self):
        translation_layout = QtWidgets.QVBoxLayout(self)
        language_panel_layout = QtWidgets.QHBoxLayout()
        self.source_lang_widget = SourceLanguageWidget()
        self.target_lang_widget = TargetLanguageWidget()
        language_panel_layout.addWidget(self.source_lang_widget, stretch=1)
        language_panel_layout.addWidget(self.target_lang_widget, stretch=1)
        translation_layout.addLayout(language_panel_layout)
        middle_v_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        middle_v_splitter.setOpaqueResize(False)
        top_middle_h_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top_middle_h_splitter.setOpaqueResize(False)
        self.table_widget = DataTableWidget()
        self.table = self.table_widget.table
        columns = [
            {
                "key": "uid",
                "header": "UID",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
            },
            {
                "key": "key",
                "header": "Original Key",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
            },
            {
                "key": "translation",
                "header": "Translated",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
            },
            {
                "key": "content_preview",
                "header": "Content Preview",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.Stretch,
            },
        ]
        self.table_widget.configure(columns)
        self.table.verticalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        top_middle_h_splitter.addWidget(self.table_widget)
        right_panel_widget = QtWidgets.QWidget()
        right_panel_layout = QtWidgets.QVBoxLayout(right_panel_widget)
        self.control_panel = TranslationControlWidget(actions_handler=self)
        right_panel_layout.addWidget(self.control_panel)
        self.connection_widget = ConnectionSelectionWidget(self.main_window)
        right_panel_layout.addWidget(self.connection_widget)
        self.gen_params_widget = GenerationParamsWidget()
        right_panel_layout.addWidget(self.gen_params_widget)
        self.rpm_status_widget = RPMStatusWidget(self)
        right_panel_layout.addWidget(self.rpm_status_widget)
        right_panel_layout.addStretch()
        top_middle_h_splitter.addWidget(right_panel_widget)
        top_middle_h_splitter.setStretchFactor(0, 2)
        top_middle_h_splitter.setStretchFactor(1, 1)
        middle_v_splitter.addWidget(top_middle_h_splitter)
        content_display_group = QtWidgets.QGroupBox("Full Content of LORE Entry")
        content_display_layout = QtWidgets.QVBoxLayout(content_display_group)
        self.full_content_display = QtWidgets.QTextEdit()
        self.full_content_display.setReadOnly(True)
        content_display_layout.addWidget(self.full_content_display)
        middle_v_splitter.addWidget(content_display_group)
        translation_layout.addWidget(middle_v_splitter, stretch=1)

    def _connect_signals(self):
        self.main_window.translation_manager.rpm_status_updated.connect(
            self.rpm_status_widget.update_status
        )
        self.source_lang_widget.language_changed.connect(self.on_source_language_change)
        self.target_lang_widget.language_changed.connect(
            self._on_target_language_changed
        )
        self.data_handler.entry_added.connect(self.populate_table_data)
        self.data_handler.entry_deleted.connect(self.populate_table_data)
        self.data_handler.entry_updated.connect(self.populate_table_data)
        self.connection_widget.model_changed.connect(
            self.gen_params_widget.set_connection_type
        )
        self.gen_params_widget.params_changed.connect(self._on_gen_params_changed)
        self.table_widget.selection_changed.connect(self._on_table_selection_changed)
        self.control_panel.item_edited.connect(self._on_item_edited)

    @QtCore.Slot(dict)
    def _on_gen_params_changed(self, params: dict):
        active_conn_name = self.main_window.get_active_connection_name()
        if active_conn_name:
            self.generation_params_updated.emit(active_conn_name, params)

    def handle_model_capability_notice(self, model_id: str, capability: str):
        active_model_full_id = self.main_window.get_active_model_full_id()
        if active_model_full_id and active_model_full_id == model_id:
            self.gen_params_widget.show_capability_notice(capability)

    @QtCore.Slot(str)
    def on_source_language_change(self, lang_name: str):
        if self.main_window.translation_manager.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Operation in Progress",
                "Cannot change source language while translations are active.",
            )
            self.source_lang_widget.update_language_combo()
            return
        logger.info(f"Source language changed to: {lang_name}")
        self.main_window.status_bar.showMessage(
            f"LORE-book source language: {lang_name}"
        )
        if self.data_handler.data:
            self.populate_table_data()

    @QtCore.Slot(str)
    def _on_target_language_changed(self, lang_name: str):
        if self.main_window.translation_manager.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Operation in Progress",
                "Cannot change target language while translations are active.",
            )
            self.target_lang_widget.update_language_combo()
            return
        logger.info(f"Target language changed to: {lang_name or 'None'}")
        self.control_panel.set_active_language(lang_name)

        hdr_text = f"Translated ({lang_name if lang_name else 'N/A'})"
        hdr_item = self.table.horizontalHeaderItem(2)
        if hdr_item:
            hdr_item.setText(hdr_text)

        self.full_content_display.clear()
        self.table.clearSelection()
        self.control_panel.clear_selection()
        if self.data_handler.data:
            self.populate_table_data()
        self.main_window.status_bar.showMessage(
            f"Target language: {lang_name if lang_name else 'None'}"
        )

    @QtCore.Slot()
    def on_data_loaded(self):
        self.populate_table_data()
        self.connection_widget.update_connections()

    def clear_view(self):
        self.table_data = []
        self.table.setRowCount(0)
        self.control_panel.clear_selection()
        self.full_content_display.clear()
        self.table.clearSelection()
        logger.debug("TranslationTab view cleared for new file.")

    def populate_table_data(self):
        sorted_entries = self.data_handler.get_sorted_lore_entries()
        if not sorted_entries:
            self.table_data.clear()
            self.table_widget.set_data([], unique_id_key="id")
            return
        new_table_data = []
        tgt_lang = self.target_lang_widget.combo.currentText()
        src_lang = self.source_lang_widget.combo.currentText()
        if not src_lang:
            self.table_data.clear()
            self.table_widget.set_data([], unique_id_key="id")
            return

        def get_preview(text: str) -> str:
            clean_text = text.replace("\n", " ")
            return (
                (clean_text[:147] + "...") if len(clean_text) > 150 else clean_text
            )

        for entry_id, entry_data in sorted_entries:
            uid = entry_data.get("uid")
            if uid is None:
                continue
            original_keys = entry_data.get("key", [])
            content = entry_data.get("content", "")
            if not isinstance(original_keys, list):
                continue

            if original_keys:
                for orig_key_text in original_keys:
                    orig_key_disp = str(orig_key_text).strip()
                    if not orig_key_disp:
                        continue
                    cached_trans = (
                        self.main_window.cache_manager.get_from_cache(
                            orig_key_disp, src_lang, tgt_lang
                        )
                        or ""
                    )
                    new_table_data.append(
                        {
                            "id": f"{uid}:{orig_key_disp}",
                            "uid": str(uid),
                            "key": orig_key_disp,
                            "translation": cached_trans,
                            "content": content,
                            "content_preview": get_preview(content),
                        }
                    )
            else:
                new_table_data.append(
                    {
                        "id": f"{uid}:",
                        "uid": str(uid),
                        "key": "",
                        "translation": "",
                        "content": content,
                        "content_preview": get_preview(content),
                    }
                )
        self.table_data = new_table_data
        self.data_availability_changed.emit(bool(self.table_data))
        self.table_widget.set_data(self.table_data, unique_id_key="id")

    @QtCore.Slot()
    def _on_table_selection_changed(self, selected_data: list[dict]):
        if not selected_data:
            self.control_panel.clear_selection()
            self.full_content_display.clear()
            return
        if self.main_window.translation_manager.active_translation_jobs > 0:
            self.table.clearSelection()
            return
        first_item = selected_data[0]
        item_id = first_item.get("id", "")
        orig_k = first_item.get("key", "")
        trans_k = first_item.get("translation", "")
        content_k = first_item.get("content", "")
        self.control_panel.set_data(item_id, orig_k, trans_k)
        self.full_content_display.setPlainText(content_k)

    @QtCore.Slot(str, str)
    def _on_item_edited(self, item_id: str, new_text: str):
        if self.main_window.translation_manager.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Operation in Progress",
                "Cannot save edits while translations are active.",
            )
            return
        try:
            uid, orig_k = item_id.split(":", 1)
        except ValueError:
            logger.error(f"Could not parse item_id '{item_id}' for editing.")
            return
        tgt_lang = self.target_lang_widget.combo.currentText()
        src_lang = self.source_lang_widget.combo.currentText()
        if not all([tgt_lang, src_lang]):
            QtWidgets.QMessageBox.warning(
                self,
                "Language Not Set",
                "Cannot apply translation: Source or target language is not selected.",
            )
            return
        self.main_window.cache_manager.update_cache(
            orig_k, new_text, src_lang, tgt_lang
        )
        self.main_window.status_bar.showMessage(
            f"Applied edit for '{orig_k}' (UID {uid}).", 3000
        )
        for row_data in self.table_data:
            if row_data.get("id") == item_id:
                row_data["translation"] = new_text
                break
        self.table_widget.update_row_by_id(item_id, {"translation": new_text})

    def get_selected_items(self) -> list[TranslatableItem]:
        selected_rows_data = self.table_widget.get_selected_rows_data()
        if not selected_rows_data:
            return []
        items_to_translate = []
        for row_data in selected_rows_data:
            uid = row_data.get("uid")
            orig_k = row_data.get("key")
            trans_k = row_data.get("translation")
            content = row_data.get("content")
            dict_key = self.data_handler.find_entry_dict_key_by_uid(str(uid))
            entry_data = (
                self.data_handler.data["entries"].get(dict_key, {})
                if dict_key and self.data_handler.data
                else {}
            )
            item = TranslatableItem(
                id=row_data.get("id", ""),
                source_text=str(orig_k),
                context=str(content),
                original_data=entry_data,
                existing_translation=str(trans_k),
            )
            items_to_translate.append(item)
        return items_to_translate

    def get_all_items(self) -> list[TranslatableItem]:
        return self.data_handler.get_translatable_items()

    def handle_translation_request(
        self, items: list[TranslatableItem], force_regen: bool
    ):
        if not self.data_handler.data:
            QtWidgets.QMessageBox.information(
                self, "Info", "Load or create a LORE-book first."
            )
            return
        self.translation_requested.emit(items, force_regen)

    def handle_deletion_request(self, items: list[TranslatableItem]):
        if self.main_window.translation_manager.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Operation in Progress",
                "Cannot delete translations while other operations are active.",
            )
            return
        tgt_lang = self.target_lang_widget.combo.currentText()
        src_lang = self.source_lang_widget.combo.currentText()
        if not all([tgt_lang, src_lang]):
            QtWidgets.QMessageBox.warning(
                self,
                "Language Not Set",
                "Cannot delete: Source or target language is not selected.",
            )
            return
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {len(items)} translation(s) for language '{tgt_lang}'?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            deleted_count = 0
            deleted_ids = []
            for item in items:
                item_id = item["id"]
                deleted_ids.append(item_id)
                source_text = item["source_text"]
                self.main_window.cache_manager.update_cache(
                    source_text, "", src_lang, tgt_lang
                )
                for row_data in self.table_data:
                    if row_data.get("id") == item_id:
                        row_data["translation"] = ""
                        break
                self.table_widget.update_row_by_id(item_id, {"translation": ""})
                if self.control_panel.current_item_id == item_id:
                    self.control_panel.update_item_display(item_id, "")
                deleted_count += 1
            if deleted_ids:
                self.table_widget.flash_row_by_id(
                    deleted_ids, color=const.FLASH_DANGER_COLOR
                )
            if deleted_count > 0:
                self.main_window.status_bar.showMessage(
                    f"Deleted {deleted_count} translation(s).", 5000
                )

    def show_info_message(self, title: str, text: str):
        QtWidgets.QMessageBox.information(self, title, text)

    @QtCore.Slot(dict)
    def update_item_display(self, update_data: dict):
        item_id = update_data.get("item_id")
        final_translation = update_data.get("final_translation", "")
        if not item_id:
            return
        self.table_widget.update_row_by_id(item_id, {"translation": final_translation})
        self.control_panel.update_item_display(item_id, final_translation)
        self.table_widget.scroll_to_row_by_id(item_id)

    def flash_items(self, item_ids: list[str]):
        for item_id in item_ids:
            self.table_widget.flash_row_by_id(item_id)

    @QtCore.Slot()
    def on_settings_changed(self):
        self.connection_widget.update_connections()
        self.source_lang_widget.update_language_combo()
        self.target_lang_widget.update_language_combo()