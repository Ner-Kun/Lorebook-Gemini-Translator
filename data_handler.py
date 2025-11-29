import os
import json
import logging
from logging import Logger
import copy
from PySide6 import QtCore
from typing import TypedDict, NotRequired, override, final, TypeGuard, cast
from omni_trans_core.interfaces import AbstractDataHandler, TranslatableItem
from .constants import LOG_PREFIX

logger: Logger = logging.getLogger(f'{LOG_PREFIX}_APP.data_handler')

class LorebookEntry(TypedDict, total=False):
    uid: int
    key: list[str]
    keysecondary: list[str]
    comment: str
    content: str
    constant: bool
    vectorized: bool
    selective: bool
    selectiveLogic: int
    addMemo: bool
    order: int
    position: int
    disable: bool
    excludeRecursion: bool
    preventRecursion: bool
    delayUntilRecursion: bool | int
    probability: int
    useProbability: bool
    depth: NotRequired[int]
    group: str
    groupOverride: bool
    groupWeight: int
    scanDepth: NotRequired[int]
    caseSensitive: NotRequired[bool]
    matchWholeWords: NotRequired[bool]
    useGroupScoring: NotRequired[bool]
    automationId: str
    role: NotRequired[str | None]
    sticky: NotRequired[int | None]
    cooldown: NotRequired[int | None]
    delay: NotRequired[int | None]

class LorebookData(TypedDict):
    entries: dict[str, LorebookEntry]
    deleted: NotRequired[list[str]]

LOREBOOK_TEMPLATE: LorebookData = {"entries": {}}

def is_lorebook_data(data: object) -> TypeGuard[LorebookData]:
    if not isinstance(data, dict):
        return False
    if "entries" not in data:
        return False
    if not isinstance(data["entries"], dict):
        return False
    return True

@final
class LorebookDataHandler(AbstractDataHandler):
    entry_added = QtCore.Signal(str)
    entry_deleted = QtCore.Signal(str)
    entry_updated = QtCore.Signal(str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.data: LorebookData | None = None
        self.original_data: LorebookData | None = None
        self.cache: dict[str, str] = {}
        self.input_path: str | None = None
        self.cache_file_path: str | None = None
        self._is_dirty: bool = False
        self.modified_entry_ids: set[str] = set()
        self.deleted_entry_ids: set[str] = set()

    def _ensure_entry_key_is_list(self, entry_data: LorebookEntry) -> None:
        current_primary_key_field: list[str] | None = entry_data.get("key")
        consolidated_keys: set[str] = set()
        if (
            isinstance(current_primary_key_field, str)
            and current_primary_key_field.strip()
        ):
            consolidated_keys.add(current_primary_key_field.strip())
        elif isinstance(current_primary_key_field, list):
            for item in current_primary_key_field:
                if item.strip():
                    consolidated_keys.add(item.strip())
        entry_data["key"] = sorted(list(consolidated_keys))

    @override
    def is_dirty(self) -> bool:
        return self._is_dirty

    def reset_state(self) -> None:
        self.data = None
        self.original_data = None
        self.modified_entry_ids.clear()
        self.deleted_entry_ids.clear()
        self.input_path = None
        self.set_dirty_flag(False)
        logger.debug("LorebookDataHandler state has been reset.")

    @override
    def load(self, path: str) -> None:
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        self.reset_state()
        try:
            with open(file=path, mode="r", encoding="utf-8") as f:
                loaded_json = cast(dict[str, object], json.load(f))
            if not is_lorebook_data(loaded_json):
                raise ValueError("Invalid LORE-book format.")
            self.original_data = loaded_json
            self.data = copy.deepcopy(x=self.original_data)
            self.input_path = path
            
            base_name, _ = os.path.splitext(self.input_path)
            edit_file_path: str = f"{base_name}_edit.json"
            if os.path.exists(path=edit_file_path):
                try:
                    with open(file=edit_file_path, mode="r", encoding="utf-8") as f:
                        edits = cast(dict[str, object], json.load(fp=f))
                    if is_lorebook_data(edits):
                        for del_id in edits.get("deleted", []):
                            if str(del_id) in self.data["entries"]:
                                del self.data["entries"][str(del_id)]
                            self.deleted_entry_ids.add(str(del_id))
                        for entry_id, edited_entry_data in edits["entries"].items():
                            self.deleted_entry_ids.discard(entry_id)
                            self.data["entries"][entry_id] = edited_entry_data
                except Exception as e:
                    logger.error(f"Failed to apply edits: {e}")

            for entry_data in self.data["entries"].values():
                self._ensure_entry_key_is_list(entry_data)
            self.data_loaded.emit()
            self.set_dirty_flag(False)
        except Exception as e:
            self.reset_state()
            raise e

    @override
    def get_cache_path(self) -> str:
        if not self.input_path:
            return ""
        cache_base_name, _ = os.path.splitext(os.path.basename(self.input_path))
        return os.path.join(
            os.path.dirname(self.input_path),
            f"{cache_base_name}_translation_cache.json",
        )

    def get_sorted_lore_entries(self) -> list[tuple[str, LorebookEntry]]:
        if not self.data:
            return []
        entries: dict[str, LorebookEntry] = self.data["entries"]

        def sort_key(item: tuple[str, LorebookEntry]) -> int:
            try:
                return item[1].get("uid", 0)
            except (ValueError, TypeError, KeyError):
                return 0

        return sorted(entries.items(), key=sort_key)

    @override
    def save(self) -> None:
        assert self.input_path is not None, "Cannot save with no input path set."
        assert self.data is not None, "Cannot save with no data loaded."

        if self.modified_entry_ids or self.deleted_entry_ids:
            base_name, _ = os.path.splitext(self.input_path)
            edit_file_path: str = f"{base_name}_edit.json"

            logger.info(f"Saving changes to {edit_file_path}...")

            edits_to_save: LorebookData = {"entries": {}, "deleted": []}

            if os.path.exists(path=edit_file_path):
                try:
                    with open(edit_file_path, mode="r", encoding="utf-8") as f:
                        existing_edits = cast(dict[str, object], json.load(fp=f))
                    if is_lorebook_data(existing_edits):
                        edits_to_save = existing_edits
                except Exception as e:
                    logger.warning(f"Could not read existing edit file: {e}")

            for entry_id in self.modified_entry_ids:
                if entry_id in self.data["entries"]:
                    edits_to_save["entries"][entry_id] = self.data["entries"][entry_id]

            for del_id in self.deleted_entry_ids:
                if del_id in edits_to_save["entries"]:
                    del edits_to_save["entries"][del_id]

            edits_to_save["deleted"] = list(self.deleted_entry_ids)

            with open(file=edit_file_path, mode="w", encoding="utf-8") as f:
                json.dump(obj=edits_to_save, fp=f, ensure_ascii=False, indent=2)

            logger.info("Successfully saved edits and deletions.")
            self.modified_entry_ids.clear()
        else:
            logger.debug("Save called, but nothing modified.")

        self.set_dirty_flag(False)

    @override
    def get_project_name(self) -> str:
        if self.input_path:
            return os.path.basename(self.input_path)
        return "New LORE-book"

    def update_entry(self, entry_id: str, new_entry_data: LorebookEntry) -> None:
        if not self.data or entry_id not in self.data["entries"]:
            logger.warning(
                f"Attempted to update a non-existent entry with ID {entry_id}"
            )
            return
        self.data["entries"][entry_id] = new_entry_data
        self.modified_entry_ids.add(entry_id)
        self.set_dirty_flag(True)
        self.entry_updated.emit(entry_id, new_entry_data)
        logger.debug(f"Entry {entry_id} has been updated and marked for saving.")

    def create_new(self, path: str) -> None:
        logger.info(f"Creating and saving new LORE-book to {path}")
        new_data: LorebookData = copy.deepcopy(LOREBOOK_TEMPLATE)
        try:
            with open(file=path, mode="w", encoding="utf-8") as f:
                json.dump(obj=new_data, fp=f, ensure_ascii=False, indent=2)
            self.load(path)
        except Exception as e:
            logger.error(f"Failed to save new LORE-book to {path}: {e}", exc_info=True)
            raise e

    @override
    def get_translatable_items(self) -> list[TranslatableItem]:
        if not self.data:
            return []
        items_to_translate: list[TranslatableItem] = []
        for _, entry_data in self.get_sorted_lore_entries():
            uid: int | None = entry_data.get("uid")
            if uid is None:
                continue
            original_keys: list[str] = entry_data.get("key", [])
            for orig_key_text in original_keys:
                orig_key_text_stripped = orig_key_text.strip()
                if not orig_key_text_stripped:
                    continue
                item_id = f"{uid}:{orig_key_text_stripped}"
                entry_dict: dict[str, object] = dict(entry_data)
                item: TranslatableItem = TranslatableItem(
                    id=item_id,
                    source_text=orig_key_text_stripped,
                    context=entry_data.get("content", ""),
                    original_data=entry_dict,
                )
                items_to_translate.append(item)
        return items_to_translate

    @override
    def set_dirty_flag(self, dirty: bool) -> None:
        if dirty != self._is_dirty:
            self._is_dirty = dirty
            logger.debug(f"set_dirty_flag({dirty}): State changed.")
            self.dirty_state_changed.emit(dirty)

    @override
    def get_project_path(self) -> str | None:
        return self.input_path
    
    @override
    def get_file_filter(self) -> str:
        return "LORE-book (*.json);;All Files (*)"
    
    def find_entry_dict_key_by_uid(self, uid_to_find: str) -> str | None:
        if not self.data:
            return None
        uid_to_find_str = str(uid_to_find)
        for dict_key, entry_data_val in self.data["entries"].items():
            entry_uid_val: int | None = entry_data_val.get("uid")
            if entry_uid_val is not None and str(entry_uid_val) == uid_to_find_str:
                return str(dict_key)
        logger.warning(f"Could not find LORE entry dict key for UID '{uid_to_find}'.")
        return None

    def get_next_uid(self) -> int:
        if not self.data:
            return 0
        all_uids: list[int] = [
            entry['uid'] 
            for entry in self.data['entries'].values() 
            if 'uid' in entry]
        return max(all_uids) + 1 if all_uids else 0

    def add_new_entry(self) -> str:
        if not self.data:
            return ""
        new_uid: int = self.get_next_uid()
        new_entry: LorebookEntry = {
            "uid": new_uid,
            "key": [],
            "keysecondary": [],
            "comment": "New Entry",
            "content": "",
            "constant": False,
            "vectorized": False,
            "selective": True,
            "selectiveLogic": 0,
            "addMemo": True,
            "order": 100,
            "position": 0,
            "disable": False,
            "excludeRecursion": False,
            "preventRecursion": False,
            "delayUntilRecursion": False,
            "probability": 100,
            "useProbability": True,
            "group": "",
            "groupOverride": False,
            "groupWeight": 100,
            "automationId": "",
        }
        entry_id: str = str(new_uid)
        self.data["entries"][entry_id] = new_entry
        self.modified_entry_ids.add(entry_id)
        self.set_dirty_flag(True)
        self.entry_added.emit(entry_id)
        logger.info(f"Added new entry with UID: {new_uid}")
        return entry_id

    def duplicate_entry(self, source_entry_id: str) -> str:
        if not self.data or source_entry_id not in self.data["entries"]:
            return ""
        original_entry: LorebookEntry = copy.deepcopy(
            x=self.data["entries"][source_entry_id]
        )
        new_uid: int = self.get_next_uid()
        new_entry_id: str = str(new_uid)
        new_entry: LorebookEntry = original_entry
        new_entry["uid"] = new_uid
        new_entry["comment"] = f"{original_entry.get('comment', 'Entry')} (Copy)"
        self.data["entries"][new_entry_id] = new_entry
        self.modified_entry_ids.add(new_entry_id)
        self.set_dirty_flag(True)
        self.entry_added.emit(new_entry_id)
        logger.info(
            f"Duplicated entry {source_entry_id} to new entry with UID: {new_uid}"
        )
        return new_entry_id

    def delete_entry(self, entry_id: str) -> None:
        if not self.data or entry_id not in self.data["entries"]:
            logger.warning(
                f"Attempted to delete a non-existent entry with ID {entry_id}"
            )
            return

        del self.data["entries"][entry_id]

        self.deleted_entry_ids.add(entry_id)

        self.modified_entry_ids.discard(entry_id)

        self.set_dirty_flag(True)
        self.entry_deleted.emit(entry_id)
        logger.info(f"Deleted entry ID: {entry_id} from current session.")