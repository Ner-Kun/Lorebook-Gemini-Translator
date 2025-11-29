import logging
import copy
from PySide6 import QtWidgets, QtCore, QtGui
from omni_trans_core.interfaces import AbstractTab
from omni_trans_core.ui.base_widgets import ShakeLineEdit, FocusOutTextEdit
from omni_trans_core.ui.widgets import DataTableWidget
from omni_trans_core.ui.animations import UIAnimator
from omni_trans_core.utils import DebounceTimer
from omni_trans_core import settings
from omni_trans_core.localization_manager import loc_man, translate
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni_trans_core.core import CoreApp
    from ..data_handler import LorebookDataHandler

logger = logging.getLogger(f'{settings.LOG_PREFIX}_APP.editor_tab')

class EditorTab(AbstractTab):
    TAB_NAME = "Editor"
    search_term_changed = QtCore.Signal(str)

    def __init__(self, main_window: "CoreApp", data_handler: "LorebookDataHandler"):
        super().__init__(main_window)
        self.main_window = main_window
        self.data_handler = data_handler
        self.selected_editor_entry_id = None
        self.editor_active_entry_copy = None
        self.is_saving_from_editor = False
        self.editor_widgets = {}
        self.editor_logic_map = {
            0: "AND ANY",
            1: "NOT ALL",
            2: "NOT ANY",
            3: "AND ALL"
        }
        self.editor_strategy_map = {
            0: "🟢 Normal",
            1: "🔵 Constant",
            2: "🔗 Vectorized",
        }
        self.editor_position_map = {
            0: "↑ Before Character",
            1: "↓ After Character",
            2: "↑ Before Extension Memory",
            3: "↓ After Extension Memory",
            4: "↑ Before Author's Note",
            5: "↓ After Author's Note",
            6: "@ System Directive ⚙️",
            7: "@ Persona Directive 👤",
            8: "@ Character Directive 🤖",
        }
        self.editor_tri_state_map = {
            0: "Use Global",
            1: "Yes",
            2: "No"
        }
        self._init_field_mapping()
        self.init_ui()
        self._connect_signals()
        self.editor_debounce_timer = DebounceTimer(
            self.editor_save_entry_changes, 1000, self
        )
        self.retranslate_ui()
        loc_man.language_changed.connect(self.retranslate_ui)

    def _init_field_mapping(self):
        self.field_mapping = {
            'disable': ('enabled_check', 'checkbox_inverted'),
            'comment': ('comment_edit', 'line_edit'),
            'key': ('keys_edit', 'string_list'),
            'keysecondary': ('keysecondary_edit', 'string_list'),
            'content': ('content_edit', 'plain_text_edit'),
            'selectiveLogic': ('logic_combo', 'combo_index'),
            'position': ('position_combo', 'combo_index'),
            'order': ('order_edit', 'numeric_line_edit', 100),
            'depth': ('depth_edit', 'numeric_line_edit', None),
            'probability': ('probability_edit', 'numeric_line_edit', 100),
            'useProbability': ('useProbability_check', 'checkbox'),
            'scanDepth': ('scanDepth_edit', 'numeric_line_edit', None),
            'caseSensitive': ('caseSensitive_combo', 'tri_state_combo'),
            'matchWholeWords': ('matchWholeWords_combo', 'tri_state_combo'),
            'useGroupScoring': ('useGroupScoring_combo', 'tri_state_combo'),
            'group': ('group_edit', 'line_edit'),
            'groupOverride': ('groupOverride_check', 'checkbox'),
            'groupWeight': ('groupWeight_edit', 'numeric_line_edit', 100),
            'sticky': ('sticky_edit', 'numeric_line_edit', 0),
            'cooldown': ('cooldown_edit', 'numeric_line_edit', 0),
            'delay': ('delay_edit', 'numeric_line_edit', 0),
            'addMemo': ('addMemo_check', 'checkbox'),
            'preventRecursion': ('preventRecursion_check', 'checkbox'),
            'excludeRecursion': ('excludeRecursion_check', 'checkbox'),
            'automationId': ('automationId_edit', 'line_edit'),
        }

    def init_ui(self):
        editor_layout = QtWidgets.QHBoxLayout(self)
        editor_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        editor_splitter.setOpaqueResize(False)
        editor_layout.addWidget(editor_splitter)
        editor_left_panel = self._create_left_panel()
        editor_splitter.addWidget(editor_left_panel)
        editor_right_panel = self._create_right_panel()
        editor_splitter.addWidget(editor_right_panel)
        editor_splitter.setSizes([400, 700])

    def _create_left_panel(self):
        editor_left_panel = QtWidgets.QWidget()
        editor_left_layout = QtWidgets.QVBoxLayout(editor_left_panel)
        editor_left_panel.setMinimumWidth(350)
        editor_left_panel.setMaximumWidth(550)
        self.lore_entries_label = QtWidgets.QLabel()
        editor_left_layout.addWidget(self.lore_entries_label)
        self.table_widget = DataTableWidget()
        self.editor_search_input = self.table_widget.search_input
        self.editor_entry_table = self.table_widget.table
        self.table_widget_columns_config = [
            {
                "key": "uid",
                "header_key": "tab.editor.table.header.uid",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.Interactive,
            },
            {
                "key": "keywords",
                "header_key": "tab.editor.table.header.keywords",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.Stretch,
            },
            {
                "key": "comment",
                "header_key": "tab.editor.table.header.comment",
                "resize_mode": QtWidgets.QHeaderView.ResizeMode.Stretch,
            },
        ]
        self.editor_entry_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.editor_entry_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.editor_entry_table.setWordWrap(False)
        editor_left_layout.addWidget(self.table_widget)
        editor_button_layout = QtWidgets.QHBoxLayout()
        self.editor_add_btn = QtWidgets.QPushButton()
        self.editor_duplicate_btn = QtWidgets.QPushButton()
        self.editor_delete_btn = QtWidgets.QPushButton()
        editor_button_layout.addWidget(self.editor_add_btn)
        editor_button_layout.addWidget(self.editor_duplicate_btn)
        editor_button_layout.addWidget(self.editor_delete_btn)
        editor_left_layout.addLayout(editor_button_layout)
        return editor_left_panel

    def _create_right_panel(self):
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.editor_form_widget = QtWidgets.QWidget()
        scroll_area.setWidget(self.editor_form_widget)
        editor_right_layout = QtWidgets.QVBoxLayout(self.editor_form_widget)
        self.editor_form_widget.setEnabled(False)
        self.basic_info_group = QtWidgets.QGroupBox()
        basic_info_layout = QtWidgets.QFormLayout(self.basic_info_group)
        self.editor_widgets["enabled_check"] = QtWidgets.QCheckBox()
        self.editor_widgets["comment_edit"] = QtWidgets.QLineEdit()
        self.editor_widgets["keys_edit"] = QtWidgets.QLineEdit()
        self.editor_widgets["keysecondary_edit"] = QtWidgets.QLineEdit()
        self.editor_widgets["content_edit"] = FocusOutTextEdit()
        self.editor_widgets["content_edit"].setAcceptRichText(False)
        self.editor_save_status_label = QtWidgets.QLabel()
        self.editor_save_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        first_row_layout = QtWidgets.QHBoxLayout()
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.addWidget(self.editor_widgets["enabled_check"])
        first_row_layout.addStretch()
        first_row_layout.addWidget(self.editor_save_status_label)
        basic_info_layout.addRow(first_row_layout)
        self.comment_label = QtWidgets.QLabel()
        self.keys_label = QtWidgets.QLabel()
        self.keysecondary_label = QtWidgets.QLabel()
        basic_info_layout.addRow(
            self.comment_label, self.editor_widgets["comment_edit"]
        )
        basic_info_layout.addRow(self.keys_label, self.editor_widgets["keys_edit"])
        basic_info_layout.addRow(
            self.keysecondary_label, self.editor_widgets["keysecondary_edit"]
        )
        editor_right_layout.addWidget(self.basic_info_group)
        self.content_label = QtWidgets.QLabel()
        editor_right_layout.addWidget(self.content_label)
        editor_right_layout.addWidget(self.editor_widgets["content_edit"], stretch=1)
        self.activation_group = QtWidgets.QGroupBox()
        activation_layout = QtWidgets.QHBoxLayout(self.activation_group)
        self.editor_widgets["logic_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["logic_combo"].addItems(self.editor_logic_map.values())
        self.editor_widgets["position_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["position_combo"].addItems(
            self.editor_position_map.values()
        )
        self.editor_widgets["strategy_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["strategy_combo"].addItems(
            self.editor_strategy_map.values()
        )
        self.editor_widgets["order_edit"] = ShakeLineEdit()
        self.editor_widgets["order_edit"].setValidator(QtGui.QIntValidator())
        self.editor_widgets["probability_edit"] = ShakeLineEdit()
        self.editor_widgets["probability_edit"].setValidator(QtGui.QIntValidator())
        self.editor_widgets["useProbability_check"] = QtWidgets.QCheckBox()
        self.editor_widgets["depth_edit"] = ShakeLineEdit()
        self.editor_widgets["depth_edit"].setValidator(QtGui.QIntValidator(0, 999))
        self.editor_widgets["depth_edit"].hide()
        self.logic_label = QtWidgets.QLabel()
        self.strategy_label = QtWidgets.QLabel()
        self.position_label = QtWidgets.QLabel()
        self.order_label = QtWidgets.QLabel()
        self.probability_label = QtWidgets.QLabel()
        activation_layout.addWidget(self.logic_label)
        activation_layout.addWidget(self.editor_widgets["logic_combo"])
        activation_layout.addWidget(self.strategy_label)
        activation_layout.addWidget(self.editor_widgets["strategy_combo"])
        position_layout = QtWidgets.QHBoxLayout()
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.addWidget(self.position_label)
        position_layout.addWidget(self.editor_widgets["position_combo"])
        position_layout.addWidget(self.editor_widgets["depth_edit"])
        activation_layout.addLayout(position_layout)
        activation_layout.addWidget(self.order_label)
        activation_layout.addWidget(self.editor_widgets["order_edit"])
        activation_layout.addWidget(self.probability_label)
        activation_layout.addWidget(self.editor_widgets["probability_edit"])
        activation_layout.addWidget(self.editor_widgets["useProbability_check"])
        editor_right_layout.addWidget(self.activation_group)
        self.scan_group = QtWidgets.QGroupBox()
        scan_layout = QtWidgets.QHBoxLayout(self.scan_group)
        self.editor_widgets["scanDepth_edit"] = ShakeLineEdit()
        self.editor_widgets["scanDepth_edit"].setValidator(QtGui.QIntValidator(0, 9999))
        self.editor_widgets["caseSensitive_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["caseSensitive_combo"].addItems(
            self.editor_tri_state_map.values()
        )
        self.editor_widgets["matchWholeWords_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["matchWholeWords_combo"].addItems(
            self.editor_tri_state_map.values()
        )
        self.editor_widgets["useGroupScoring_combo"] = QtWidgets.QComboBox()
        self.editor_widgets["useGroupScoring_combo"].addItems(
            self.editor_tri_state_map.values()
        )
        self.scan_depth_label = QtWidgets.QLabel()
        self.case_sensitive_label = QtWidgets.QLabel()
        self.whole_words_label = QtWidgets.QLabel()
        self.group_scoring_label = QtWidgets.QLabel()
        scan_layout.addWidget(self.scan_depth_label)
        scan_layout.addWidget(self.editor_widgets["scanDepth_edit"])
        scan_layout.addWidget(self.case_sensitive_label)
        scan_layout.addWidget(self.editor_widgets["caseSensitive_combo"])
        scan_layout.addWidget(self.whole_words_label)
        scan_layout.addWidget(self.editor_widgets["matchWholeWords_combo"])
        scan_layout.addWidget(self.group_scoring_label)
        scan_layout.addWidget(self.editor_widgets["useGroupScoring_combo"])
        editor_right_layout.addWidget(self.scan_group)
        self.advanced_group = QtWidgets.QGroupBox()
        advanced_layout = QtWidgets.QGridLayout(self.advanced_group)
        advanced_layout.setColumnStretch(1, 1)
        group_layout = QtWidgets.QHBoxLayout()
        self.editor_widgets["group_edit"] = QtWidgets.QLineEdit()
        self.editor_widgets["groupOverride_check"] = QtWidgets.QCheckBox()
        group_layout.addWidget(self.editor_widgets["group_edit"], 1)
        group_layout.addWidget(self.editor_widgets["groupOverride_check"])
        self.inclusion_group_label = QtWidgets.QLabel()
        advanced_layout.addWidget(self.inclusion_group_label, 0, 0)
        advanced_layout.addLayout(group_layout, 0, 1, 1, 3)
        self.editor_widgets["groupWeight_edit"] = ShakeLineEdit()
        self.editor_widgets["groupWeight_edit"].setValidator(QtGui.QIntValidator())
        self.editor_widgets["sticky_edit"] = ShakeLineEdit()
        self.editor_widgets["sticky_edit"].setValidator(QtGui.QIntValidator())
        self.editor_widgets["cooldown_edit"] = ShakeLineEdit()
        self.editor_widgets["cooldown_edit"].setValidator(QtGui.QIntValidator())
        self.editor_widgets["delay_edit"] = ShakeLineEdit()
        self.editor_widgets["delay_edit"].setValidator(QtGui.QIntValidator())
        numeric_fields_layout = QtWidgets.QHBoxLayout()
        self.group_weight_label = QtWidgets.QLabel()
        self.sticky_label = QtWidgets.QLabel()
        self.cooldown_label = QtWidgets.QLabel()
        self.delay_label = QtWidgets.QLabel()
        numeric_fields_layout.addWidget(self.group_weight_label)
        numeric_fields_layout.addWidget(self.editor_widgets["groupWeight_edit"])
        numeric_fields_layout.addWidget(self.sticky_label)
        numeric_fields_layout.addWidget(self.editor_widgets["sticky_edit"])
        numeric_fields_layout.addWidget(self.cooldown_label)
        numeric_fields_layout.addWidget(self.editor_widgets["cooldown_edit"])
        numeric_fields_layout.addWidget(self.delay_label)
        numeric_fields_layout.addWidget(self.editor_widgets["delay_edit"])
        advanced_layout.addLayout(numeric_fields_layout, 1, 0, 1, 4)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        advanced_layout.addWidget(separator, 2, 0, 1, 4)
        self.editor_widgets["addMemo_check"] = QtWidgets.QCheckBox()
        self.editor_widgets["preventRecursion_check"] = QtWidgets.QCheckBox()
        self.editor_widgets["excludeRecursion_check"] = QtWidgets.QCheckBox()
        delay_recursion_layout = QtWidgets.QHBoxLayout()
        delay_recursion_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_widgets["delayUntilRecursion_check"] = QtWidgets.QCheckBox()
        self.editor_widgets["delayRecursionLevel_edit"] = ShakeLineEdit()
        self.editor_widgets["delayRecursionLevel_edit"].setValidator(
            QtGui.QIntValidator(1, 999)
        )
        self.editor_widgets["delayRecursionLevel_edit"].setVisible(False)
        delay_recursion_layout.addWidget(
            self.editor_widgets["delayUntilRecursion_check"]
        )
        delay_recursion_layout.addWidget(
            self.editor_widgets["delayRecursionLevel_edit"]
        )
        recursion_checkboxes_layout = QtWidgets.QHBoxLayout()
        recursion_checkboxes_layout.addWidget(self.editor_widgets["addMemo_check"])
        recursion_checkboxes_layout.addStretch()
        recursion_checkboxes_layout.addWidget(
            self.editor_widgets["preventRecursion_check"]
        )
        recursion_checkboxes_layout.addStretch()
        recursion_checkboxes_layout.addWidget(
            self.editor_widgets["excludeRecursion_check"]
        )
        recursion_checkboxes_layout.addStretch()
        recursion_checkboxes_layout.addLayout(delay_recursion_layout)
        advanced_layout.addLayout(recursion_checkboxes_layout, 3, 0, 1, 4)
        self.editor_widgets["automationId_edit"] = QtWidgets.QLineEdit()
        self.automation_id_label = QtWidgets.QLabel()
        advanced_layout.addWidget(self.automation_id_label, 4, 0)
        advanced_layout.addWidget(self.editor_widgets["automationId_edit"], 4, 1, 1, 3)
        editor_right_layout.addWidget(self.advanced_group)
        editor_right_layout.addStretch()
        return scroll_area

    def retranslate_ui(self):
        loc_man.register(self.lore_entries_label, "text", "tab.editor.label.lore_entries")
        loc_man.register(self.editor_search_input, "placeholderText", "tab.editor.search.placeholder")
        loc_man.register(self.editor_add_btn, "text", "tab.editor.button.add")
        loc_man.register(self.editor_duplicate_btn, "text", "tab.editor.button.duplicate")
        loc_man.register(self.editor_delete_btn, "text", "tab.editor.button.delete")
        columns = [{'key': col['key'], 'header': translate(col['header_key']), 'resize_mode': col['resize_mode']} for col in self.table_widget_columns_config]
        self.table_widget.configure(columns)
        loc_man.register(self.editor_save_status_label, "text", "tab.editor.status.select_entry")
        loc_man.register(self.basic_info_group, "title", "tab.editor.group.basic_info")
        loc_man.register(self.editor_widgets['enabled_check'], "text", "tab.editor.check.entry_enabled")
        loc_man.register(self.comment_label, "text", "tab.editor.label.comment")
        loc_man.register(self.keys_label, "text", "tab.editor.label.primary_keywords")
        loc_man.register(self.keysecondary_label, "text", "tab.editor.label.secondary_keywords")
        loc_man.register(self.content_label, "text", "tab.editor.label.content")
        loc_man.register(self.activation_group, "title", "tab.editor.group.activation")
        loc_man.register(self.logic_label, "text", "tab.editor.label.logic")
        loc_man.register(self.strategy_label, "text", "tab.editor.label.strategy")
        loc_man.register(self.position_label, "text", "tab.editor.label.position")
        loc_man.register(self.order_label, "text", "tab.editor.label.order")
        loc_man.register(self.probability_label, "text", "tab.editor.label.trigger_percent")
        loc_man.register(self.editor_widgets['useProbability_check'], "text", "tab.editor.check.use_probability")
        loc_man.register(self.editor_widgets['depth_edit'], "placeholderText", "tab.editor.placeholder.depth")
        loc_man.register(self.scan_group, "title", "tab.editor.group.scanning")
        loc_man.register(self.scan_depth_label, "text", "tab.editor.label.scan_depth")
        loc_man.register(self.editor_widgets['scanDepth_edit'], "placeholderText", "tab.editor.placeholder.global")
        loc_man.register(self.case_sensitive_label, "text", "tab.editor.label.case_sensitive")
        loc_man.register(self.whole_words_label, "text", "tab.editor.label.whole_words")
        loc_man.register(self.group_scoring_label, "text", "tab.editor.label.group_scoring")
        loc_man.register(self.advanced_group, "title", "tab.editor.group.advanced")
        loc_man.register(self.inclusion_group_label, "text", "tab.editor.label.inclusion_group")
        loc_man.register(self.editor_widgets['groupOverride_check'], "text", "tab.editor.check.prioritize")
        loc_man.register(self.group_weight_label, "text", "tab.editor.label.group_weight")
        loc_man.register(self.sticky_label, "text", "tab.editor.label.sticky")
        loc_man.register(self.cooldown_label, "text", "tab.editor.label.cooldown")
        loc_man.register(self.delay_label, "text", "tab.editor.label.delay")
        loc_man.register(self.editor_widgets['addMemo_check'], "text", "tab.editor.check.add_memo")
        loc_man.register(self.editor_widgets['preventRecursion_check'], "text", "tab.editor.check.prevent_recursion")
        loc_man.register(self.editor_widgets['excludeRecursion_check'], "text", "tab.editor.check.exclude_recursion")
        loc_man.register(self.editor_widgets['delayUntilRecursion_check'], "text", "tab.editor.check.delay_until_recursion")
        loc_man.register(self.editor_widgets['delayRecursionLevel_edit'], "placeholderText", "tab.editor.placeholder.level")
        loc_man.register(self.automation_id_label, "text", "tab.editor.label.automation_id")

    def _load_strategy(self, entry_data):
        strategy_idx = 1 if entry_data.get('constant') else 2 if entry_data.get('vectorized') else 0
        self.editor_widgets['strategy_combo'].setCurrentIndex(strategy_idx)

    def _save_strategy(self, entry_data):
        strategy_idx = self.editor_widgets["strategy_combo"].currentIndex()
        entry_data["constant"] = strategy_idx == 1
        entry_data["vectorized"] = strategy_idx == 2

    def _load_delay_recursion(self, entry_data):
        delay_value = entry_data.get("delayUntilRecursion", False)
        is_delayed = bool(delay_value)
        self.editor_widgets["delayUntilRecursion_check"].setChecked(is_delayed)
        self.editor_widgets["delayRecursionLevel_edit"].setVisible(is_delayed)
        if isinstance(delay_value, int) and delay_value > 1:
            self.editor_widgets["delayRecursionLevel_edit"].setText(str(delay_value))
        else:
            self.editor_widgets["delayRecursionLevel_edit"].clear()

    def _save_delay_recursion(self, entry_data):
        if not self.editor_widgets["delayUntilRecursion_check"].isChecked():
            entry_data["delayUntilRecursion"] = False
        else:
            level_text = self.editor_widgets["delayRecursionLevel_edit"].text().strip()
            entry_data["delayUntilRecursion"] = (
                int(level_text) if level_text.isdigit() else True
            )

    def _connect_signals(self):
        self.editor_search_input.textChanged.connect(self.on_global_search_changed)
        self.table_widget.selection_changed.connect(self.editor_load_entry_details)
        self.editor_add_btn.clicked.connect(self.editor_add_entry)
        self.editor_duplicate_btn.clicked.connect(self.editor_duplicate_entry)
        self.editor_delete_btn.clicked.connect(self.editor_delete_entry)
        self.editor_widgets["position_combo"].currentIndexChanged.connect(
            self._update_insertion_depth_visibility
        )
        self.editor_widgets["delayUntilRecursion_check"].toggled.connect(
            self.toggle_recursion_level_field_animated
        )
        for widget_name in [
            "comment_edit",
            "keys_edit",
            "keysecondary_edit",
            "order_edit",
            "probability_edit",
            "scanDepth_edit",
            "group_edit",
            "groupWeight_edit",
            "sticky_edit",
            "cooldown_edit",
            "delay_edit",
            "delayRecursionLevel_edit",
            "automationId_edit",
            "depth_edit",
        ]:
            if widget_name in self.editor_widgets and isinstance(
                self.editor_widgets[widget_name], QtWidgets.QLineEdit
            ):
                self.editor_widgets[widget_name].textChanged.connect(
                    self._trigger_editor_debounce_save
                )
        self.editor_widgets["content_edit"].textChanged.connect(
            self._trigger_editor_debounce_save
        )
        for widget_name in [
            "logic_combo",
            "position_combo",
            "strategy_combo",
            "caseSensitive_combo",
            "matchWholeWords_combo",
            "useGroupScoring_combo",
        ]:
            if widget_name in self.editor_widgets and isinstance(
                self.editor_widgets[widget_name], QtWidgets.QComboBox
            ):
                self.editor_widgets[widget_name].currentIndexChanged.connect(
                    self._trigger_editor_debounce_save
                )
        for widget_name in [
            "enabled_check",
            "useProbability_check",
            "groupOverride_check",
            "addMemo_check",
            "preventRecursion_check",
            "excludeRecursion_check",
            "delayUntilRecursion_check",
        ]:
            if widget_name in self.editor_widgets and isinstance(
                self.editor_widgets[widget_name], QtWidgets.QCheckBox
            ):
                self.editor_widgets[widget_name].toggled.connect(
                    self._trigger_editor_debounce_save
                )
        self.editor_widgets["content_edit"].focus_out.connect(self.on_before_save)
        self.data_handler.entry_deleted.connect(self.editor_refresh_listbox)
        self.data_handler.entry_updated.connect(self._on_entry_updated)

    @QtCore.Slot(bool)
    def toggle_recursion_level_field_animated(self, checked):
        widget = self.editor_widgets.get("delayRecursionLevel_edit")
        UIAnimator.toggle_visibility_animated(widget, show=checked)

    @QtCore.Slot(str, dict)
    def _on_entry_updated(self, entry_id: str, new_data: dict):
        update_dict = {
            "uid": str(new_data.get("uid", "N/A")),
            "keywords": ", ".join(new_data.get("key", [])),
            "comment": new_data.get("comment", ""),
        }
        self.table_widget.update_row_by_id(entry_id, update_dict)

    @QtCore.Slot()
    def on_data_loaded(self):
        self.editor_refresh_listbox()

    def clear_view(self):
        self.editor_clear_form()
        self.editor_form_widget.setEnabled(False)
        self.editor_refresh_listbox()

    @QtCore.Slot()
    def on_before_save(self):
        logger.debug("Forcing editor changes via debounce timer.")
        self.editor_debounce_timer.force_run()

    def editor_clear_form(self):
        for widget in self.editor_widgets.values():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.clear()
            elif isinstance(widget, QtWidgets.QTextEdit):
                widget.clear()
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(0)
        self.selected_editor_entry_id = None
        self.editor_active_entry_copy = None

    def editor_refresh_listbox(self):
        selected_id_before_refresh = self.selected_editor_entry_id
        sorted_entries = self.data_handler.get_sorted_lore_entries()
        if not sorted_entries:
            self.table_widget.set_data([], unique_id_key="id")
            return
        table_data = []
        for entry_id, entry_data in sorted_entries:
            uid = str(entry_data.get("uid", "N/A"))
            comment = entry_data.get("comment", "")
            keywords = ", ".join(entry_data.get("key", []))
            full_searchable_text = (
                f"{uid} {keywords} {comment} {entry_data.get('content', '')}"
            )
            table_data.append(
                {
                    "id": entry_id,
                    "uid": uid,
                    "keywords": keywords,
                    "comment": comment,
                    "search_text": full_searchable_text,
                }
            )
        self.table_widget.set_data(table_data, unique_id_key="id")
        if (
            selected_id_before_refresh
            and selected_id_before_refresh in self.table_widget._id_to_row_map
        ):
            self._select_entry_in_list_by_id(selected_id_before_refresh)

    @QtCore.Slot(list)
    def editor_load_entry_details(self, selected_data: list[dict]):
        self.on_before_save()
        if not selected_data:
            self.editor_clear_form()
            self.editor_form_widget.setEnabled(False)
            return
        first_item = selected_data[0]
        entry_id = first_item.get("id")
        
        if (
            not self.data_handler.data
            or "entries" not in self.data_handler.data
            or entry_id not in self.data_handler.data["entries"]
        ):
            return
        self.selected_editor_entry_id = entry_id
        self.editor_active_entry_copy = copy.deepcopy(
            self.data_handler.data["entries"][entry_id]
        )
        entry = self.editor_active_entry_copy
        for widget in self.editor_widgets.values():
            widget.blockSignals(True)
        for key, (widget_name, type, *default) in self.field_mapping.items():
            widget = self.editor_widgets[widget_name]
            default_val = default[0] if default else None
            value = entry.get(key, default_val)
            if type == "line_edit":
                widget.setText(value)
            elif type == "numeric_line_edit":
                set_numeric_field(widget, value, default_val)
            elif type == "plain_text_edit":
                widget.setPlainText(value)
            elif type == "string_list":
                widget.setText(", ".join(value))
            elif type == "checkbox":
                widget.setChecked(bool(value))
            elif type == "checkbox_inverted":
                widget.setChecked(not bool(value))
            elif type == "combo_index":
                widget.setCurrentIndex(value)
            elif type == "tri_state_combo":
                set_tri_state_combo(widget, value)
        self._load_strategy(entry)
        self._load_delay_recursion(entry)
        for widget in self.editor_widgets.values():
            widget.blockSignals(False)
        current_pos_index = self.editor_widgets["position_combo"].currentIndex()
        self._update_insertion_depth_visibility(current_pos_index)
        self.editor_form_widget.setEnabled(True)
        UIAnimator.flash_status_label(self.editor_save_status_label, "<b>Loaded ✅</b>")
        logger.debug(f"Loaded entry '{entry_id}' fully into editor form.")

    @QtCore.Slot()
    def editor_save_entry_changes(self):
        if not self.selected_editor_entry_id or self.editor_active_entry_copy is None:
            return
        self.editor_debounce_timer.cancel()
        entry = self.editor_active_entry_copy
        for key, (widget_name, type, *default) in self.field_mapping.items():
            widget = self.editor_widgets[widget_name]
            default_val = default[0] if default else None
            if type == "line_edit":
                entry[key] = widget.text().strip()
            elif type == "numeric_line_edit":
                entry[key] = get_int_or_default(widget, default_val)
            elif type == "plain_text_edit":
                entry[key] = widget.toPlainText()
            elif type == "string_list":
                entry[key] = [k.strip() for k in widget.text().split(",") if k.strip()]
            elif type == "checkbox":
                entry[key] = widget.isChecked()
            elif type == "checkbox_inverted":
                entry[key] = not widget.isChecked()
            elif type == "combo_index":
                entry[key] = widget.currentIndex()
            elif type == "tri_state_combo":
                entry[key] = get_tri_state_value(widget)
        self._save_strategy(entry)
        self._save_delay_recursion(entry)
        keys_to_remove_if_none = [
            "scanDepth",
            "depth",
            "caseSensitive",
            "matchWholeWords",
            "useGroupScoring",
        ]
        for key in keys_to_remove_if_none:
            if entry.get(key) is None and key in entry:
                del entry[key]
        self.data_handler.update_entry(
            self.selected_editor_entry_id, self.editor_active_entry_copy
        )
        UIAnimator.flash_status_label(
            self.editor_save_status_label, "<b>Applied ✅</b>"
        )

    @QtCore.Slot()
    def editor_add_entry(self):
        if not self.data_handler.data:
            QtWidgets.QMessageBox.warning(
                self,
                translate("tab.editor.dialog.action_failed.title"),
                translate("tab.editor.dialog.action_failed.no_lorebook_loaded"),
            )
            return
        new_entry_id = self.data_handler.add_new_entry()
        if new_entry_id:
            self.editor_refresh_listbox()
            self._select_entry_in_list_by_id(new_entry_id)
            selected_data = self.table_widget.get_selected_rows_data()
            self.editor_load_entry_details(selected_data)

    @QtCore.Slot()
    def editor_duplicate_entry(self):
        if not self.selected_editor_entry_id:
            QtWidgets.QMessageBox.warning(
                self,
                translate("tab.editor.dialog.action_failed.title"),
                translate(
                    "tab.editor.dialog.action_failed.no_entry_selected_duplicate"),
            )
            return
        self.on_before_save()
        new_entry_id = self.data_handler.duplicate_entry(self.selected_editor_entry_id)
        if new_entry_id:
            self.editor_refresh_listbox()
            self._select_entry_in_list_by_id(new_entry_id)
            selected_data = self.table_widget.get_selected_rows_data()
            self.editor_load_entry_details(selected_data)

    @QtCore.Slot()
    def editor_delete_entry(self):
        if not self.selected_editor_entry_id:
            QtWidgets.QMessageBox.warning(
                self,
                translate("tab.editor.dialog.action_failed.title"),
                translate("tab.editor.dialog.action_failed.no_entry_selected_delete"),
            )
            return
        self.on_before_save()
        entry_name = self.data_handler.data["entries"][
            self.selected_editor_entry_id
        ].get("comment", self.selected_editor_entry_id)
        title = translate("tab.editor.dialog.confirm_delete.title")
        text = translate("tab.editor.dialog.confirm_delete.text", entry_name=entry_name)
        reply = QtWidgets.QMessageBox.question(
            self,
            title,
            text,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            row_to_reselect = self.editor_entry_table.currentRow()
            self.data_handler.delete_entry(self.selected_editor_entry_id)
            self.editor_clear_form()
            self.editor_form_widget.setEnabled(False)
            new_row_count = self.editor_entry_table.rowCount()
            if new_row_count > 0:
                index_to_select = min(row_to_reselect, new_row_count - 1)
                self.editor_entry_table.setCurrentCell(index_to_select, 0)

    @QtCore.Slot(str)
    def on_global_search_changed(self, text):
        self.search_term_changed.emit(text)

    def _select_entry_in_list_by_id(self, entry_id_to_select):
        row_index = self.table_widget._id_to_row_map.get(entry_id_to_select)
        if row_index is not None:
            self.editor_entry_table.blockSignals(True)
            self.editor_entry_table.selectRow(row_index)
            self.editor_entry_table.blockSignals(False)
            item = self.editor_entry_table.item(row_index, 0)
            if item:
                self.editor_entry_table.scrollToItem(
                    item, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter
                )

    @QtCore.Slot(int)
    def _update_insertion_depth_visibility(self, index):
        widget = self.editor_widgets.get('depth_edit')
        is_visible = index in [6, 7, 8]
        if widget.isVisible() != is_visible:
            UIAnimator.toggle_visibility_animated(widget, show=is_visible)

    @QtCore.Slot()
    def _trigger_editor_debounce_save(self):
        if self.selected_editor_entry_id is not None:
            UIAnimator.flash_status_label(
                self.editor_save_status_label,
                "⚠️ <i>Changes detected...</i>",
                color="#f1fa8c",
                duration_ms=800,
            )
            self.editor_debounce_timer.trigger()

def get_int_or_default(widget, default_val):
    text = widget.text().strip()
    return int(text) if text.isdigit() else default_val

def set_numeric_field(widget, value, default=0):
    widget.setText(str(value) if value is not None and value != default else "")

def get_tri_state_value(widget):
    idx = widget.currentIndex()
    return None if idx == 0 else idx == 1

def set_tri_state_combo(widget, value):
    if value is None:
        widget.setCurrentIndex(0)
    else:
        widget.setCurrentIndex(1) if value else widget.setCurrentIndex(2)