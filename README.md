
# Lorebook Gemini Translator

[![English](https://img.shields.io/badge/README-English-blue)](../README.md)
[![Українська](https://img.shields.io/badge/README-Українською-yellow)](README/README_UA.md)
[![Русский](https://img.shields.io/badge/README-Русский-white)](README/README_ru.md)

## 📖 Description

Application designed to help translate LORE-book keys/triggers from one language to another using Gemini. It also includes a full-featured lorebook editor.

**Why?** If you play in Ukrainian, for example, a key/trigger from the LORE-book written in English (or any other language) will never work! That's why you need to translate the keys/triggers.

---

## ✨ Key Features

* **Tabbed Interface:** Separate, dedicated tabs for "Editor" and "Translation" for a streamlined workflow.
* **Full-Featured Lorebook Editor:**
  * Create, edit, and delete lorebook entries directly within the app.
  * Functionality designed to be similar to the SillyTavern editor.
  * Create new, empty lorebooks from scratch (`File > New`).
* **Translation:**
  * Translate key strings from your LORE-book using Gemini AI models.
  * **Contextual Translation:** Use the `content` field of an entry to improve translation quality.
  * **Model Thinking:** You can enable thinking (enabled by default) to improve translation quality, with a configurable token budget.
* **API Management:**
  * **API Key Rotation:** Use a list of API keys. The app automatically rotates them to bypass RPD (Requests per day) limits.
  * **Smart Error Handling:** If a key hits its rate limit, it's temporarily disabled, and the app seamlessly switches to the next one. Failed tasks are automatically re-queued.
  * **Dynamic Rate Limiting:** The app automatically calculates the optimal delay between requests based on RPM. It even listens to API error messages to adjust speed on the fly.
* **Batch & Search Operations:**
  * Translate all or selected entries.
  * Regenerate selected translations.
  * **Search:** Quickly find entries by key, content, or translation within the Editor and Translation tabs.
* **Cache & Autosave:**
  * **Real-time Autosave:** All changes in the editor and translations are saved automatically in the background. No more lost work!
  * A `*` in the window title indicates unsaved changes.
  * Cache is stored per file: `<lorebook_name>_translation_cache.json` and `<lorebook_name>_edit.json`.
* **Automatic Updates:** The app checks for new versions on startup and can update itself.
* **RPM Monitoring:** Visual indicator shows the current API key, its load, and cooldown status.
* **Flexible Export:**
  * The export dialog gives you full control.
  * Choose which translated languages to include.
  * Decide whether to include or exclude original keys.
  * Configure how to handle keys that have no translation (keep original or skip).

### 📸 Screenshots

<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD003 -->
<!-- markdownlint-disable MD023 -->
<details>
  <summary>🖼️ Click to view app screenshots</summary>
  <br>

  **Translator**
  ![Translator](images/s_1.png)

  **Editor**
  ![Editor](images/s_2.png)

  **Export**
  ![Export](images/s_3.png)

  **Inspector**
  ![Inspector](images/s_4.png)
</details>
<!-- markdownlint-enable MD033 -->
<!-- markdownlint-enable MD003 -->
<!-- markdownlint-enable MD023 -->

---
💬 If you like the tool — give it a ⭐ on GitHub or suggest improvements

---

## 🚀 Easy Run (Windows)

1. **Ensure Python 3.9+ is installed:** Download and install Python from [python.org](https://www.python.org/downloads/) if you haven't already. **Make sure to check "Add Python to PATH" during installation.**
2. **Download the launcher:**
    * Go to the [Releases](https://github.com/Ner-Kun/Lorebook-Gemini-Translator/releases).
    * Download the `run_translator.bat` files.
3. **Run:**
    * Place `run_translator.bat` in a folder of your choice.
    * Double-click `run_translator.bat` to launch the application.
    * Waiting a little...
    * The app will automatically check for updates on startup.

---

## 🛠️ Requirements (Manual)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white) ![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-blue?style=for-the-badge&logo=qt&logoColor=white) [![pyqtdarktheme-fork](https://img.shields.io/badge/pyqtdarktheme%20fork-2.3.4%2B-blue?style=for-the-badge)](https://pypi.org/project/PyQtDarkTheme-fork/) ![Gemini%20API](https://img.shields.io/badge/Gemini%20API-Google%20genai-blue?style=for-the-badge&logo=google&logoColor=white) ![Gemini%20API](https://img.shields.io/badge/Gemini%20API-google%20api%20core-blue?style=for-the-badge&logo=google&logoColor=white) [![API%20Key](https://img.shields.io/badge/API%20Key-Click_on_me-red?style=for-the-badge&logo=lock&logoColor=white)](https://aistudio.google.com/app/apikey)

---

## ⚙️ Installation (Manual)

> ⚠️ **Note for Manual Installation (v0.1.x):** This method is intended for advanced users. The built-in automatic updater (`update.bat`) is designed to work with the virtual environment created by `run_translator.bat`. A manual installation will **not** be able to use the auto-updater. This will be addressed in a future release.

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Ner-Kun/Lorebook-Gemini-Translator.git
    cd Lorebook-Gemini-Translator
    ```

2. **Install dependencies:**

    ```bash
    pip install PySide6 google-genai google-api-core requests packaging pyqtdarktheme-fork rich
    ```

---

## 🔧 Configuration

### 1. API Key

* On first run, you'll be prompted to enter your Google Gemini API key(s). ([Get key](https://aistudio.google.com/app/apikey))
* Also, immediately check the RPM limits and set the ones you need for your chosen model (everything is already configured by default). Google changes them quite often  - [See here](https://ai.google.dev/gemini-api/docs/rate-limits)
* The application supports a **list of API keys**. You can add multiple keys in the settings (`File > Settings`), and the app will rotate through them to manage rate limits.

### 2. Gemini Model

* Default: `gemini-2.5-flash-lite-preview-06-17`
* Changeable via `File > Settings`.
* Some models may require paid tiers — see [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits#free-tier).

### 3. Languages

* **Source Language:** Original language of your LORE-book's keys (default: English).
* **Target Languages:** Add any number of target languages.

---

## ▶️ Usage

1. **Run the app:**

    ```bash
    python Lorebook_Gemini_Translator.py
    ```

    *(or just launch `run_translator.bat` on Windows)*

2. **Open a LORE-book:** via the menu. You can also create a new one via `File > New`.

3. **Navigate the App:**
    * Use the **Editor** tab to view, add, or modify lorebook entries.
    * Use the **Translation** tab to manage translations.

4. **Translate:**
    * Set the source and target languages.
    * Translate individual, selected, or all entries.
    * Use the search bar to quickly find entries.

5. **Edit/Save:**
    * Manually edit translations or lorebook content.
    * Changes are saved automatically to a cache file.

6. **Export Translated LORE-book:**
    * Click “Export LORE-book”.
    * Use the advanced export options to customize your final file.
    * The exported file is fully compatible with SillyTavern and similar tools.

---

## ✅ TODO

### 🛠️ Core Functionality

* [ ] **📖 Translate Main LORE Content (the "content" field):** Implement translation for the main content of LORE entries.
* [ ] **🔧 Improve Manual Installation:** Rework the auto-update mechanism to be compatible with manual/git-based installations that do not use the provided `run_translator.bat` script and its virtual environment.
* **AI-Powered Key Generation:**
  * [ ] **🔑 Generate Synonyms for Keys:** Add a feature to query the AI for a list of synonyms for a selected key in the target language.
  * [ ] **🔑 Generate Keys with Errors:** Implement the ability to generate key variations with common typos.
  * [ ] **🔑 Generate Plural Forms for Keys:** Add an option to automatically create plural forms for selected keys.
  * [ ] **🔑 Extract Keys from Content:** Introduce a feature allowing the AI to analyze the "content" field of a LORE entry and suggest a list of potential keys based on its text.

### ☁️ API & Models

* [ ] **🌐 Support Alternative Backends:** Add support for Chutes.ai/OpenRouter.ai to provide more model choices and robust rate-limit workarounds.
* [ ] **🤖 Dual-Model Cross-Check:** The ability to cross-check/compare results between two different models or services.

### 💡 Future Features

* [ ] **📝 Aggressively Compress "content" for LLMs:** A feature for AI-driven compression of the "content" field to maximize essence retention with minimal volume, for use in models with limited context. *The main goal is machine-readable, not human-readable, output.*
* [ ] **🌎 Interface localization**

### 🤔 Miscellaneous

* [ ] ❓ Maybe something else... ideas welcome!

### ✅ Completed

* [x] **🔁 API Key Rotation:** Implement a mechanism to work with multiple API keys. (v0.1.0)
* [x] **🔍 Search:** Add a search function. (v0.1.0)
* [x] **📝 Lorbook editor:** Make the editor functionality similar to SillyTavern. (v0.1.0)
* [x] **💾 Real-time auto-save:** Make the app save everything automatically. (v0.1.0)
* [x] **🚀 Automatic updates:** The app automatically checks for new versions and offers to update (also automatically). (v0.1.0)
* [x] **🔧 RPM self-control:** Make it so that the suggestion can lower the RPM if the user has set it higher than possible. (v0.1.0)
