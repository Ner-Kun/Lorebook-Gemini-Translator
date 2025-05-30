[![🇬🇧 English](https://img.shields.io/badge/README-English-blue)](../README.md)
[![🇺🇦 Українська](https://img.shields.io/badge/README-Українською-yellow)](README/README_UA.md)

# Lorebook Gemini Translator

## 📖 Description

Аpplication designed to help translate LORE-book keys/triggers from one language to another using Gemini.

**Why?** If you play in Ukrainian, for example, a key/trigger from the LORE-book written in English (or any other language) will never work! That's why you need to translate the keys/triggers.

![Main Window](images/S_1.png)
---

## ✨ Key Features

*   **LORE-book Translation:** Translate key strings from your LORE-book.
*   **Gemini Integration:** Uses Gemini AI models for translation.
*   **Language Management:** Add/remove/choose source and target languages.
*   **Batch Operations:**
    *   Translate all entries.
    *   Translate selected entries.
    *   Regenerate selected translations.
*   **Manual Editing:** Modify translations directly in-app.
*   **Contextual Translation:** Use the `content` field of an entry to improve translation quality (disable if responses are empty).
*   **Model Thinking Output:** Adds a system hint “thinking” to improve translation quality. *Sometimes simpler models (e.g., `gemini-2.0-flash`) work even better with it.* (disable if responses are empty.)
*   **Translation Cache:**
    *   Auto-saves progress.
    *   No data loss on accidental close or power outage.
    *   Cache stored per file: `<lorebook_name>_translation_cache.json`
*   **RPM Monitoring:**
    *   Visual indicator and cooldowns to avoid exceeding Gemini API limits.
    *   Customizable RPM thresholds.
*   **Recent Files:** Quick access to previously opened LORE-books.
*   **Export Translations:** Merge original keys with translations into the exported file for use in SillyTavern.

---

## 🚀 Easy Run (Windows)
1.  **Ensure Python 3.9+ is installed:** Download and install Python from [python.org](https://www.python.org/downloads/) if you haven't already. **Make sure to check "Add Python to PATH" during installation.**
2.  **Download the launcher:**
    *   Go to the [Download](https://github.com/Ner-Kun/Lorebook-Gemini-Translator/releases).
    *   Download the `run_translator.bat` file.
    *   (Alternatively, clone the whole repository and find `run_translator.bat` in the root directory).
3.  **Run:**
    *   Place `run_translator.bat` in a folder of your choice.
    *   Double-click `run_translator.bat`.
    *   On subsequent runs, it will activate the existing environment and launch the app.

---
## ✅ TODO

### 🚀 Priority Tasks
- [ ] **🔁 API Key Rotation:** Implement a mechanism to work with multiple API keys.  
- [ ] **🔑 Generate Synonyms for Keys:** Add a feature to query the AI for a list of synonyms for a selected key in the target language.  
- [ ] **🔑 Generate Keys with Errors:** Implement the ability to generate key variations with common typos.  
- [ ] **🔑 Generate Plural Forms for Keys:** Add an option to automatically create plural forms for selected key.  
- [ ] **🔑 Extract Keys from Content:** Introduce a feature allowing the AI to analyze the "content" field of a LORE entry and suggest a list of potential keys based on its text.

### 🛠️ Core Functionality
- [ ] **📖 Translate Main LORE Content (the "content" field):** Implement translation not only for keys but also for the main content of LORE entries (For larger models, this is not as important, so it is not a priority).  
- [ ] **🔍 Search within Lorebook:** Add a search function for the loaded lorebook (by key, content, translations).

### ☁️ API & Models
- [ ] **🌐 Support Alternative Backends:** Аdd support for Chutes.ai/OpenRouter.ai.  
- [ ] **🤖 Dual-Model Cross-Check:** The ability to cross-check/compare results between two different models or services.

### 💡 Future Features
- [ ] **📝 Aggressively Compress "content" for LLMs:** A feature for AI-driven compression of the "content" field to maximize essence retention with minimal volume, for use in models with limited context. *The main goal is machine-readable, not human-readable, output.*
- [ ] **🌎 Interface localization**

### 🤔 Miscellaneous
- [ ] ❓ Maybe something else... ideas welcome!

---

## 🛠️ Requirements (Manual)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)]() ![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-blue?style=for-the-badge&logo=qt&logoColor=white) [![pyqtdarktheme-fork](https://img.shields.io/badge/pyqtdarktheme%20fork-2.3.4%2B-blue?style=for-the-badge)](https://pypi.org/project/PyQtDarkTheme-fork/) ![Gemini%20API](https://img.shields.io/badge/Gemini%20API-Google%20generativeai-blue?style=for-the-badge&logo=google&logoColor=white) [![API%20Key](https://img.shields.io/badge/API%20Key-Click_on_me-red?style=for-the-badge&logo=lock&logoColor=white)](https://aistudio.google.com/app/apikey)

---

## ⚙️ Installation (Manual)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Ner-Kun/Lorebook-Gemini-Translator.git
    cd Lorebook-Gemini-Translator
    ```

2.  **Install dependencies:**
    ```bash
    pip install PySide6 google-generativeai pyqtdarktheme-fork
    ```

---

## 🔧 Configuration

### 1. API Key

* On first run, you'll be prompted to enter your Google Gemini API key. ([Get key](https://aistudio.google.com/app/apikey))
* You can also access settings anytime via `File > Settings`.

### 2. Gemini Model

* Default: `gemini-2.5-flash-preview-05-20`
* Changeable via `File > Settings`
* Some models may require paid tiers — see [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits#free-tier)

### 3. Languages

* **Source Language:** Original language of your LORE-book's keys (default: English)
* **Target Languages:** Add any number of target languages

---

## ▶️ Usage

1. **Run the app:**
    ```bash
    python "Lorebook Gemini Translator.py"
    ```
    *(or just launch `run_translator.bat` on Windows)*

2. **Enter API Key** when prompted. (_You can get an API key here - [Get key](https://aistudio.google.com/app/apikey)_)

3. **Open a LORE-book:** via menu or "Open LORE-book" button.

4. **Choose Languages:**
    * Set source language.
    * Set target language.

5. **Translate:**
    * Translate individual, selected, or all entries.
    * Regenerate entries if needed.

6. **Edit/Save:**
    * Manually edit translations.
    * Saved instantly to cache.

7. **Manage Cache:**
    * Clear specific or all translations for a language.

8. **Export Translated LORE-book:**
    * Click “Export LORE-book” or `File > Save As...`
    * Fully compatible with SillyTavern and similar tools.

---
💬 If you like the tool — give it a ⭐ on GitHub or suggest improvements!
