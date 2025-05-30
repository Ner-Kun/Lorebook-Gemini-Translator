import sys
import os
import json
import logging
import hashlib
import re
import collections
import time
import copy

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from PySide6 import QtWidgets, QtCore, QtGui
import qdarktheme

APP_VERSION = "0.0.2"
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
elif __file__:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    APP_DIR = os.getcwd()

SETTINGS_FILE = os.path.join(APP_DIR, "translator_settings.json")
LOG_FILE = os.path.join(APP_DIR, "translator.log")
MAX_RECENT_FILES = 10

logger = logging.getLogger('Lorebook_Gemini_Translator')
default_settings = {
    "api_key": "",
    "gemini_model": "gemini-2.5-flash-preview-05-20",
    "log_to_file": False,
    "show_log_panel": False,
    "log_level": "INFO",
    "enable_model_thinking": True,
    "api_request_delay": 0.6,
    "use_content_as_context": True,
    "recent_files": [],
    "target_languages": [],
    "available_source_languages": ["English"],
    "selected_target_language": "",
    "selected_source_language": "English",
    "rpm_limit": 10,
    "rpm_warning_threshold_percent": 75,
    "rpm_monitor_update_interval_ms": 1000,
    "available_gemini_models_fallback": [
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.0-flash"
            ]
}
current_settings = default_settings.copy()
fh = None

class JobSignals(QtCore.QObject):
    job_completed = QtCore.Signal(object, str, str, str)
    job_failed = QtCore.Signal(object, str, str, str)
    inspector_update = QtCore.Signal(str, str, str)

class TranslationJobRunnable(QtCore.QRunnable):
    def __init__(self, app_ref, job_data, signals):
        super().__init__()
        self.app_ref = app_ref
        self.job_data = job_data
        self.signals = signals

    @QtCore.Slot()
    def run(self):
        try:
            text_to_translate = self.job_data['text_to_translate']
            source_lang = self.job_data['source_lang']
            target_lang = self.job_data['target_lang']
            context_content_for_api = self.job_data['context_content_for_api']

            prompt, full_raw_api_response, metadata_and_thinking, final_processed_translation = \
                self.app_ref._execute_gemini_api_call_internal(text_to_translate, source_lang, target_lang, context_content_for_api)

            inspector_metadata_field_text = f"{metadata_and_thinking}\n\n[Raw API Response]\n{full_raw_api_response}"
            self.signals.inspector_update.emit(prompt, final_processed_translation if final_processed_translation is not None else "", inspector_metadata_field_text)

            if final_processed_translation is not None:
                self.signals.job_completed.emit(self.job_data, final_processed_translation, full_raw_api_response, metadata_and_thinking)
            else:
                self.signals.job_failed.emit(self.job_data, "API call failed or returned no text.", full_raw_api_response, metadata_and_thinking)

        except Exception as e:
            logger.error(f"Exception in TranslationJobRunnable for '{self.job_data.get('text_to_translate')}': {e}", exc_info=True)
            self.signals.job_failed.emit(self.job_data, str(e), "N/A", f"Exception in worker: {e}")


def setup_logger():
    global fh
    logger.setLevel(getattr(logging, current_settings.get("log_level", "INFO").upper(), logging.INFO))
    for handler in logger.handlers[:]:
        if handler is not fh and not isinstance(handler, QtLogHandler):
            logger.removeHandler(handler)
        elif isinstance(handler, logging.FileHandler) and handler is fh:
            if not current_settings.get("log_to_file", False):
                logger.removeHandler(fh); fh.close(); fh = None
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler(sys.stdout); ch.setFormatter(formatter); logger.addHandler(ch)
    if current_settings.get("log_to_file", False) and fh is None:
        try:
            fh = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'); fh.setFormatter(formatter); logger.addHandler(fh)
        except Exception as e: print(f"ERROR: Failed file logging: {e}"); current_settings["log_to_file"] = False
    elif not current_settings.get("log_to_file", False) and fh is not None:
        logger.removeHandler(fh); fh.close(); fh = None

def load_settings():
    global current_settings
    current_settings = default_settings.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_s = json.load(f)
                for key in default_settings:
                    if key in loaded_s:
                        if isinstance(default_settings[key], bool) and isinstance(loaded_s[key], bool):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], (int, float)) and isinstance(loaded_s[key], (int, float)):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], str) and isinstance(loaded_s[key], str):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], list) and isinstance(loaded_s[key], list):
                            current_settings[key] = loaded_s[key]

                if "recent_files" in current_settings:
                    if not isinstance(current_settings["recent_files"], list):
                        current_settings["recent_files"] = []
                    current_settings["recent_files"] = [
                        f for f in current_settings["recent_files"] if isinstance(f, str) and f
                    ][:MAX_RECENT_FILES]
                else:
                    current_settings["recent_files"] = []

                if "target_languages" not in current_settings or not isinstance(current_settings["target_languages"], list):
                    current_settings["target_languages"] = []
                current_settings["target_languages"] = [str(lang) for lang in current_settings["target_languages"] if lang]

                if "available_source_languages" not in current_settings or not isinstance(current_settings["available_source_languages"], list):
                    current_settings["available_source_languages"] = default_settings["available_source_languages"]
                current_settings["available_source_languages"] = [str(lang) for lang in current_settings["available_source_languages"] if lang]
                if not current_settings["available_source_languages"]:
                    current_settings["available_source_languages"] = ["English"]

                if "selected_target_language" not in current_settings:
                    current_settings["selected_target_language"] = ""
                if "selected_source_language" not in current_settings:
                    current_settings["selected_source_language"] = default_settings["available_source_languages"][0]
                if current_settings["selected_source_language"] not in current_settings["available_source_languages"]:
                    if current_settings["available_source_languages"]:
                        current_settings["selected_source_language"] = current_settings["available_source_languages"][0]
                    else:
                        current_settings["selected_source_language"] = "English"

        except Exception as e:
            print(f"ERROR: Failed settings load: {e}. Using defaults or last known good.")
            current_settings = default_settings.copy()
        finally:
            if not current_settings.get("available_source_languages"):
                current_settings["available_source_languages"] = ["English"]
            if not current_settings.get("selected_source_language") or current_settings["selected_source_language"] not in current_settings["available_source_languages"]:
                current_settings["selected_source_language"] = current_settings["available_source_languages"][0]
            if not current_settings.get("gemini_model"):
                current_settings["gemini_model"] = default_settings["gemini_model"]
    else:
        pass
    setup_logger()

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(current_settings, f, ensure_ascii=False, indent=2)
        logger.info("Settings saved.")
    except Exception as e: logger.error(f"Failed to save settings: {e}")

class QtLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__(); self.widget = text_widget; self.widget.setReadOnly(True)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')); self.setLevel(logging.DEBUG)
    def emit(self, record):
        if self.widget and self.widget.isVisible():
            msg = self.format(record); self.widget.append(msg); self.widget.moveCursor(QtGui.QTextCursor.End)


class ModelInspectorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Inspector"); self.setMinimumSize(700, 600)
        flags = self.windowFlags()
        flags &= ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        layout = QtWidgets.QVBoxLayout(self)
        self.prompt_label = QtWidgets.QLabel("Last Prompt Sent to Model:")
        self.prompt_text_edit = QtWidgets.QTextEdit(); self.prompt_text_edit.setReadOnly(True)

        self.processed_translation_label = QtWidgets.QLabel("Final Translation:")
        self.processed_translation_text_edit = QtWidgets.QTextEdit(); self.processed_translation_text_edit.setReadOnly(True)

        self.metadata_label = QtWidgets.QLabel("Raw API Response:")
        self.metadata_text_edit = QtWidgets.QTextEdit(); self.metadata_text_edit.setReadOnly(True)

        layout.addWidget(self.prompt_label); layout.addWidget(self.prompt_text_edit, stretch=2)
        layout.addWidget(self.processed_translation_label); layout.addWidget(self.processed_translation_text_edit, stretch=1)
        layout.addWidget(self.metadata_label); layout.addWidget(self.metadata_text_edit, stretch=2)
        self.setModal(False)

    @QtCore.Slot(str, str, str)
    def update_data(self, prompt, final_translation_text, metadata_and_full_raw_text):
        self.prompt_text_edit.setPlainText(prompt)
        self.processed_translation_text_edit.setPlainText(final_translation_text)
        self.metadata_text_edit.setPlainText(metadata_and_full_raw_text)

    def clear_data(self):
        self.prompt_text_edit.clear();
        self.processed_translation_text_edit.clear();
        self.metadata_text_edit.clear()
    def closeEvent(self, event): self.hide(); event.ignore()

class ManageLanguagesDialog(QtWidgets.QDialog):
    def __init__(self, current_languages, language_type="Target", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Manage {language_type} Languages")
        self.setMinimumWidth(350)
        flags = self.windowFlags()
        flags &= ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.languages = list(current_languages)
        self.language_type = language_type

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(self.languages)
        layout.addWidget(self.list_widget)

        input_layout = QtWidgets.QHBoxLayout()
        self.lang_input = QtWidgets.QLineEdit()
        self.lang_input.setPlaceholderText(f"Enter language name (e.g., Ukrainian)")
        input_layout.addWidget(self.lang_input)
        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_language)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)

        remove_button = QtWidgets.QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_language)
        layout.addWidget(remove_button)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def add_language(self):
        lang_name = self.lang_input.text().strip()
        if lang_name and lang_name not in self.languages:
            self.languages.append(lang_name)
            self.languages.sort()
            self.list_widget.clear()
            self.list_widget.addItems(self.languages)
            self.lang_input.clear()
        elif lang_name in self.languages:
            QtWidgets.QMessageBox.information(self, "Duplicate", f"Language '{lang_name}' already exists.")
        elif not lang_name:
            QtWidgets.QMessageBox.warning(self, "Empty Name", "Language name cannot be empty.")


    def remove_language(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        if self.language_type == "Source" and len(self.languages) - len(selected_items) < 1:
            QtWidgets.QMessageBox.warning(self, "Cannot Remove", "At least one source language must remain.")
            return

        for item in selected_items:
            lang_to_remove = item.text()
            if lang_to_remove in self.languages:
                self.languages.remove(lang_to_remove)
        self.list_widget.clear()
        self.list_widget.addItems(self.languages)

    def get_languages(self):
        return self.languages

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About Lorebook Gemini Translator v{APP_VERSION}")
        self.setMinimumWidth(350)
        flags = self.windowFlags()
        flags &= ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

        layout = QtWidgets.QVBoxLayout(self)

        title_label = QtWidgets.QLabel(f"Lorebook Gemini Translator")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        version_label = QtWidgets.QLabel(f"Version: {APP_VERSION}")
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        layout.addSpacing(20)

        author_label = QtWidgets.QLabel("Developed by: Ner_Kun")
        author_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)

        github_link_label = QtWidgets.QLabel("<a href=\"https://github.com/Ner-Kun\">Ner_Kun on GitHub</a>")
        github_link_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        github_link_label.setOpenExternalLinks(True)
        layout.addWidget(github_link_label)

        layout.addStretch()

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)



class SettingsDialog(QtWidgets.QDialog):
    clear_cache_requested = QtCore.Signal()

    def __init__(self, settings_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(550)
        flags = self.windowFlags()
        flags &= ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

        self.settings_data = settings_data.copy()

        main_layout = QtWidgets.QVBoxLayout(self)
        tab_widget = QtWidgets.QTabWidget(self)
        api_tab = QtWidgets.QWidget()
        api_layout = QtWidgets.QFormLayout(api_tab)

        self.apiKeyEdit = QtWidgets.QLineEdit(self.settings_data.get("api_key", ""))
        self.apiKeyEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        api_layout.addRow("API Key:", self.apiKeyEdit)

        self.modelCombo = QtWidgets.QComboBox()
        self._populate_models_combo()
        api_layout.addRow("Gemini Model:", self.modelCombo)

        self.delaySpin = QtWidgets.QDoubleSpinBox()
        self.delaySpin.setRange(0.1, 10.0)
        self.delaySpin.setSingleStep(0.1)
        self.delaySpin.setValue(self.settings_data.get("api_request_delay", default_settings["api_request_delay"]))
        self.delaySpin.setSuffix(" seconds")
        api_layout.addRow("API Request Delay:", self.delaySpin)

        api_layout.addRow(QtWidgets.QLabel("<b>API Rate Limiting (RPM):</b>"))

        self.rpmLimitSpin = QtWidgets.QSpinBox()
        self.rpmLimitSpin.setRange(1, 1000)
        self.rpmLimitSpin.setValue(self.settings_data.get("rpm_limit", default_settings["rpm_limit"]))
        api_layout.addRow("RPM Limit:", self.rpmLimitSpin)

        self.rpmWarningSpin = QtWidgets.QSpinBox()
        self.rpmWarningSpin.setRange(10, 95)
        self.rpmWarningSpin.setSuffix(" %")
        self.rpmWarningSpin.setValue(self.settings_data.get("rpm_warning_threshold_percent", default_settings["rpm_warning_threshold_percent"]))
        api_layout.addRow("Warning Threshold:", self.rpmWarningSpin)

        self.clearCacheButton = QtWidgets.QPushButton("Clear Active LORE-book Cache")
        self.clearCacheButton.clicked.connect(self.on_clear_cache_clicked)
        api_layout.addRow(self.clearCacheButton)

        tab_widget.addTab(api_tab, "API & Model")

        log_tab = QtWidgets.QWidget()
        log_layout_main = QtWidgets.QVBoxLayout(log_tab)

        self.logToFileCheck = QtWidgets.QCheckBox("Log to file")
        self.logToFileCheck.setChecked(self.settings_data.get("log_to_file", default_settings["log_to_file"]))
        log_layout_main.addWidget(self.logToFileCheck)

        self.showLogPanelCheck = QtWidgets.QCheckBox("Show log panel")
        self.showLogPanelCheck.setChecked(self.settings_data.get("show_log_panel", default_settings["show_log_panel"]))
        log_layout_main.addWidget(self.showLogPanelCheck)
        log_level_layout = QtWidgets.QHBoxLayout()
        log_level_layout.addWidget(QtWidgets.QLabel("Log Level:"))
        self.logLevelCombo = QtWidgets.QComboBox()
        self.logLevelCombo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.logLevelCombo.setCurrentText(self.settings_data.get("log_level", default_settings["log_level"]).upper())
        log_level_layout.addWidget(self.logLevelCombo)
        log_layout_main.addLayout(log_level_layout)
        log_layout_main.addStretch()
        tab_widget.addTab(log_tab, "Logging")

        main_layout.addWidget(tab_widget)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)

    def _populate_models_combo(self):
        current_selected_model = self.settings_data.get("gemini_model", default_settings["gemini_model"])
        
        fetched_models = []
        api_key_present = self.settings_data.get("api_key") or self.apiKeyEdit.text()

        try:
            if not api_key_present:
                logger.warning("API key is not set. Cannot fetch models from API for settings dialog.")
            else:
                logger.info("Fetching available Gemini models for settings dialog...")
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                
                models_from_api = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        model_name = m.name.replace("models/", "")
                        models_from_api.append(model_name)
                
                if models_from_api:
                    fetched_models = sorted(list(set(models_from_api)))
                    logger.info(f"Successfully fetched models: {fetched_models}")
                else:
                    logger.warning("API returned no models supporting 'generateContent'.")

        except Exception as e:
            logger.error(f"Failed to fetch models from API for settings dialog: {e}", exc_info=False)
            QtWidgets.QMessageBox.warning(self, "Model Fetch Error", f"Could not fetch models from API: {e}\nUsing fallback list.")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        final_model_list = []
        if fetched_models:
            final_model_list.extend(fetched_models)
        else:
            fallback_models = default_settings.get("available_gemini_models_fallback", ["gemini-2.5-flash-preview-05-20", "gemini-2.5-flash-preview-04-17", "gemini-2.0-flash"])
            final_model_list.extend(fallback_models)
            logger.info(f"Using fallback/default models: {fallback_models}")

        if current_selected_model and current_selected_model not in final_model_list:
            final_model_list.append(current_selected_model)
        
        final_model_list = sorted(list(set(final_model_list)))

        self.modelCombo.clear()
        if final_model_list:
            self.modelCombo.addItems(final_model_list)
            if current_selected_model in final_model_list:
                self.modelCombo.setCurrentText(current_selected_model)
            elif final_model_list:
                self.modelCombo.setCurrentIndex(0)
        else:
            self.modelCombo.setPlaceholderText("No models available")
            if current_selected_model:
                self.modelCombo.addItem(current_selected_model)
                self.modelCombo.setCurrentText(current_selected_model)

    def on_clear_cache_clicked(self):
        self.clear_cache_requested.emit()
        logger.info("Cache clear requested from settings dialog.")

    def accept_settings(self):
        self.settings_data["api_key"] = self.apiKeyEdit.text()
        self.settings_data["gemini_model"] = self.modelCombo.currentText()
        self.settings_data["api_request_delay"] = self.delaySpin.value()
        self.settings_data["rpm_limit"] = self.rpmLimitSpin.value()
        self.settings_data["rpm_warning_threshold_percent"] = self.rpmWarningSpin.value()
        self.settings_data["log_to_file"] = self.logToFileCheck.isChecked()
        self.settings_data["show_log_panel"] = self.showLogPanelCheck.isChecked()
        self.settings_data["log_level"] = self.logLevelCombo.currentText()
        self.accept()

    def get_settings(self):
        return self.settings_data



class TranslatorApp(QtWidgets.QMainWindow):

    def __init__(self, gemini_model_instance):
        super().__init__()
        self.setWindowTitle(f'Lorebook Gemini Translator v{APP_VERSION}')
        self.resize(1000, 800); self.gemini_model = gemini_model_instance
        self.cache = {}; self.cache_file_path = None
        self.data = None; self.input_path = None;
        self.table_data = []
        self.current_row = None
        self.current_target_language = current_settings.get("selected_target_language", "")
        self.current_source_language = current_settings.get("selected_source_language", default_settings["available_source_languages"][0])

        self.current_orig_key_for_editor = None; self.current_translation_in_editor_before_change = None
        self.recent_files = current_settings.get("recent_files", []); self.recent_menu = None
        self.qt_log_handler = None; self.model_inspector_window = None

        self.thread_pool = QtCore.QThreadPool()
        logger.info(f"QThreadPool maxThreadCount: {self.thread_pool.maxThreadCount()}")
        self.pending_translation_jobs = collections.deque()
        self.active_translation_jobs = 0
        self.progress_dialog = None
        self.translation_timer = QtCore.QTimer(self)
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self._dispatch_next_job_to_pool)
        self.total_jobs_for_progress = 0
        self.completed_jobs_for_progress = 0

        self.api_request_timestamps = collections.deque()
        self.is_rpm_cooldown_active = False
        self.rpm_cooldown_end_time = 0
        self.rpm_monitor_timer = QtCore.QTimer(self)
        self.rpm_monitor_timer.timeout.connect(self.update_rpm_display_and_check_cooldown)

        self.apply_rpm_settings_effects() 

        self.init_ui()
        self._update_target_language_combo()
        self._update_source_language_combo()

        if self.log_text_edit: self.qt_log_handler = QtLogHandler(self.log_text_edit); logger.addHandler(self.qt_log_handler)
        self.apply_settings_effects(); self.update_recent_files_menu(); logger.info("Application initialized.")

    def find_entry_dict_key_by_uid(self, uid_to_find):
        if self.data and 'entries' in self.data:
            uid_to_find_str = str(uid_to_find)
            for dict_key, entry_data_val in self.data['entries'].items():
                if isinstance(entry_data_val, dict):
                    entry_uid_val = entry_data_val.get('uid')
                    if entry_uid_val is not None and str(entry_uid_val) == uid_to_find_str:
                        return dict_key
        logger.warning(f"Could not find LORE entry dictionary key for UID '{uid_to_find}'.")
        return None

    def _ensure_entry_key_is_list(self, entry_data):
            if not isinstance(entry_data, dict):
                return

            current_primary_key_field = entry_data.get('key')
            
            consolidated_keys = set()

            if isinstance(current_primary_key_field, str) and current_primary_key_field.strip():
                consolidated_keys.add(current_primary_key_field.strip())
            elif isinstance(current_primary_key_field, list):
                for item in current_primary_key_field:
                    if isinstance(item, str) and item.strip():
                        consolidated_keys.add(item.strip())

            entry_data['key'] = sorted(list(consolidated_keys))

    @QtCore.Slot(str, str, str)
    def handle_inspector_update(self, prompt, final_translation, metadata_and_raw):
        if self.model_inspector_window and self.model_inspector_window.isVisible():
            self.model_inspector_window.update_data(prompt, final_translation, metadata_and_raw)

    def init_ui(self):
        self.create_actions(); self.create_menus()
        central_widget = QtWidgets.QWidget(); self.setCentralWidget(central_widget); main_layout = QtWidgets.QVBoxLayout(central_widget)

        language_panel_layout = QtWidgets.QHBoxLayout()

        source_lang_group = QtWidgets.QGroupBox("LORE-book Language")
        source_lang_layout = QtWidgets.QHBoxLayout(source_lang_group)
        self.source_lang_combo = QtWidgets.QComboBox()
        self.source_lang_combo.currentTextChanged.connect(self.on_source_language_change)
        manage_source_langs_button = QtWidgets.QPushButton("Manage")
        manage_source_langs_button.clicked.connect(self.open_manage_source_languages_dialog)
        source_lang_layout.addWidget(self.source_lang_combo)
        source_lang_layout.addWidget(manage_source_langs_button)
        language_panel_layout.addWidget(source_lang_group, stretch=1)


        target_lang_group = QtWidgets.QGroupBox("Language for Translation")
        target_lang_layout = QtWidgets.QHBoxLayout(target_lang_group)
        self.target_lang_combo = QtWidgets.QComboBox()
        self.target_lang_combo.currentTextChanged.connect(self.on_target_language_change)
        manage_target_langs_button = QtWidgets.QPushButton("Manage")
        manage_target_langs_button.clicked.connect(self.open_manage_target_languages_dialog)
        target_lang_layout.addWidget(self.target_lang_combo)
        target_lang_layout.addWidget(manage_target_langs_button)
        language_panel_layout.addWidget(target_lang_group, stretch=1)

        main_layout.addLayout(language_panel_layout)

        top_panel_layout = QtWidgets.QHBoxLayout()
        file_group = QtWidgets.QGroupBox("LORE-book File"); file_layout = QtWidgets.QHBoxLayout(file_group)
        self.file_input = QtWidgets.QLineEdit(); self.file_input.setPlaceholderText("Path to .json"); self.file_input.setReadOnly(True)
        open_lorebook_btn = QtWidgets.QPushButton("Open LORE-book"); open_lorebook_btn.clicked.connect(self.browse_and_load)
        file_layout.addWidget(self.file_input); file_layout.addWidget(open_lorebook_btn); top_panel_layout.addWidget(file_group, stretch=1)
        main_layout.addLayout(top_panel_layout)

        middle_v_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        middle_v_splitter.setOpaqueResize(False)
        top_middle_h_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top_middle_h_splitter.setOpaqueResize(False)


        table_group = QtWidgets.QGroupBox("LORE Entries"); table_layout = QtWidgets.QVBoxLayout(table_group)
        self.table = QtWidgets.QTableWidget(); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['UID', 'Original Key', f'Translated ({self.current_target_language if self.current_target_language else "N/A"})', 'Content Preview'])
        self.table.cellClicked.connect(self.on_cell_click)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows); self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers); self.table.setWordWrap(False)
        table_layout.addWidget(self.table); top_middle_h_splitter.addWidget(table_group)

        edit_group = QtWidgets.QGroupBox("Edit Selected Translation")
        edit_layout = QtWidgets.QFormLayout(edit_group)

        self.orig_label = QtWidgets.QLabel(''); self.orig_label.setWordWrap(True)
        edit_layout.addRow('Original Key:', self.orig_label)

        self.trans_edit_label = QtWidgets.QLabel(f'Translation ({self.current_target_language if self.current_target_language else "N/A"}):')
        self.trans_edit = QtWidgets.QLineEdit(); self.trans_edit.setPlaceholderText("Edit or enter translation here")
        edit_layout.addRow(self.trans_edit_label, self.trans_edit)

        edit_buttons_layout = QtWidgets.QHBoxLayout()
        save_row_btn = QtWidgets.QPushButton('Save Edited'); save_row_btn.clicked.connect(self.save_edited_translation)
        self.regenerate_btn = QtWidgets.QPushButton('Regenerate'); self.regenerate_btn.clicked.connect(self.regenerate_selected_translation_action)
        delete_trans_btn = QtWidgets.QPushButton('Delete This'); delete_trans_btn.clicked.connect(self.delete_current_translation)
        edit_buttons_layout.addWidget(save_row_btn); edit_buttons_layout.addWidget(self.regenerate_btn); edit_buttons_layout.addWidget(delete_trans_btn)
        edit_layout.addRow(edit_buttons_layout)

        batch_operations_layout = QtWidgets.QHBoxLayout()
        trans_sel_btn = QtWidgets.QPushButton('Translate Selected'); trans_sel_btn.clicked.connect(self.translate_selected_rows_action)
        trans_all_btn = QtWidgets.QPushButton('Translate All'); trans_all_btn.clicked.connect(self.translate_all_action)
        self.clear_all_trans_btn = QtWidgets.QPushButton('Clear All Translations (Current Lang)'); self.clear_all_trans_btn.clicked.connect(self.clear_all_translations_for_display_lang)
        
        batch_operations_layout.addWidget(trans_sel_btn)
        batch_operations_layout.addWidget(trans_all_btn)
        batch_operations_layout.addWidget(self.clear_all_trans_btn)
        edit_layout.addRow(batch_operations_layout)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        edit_layout.addRow(separator)

        self.useContentContextCheck = QtWidgets.QCheckBox("Use LORE 'content' as context")
        self.useContentContextCheck.setChecked(current_settings.get("use_content_as_context", True))
        self.useContentContextCheck.setToolTip("Use the 'content' field from the LORE entry as additional context for the translation.")
        self.useContentContextCheck.toggled.connect(self.on_toggle_use_context)
        edit_layout.addRow(self.useContentContextCheck)

        self.enableModelThinkingCheck = QtWidgets.QCheckBox("Enable Model Thinking Output")
        self.enableModelThinkingCheck.setChecked(current_settings.get("enable_model_thinking", True))
        self.enableModelThinkingCheck.setToolTip("If checked, the model will attempt to show its reasoning process.\nThis may improve translation quality but will increase API usage.\n(If you get a blank answer, try turning this off or regenerating)")
        self.enableModelThinkingCheck.toggled.connect(self.on_toggle_enable_thinking)
        edit_layout.addRow(self.enableModelThinkingCheck)

        self.rpm_status_label = QtWidgets.QLabel("RPM: 0/60")
        self.rpm_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rpm_status_label.setStyleSheet("QLabel { color : green; font-weight: bold; }")
        self.rpm_status_label.setToolTip("API Requests Per Minute status. Helps to avoid rate limits.")

        edit_layout.addRow(self.rpm_status_label)

        top_middle_h_splitter.addWidget(edit_group)
        top_middle_h_splitter.setStretchFactor(0, 2)
        top_middle_h_splitter.setStretchFactor(1, 1)

        middle_v_splitter.addWidget(top_middle_h_splitter)
        
        content_display_group = QtWidgets.QGroupBox("Full Content of Selected Entry"); content_display_layout = QtWidgets.QVBoxLayout(content_display_group)
        self.full_content_display = QtWidgets.QTextEdit(); self.full_content_display.setReadOnly(True)
        content_display_layout.addWidget(self.full_content_display); middle_v_splitter.addWidget(content_display_group)

        main_layout.addWidget(middle_v_splitter, stretch=2)
        action_buttons_layout = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton('Export LORE-book'); export_btn.clicked.connect(self.export_json)
        action_buttons_layout.addStretch(); 
        action_buttons_layout.addWidget(export_btn); 
        main_layout.addLayout(action_buttons_layout)

        self.log_panel = QtWidgets.QGroupBox("Application Log"); log_panel_layout = QtWidgets.QVBoxLayout(self.log_panel)
        self.log_text_edit = QtWidgets.QTextEdit(); self.log_text_edit.setReadOnly(True)
        log_panel_layout.addWidget(self.log_text_edit); self.log_panel.setVisible(current_settings.get("show_log_panel", True)); main_layout.addWidget(self.log_panel, stretch=1)
        self.statusBar = QtWidgets.QStatusBar(); self.setStatusBar(self.statusBar); self.statusBar.showMessage("Ready.")

    @QtCore.Slot(bool)
    def on_toggle_use_context(self, checked_boolean_value):
        current_settings["use_content_as_context"] = checked_boolean_value
        logger.info(f"Setting 'Use LORE content as context' changed to: {checked_boolean_value}")
        save_settings()

    @QtCore.Slot(bool)
    def on_toggle_enable_thinking(self, checked_boolean_value):
        current_settings["enable_model_thinking"] = checked_boolean_value
        logger.info(f"Setting 'Enable Model Thinking Output' changed to: {checked_boolean_value}")
        save_settings()

    def _update_target_language_combo(self):
        self.target_lang_combo.blockSignals(True)
        self.target_lang_combo.clear()
        stored_target_langs = current_settings.get("target_languages", [])
        if stored_target_langs:
            self.target_lang_combo.addItems(stored_target_langs)
            selected_lang = current_settings.get("selected_target_language", "")
            if selected_lang and selected_lang in stored_target_langs:
                self.target_lang_combo.setCurrentText(selected_lang)
            elif stored_target_langs:
                self.target_lang_combo.setCurrentIndex(0)
                current_settings["selected_target_language"] = stored_target_langs[0]
        else:
            self.target_lang_combo.setPlaceholderText("No target languages defined")
            current_settings["selected_target_language"] = ""
        
        self.target_lang_combo.blockSignals(False)
        self.on_target_language_change(self.target_lang_combo.currentText())


    def _update_source_language_combo(self):
        self.source_lang_combo.blockSignals(True)
        self.source_lang_combo.clear()
        available_source_langs = current_settings.get("available_source_languages", [default_settings["available_source_languages"][0]])
        if not available_source_langs:
            available_source_langs = ["English"]
            current_settings["available_source_languages"] = available_source_langs

        self.source_lang_combo.addItems(available_source_langs)
        selected_source = current_settings.get("selected_source_language", "")

        if selected_source and selected_source in available_source_langs:
            self.source_lang_combo.setCurrentText(selected_source)
        elif available_source_langs:
            self.source_lang_combo.setCurrentIndex(0)
            current_settings["selected_source_language"] = available_source_langs[0]
        
        self.source_lang_combo.blockSignals(False)
        self.on_source_language_change(self.source_lang_combo.currentText())

    def open_manage_target_languages_dialog(self):
        current_langs = current_settings.get("target_languages", [])
        dialog = ManageLanguagesDialog(current_langs, "Target", self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_langs = dialog.get_languages()
            current_settings["target_languages"] = new_langs
            logger.info(f"Target languages updated: {new_langs}")
            
            selected_target_lang = current_settings.get("selected_target_language", "")
            if new_langs and selected_target_lang not in new_langs:
                current_settings["selected_target_language"] = new_langs[0]
            elif not new_langs:
                current_settings["selected_target_language"] = ""

            self._update_target_language_combo()
            save_settings()


    def open_manage_source_languages_dialog(self):
        current_langs = current_settings.get("available_source_languages", [])
        dialog = ManageLanguagesDialog(current_langs, "Source", self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_langs = dialog.get_languages()
            if not new_langs:
                new_langs = ["English"]
                QtWidgets.QMessageBox.information(self, "Defaulting Source Language", "Source languages cannot be empty. Defaulted to 'English'.")

            current_settings["available_source_languages"] = new_langs
            logger.info(f"Available source languages updated: {new_langs}")

            selected_source_lang = current_settings.get("selected_source_language", "")
            if selected_source_lang not in new_langs:
                 current_settings["selected_source_language"] = new_langs[0]
            
            self._update_source_language_combo()
            save_settings()


    def on_target_language_change(self, lang_name):
        if self.active_translation_jobs > 0 and lang_name != self.current_target_language :
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot change target language while translations are in progress.")
            self.target_lang_combo.blockSignals(True)
            self.target_lang_combo.setCurrentText(self.current_target_language if self.current_target_language else "")
            self.target_lang_combo.blockSignals(False)
            return

        self.current_target_language = lang_name if lang_name else ""
        current_settings["selected_target_language"] = self.current_target_language

        logger.debug(f"Target language changed to: {self.current_target_language or 'None'}")
        hdr_text = f'Translated ({self.current_target_language if self.current_target_language else "N/A"})'
        hdr = self.table.horizontalHeaderItem(2)
        if hdr: hdr.setText(hdr_text)
        else: self.table.setHorizontalHeaderLabels(['UID', 'Original Key', hdr_text, 'Content Preview'])


        if hasattr(self, 'trans_edit_label'): self.trans_edit_label.setText(f'Translation ({self.current_target_language if self.current_target_language else "N/A"}):')

        self.orig_label.clear(); self.trans_edit.clear(); self.full_content_display.clear()
        self.current_row = None; self.current_orig_key_for_editor = None; self.current_translation_in_editor_before_change = None
        self.table.clearSelection()

        if self.data: self.populate_table_data()
        self.statusBar.showMessage(f"Target language: {self.current_target_language if self.current_target_language else 'None'}")
        save_settings()


    def on_source_language_change(self, lang_name):
        if self.active_translation_jobs > 0 and lang_name != self.current_source_language:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot change source language while translations are in progress.")
            self.source_lang_combo.blockSignals(True)
            self.source_lang_combo.setCurrentText(self.current_source_language)
            self.source_lang_combo.blockSignals(False)
            return

        self.current_source_language = lang_name if lang_name else default_settings["available_source_languages"][0]
        current_settings["selected_source_language"] = self.current_source_language
        logger.info(f"Source language changed to: {self.current_source_language}")
        self.statusBar.showMessage(f"LORE-book source language: {self.current_source_language}")
        save_settings()
        if self.data:
            self.populate_table_data()

    def apply_rpm_settings_effects(self):
        update_interval = current_settings.get("rpm_monitor_update_interval_ms", 1000)
        if self.rpm_monitor_timer.isActive():
            self.rpm_monitor_timer.stop()
        self.rpm_monitor_timer.start(update_interval)
        self.update_rpm_display_and_check_cooldown()
        logger.info(f"RPM monitor configured: Limit {current_settings.get('rpm_limit', 60)}, Warning at {current_settings.get('rpm_warning_threshold_percent', 75)}%, Update every {update_interval}ms.")


    def _record_api_request_timestamp(self):
        self.api_request_timestamps.append(time.monotonic())
        self.update_rpm_display_and_check_cooldown()

    def _get_current_rpm(self):
        now = time.monotonic()
        while self.api_request_timestamps and self.api_request_timestamps[0] < now - 60:
            self.api_request_timestamps.popleft()
        return len(self.api_request_timestamps)

    def _is_rpm_limit_reached(self):
        return self._get_current_rpm() >= current_settings.get("rpm_limit", 60)

    def update_rpm_display_and_check_cooldown(self):
        if not hasattr(self, 'rpm_status_label'):
            return

        current_rpm = self._get_current_rpm()
        limit = current_settings.get("rpm_limit", 60)
        warning_threshold_percent = current_settings.get("rpm_warning_threshold_percent", 75)
        warning_threshold_value = limit * (warning_threshold_percent / 100.0)

        text_color_hex = "#00FF00"
        status_text = f"RPM: {current_rpm}/{limit}"

        if self.is_rpm_cooldown_active:
            now = time.monotonic()
            if now < self.rpm_cooldown_end_time:
                remaining_cooldown = int(self.rpm_cooldown_end_time - now)
                status_text = f"RPM Limit Reached! Cooldown: {remaining_cooldown}s"
                text_color_hex = "#FF0000"
            else:
                self.is_rpm_cooldown_active = False
                logger.info("RPM cooldown finished.")
                self.statusBar.showMessage("RPM cooldown finished. Resuming translations...", 3000)
                if self.pending_translation_jobs and self.active_translation_jobs == 0 :
                    self.translation_timer.start(0)
        
        if not self.is_rpm_cooldown_active:
            if current_rpm >= limit:
                text_color_hex = "#FF0000"
                status_text += " (Limit Reached!)"
            elif current_rpm >= warning_threshold_value:
                text_color_hex = "#FFA500"
        
        self.rpm_status_label.setText(status_text)
        self.rpm_status_label.setStyleSheet(f"QLabel {{ color : {text_color_hex}; font-weight: bold; }}")


    def create_actions(self):
        self.open_action=QtGui.QAction(QtGui.QIcon.fromTheme("document-open"),"&Open...",self); self.open_action.setShortcut(QtGui.QKeySequence.Open); self.open_action.triggered.connect(self.browse_and_load)
        self.save_action=QtGui.QAction(QtGui.QIcon.fromTheme("document-save"),"&Save As...",self); self.save_action.setShortcut(QtGui.QKeySequence.SaveAs); self.save_action.triggered.connect(self.export_json); self.save_action.setEnabled(False)
        self.exit_action=QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"),"E&xit",self); self.exit_action.setShortcut(QtGui.QKeySequence.Quit); self.exit_action.triggered.connect(self.close)
        self.settings_action=QtGui.QAction(QtGui.QIcon.fromTheme("preferences-system"),"&Settings...",self); self.settings_action.triggered.connect(self.open_settings_dialog)
        self.toggleModelInspectorAction=QtGui.QAction("Model Inspector",self,checkable=True); self.toggleModelInspectorAction.setStatusTip("Show/Hide model inspector"); self.toggleModelInspectorAction.triggered.connect(self.toggle_model_inspector)
        self.about_action = QtGui.QAction("About", self); self.about_action.triggered.connect(self.show_about_dialog)


    def create_menus(self):
        self.file_menu=self.menuBar().addMenu("&File"); self.file_menu.addAction(self.open_action)
        self.recent_menu = self.file_menu.addMenu("Open &Recent"); self.file_menu.addSeparator()
        self.file_menu.addAction(self.save_action); self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_action); self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        self.view_menu=self.menuBar().addMenu("&View"); self.view_menu.addAction(self.toggleModelInspectorAction)
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.about_action)

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()


    def update_recent_files(self, new_path):
        if not new_path: return
        if new_path in self.recent_files: self.recent_files.remove(new_path)
        self.recent_files.insert(0, new_path); self.recent_files = self.recent_files[:MAX_RECENT_FILES]
        current_settings["recent_files"] = self.recent_files

    def update_recent_files_menu(self):
        if not self.recent_menu: return
        self.recent_menu.clear()
        self.recent_files = [path for path in current_settings.get("recent_files", []) if path and os.path.exists(path)]
        current_settings["recent_files"] = self.recent_files
        
        if not self.recent_files: self.recent_menu.setEnabled(False); return
        
        self.recent_menu.setEnabled(True)
        for i, path in enumerate(self.recent_files):
            action_text = f"&{i+1}. {os.path.basename(path)}"; action = QtGui.QAction(action_text, self)
            action.setData(path); action.triggered.connect(self.load_file_from_history_action); self.recent_menu.addAction(action)
        self.recent_menu.addSeparator(); clear_action = QtGui.QAction("Clear Recent Files List", self)
        clear_action.triggered.connect(self.clear_recent_files_list_action); self.recent_menu.addAction(clear_action)

    def load_file_from_history_action(self):
        action = self.sender()
        if action and isinstance(action, QtGui.QAction):
            path = action.data()
            if path and os.path.exists(path):
                if self.active_translation_jobs > 0:
                    QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot load a new file while translations are in progress.")
                    return
                self.file_input.setText(path); self.load_file()
            elif path:
                QtWidgets.QMessageBox.warning(self, "File Not Found", f"The file '{path}' no longer exists.")
                if path in current_settings["recent_files"]:
                    current_settings["recent_files"].remove(path)
                    save_settings()
                    self.update_recent_files_menu()

    def clear_recent_files_list_action(self):
        reply = QtWidgets.QMessageBox.question(self, "Clear Recent Files", "Are you sure you want to clear the list of recent files?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes: 
            self.recent_files.clear()
            current_settings["recent_files"] = []
            save_settings()
            self.update_recent_files_menu(); 
            logger.info("Recent files list cleared.")

    def toggle_model_inspector(self):
        if not self.model_inspector_window: self.model_inspector_window = ModelInspectorDialog(self)
        if self.model_inspector_window.isVisible(): self.model_inspector_window.hide(); self.toggleModelInspectorAction.setChecked(False); logger.debug("Inspector hidden.")
        else: self.model_inspector_window.show(); self.model_inspector_window.raise_(); self.model_inspector_window.activateWindow(); self.toggleModelInspectorAction.setChecked(True); logger.debug("Inspector shown.")

    def open_settings_dialog(self):
        global current_settings
        dialog = SettingsDialog(current_settings, self)
        dialog.clear_cache_requested.connect(self.handle_clear_cache_request)

        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_settings_data = dialog.get_settings()
            api_key_changed = current_settings.get("api_key", "") != new_settings_data.get("api_key", "")
            model_changed = current_settings.get("gemini_model", default_settings["gemini_model"]) != new_settings_data.get("gemini_model", default_settings["gemini_model"])

            current_settings.update(new_settings_data)
            save_settings()
            self.apply_settings_effects(api_key_changed=api_key_changed, model_changed=model_changed)
            logger.info("Settings updated.")
            if hasattr(self, 'log_panel') and self.log_panel.isVisible() != current_settings.get("show_log_panel", True):
                self.log_panel.setVisible(current_settings.get("show_log_panel", True))


    def handle_clear_cache_request(self):
        if not self.cache_file_path: QtWidgets.QMessageBox.information(self, "Info", "No LORE-book loaded, so no specific cache to clear."); logger.info("Clear cache request: No active lorebook cache file path."); return
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Cache Clear', f"Clear translation cache for the current file?\n({os.path.basename(self.cache_file_path)})", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.cache.clear()
            cache_file_existed_and_deleted = False
            if os.path.exists(self.cache_file_path):
                try: 
                    os.remove(self.cache_file_path)
                    logger.info(f"Cache file {self.cache_file_path} deleted.")
                    cache_file_existed_and_deleted = True
                except Exception as e: 
                    logger.error(f"Failed to delete cache file {self.cache_file_path}: {e}")
                    QtWidgets.QMessageBox.warning(self, "Cache Clear Error", f"Could not delete cache file: {e}")
            else: 
                logger.info(f"Cache file {self.cache_file_path} not found (already cleared or never existed).")

            if cache_file_existed_and_deleted:
                QtWidgets.QMessageBox.information(self, "Cache Cleared", f"Cache file {os.path.basename(self.cache_file_path)} and in-memory cache cleared.")
            else:
                QtWidgets.QMessageBox.information(self, "Cache Cleared", "In-memory cache cleared. Cache file was not found or could not be deleted.")

            if self.data: self.populate_table_data()
            self.statusBar.showMessage(f"Cache for {os.path.basename(self.input_path)} cleared.")

    def apply_settings_effects(self, api_key_changed=True, model_changed=True):
        setup_logger()
        self.apply_rpm_settings_effects()

        if hasattr(self, 'log_panel'):
            self.log_panel.setVisible(current_settings.get("show_log_panel", True))
        
        if api_key_changed or model_changed:
            try:
                logger.info("Applying API/model settings...")
                if api_key_changed and current_settings.get("api_key"):
                    genai.configure(api_key=current_settings["api_key"])
                    logger.info("Gemini API key reconfigured.")
                elif api_key_changed and not current_settings.get("api_key"):
                    logger.warning("API key is empty. Gemini API not configured.")

                if current_settings.get("api_key") and (model_changed or api_key_changed or not self.gemini_model) :
                    model_name_to_init = current_settings.get("gemini_model", default_settings["gemini_model"])
                    logger.info(f"Gemini model (re)initializing to: {model_name_to_init}")
                    self.gemini_model = genai.GenerativeModel(model_name=model_name_to_init);
                    logger.info(f"Gemini model (re)initialized successfully: {self.gemini_model.model_name}")
                elif not current_settings.get("api_key"):
                    self.gemini_model = None
                    logger.warning("Gemini model not initialized due to missing API key.")
            except Exception as e:
                logger.error(f"Failed API/model settings application: {e}", exc_info=True);
                QtWidgets.QMessageBox.critical(self, "Model Re-init Error", f"Could not apply API/model settings:\n{e}")
                self.gemini_model = None


    def browse_and_load(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot load a new file while translations are in progress.")
            return
        if self.browse_file(): self.load_file()

    def browse_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open LORE-book', os.path.expanduser("~"), 'LORE-book (*.json);;All Files (*)')
        if path: self.file_input.setText(path); logger.info(f"Selected LORE-book: {path}"); return True
        return False

    def load_cache(self):
        self.cache = {}

        if not self.cache_file_path:
            logger.info("Cache file path is not set (e.g., no LORE-book loaded). " "Starting with an empty in-memory cache.")
            return

        if os.path.exists(self.cache_file_path):
            logger.info(f"Attempting to load cache from: {self.cache_file_path}")
            try:
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    loaded_cache_data = json.load(f)
                
                if isinstance(loaded_cache_data, dict):
                    self.cache = loaded_cache_data
                    logger.info(f"Successfully loaded cache from: {self.cache_file_path} " f"({len(self.cache)} entries)")
                else:
                    logger.error(f"ERROR: Cache file '{self.cache_file_path}' exists but does not " f"contain a valid JSON dictionary structure. " "Starting with an empty cache for this session.")
                    QtWidgets.QMessageBox.warning(self, "Cache Load Error", f"The cache file:\n{self.cache_file_path}\n" "is not in the expected format (not a JSON dictionary).\n\n" "An empty cache will be used for this session. " "Please check or delete the cache file manually if it's corrupted.")
            except json.JSONDecodeError as e:
                logger.error(f"ERROR parsing JSON from cache file '{self.cache_file_path}': {e}. " "Starting with an empty cache for this session.")
                QtWidgets.QMessageBox.warning(self, "Cache Parse Error", f"Could not parse JSON from the cache file:\n" f"{self.cache_file_path}\n\nError: {e}\n\n" "An empty cache will be used for this session. " "The corrupted cache file will NOT be overwritten automatically. " "Please check or delete it manually.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading cache from " f"'{self.cache_file_path}': {e}", exc_info=True)
                QtWidgets.QMessageBox.critical(self, "Cache Load Error", f"An unexpected error occurred while loading the cache file:\n" f"{self.cache_file_path}\n\nError: {e}\n\n" "An empty cache will be used for this session.")
        else: 
            logger.info(f"No cache file found at '{self.cache_file_path}'. "
                        "Starting with an empty in-memory cache for this LORE-book.")

    def load_file(self):
        path = self.file_input.text().strip()
        if not path: 
            QtWidgets.QMessageBox.warning(self, "No File", "No LORE-book path selected."); return
        if not os.path.exists(path): 
            QtWidgets.QMessageBox.critical(self, 'Error', f'File not found: {path}'); 
            logger.error(f'LORE-book file not found: {path}'); return

        if self.input_path and self.cache_file_path and self.cache:
            self.save_cache()

        self._cancel_batch_translation(silent=True)

        self.input_path = path
        base_name, _ = os.path.splitext(os.path.basename(self.input_path))
        self.cache_file_path = os.path.join(os.path.dirname(self.input_path), f"{base_name}_translation_cache.json")
        logger.info(f"Set active LORE-book: {self.input_path}")
        logger.info(f"Set active cache file to: {self.cache_file_path}")

        logger.info(f"Loading LORE-book from: {path}")
        self.statusBar.showMessage(f"Loading {os.path.basename(path)}...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            with open(path, 'r', encoding='utf-8') as f: 
                self.data = json.load(f)

            if self.data and 'entries' in self.data and isinstance(self.data['entries'], dict):
                for _entry_dict_key, entry_item_data in self.data['entries'].items():
                    self._ensure_entry_key_is_list(entry_item_data)
                logger.info("LORE-book entries normalized ('key' as list, 'keys' removed).")

            logger.info(f"Loaded LORE-book. Entries: {len(self.data.get('entries', {})) if self.data else 'N/A'}")
            self.save_action.setEnabled(True if self.data else False)
            self.update_recent_files(self.input_path)
            self.update_recent_files_menu()
            save_settings()
        except json.JSONDecodeError as e:
            QtWidgets.QMessageBox.critical(self, 'LORE-book Load Error', f'Failed to parse JSON from LORE-book file: {e}'); 
            logger.error(f'LORE-book load/parse error {path}: {e}'); 
            self.data = None; self.input_path = None; self.cache_file_path = None; self.save_action.setEnabled(False)
            self.table_data.clear(); self.update_table_widget()
            self.statusBar.showMessage(f"Error loading LORE-book: {os.path.basename(path)}.")
            return
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'LORE-book Load Error', f'Failed to load LORE-book file: {e}'); 
            logger.error(f'LORE-book load error {path}: {e}', exc_info=True); 
            self.data = None; self.input_path = None; self.cache_file_path = None; self.save_action.setEnabled(False)
            self.table_data.clear(); self.update_table_widget()
            self.statusBar.showMessage(f"Error loading LORE-book: {os.path.basename(path)}.")
            return
        finally: 
            QtWidgets.QApplication.restoreOverrideCursor()

        if not self.data or 'entries' not in self.data or not isinstance(self.data['entries'], dict): 
            QtWidgets.QMessageBox.critical(self, 'Invalid LORE-book', 'Invalid LORE-book format: Missing "entries" dictionary or data is null.'); 
            logger.error(f'Invalid LORE-book format: {path}.'); 
            self.data = None; self.input_path = None; self.cache_file_path = None; self.save_action.setEnabled(False); 
            self.table_data.clear(); self.update_table_widget(); 
            self.statusBar.showMessage("Invalid LORE-book format.")
            return

        self.load_cache()
        self.populate_table_data()
        self.statusBar.showMessage(f"Loaded {os.path.basename(path)}. {len(self.table_data)} displayable keys.")


    def populate_table_data(self):
        if not self.data or 'entries' not in self.data:
            self.table_data.clear()
            self.update_table_widget()
            return

        entries = self.data.get('entries', {})
        new_table_data = []

        current_target_lang = self.current_target_language
        current_source_lang = self.current_source_language
        if not current_source_lang:
            logger.error("Cannot populate table: LORE-book source language (current_source_lang) is not set.")
            self.table_data.clear()
            self.update_table_widget()
            return

        for entry_dict_key, entry_data_val in entries.items():
            uid_val = entry_data_val.get('uid')
            if uid_val is None:
                logger.warning(f"Entry with dict key '{entry_dict_key}' is missing 'uid' field. Skipping display.")
                continue
            uid_val_str = str(uid_val)

            original_keys_from_lore_field = entry_data_val.get('key', [])
            
            if not isinstance(original_keys_from_lore_field, list) or not original_keys_from_lore_field:
                logger.warning(f"Entry UID {uid_val_str} (dict key {entry_dict_key}) 'key' field is missing, not a list, or empty. Skipping display.")
                continue

            full_content = entry_data_val.get('content', '')

            for orig_key_text_from_lore in original_keys_from_lore_field:
                orig_key_to_display_in_table = str(orig_key_text_from_lore).strip()
                
                if not orig_key_to_display_in_table:
                    continue

                cached_translation_text = ""
                if current_target_lang:
                    cache_key_for_lookup = self._generate_cache_key(uid_val_str, orig_key_to_display_in_table, current_source_lang, current_target_lang)
                    cached_translation_text = str(self.cache.get(cache_key_for_lookup, "")).strip()
                
                new_table_data.append([uid_val_str, orig_key_to_display_in_table, cached_translation_text, full_content])

        self.table_data = new_table_data
        logger.debug(f"Populated table with {len(self.table_data)} displayable original key(s)/rows for target language '{current_target_lang or 'N/A'}'.")
        self.update_table_widget()

    def update_table_widget(self):
        self.table.setRowCount(0)
        current_target_lang_for_header = self.current_target_language
        header_label = f'Translated ({current_target_lang_for_header if current_target_lang_for_header else "N/A"})'
        self.table.setHorizontalHeaderLabels(['UID', 'Original Key', header_label, 'Content Preview'])

        if not self.table_data:
            return

        self.table.setRowCount(len(self.table_data))
        try:
            self.table.setUpdatesEnabled(False)
            for r, row_content in enumerate(self.table_data):
                if len(row_content) == 4:
                    uid_val_str, orig, trans, content = row_content
                    self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(uid_val_str))
                    self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(orig))
                    self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(trans))
                    
                    preview_content = str(content).replace("\n", " ")
                    max_preview_len = 150
                    if len(preview_content) > max_preview_len:
                        preview_content = preview_content[:max_preview_len-3] + "..."
                    self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(preview_content))
                else:
                    logger.warning(f"Row {r} in table_data has unexpected format: {row_content}. Skipping.")
        finally:
            self.table.setUpdatesEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Interactive)
        
        self.table.resizeColumnsToContents()

        header.setMinimumSectionSize(50) 
        if self.table.columnWidth(0) < 60 : self.table.setColumnWidth(0,60)
        if self.table.columnWidth(1) < 150 : self.table.setColumnWidth(1,150)
        if self.table.columnWidth(2) < 150 : self.table.setColumnWidth(2,150)
        
        preview_col_width = self.table.columnWidth(3)
        desired_preview_min = 150
        desired_preview_initial_max = 300
        
        if preview_col_width < desired_preview_min:
            self.table.setColumnWidth(3, desired_preview_min)
        elif preview_col_width > desired_preview_initial_max:
            self.table.setColumnWidth(3, desired_preview_initial_max)

    def on_cell_click(self, row, column):
        if self.active_translation_jobs > 0:
            logger.debug("Cell click ignored during active translation jobs.")
            self.table.clearSelection()
            return

        if not (0 <= row < len(self.table_data)):
            logger.warning(f"Cell click on row {row} is out of bounds for current table data ({len(self.table_data)} rows). Clearing editor.")
            self.orig_label.clear(); self.trans_edit.clear(); self.full_content_display.clear();
            self.current_row = None; self.current_orig_key_for_editor = None; self.current_translation_in_editor_before_change = None
            self.table.clearSelection()
            return

        self.current_row = row
        _uid_val_str, orig_key_in_row, trans_in_row, full_content_of_entry = self.table_data[row]
        
        self.orig_label.setText(orig_key_in_row);
        self.trans_edit.setText(trans_in_row);
        self.full_content_display.setPlainText(full_content_of_entry); 
        
        self.current_orig_key_for_editor = orig_key_in_row
        self.current_translation_in_editor_before_change = trans_in_row
        logger.debug(f"Cell clicked: R{row}, UID in Row: '{_uid_val_str}', Original Key in Row: '{orig_key_in_row}', Translation in Row: '{trans_in_row}'. Stored for editor state.")


    def _generate_cache_key(self, uid, text_to_translate, source_lang, target_lang):
        uid_str = str(uid).strip()
        src = str(source_lang).strip()
        tgt = str(target_lang).strip()
        text_clean = str(text_to_translate).strip()
        text_hash = hashlib.sha256(text_clean.encode('utf-8')).hexdigest()[:16]
        return f"{uid_str}_{src}_{tgt}_{text_hash}"

    def _update_translation_cache(self, uid_val_for_lookup, orig_key_for_this_op, new_translation_value, source_lang, target_lang):
        if not uid_val_for_lookup or not orig_key_for_this_op or not target_lang or not source_lang:
            logger.warning(f"Cache not updated for UID '{uid_val_for_lookup}', Orig '{orig_key_for_this_op}': " f"missing critical identifiers (UID, OrigKey, SrcLang, TrgLang).")
            return False

        cache_key = self._generate_cache_key(uid_val_for_lookup, orig_key_for_this_op, source_lang, target_lang)
        new_trans_norm = str(new_translation_value).strip() if new_translation_value is not None else None

        if new_trans_norm:
            self.cache[cache_key] = new_trans_norm
            logger.info(f"Stored/Updated in cache: K='{cache_key}' V='{new_trans_norm}'")
        elif cache_key in self.cache:
            del self.cache[cache_key]
            logger.info(f"Removed from cache: K='{cache_key}'")
        else:
            logger.debug(f"Cache key '{cache_key}' not found for removal, and new translation is empty. No cache change.")
        return True

    def save_edited_translation(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot save manual edits while translations are in progress.")
            return
        if self.current_row is None or not (0 <= self.current_row < len(self.table_data)): 
            QtWidgets.QMessageBox.warning(self, "Warning", "No row selected to save."); 
            logger.warning("Save edited: No row selected."); return

        row_data_idx = self.current_row
        uid_val_str, orig_key_from_table_row, _ , full_content_of_lore_entry = self.table_data[row_data_idx]
        if self.current_orig_key_for_editor != orig_key_from_table_row:
            logger.warning(f"Editor's original key context ('{self.current_orig_key_for_editor}') does not match selected table row's original key ('{orig_key_from_table_row}'). Aborting save.")
            QtWidgets.QMessageBox.warning(self, "Save Error", "Editor state mismatch with table selection. Please re-select the row and try again.")
            return

        new_trans_from_editor_field = self.trans_edit.text().strip()
        old_trans_that_was_in_editor_field = self.current_translation_in_editor_before_change


        current_target_lang_for_op = self.current_target_language

        if not current_target_lang_for_op:
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Cannot save translation: No target language selected."); return

        current_source_lang_for_op = self.current_source_language
        if not current_source_lang_for_op:
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Cannot save translation: LORE-book source language is not selected.")
            return

        update_cache_success = self._update_translation_cache(uid_val_str, orig_key_from_table_row, new_trans_from_editor_field, current_source_lang_for_op, current_target_lang_for_op)

        if update_cache_success:
            self.table_data[row_data_idx][2] = new_trans_from_editor_field
            table_item_to_update = self.table.item(row_data_idx, 2)
            if table_item_to_update: table_item_to_update.setText(new_trans_from_editor_field)
            else: self.table.setItem(row_data_idx, 2, QtWidgets.QTableWidgetItem(new_trans_from_editor_field))
            self.current_translation_in_editor_before_change = new_trans_from_editor_field
            self.save_cache()
            self.statusBar.showMessage(f"Translation for '{orig_key_from_table_row}' (UID {uid_val_str}) saved for {current_target_lang_for_op}.", 5000)
            logger.info(f"Manually saved translation for '{orig_key_from_table_row}' (UID {uid_val_str}) to '{new_trans_from_editor_field}' for {current_target_lang_for_op}.")
        else:
            self.statusBar.showMessage(f"Failed to update LORE data for UID {uid_val_str}.", 5000)
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to update LORE data for entry with UID {uid_val_str}. Check logs.")

    def delete_current_translation(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot delete translation while other translations are in progress.")
            return
        if self.current_row is None or not (0 <= self.current_row < len(self.table_data)): 
            QtWidgets.QMessageBox.warning(self, "Warning", "No row selected to delete translation from."); return

        row_data_idx = self.current_row
        uid_val_str, orig_key_from_table_row, current_trans_in_table_cell, full_content_of_lore_entry = self.table_data[row_data_idx]

        if self.current_orig_key_for_editor != orig_key_from_table_row:
            logger.warning(f"Editor's original key context ('{self.current_orig_key_for_editor}') does not match selected table row's original key ('{orig_key_from_table_row}'). Aborting delete.")
            QtWidgets.QMessageBox.warning(self, "Delete Error", "Editor state mismatch with table selection. Please re-select the row and try again.")
            return

        current_target_lang_for_op = self.current_target_language
        if not current_target_lang_for_op:
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Cannot delete translation: No target language selected."); return

        string_to_delete_from_lore = current_trans_in_table_cell.strip()

        if not string_to_delete_from_lore:
            QtWidgets.QMessageBox.information(self, "Info", "No translation to delete for this key and language in the table cell.")
            return

        reply = QtWidgets.QMessageBox.question(self, 'Confirm Delete', f"Delete translation '{string_to_delete_from_lore}' for original key '{orig_key_from_table_row}' (UID {uid_val_str}, language: {current_target_lang_for_op})?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            current_source_lang_for_op = self.current_source_language
            if not current_source_lang_for_op:
                QtWidgets.QMessageBox.warning(self, "No Source Language", "Cannot delete translation: LORE-book source language is not selected.")
                logger.warning("delete_current_translation: Aborted due to missing current_source_language.")
                return
            update_cache_success = self._update_translation_cache(uid_val_for_lookup=uid_val_str, orig_key_for_this_op=orig_key_from_table_row, new_translation_value="", source_lang=current_source_lang_for_op,target_lang=current_target_lang_for_op)

            if update_cache_success:
                self.table_data[row_data_idx][2] = "" 
                table_item_to_update = self.table.item(row_data_idx, 2)
                if table_item_to_update: 
                    table_item_to_update.setText("")
                else:
                    self.table.setItem(row_data_idx, 2, QtWidgets.QTableWidgetItem(""))
                
                if self.current_orig_key_for_editor == orig_key_from_table_row:
                    self.trans_edit.clear()
                    self.current_translation_in_editor_before_change = ""

                self.save_cache()
                logger.info(f"Deleted translation from cache for original key '{orig_key_from_table_row}' (UID {uid_val_str}, lang: {current_target_lang_for_op}).")
                self.statusBar.showMessage(f"Translation for '{orig_key_from_table_row}' (UID {uid_val_str}, lang: {current_target_lang_for_op}) deleted from cache.", 5000)
            else:
                self.statusBar.showMessage(f"Failed to update cache for UID {uid_val_str} during delete.", 5000)
                QtWidgets.QMessageBox.critical(self, "Delete Error", f"Failed to update cache for entry with UID {uid_val_str}. Check logs.")

    def save_cache(self):
        if not self.cache_file_path: 
            logger.debug("Cache file path not set. Cannot save cache.")
            return
        if not self.cache:
            logger.info(f"In-memory cache is empty. No data to save to {self.cache_file_path}.")
            return

        try:
            temp_cache_path = self.cache_file_path + ".tmp"
            with open(temp_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            os.replace(temp_cache_path, self.cache_file_path)
            logger.info(f"Cache saved to: {self.cache_file_path} ({len(self.cache)} entries)")
        except Exception as e:
            logger.error(f"Cache Save Error to {self.cache_file_path}: {e}", exc_info=True)
            try:
                if os.path.exists(temp_cache_path): os.remove(temp_cache_path)
            except Exception as e_rem:
                logger.error(f"Failed to remove temporary cache file {temp_cache_path} after save error: {e_rem}")

    def _execute_gemini_api_call_internal(self, text_to_translate, source_lang_name_for_prompt, target_lang_name_for_prompt, context_content_for_api_call):
        prompt_for_inspector = "Error: Prompt not captured."
        full_raw_api_response = "Error: Response not captured."
        metadata_and_thinking_text = "No metadata or thinking captured."
        final_processed_translation = None
        thinking_content = None

        base_prompt_template = (
            "You are a master linguist and loremaster specializing in video game localization. "
            "Your task is to translate LORE keywords from {source_language_name} into {target_language_name}.\n\n"
            "Instructions:\n"
            "The translation MUST be concise, accurate, and function effectively as a search key or in-game display term.\n"
            "For proper nouns (character names, specific unique locations, named items/technologies):\n"
            "    *   Prioritize officially localized terms or widely accepted community translations for {target_language_name} if they exist for the specific game world this LORE belongs to.\n"
            "    *   If no established translation exists, provide a phonetically accurate and natural-sounding transliteration.\n"
            "    *   If the term is a common {source_language_name} word used as a name (e.g., 'The Afterlife' club in English), translate it if a direct, natural, and fitting equivalent exists in {target_language_name}; otherwise, transliterate or use the original {source_language_name} if that's common practice.\n"
            "{thinking_instructions}\n\n"
            "{context_instructions}\n"
            "\n\nNow, process the following:"
            " {source_language_name} keyword: \"{keyword}\"\n"
            "{target_language_name} translation:"
        )

        context_instructions_text = ""
        thinking_instructions_text = ""
        context_section_text_for_prompt = "No additional context provided for this API call."
        
        enable_thinking = current_settings.get("enable_model_thinking", False)

        if context_content_for_api_call:
            stripped_context = str(context_content_for_api_call).strip()
            if stripped_context:
                context_instructions_text = "The provided context (inside <context> tags) is CRUCIAL. Analyze it carefully to understand the keyword's meaning, usage, and significance within the LORE. This will help you decide between translation, transliteration, or neologism.\n" \
                "\n<context>\n{context_section}\n</context>"
                context_section_text_for_prompt = stripped_context
            else:
                pass

        if enable_thinking:
            thinking_instructions_text = (
            "Provide your thinking process, if any, wrapped in HTML-like <Thinking>...</Thinking> tags. This is for debugging and understanding your process. The thinking process should be clear and concise.\n"
            "Your final, concise translation MUST be wrapped in HTML-like <Response>...</Response> tags. The content within <Response> should be ONLY the translation, suitable as a search key or in-game display term, with no extra explanations or quotation marks around or inside the <Response> content itself (unless they are part of the translation).\n\n"
            "   Example of output format if thinking is provided:\n"
            "   <Thinking>\n"
            "   The keyword is 'Example'. Target language is Ukrainian.\n"
            "   This is a common noun. Direct translation is 'Зразок'.\n"
            "   Context suggests it's used as a general term.\n"
            "   </Thinking>\n"
            "   <Response>Зразок</Response>\n\n"
            "   Example of output format if no thinking is provided (or you choose not to output thinking):\n"
            "   <Response>Зразок</Response>"
            )
        else:
            thinking_instructions_text = "Your SOLE output MUST be the translated keyword/phrase. Do NOT include any surrounding text, explanations, or quotation marks.\n" \
            "Provide ONLY the final translation, with no other text, tags, or quotation marks."

        try:
            formatted_context_instructions = context_instructions_text.format(context_section=context_section_text_for_prompt) if "{context_section}" in context_instructions_text else context_instructions_text

            prompt_for_inspector = base_prompt_template.format(source_language_name=source_lang_name_for_prompt, target_language_name=target_lang_name_for_prompt, keyword=text_to_translate, context_instructions=formatted_context_instructions, thinking_instructions=thinking_instructions_text)
        except KeyError as e_f:
            logger.error(f"Prompt format error (KeyError: '{e_f}'). This should not happen.")
            return prompt_for_inspector, "N/A - Prompt format error", f"INTERNAL PROMPT FORMAT ERROR: Missing key '{e_f}'.", ""


        logger.info(f"API Call: Translating '{text_to_translate}' from '{source_lang_name_for_prompt}' to '{target_lang_name_for_prompt}' (thinking: {enable_thinking}, ctx: {bool(context_content_for_api_call and str(context_content_for_api_call).strip())})")

        metadata_parts_collector = []
        try:
            safety_settings_config = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            if not self.gemini_model:
                logger.error("Gemini model not initialized. Cannot translate.")
                return prompt_for_inspector, "Error: Gemini model not initialized.", "Error: Gemini model not initialized.", ""


            gen_config = genai.types.GenerationConfig(
                # temperature=2.0,
                # top_p=0.95,
                # stop_sequences=[f"<Response>", "<Thinking>"]
            )

            response = self.gemini_model.generate_content(
                prompt_for_inspector,
                generation_config=gen_config,
                safety_settings=safety_settings_config
            )

            current_raw_response_text_intermediate = "Error: Could not extract raw response or candidates list was empty."
            try:
                if hasattr(response, 'text') and response.text:
                    current_raw_response_text_intermediate = response.text
                elif response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        current_raw_response_text_intermediate = "".join(p.text for p in candidate.content.parts if hasattr(p, 'text'))
                    elif hasattr(candidate, 'finish_reason') and candidate.finish_reason == genai.types.Candidate.FinishReason.SAFETY:
                        safety_ratings_text = " ".join([f"{r.category.name}:{r.probability.name}" for r in candidate.safety_ratings if hasattr(r, 'category') and hasattr(r, 'probability')]) if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings else "No specific ratings."
                        current_raw_response_text_intermediate = f"Error: Response blocked due to safety settings. Ratings: {safety_ratings_text}"
                        logger.warning(f"Candidate response blocked due to safety settings for '{text_to_translate}'. Candidate: {candidate}")
                    else:
                        finish_reason_str = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
                        current_raw_response_text_intermediate = f"Error: Candidate has no processable content. Finish Reason: {finish_reason_str}"
                        logger.warning(f"Candidate present but no text found for '{text_to_translate}'. Candidate: {candidate}")
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    block_reason_name = response.prompt_feedback.block_reason.name if hasattr(response.prompt_feedback.block_reason, 'name') else str(response.prompt_feedback.block_reason)
                    block_message = getattr(response.prompt_feedback, 'block_reason_message', '')
                    safety_ratings_text = " ".join([f"{r.category.name}:{r.probability.name}" for r in response.prompt_feedback.safety_ratings if hasattr(r, 'category') and hasattr(r, 'probability')]) if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings else "No specific ratings."
                    current_raw_response_text_intermediate = f"Error: Prompt blocked - {block_reason_name}. Message: {block_message}. Ratings: {safety_ratings_text}"
                    logger.error(f"Prompt blocked for '{text_to_translate}': {current_raw_response_text_intermediate}")
                else:
                    logger.warning(f"Unrecognized response structure or empty response for '{text_to_translate}'. Full response object: {response}")
                    current_raw_response_text_intermediate = "Error: Unrecognized response structure or empty candidates list."
            except AttributeError as e_a:
                current_raw_response_text_intermediate = f"Error during raw response extraction (AttributeError): {e_a}\nResponse Obj: {response}"
                logger.error(current_raw_response_text_intermediate, exc_info=True)
            except Exception as e_r:
                current_raw_response_text_intermediate = f"Error during raw response extraction: {type(e_r).__name__} - {e_r}\nResponse Obj: {response}"
                logger.error(current_raw_response_text_intermediate, exc_info=True)

            full_raw_api_response = current_raw_response_text_intermediate

            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                metadata_parts_collector.append("[Usage Metadata]")
                metadata_parts_collector.append(f"  Prompt Tokens: {getattr(response.usage_metadata, 'prompt_token_count', 'N/A')}")
                cand_tokens = getattr(response.usage_metadata, 'candidates_token_count', getattr(response.usage_metadata, 'candidate_token_count', 'N/A'))
                metadata_parts_collector.append(f"  Candidates Tokens: {cand_tokens}")
                metadata_parts_collector.append(f"  Total Tokens: {getattr(response.usage_metadata, 'total_token_count', 'N/A')}")

            if hasattr(response, 'prompt_feedback') and (response.prompt_feedback.block_reason or (hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings)):
                metadata_parts_collector.append("\n[Prompt Feedback]")
                block_reason_val = response.prompt_feedback.block_reason
                metadata_parts_collector.append(f"  Block Reason: {block_reason_val.name if hasattr(block_reason_val, 'name') else block_reason_val}")
                if hasattr(response.prompt_feedback, 'block_reason_message') and response.prompt_feedback.block_reason_message:
                    metadata_parts_collector.append(f"  Block Reason Message: {response.prompt_feedback.block_reason_message}")
                if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                    for rating in response.prompt_feedback.safety_ratings: 
                        if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                            metadata_parts_collector.append(f"  Safety (Prompt): {rating.category.name} - {rating.probability.name}")
            
            if hasattr(response, 'candidates') and response.candidates:
                for i, candidate_item in enumerate(response.candidates):
                    if hasattr(candidate_item,'finish_reason') or (hasattr(candidate_item, 'safety_ratings') and candidate_item.safety_ratings):
                        metadata_parts_collector.append(f"\n[Candidate {i+1}]")
                        if hasattr(candidate_item, 'finish_reason'):
                            finish_reason_name = candidate_item.finish_reason.name if hasattr(candidate_item.finish_reason, 'name') else str(candidate_item.finish_reason)
                            metadata_parts_collector.append(f"  Finish Reason: {finish_reason_name}")
                        if hasattr(candidate_item, 'safety_ratings') and candidate_item.safety_ratings:
                            for rating in candidate_item.safety_ratings: 
                                if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                                    metadata_parts_collector.append(f"  Safety (Candidate): {rating.category.name} - {rating.probability.name}")


            extracted_translation_via_tag = None

            if enable_thinking:
                think_match = re.search(r"<Thinking>(.*?)</Thinking>", full_raw_api_response, re.DOTALL | re.IGNORECASE)
                resp_match = re.search(r"<Response>(.*?)</Response>", full_raw_api_response, re.DOTALL | re.IGNORECASE)

                if think_match:
                    thinking_content = think_match.group(1).strip()

                if resp_match:
                    extracted_translation_via_tag = resp_match.group(1).strip()
                    logger.debug(f"Extracted from <Response> tag: '{extracted_translation_via_tag}'")
                elif not full_raw_api_response.startswith("Error:"):
                    logger.warning(f"Thinking mode enabled, but <Response> tag not found in: '{full_raw_api_response[:100]}...' for '{text_to_translate}'. Using full response text after stripping any <Thinking> part.")
                    if think_match:
                        extracted_translation_via_tag = full_raw_api_response.replace(think_match.group(0), "").strip()
                    else:
                        extracted_translation_via_tag = full_raw_api_response.strip()

            if enable_thinking:
                final_processed_translation = extracted_translation_via_tag if extracted_translation_via_tag is not None else ""
            else: 
                raw_response_text = full_raw_api_response.strip()
                if raw_response_text.startswith("Error:"):
                    final_processed_translation = ""
                    logger.warning(f"API returned an error message for '{text_to_translate}': {raw_response_text}")
                elif len(raw_response_text) >= 2 and raw_response_text.startswith('"') and raw_response_text.endswith('"'):
                    final_processed_translation = raw_response_text[1:-1]
                elif len(raw_response_text) >= 2 and raw_response_text.startswith("'") and raw_response_text.endswith("'"):
                    final_processed_translation = raw_response_text[1:-1]
                else:
                    final_processed_translation = raw_response_text

            if not final_processed_translation and not full_raw_api_response.startswith("Error:"):
                logger.warning(f"Gemini API returned text that resulted in an empty translation for '{text_to_translate}'. Raw Response: '{full_raw_api_response[:100]}' Processed: '{final_processed_translation}'")

            logger.info(f"API Call Result for '{text_to_translate}' -> '{final_processed_translation}'")

        except genai.types.generation_types.BlockedPromptException as e_b:
            logger.error(f"Gemini API call failed for '{text_to_translate}' due to BLOCKED PROMPT: {e_b}", exc_info=True)
            full_raw_api_response = f"Exception: Prompt Blocked by API - {e_b}"
            metadata_parts_collector.append(f"\nAPI CALL EXCEPTION (Blocked Prompt): {e_b}")
            final_processed_translation = ""
        except Exception as e_api:
            error_type = type(e_api).__name__
            logger.error(f"Gemini API call failed for '{text_to_translate}': {error_type} - {e_api}", exc_info=True)
            full_raw_api_response = f"Exception during API call: {error_type} - {e_api}"
            metadata_parts_collector.append(f"\nAPI CALL EXCEPTION ({error_type}): {e_api}")
            final_processed_translation = ""
        metadata_and_thinking_text = "\n".join(metadata_parts_collector).strip() if metadata_parts_collector else "No specific API metadata found."
        # if thinking_content:
        #     metadata_and_thinking_text += f"\n\n[Model Thinking Process (if <Thinking> tag was present)]\n{thinking_content}"


        return prompt_for_inspector, full_raw_api_response, metadata_and_thinking_text, final_processed_translation if final_processed_translation is not None else ""


    def _get_translation_from_cache_or_prepare_job(self, orig_text_to_translate: str, source_lang: str, target_lang: str, uid: str, full_content_of_entry_for_api_context: str, force_regenerate: bool = False, prepare_only: bool = False):
        
        uid_str = str(uid)
        cache_key = self._generate_cache_key(uid_str, orig_text_to_translate, source_lang, target_lang)
        if cache_key in self.cache and not force_regenerate:
            cached_value = self.cache[cache_key]
            return cached_value, True
        if prepare_only:
            return None, False
        context_to_send_to_api = None
        if current_settings.get("use_content_as_context", True) and full_content_of_entry_for_api_context:
            stripped_lore_content = str(full_content_of_entry_for_api_context).strip()
            if stripped_lore_content:
                context_to_send_to_api = stripped_lore_content
        
        job_data = {'text_to_translate': orig_text_to_translate, 'source_lang': source_lang, 'target_lang': target_lang, 'uid_val_for_lookup': uid_str,'context_content_for_api': context_to_send_to_api}
        return job_data, False

    def _start_translation_batch(self, jobs_to_queue, operation_name="Translating"):
        if not self.gemini_model and not current_settings.get("api_key"):
            QtWidgets.QMessageBox.critical(self, "API Error", "Gemini model is not initialized, and/or API key is missing. Cannot start translation. Check API key and settings.")
            logger.error("Translation batch start failed: Gemini model not initialized or API key missing.")
            return
        elif not self.gemini_model: 
            QtWidgets.QMessageBox.critical(self, "API Error", "Gemini model is not initialized (e.g. invalid model name or API issue). Cannot start translation. Check settings & logs.")
            logger.error("Translation batch start failed: Gemini model not initialized (model name or other API issue).")
            return


        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Another translation batch is already running.")
            return

        if not jobs_to_queue:
            QtWidgets.QMessageBox.information(self, "No Work", f"No items found needing {operation_name.lower()}.")
            return

        current_target_lang = self.current_target_language
        if not current_target_lang:
            QtWidgets.QMessageBox.warning(self, "No Target Language", f"Cannot start {operation_name.lower()}: No target language selected.")
            return


        self.pending_translation_jobs.clear()
        if isinstance(jobs_to_queue, list) and all(isinstance(job, dict) for job in jobs_to_queue):
            for job_data in jobs_to_queue:
                self.pending_translation_jobs.append(job_data)
        else:
            logger.error(f"Invalid jobs_to_queue format for {operation_name}: {type(jobs_to_queue)}. Expected list of dicts.")
            QtWidgets.QMessageBox.critical(self, "Internal Error", "Invalid job data for batch operation.")
            return


        self.total_jobs_for_progress = len(self.pending_translation_jobs)
        self.completed_jobs_for_progress = 0


        if self.progress_dialog:
            self.progress_dialog.cancel()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

        self.progress_dialog = QtWidgets.QProgressDialog(f"{operation_name} {self.total_jobs_for_progress} item(s) for '{current_target_lang}'", "Cancel", 0, self.total_jobs_for_progress, self)

        dialog_title = f"{operation_name} Progress"
        self.progress_dialog.setWindowTitle(dialog_title)
        flags = self.progress_dialog.windowFlags()
        self.progress_dialog.setWindowFlags(flags & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.canceled.connect(self._cancel_batch_translation)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.show()

        logger.info(f"Starting batch operation: {operation_name} with {self.total_jobs_for_progress} item(s) for language '{current_target_lang}'.")
        self.statusBar.showMessage(f"{operation_name} {self.total_jobs_for_progress} item(s) for '{current_target_lang}'...")
        if self.total_jobs_for_progress > 0:
            self.translation_timer.start(0)


    def _dispatch_next_job_to_pool(self):

        if self.is_rpm_cooldown_active:
            now = time.monotonic()
            if now < self.rpm_cooldown_end_time:
                remaining_cooldown = int(self.rpm_cooldown_end_time - now) + 1
                logger.debug(f"RPM Cooldown active. Delaying dispatch for {remaining_cooldown}s.")
                self.translation_timer.start(remaining_cooldown * 1000)
                return 
            else:
                self.is_rpm_cooldown_active = False
                logger.info("RPM cooldown finished during dispatch check.")
                self.update_rpm_display_and_check_cooldown()

        if not self.pending_translation_jobs:
            if self.active_translation_jobs == 0:
                self._finalize_batch_translation("completed (no pending jobs and no active jobs)")
            else:
                logger.debug("No more pending jobs, but waiting for active jobs to complete.")
            return

        if self.progress_dialog and self.progress_dialog.wasCanceled():
            logger.warning("Dispatch loop interrupted because progress dialog was cancelled.")
            if self.active_translation_jobs == 0 and self.progress_dialog:
                self._finalize_batch_translation("cancelled before dispatching next job")
            return
        
        if self._is_rpm_limit_reached():
            if not self.is_rpm_cooldown_active:
                self.is_rpm_cooldown_active = True
                self.rpm_cooldown_end_time = time.monotonic() + 61
                rpm_limit_val = current_settings.get('rpm_limit', 60)
                logger.warning(f"RPM limit ({rpm_limit_val}) reached before dispatch. Starting 61s cooldown.")
                self.statusBar.showMessage(f"RPM limit ({rpm_limit_val}) reached! Pausing for 61s...", 5000)
                self.update_rpm_display_and_check_cooldown()
            remaining_cooldown_ms = max(0, int((self.rpm_cooldown_end_time - time.monotonic()) * 1000)) + 1000 
            logger.debug(f"RPM limit reached. Deferring dispatch. Rescheduling in {remaining_cooldown_ms / 1000:.1f}s")
            self.translation_timer.start(remaining_cooldown_ms)
            return

        job_data = self.pending_translation_jobs.popleft()
        self._record_api_request_timestamp()

        signals = JobSignals()
        signals.job_completed.connect(self._handle_job_completed)
        signals.job_failed.connect(self._handle_job_failed)
        signals.inspector_update.connect(self.handle_inspector_update)

        runnable = TranslationJobRunnable(self, job_data, signals)
        self.thread_pool.start(runnable)
        self.active_translation_jobs += 1

        logger.debug(f"Dispatched job for '{job_data['text_to_translate']}' (UID {job_data.get('uid_val_for_lookup', 'N/A')}). Active jobs: {self.active_translation_jobs}. Pending: {len(self.pending_translation_jobs)}")

        if self.pending_translation_jobs:
            delay_ms = int(current_settings.get("api_request_delay", 0.6) * 1000)
            self.translation_timer.start(max(delay_ms, 100))
        elif self.active_translation_jobs == 0:
            logger.debug("Last pending job dispatched, and no other active jobs. Finalizing soon if it completes.")

    def _handle_job_completed(self, job_data, translated_text):
        self.active_translation_jobs -= 1
        uid_val_for_lookup = job_data.get('uid_val_for_lookup', 'N/A')
        logger.info(f"Job completed for '{job_data.get('text_to_translate')}' (UID {uid_val_for_lookup}) -> '{translated_text}'. Active jobs remaining: {self.active_translation_jobs}")

        row_idx = job_data.get('row_idx', -1)
        orig_key_for_lore_update = job_data.get('text_to_translate')
        target_lang = job_data.get('target_lang', '')
        source_lang_from_job = job_data.get('source_lang')

        if not uid_val_for_lookup or not orig_key_for_lore_update or not target_lang or not source_lang_from_job:
            logger.error(f"Missing critical job_data in _handle_job_completed for cache update. UID: {uid_val_for_lookup}, OrigKey: {orig_key_for_lore_update}, TargetLang: {target_lang}, SourceLang: {source_lang_from_job}. Job: {job_data}")
            self._update_progress_dialog()
            if not self.pending_translation_jobs and self.active_translation_jobs == 0:
                self._finalize_batch_translation("completed with error in job_data for cache update")
            return

        update_cache_success = self._update_translation_cache(uid_val_for_lookup=uid_val_for_lookup, orig_key_for_this_op=orig_key_for_lore_update, new_translation_value=translated_text, source_lang=source_lang_from_job, target_lang=target_lang)

        if update_cache_success:
            if target_lang == self.current_target_language:
                if 0 <= row_idx < len(self.table_data):
                    current_uid_in_table_row, current_orig_in_table_row, _, _ = self.table_data[row_idx]
                    if str(current_uid_in_table_row) == str(uid_val_for_lookup) and \
                    current_orig_in_table_row == orig_key_for_lore_update:
                        
                        self.table_data[row_idx][2] = translated_text
                        item = self.table.item(row_idx, 2)
                        if item: 
                            item.setText(translated_text)
                        else: 
                            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(translated_text))

                        if self.current_row == row_idx and self.current_orig_key_for_editor == orig_key_for_lore_update:
                            self.trans_edit.setText(translated_text)
                            self.current_translation_in_editor_before_change = translated_text
                    else:
                        logger.warning(f"Skipping UI table update for completed job UID '{uid_val_for_lookup}', " f"orig '{orig_key_for_lore_update}' (Row {row_idx}). " f"Table data at this index appears to have changed " f"(UID: '{current_uid_in_table_row}', Orig: '{current_orig_in_table_row}'). " "Cache was updated.")
                else:
                    logger.warning(f"Row index {row_idx} for completed job UID '{uid_val_for_lookup}', " f"orig '{orig_key_for_lore_update}' is out of bounds for table_data " f"(len {len(self.table_data)}). UI Table not updated. Cache was updated.")
        else:
            logger.error(f"Failed to update translation cache for UID {uid_val_for_lookup} after successful API call for '{orig_key_for_lore_update}'.")

        self._update_progress_dialog()
        if not self.pending_translation_jobs and self.active_translation_jobs == 0:
            self._finalize_batch_translation("completed (last job finished handling)")

    def _handle_job_failed(self, job_data, error_message, raw_response, metadata):
        uid_val_for_lookup = job_data.get('uid_val_for_lookup', 'N/A')
        self.active_translation_jobs -= 1
        logger.error(f"Job failed for '{job_data.get('text_to_translate','Unknown Text')}' (UID {uid_val_for_lookup}): {error_message}. Raw: {raw_response[:100]} Metadata: {metadata}. Active jobs remaining: {self.active_translation_jobs}")
        self._update_progress_dialog()
        if not self.pending_translation_jobs and self.active_translation_jobs == 0:
            self._finalize_batch_translation("completed (last job failed handling)")


    def _update_progress_dialog(self):
        self.completed_jobs_for_progress += 1
        if self.progress_dialog:
            if self.progress_dialog.wasCanceled():
                logger.debug("Progress update skipped, dialog was cancelled.")
                return

            self.progress_dialog.setValue(self.completed_jobs_for_progress)
            if self.completed_jobs_for_progress >= self.total_jobs_for_progress:
                if self.active_translation_jobs == 0:
                    self._finalize_batch_translation("completed normally (all jobs processed)")

    def _finalize_batch_translation(self, reason=""):
        if not self.progress_dialog and self.total_jobs_for_progress == 0:
            return

        logger.info(f"Attempting to finalize batch translation. Reason: {reason}. Total: {self.total_jobs_for_progress}, Completed: {self.completed_jobs_for_progress}, Active: {self.active_translation_jobs}")

        if self.progress_dialog:
            self.progress_dialog.setValue(self.total_jobs_for_progress)
            self.progress_dialog.done(QtWidgets.QDialog.Accepted)
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

        self.save_cache()

        status_message = f"Batch operation {reason}. Processed {self.completed_jobs_for_progress} of {self.total_jobs_for_progress} items."
        if "cancel" in reason and self.pending_translation_jobs:
            remaining_pending = len(self.pending_translation_jobs)
            if remaining_pending > 0 :
                status_message += f" {remaining_pending} pending jobs were cancelled."
            self.pending_translation_jobs.clear()
        
        self.statusBar.showMessage(status_message, 7000)
        logger.info(status_message)

        self.active_translation_jobs = 0
        self.total_jobs_for_progress = 0
        self.completed_jobs_for_progress = 0


    @QtCore.Slot()
    def _cancel_batch_translation(self, silent=False):
        if not silent:
            logger.warning("Batch translation cancellation requested by user (or programmatically).")
        self.pending_translation_jobs.clear()
        if self.active_translation_jobs == 0:
            self._finalize_batch_translation("cancelled (no active jobs running)")
        else:
            logger.info(f"Cancellation requested. {self.active_translation_jobs} job(s) still active. Will finalize when they complete.")
            if self.progress_dialog:
                self.progress_dialog.setLabelText("Cancelling active jobs... Please wait.")

    def _prepare_jobs_for_rows(self, row_indices, source_lang, target_lang, force_regenerate=False):
        jobs_to_queue = []

        if not target_lang:
            logger.error("Cannot prepare jobs: Target language is not set.")
            QtWidgets.QMessageBox.warning(self, "Target Language Error", "Target language is not set. Cannot prepare translation jobs.")
            return jobs_to_queue

        if not source_lang:
            logger.error("Cannot prepare jobs: Source language is not set.")
            QtWidgets.QMessageBox.warning(self, "Source Language Error", "LORE-book source language is not set. Cannot prepare translation jobs.")
            return jobs_to_queue

        logger.info(f"Preparing jobs for {len(row_indices)} row(s). Source: '{source_lang}', Target: '{target_lang}', Regenerate: {force_regenerate}")

        for row_idx in row_indices:
            if not (0 <= row_idx < len(self.table_data)):
                logger.warning(f"Skipping row index {row_idx} for job preparation - out of bounds for table_data (len {len(self.table_data)}).")
                continue

            uid_val_str, orig_key_in_table_row, current_trans_in_cell, full_content_of_lore_entry = self.table_data[row_idx]

            api_job_data_or_cached_translation, is_cached = self._get_translation_from_cache_or_prepare_job(orig_text_to_translate=orig_key_in_table_row, source_lang=source_lang, target_lang=target_lang, uid=uid_val_str, full_content_of_entry_for_api_context=full_content_of_lore_entry, force_regenerate=force_regenerate, prepare_only=False)

            if is_cached:
                cached_translation_str = str(api_job_data_or_cached_translation).strip()
                current_cell_str = str(current_trans_in_cell).strip()
                if cached_translation_str != current_cell_str:
                    logger.debug(f"Row {row_idx} (UID '{uid_val_str}', Orig '{orig_key_in_table_row}'): " f"Updating table cell from cache. Was: '{current_cell_str}', Is: '{cached_translation_str}'.")
                    self.table_data[row_idx][2] = cached_translation_str
                    
                    table_item = self.table.item(row_idx, 2)
                    if table_item:
                        table_item.setText(cached_translation_str)
                    else:
                        self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(cached_translation_str))
                    if self.current_row == row_idx and self.current_orig_key_for_editor == orig_key_in_table_row:
                        self.trans_edit.setText(cached_translation_str)
                        self.current_translation_in_editor_before_change = cached_translation_str
                
                logger.debug(f"Row {row_idx} (UID '{uid_val_str}', Orig '{orig_key_in_table_row}'): "f"Translation '{cached_translation_str}' found in cache. No job needed.")
                continue

            if isinstance(api_job_data_or_cached_translation, dict):
                job_data_dict = api_job_data_or_cached_translation

                job_data_dict['row_idx'] = row_idx
                
                if not all(k in job_data_dict for k in ['text_to_translate', 'source_lang', 'target_lang', 'uid_val_for_lookup']):
                    logger.error(f"Internal Error: Job data from _get_translation_from_cache_or_prepare_job is missing critical keys for row {row_idx}. Job data: {job_data_dict}")
                    continue

                jobs_to_queue.append(job_data_dict)
                logger.debug(f"Row {row_idx} (UID '{uid_val_str}', Orig '{orig_key_in_table_row}'): "f"Job prepared for API translation to '{target_lang}'.")
            else:
                logger.error(f"Internal Error: _get_translation_from_cache_or_prepare_job returned unexpected data for row {row_idx} "f"when cache was missed and not prepare_only. Data: {api_job_data_or_cached_translation}")
                continue
                
        if jobs_to_queue:
            logger.info(f"Successfully prepared {len(jobs_to_queue)} job(s) for translation.")
        else:
            logger.info("No new jobs were prepared (all items might be cached or encountered errors).")
            
        return jobs_to_queue

    def translate_selected_rows_action(self):
        if not self.data: QtWidgets.QMessageBox.information(self, "Info", "Load LORE-book."); return
        sel_model_indices = self.table.selectionModel().selectedRows()
        if not sel_model_indices: QtWidgets.QMessageBox.information(self, "Info", "Select row(s)."); return

        sel_rows = sorted([index.row() for index in sel_model_indices])
        
        target_lang = self.current_target_language
        source_lang = self.current_source_language
        if not target_lang: QtWidgets.QMessageBox.warning(self, "No Target Language", "Please select or add a target language."); return
        if not source_lang: QtWidgets.QMessageBox.warning(self, "No Source Language", "Please select a source language."); return

        jobs = self._prepare_jobs_for_rows(sel_rows, source_lang, target_lang, force_regenerate=False)
        if jobs:
            self._start_translation_batch(jobs, "Translating Selected")
        else:
            QtWidgets.QMessageBox.information(self, "Already Translated", "Selected items are already translated (or in cache). Use 'Regenerate' to force new translation.")
            self.statusBar.showMessage("Selected items already translated/cached.", 3000)


    def translate_all_action(self):
        if not self.data: QtWidgets.QMessageBox.information(self, "Info", "Load file."); return

        all_row_indices = list(range(len(self.table_data)))
        if not all_row_indices:
            QtWidgets.QMessageBox.information(self, "Empty Table", "No data in table to translate.")
            return
            
        target_lang = self.current_target_language
        source_lang = self.current_source_language
        if not target_lang: QtWidgets.QMessageBox.warning(self, "No Target Language", "Please select or add a target language."); return
        if not source_lang: QtWidgets.QMessageBox.warning(self, "No Source Language", "Please select a source language."); return

        jobs = self._prepare_jobs_for_rows(all_row_indices, source_lang, target_lang, force_regenerate=False)
        if jobs:
            self._start_translation_batch(jobs, "Translating All")
        else:
            QtWidgets.QMessageBox.information(self, "All Translated", "All items appear to be already translated (or in cache). Use 'Regenerate' or clear cache if you need to re-translate.")
            self.statusBar.showMessage("All items already translated/cached.", 3000)

    def regenerate_selected_translation_action(self):
        if not self.data:
            QtWidgets.QMessageBox.information(self, "Info", "Please load a LORE-book file first.")
            return

        sel_rows = []
        sel_model_indices = self.table.selectionModel().selectedRows()
        if sel_model_indices:
            sel_rows = sorted([index.row() for index in sel_model_indices])
        elif self.current_row is not None and (0 <= self.current_row < len(self.table_data)):
            sel_rows = [self.current_row]

        if not sel_rows:
            QtWidgets.QMessageBox.information(self, "Info", "Please select row(s) in the table or ensure a row is active in the editor.")
            return

        target_lang = self.current_target_language
        source_lang = self.current_source_language
        if not target_lang:
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Please select or add a target language for regeneration.")
            return
        if not source_lang:
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Please select a source language for regeneration.")
            return
        jobs = self._prepare_jobs_for_rows(sel_rows, source_lang, target_lang, force_regenerate=True)
        if jobs:
            self._start_translation_batch(jobs, "Regenerating")
        else:
            self.statusBar.showMessage("No items selected or prepared for regeneration (check selection or LORE data).", 3000)
            logger.warning("Regeneration requested, but no jobs prepared. Selected rows: %s", sel_rows)


    def clear_all_translations_for_display_lang(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot clear translations while other translations are in progress.")
            return

        if not self.data or 'entries' not in self.data:
            QtWidgets.QMessageBox.information(self, "Info", "Please load a LORE-book file first.")
            return

        target_lang_to_clear = self.current_target_language
        if not target_lang_to_clear:
            QtWidgets.QMessageBox.information(self, "Info", "No target language selected to clear translations for.")
            return

        source_lang_for_originals = self.current_source_language
        if not source_lang_for_originals:
            QtWidgets.QMessageBox.warning(self, "No Source Language", "LORE-book source language is not selected. " "Cannot determine which cache entries to clear accurately.")
            logger.warning("clear_all_translations_for_display_lang: Aborted due to missing LORE-book source language.")
            return

        reply = QtWidgets.QMessageBox.question(self, 'Confirm Clear Cached Translations', f"Are you sure you want to delete ALL translations from the cache for:\n\n" f"Target Language: '{target_lang_to_clear}'\n" f"LORE-book Original Language: '{source_lang_for_originals}'\n\n" "This will only affect the in-memory cache and, upon saving the cache, " "the translation cache file associated with this LORE-book.\n" "The main LORE-book data (loaded in memory or on disk) will NOT be changed by this operation.", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            logger.info(f"Clearing cached translations for target '{target_lang_to_clear}' " f"(source: '{source_lang_for_originals}') cancelled by user.")
            return

        logger.info(f"Starting to clear cached translations for target language: '{target_lang_to_clear}' " f"(LORE-book source: '{source_lang_for_originals}')")
        self.statusBar.showMessage(f"Clearing cached translations for {target_lang_to_clear}...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        cleared_cache_keys_count = 0
        keys_to_delete_from_cache = []
        if self.data and 'entries' in self.data:
            for entry_data_val in self.data['entries'].values():
                if not isinstance(entry_data_val, dict):
                    continue
                
                uid_val = entry_data_val.get('uid')
                if uid_val is None:
                    logger.warning(f"Skipping entry during cache clear: UID missing. Entry keys: {entry_data_val.get('key', 'N/A')}")
                    continue
                uid_str = str(uid_val)
                original_keys_from_lore_field = entry_data_val.get('key', [])
                if not isinstance(original_keys_from_lore_field, list):
                    logger.warning(f"Skipping entry UID {uid_str} during cache clear: 'key' field is not a list.")
                    continue

                for orig_key_text_from_lore in original_keys_from_lore_field:
                    orig_key_to_check_in_cache = str(orig_key_text_from_lore).strip()
                    
                    if not orig_key_to_check_in_cache:
                        continue
                    cache_key_to_delete = self._generate_cache_key(uid_str, orig_key_to_check_in_cache, source_lang_for_originals, target_lang_to_clear)
                    if cache_key_to_delete in self.cache:
                        keys_to_delete_from_cache.append(cache_key_to_delete)
        else:
            logger.info("No LORE-book data loaded, so no specific cache entries to identify for clearing.")

        for key_to_del in set(keys_to_delete_from_cache):
            if key_to_del in self.cache:
                del self.cache[key_to_del]
                cleared_cache_keys_count += 1
                logger.debug(f"Removed from cache: {key_to_del}")
        
        QtWidgets.QApplication.restoreOverrideCursor()

        if cleared_cache_keys_count > 0:
            self.save_cache()
            logger.info(f"Finished clearing cached translations for target '{target_lang_to_clear}' " f"(source: '{source_lang_for_originals}'). " f"{cleared_cache_keys_count} cache entries removed.")
            self.statusBar.showMessage(f"Cleared {cleared_cache_keys_count} cached translations for '{target_lang_to_clear}'.", 7000)
        else:
            logger.info(f"No cached translations found for target '{target_lang_to_clear}' " f"(source: '{source_lang_for_originals}') to clear.")
            self.statusBar.showMessage(f"No cached translations found for '{target_lang_to_clear}' (source: '{source_lang_for_originals}') to clear.", 5000)
        self.populate_table_data()

    def export_json(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot export while translations are in progress.")
            return
        if not self.input_path or not self.data:
            QtWidgets.QMessageBox.warning(self, "Export Error", "No data loaded to export.")
            logger.warning("Export attempted with no data loaded.")
            return
        self.save_cache()
        logger.info("Cache saved before starting export process.")

        try:
            data_for_export = copy.deepcopy(self.data)
            logger.info("Created a deep copy of self.data for the export operation.")
        except Exception as e:
            logger.error(f"Failed to deepcopy self.data for export: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Internal error during export preparation (deepcopy failed): {e}")
            return
        original_lorebook_name_in_copy = None
        lorebook_name_was_present_in_copy = False

        if isinstance(data_for_export, dict):
            if "name" in data_for_export:
                original_lorebook_name_in_copy = str(data_for_export.get("name", ""))
                lorebook_name_was_present_in_copy = True
                
                new_name_for_export, ok_name_dialog = QtWidgets.QInputDialog.getText(self, "Set LORE-book Name for Export", "Enter the name for the LORE-book to be saved:", QtWidgets.QLineEdit.Normal, original_lorebook_name_in_copy)
                if ok_name_dialog:
                    if new_name_for_export.strip():
                        data_for_export["name"] = new_name_for_export.strip()
                        logger.info(f"LORE-book name for export set to '{data_for_export['name']}' (was '{original_lorebook_name_in_copy}').")
                    else:
                        data_for_export["name"] = "" 
                        logger.info(f"LORE-book name for export explicitly set to empty (was '{original_lorebook_name_in_copy}').")
                else:
                    logger.info("LORE-book name change for export cancelled by user. Original name from copy will be used if export continues.")
            elif "name" not in data_for_export:
                add_new_name, ok_add_name_dialog = QtWidgets.QInputDialog.getText(
                    self, "Set LORE-book Name for Export", "LORE-book 'name' field is missing. Enter a name to add for export (optional):", QtWidgets.QLineEdit.Normal, "")
                if ok_add_name_dialog and add_new_name.strip():
                    data_for_export["name"] = add_new_name.strip()
                    logger.info(f"LORE-book 'name' field added for export: '{data_for_export['name']}'.")
                else:
                    logger.info("User chose not to add a 'name' field for export, or entered an empty name.")
        else:
            logger.error("Export Error: data_for_export is not a dictionary. Cannot process 'name' field or entries.")
            QtWidgets.QMessageBox.critical(self, "Export Error", "Internal error: LORE-book data structure is invalid for export.")
            return

        if data_for_export and 'entries' in data_for_export and isinstance(data_for_export['entries'], dict):
            source_lang_of_lore_originals = self.current_source_language 
            if not source_lang_of_lore_originals:
                logger.warning("LORE-book source language (current_source_language) is not selected. " "Translations from cache might not be correctly matched or added during export. " "Please select the LORE-book's original language.")
                reply = QtWidgets.QMessageBox.warning(self, "Missing Source Language", "The LORE-book's original language is not selected in the UI. " "This is needed to correctly find translations in the cache.\n\n" "Do you want to proceed with export (translations might be incomplete)?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    logger.info("Export cancelled by user due to missing source language.")
                    return

            for entry_dict_key, entry_item_data_in_copy in data_for_export['entries'].items():
                if not isinstance(entry_item_data_in_copy, dict):
                    logger.warning(f"Skipping entry with dict key '{entry_dict_key}' during export: not a dictionary.")
                    continue
                self._ensure_entry_key_is_list(entry_item_data_in_copy) 
                current_entry_uid = entry_item_data_in_copy.get('uid')
                if current_entry_uid is None:
                    logger.warning(f"Skipping entry with dict key '{entry_dict_key}' during export: UID missing.")
                    continue
                uid_str = str(current_entry_uid)

                original_keys_for_this_entry = set(entry_item_data_in_copy.get('key', []))
                final_keys_for_this_entry_export = set(original_keys_for_this_entry) 

                if source_lang_of_lore_originals:
                    for original_key_text in original_keys_for_this_entry:
                        for target_lang_name in current_settings.get("target_languages", []):
                            if not target_lang_name:
                                continue

                            cache_lookup_key = self._generate_cache_key(uid_str, original_key_text, source_lang_of_lore_originals, target_lang_name)
                            if cache_lookup_key in self.cache:
                                cached_translation = str(self.cache[cache_lookup_key]).strip()
                                if cached_translation and cached_translation.lower() != original_key_text.lower():
                                    final_keys_for_this_entry_export.add(cached_translation)
                else:
                    logger.warning(f"Entry UID {uid_str}: Could not add translations from cache because LORE-book source language is not set.")
                entry_item_data_in_copy['key'] = sorted(list(k for k in final_keys_for_this_entry_export if k))
                if not entry_item_data_in_copy['key'] and original_keys_for_this_entry:
                    logger.warning(f"Entry UID {uid_str}: 'key' list became empty after processing for export, but originals existed. Restoring original keys: {sorted(list(original_keys_for_this_entry))}")
                    entry_item_data_in_copy['key'] = sorted(list(original_keys_for_this_entry))

        default_filename_base = os.path.basename(self.input_path)
        file_dir = os.path.dirname(self.input_path)

        if default_filename_base.lower().endswith(".json"):
            default_export_name = default_filename_base[:-5] + '_translated.json'
        else:
            base_name_no_ext, _ = os.path.splitext(default_filename_base)
            default_export_name = base_name_no_ext + '_translated.json'
        
        default_save_path = os.path.join(file_dir, default_export_name)

        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save LORE-book As", default_save_path, "LORE-book Files (*.json);;JSON files (*.json);;All Files (*)")
        
        if not out_path:
            logger.info("Export file dialog cancelled by user. No file saved.")
            if isinstance(data_for_export, dict) and "name" in data_for_export:
                if lorebook_name_was_present_in_copy and data_for_export.get("name") != original_lorebook_name_in_copy:
                    data_for_export["name"] = original_lorebook_name_in_copy
                    logger.info(f"Export cancelled. LORE-book name in copy restored to '{original_lorebook_name_in_copy}'.")
                elif not lorebook_name_was_present_in_copy and data_for_export.get("name") is not None:
                    if "name" in data_for_export: del data_for_export["name"]
                    logger.info("Export cancelled. Temporarily added 'name' field removed from copy.")
            return
        
        logger.info(f"Attempting to export LORE-book data (with translations from cache) to: {out_path}")
        self.statusBar.showMessage(f"Exporting to {os.path.basename(out_path)}...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        export_successful = False
        try:
            temp_lore_path = out_path + ".tmp"
            with open(temp_lore_path, 'w', encoding='utf-8') as f:
                json.dump(data_for_export, f, ensure_ascii=False, indent=2) 
            os.replace(temp_lore_path, out_path)
            
            logger.info(f'LORE-book exported successfully to: {out_path}')
            QtWidgets.QMessageBox.information(self, 'Export Successful', f'LORE-book exported to:\n{out_path}')
            self.statusBar.showMessage(f"Exported to {os.path.basename(out_path)}.", 5000)
            export_successful = True
        except Exception as e:
            logger.error(f'Export failed for {out_path}: {e}', exc_info=True)
            QtWidgets.QMessageBox.critical(self, 'Export Error', f'Failed to export LORE-book: {e}')
            self.statusBar.showMessage(f"Export failed for {os.path.basename(out_path)}.", 5000)
            try:
                if os.path.exists(temp_lore_path): 
                    os.remove(temp_lore_path)
            except Exception as e_rem:
                logger.error(f"Failed to remove temporary export file {temp_lore_path} after export error: {e_rem}")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            if isinstance(data_for_export, dict) and not export_successful and "name" in data_for_export:
                if lorebook_name_was_present_in_copy and data_for_export.get("name") != original_lorebook_name_in_copy:
                    data_for_export["name"] = original_lorebook_name_in_copy
                    logger.info(f"Export failed. LORE-book name in copy restored to '{original_lorebook_name_in_copy}'.")
                elif not lorebook_name_was_present_in_copy and data_for_export.get("name") is not None:
                    if "name" in data_for_export: del data_for_export["name"]
                    logger.info("Export failed. Temporarily added 'name' field removed from copy.")

    def closeEvent(self, event: QtGui.QCloseEvent):
        logger.info("Close event triggered.")
        if self.active_translation_jobs > 0:
            reply = QtWidgets.QMessageBox.question(self, "Confirm Exit", f"{self.active_translation_jobs} translation job(s) are still active. Are you sure you want to exit? Pending jobs will be cancelled.", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                logger.info("Exit cancelled by user due to active jobs.")
                if event: event.ignore()
                return
        
        self._cancel_batch_translation(silent=True)

        if self.thread_pool.activeThreadCount() > 0:
            logger.warning(f"Application closing with {self.thread_pool.activeThreadCount()} thread(s) still potentially active in QThreadPool.")
        
        if self.input_path and self.cache_file_path and self.cache:
            self.save_cache()
        
        save_settings(); logger.info("Settings (including recent files) saved on close.")
        
        if self.model_inspector_window: 
            self.model_inspector_window.close()

        global fh
        if fh:
            try:
                logger.removeHandler(fh); fh.close(); fh = None; 
                logger.info("File log handler closed.")
            except Exception as e_log:
                print(f"Error closing file log handler: {e_log}")

        if self.qt_log_handler:
            try:
                logger.removeHandler(self.qt_log_handler)
                self.qt_log_handler.widget = None
                self.qt_log_handler = None
            except Exception as e_log_qt:
                print(f"Error removing Qt log handler: {e_log_qt}")

        logger.info("Application closing.");
        if event: event.accept()


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)

    if not os.path.exists(APP_DIR):
        try: os.makedirs(APP_DIR)
        except Exception as e: print(f"Could not create app directory {APP_DIR}: {e}")

    load_settings()

    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = os.path.join(APP_DIR, 'icon.ico')

        if os.path.exists(icon_path):
            app.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            app.setWindowIcon(QtGui.QIcon.fromTheme("applications-education-translation", QtGui.QIcon.fromTheme("accessories-dictionary")))
            logger.warning(f"Bundled icon.ico not found at expected path: {icon_path}")
    elif __file__:
        icon_path_dev = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path_dev):
            app.setWindowIcon(QtGui.QIcon(icon_path_dev))
        else:
            app.setWindowIcon(QtGui.QIcon.fromTheme("applications-education-translation", QtGui.QIcon.fromTheme("accessories-dictionary")))
    else:
        app.setWindowIcon(QtGui.QIcon.fromTheme("applications-education-translation", QtGui.QIcon.fromTheme("accessories-dictionary")))

    try:
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
        logger.info("Applied qdarktheme (dark).")
    except ImportError:
        logger.warning("pyqtdarktheme library not found. Please install it (e.g., pip install pyqtdarktheme). Using default OS theme.")
    except Exception as e:
        logger.error(f"Failed to apply qdarktheme: {e}. Using default OS theme.", exc_info=True)

    if not current_settings.get("api_key"):
        logger.warning("Gemini API Key not found in settings. Prompting user.")
        temp_parent_for_dialog = QtWidgets.QWidget()
        s_dialog = SettingsDialog(current_settings, temp_parent_for_dialog)
        result = s_dialog.exec()
        if result == QtWidgets.QDialog.Accepted:
            updated_settings = s_dialog.get_settings()
            current_settings.update(updated_settings)
            save_settings()
            if not current_settings.get("api_key"):
                QtWidgets.QMessageBox.critical(None,"API Key Error","API Key was not provided. The application cannot function without it.\nExiting.");
                logger.critical("API Key not provided after settings dialog. Exiting.");
                sys.exit(1)
            else:
                logger.info("API key provided via initial dialog.")
        else:
            QtWidgets.QMessageBox.warning(None, "API Key Missing", "API Key is required for translation.\nExiting as it was not provided.");
            logger.warning("User cancelled or closed API key input dialog during startup. Exiting.");
            sys.exit(1)
        temp_parent_for_dialog.deleteLater()

    gem_model = None
    model_name_for_init = current_settings.get("gemini_model", default_settings["gemini_model"])
    try:
        api_key_to_log = current_settings.get('api_key', '');
        log_api_key_display = f"...{api_key_to_log[-4:]}" if len(api_key_to_log) >=4 else 'KEY_TOO_SHORT_OR_EMPTY'
        logger.info(f"Configuring Gemini API key ending with: {log_api_key_display}")
        genai.configure(api_key=current_settings["api_key"])
        
        logger.info(f"Initializing Gemini model: {model_name_for_init}");
        gem_model = genai.GenerativeModel(model_name_for_init)
    except Exception as e:
        logger.critical(f"Failed to initialize Gemini API/Model with '{model_name_for_init}': {e}. Please check API key and model name in settings. Exiting.", exc_info=True);
        QtWidgets.QMessageBox.critical(None, "API/Model Initialization Error", f"Failed to initialize Gemini services with model '{model_name_for_init}':\n{e}\n\n- Ensure your API key is correct and active.\n- Ensure the model name is valid and available for your API key.\n- Check your internet connection.\n\nThe application will now exit.")
        sys.exit(1)

    win = TranslatorApp(gem_model);
    win.show();
    logger.info(f"Lorebook Gemini Translator v{APP_VERSION} started successfully.")
    sys.exit(app.exec())