import os
import json
import copy
import logging
from PySide6 import QtWidgets
from .ui.dialogs import ExportSettingsDialog
from omni_trans_core import settings
from omni_trans_core.localization_manager import translate
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni_trans_core.core import CoreApp

logger = logging.getLogger(f"{settings.LOG_PREFIX}_APP.export_manager")

def export_lorebook(main_window: "CoreApp"):
    if not main_window.data_handler.data:
        QtWidgets.QMessageBox.warning(
            main_window,
            translate("app.dialog.export_error.title"),
            "No LORE-book data loaded to export.",
        )
        return
    main_window.save_all_changes()
    current_lore_name = os.path.splitext(main_window.data_handler.get_project_name())[0]
    export_dialog = ExportSettingsDialog(main_window, current_lore_name, main_window)
    if not export_dialog.exec() == QtWidgets.QDialog.Accepted:
        logger.info("Export operation cancelled by user in settings dialog.")
        return
    lore_name, selected_langs, include_originals, missing_rule = (
        export_dialog.get_export_settings()
    )
    src_lang = settings.current_settings.get("selected_source_language")
    if not lore_name:
        QtWidgets.QMessageBox.warning(
            main_window,
            translate("dialog.export.error.no_name.title"),
            translate("dialog.export.error.no_name.text"),
        )
        return
    data_to_export = copy.deepcopy(main_window.data_handler.data)
    if selected_langs:
        logger.info(f"Applying translations for languages: {selected_langs}")
        for entry_data in data_to_export["entries"].values():
            original_keys = list(entry_data.get("key", []))
            final_keys = set()
            if include_originals:
                final_keys.update(original_keys)
            for key_text in original_keys:
                found_translation = False
                for lang in selected_langs:
                    cached_trans = main_window.cache_manager.get_from_cache(
                        key_text, src_lang, lang
                    )
                    if cached_trans:
                        final_keys.add(cached_trans)
                        found_translation = True
                if (
                    not found_translation
                    and missing_rule == "leave"
                    and not include_originals
                ):
                    final_keys.add(key_text)
            entry_data["key"] = sorted(list(final_keys))
    project_path = main_window.data_handler.get_project_path()
    start_dir = (
        os.path.dirname(project_path) if project_path else os.path.expanduser("~")
    )
    default_save_path = os.path.join(start_dir, f"{lore_name}.json")
    output_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        translate("action.export"),
        default_save_path,
        "LORE-book (*.json);;All Files (*)",
    )
    if not output_path:
        logger.info("Export operation cancelled by user in file dialog.")
        return
    logger.info(f"Attempting to export compiled LORE-book to: {output_path}")
    main_window.loading_overlay.start_animation(
        translate("app.status.exporting_file", filename=os.path.basename(output_path))
    )
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_to_export, f, ensure_ascii=False, indent=2)
        QtWidgets.QMessageBox.information(
            main_window,
            translate("app.dialog.export_success.title"),
            translate("app.dialog.export_success.text", path=output_path),
        )
        logger.info("Export successful.")
    except Exception as e:
        logger.error(f"Export failed for {output_path}: {e}", exc_info=True)
        QtWidgets.QMessageBox.critical(
            main_window,
            translate("app.dialog.export_error.title"),
            translate("app.dialog.export_error.text", error=str(e)),
        )
    finally:
        main_window.loading_overlay.stop_animation()
