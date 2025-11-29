# Changelog

## [0.2.0] - 2025-11-22

**TL;DR**: Complete architecture overhaul. Transition from a monolithic script to a modular system (Core + App). Added support for any OpenAI-compatible APIs, as well as local models (Ollama, LM Studio, etc.). Implemented a new launcher based on `uv` and full interface localization.

### 🚀 Added

- **Modular architecture**: The project is divided into `omni_trans_core` (universal core) and `lgt_app` (Lorebook-specific functionality).
- **API and Provider Support**:
  - **Local LLMs**: Full support for Ollama and LM Studio.
  - **Cloud providers**: Integration with OpenRouter, Mistral, DeepSeek, NVIDIA NIM.
  - **OpenAI-compatible APIs**: Ability to connect to any API supporting the OpenAI format.
  - **Flexible configuration**: Ability to override `base_url` even for built-in providers.
- **Thought parsing (CoT)**: Configuration of custom tags for extracting model "thoughts" from the response.
- **Thinking Modes**:
  - **Auto**: Using the `reasoning_effort` parameter.
  - **By Commands**: Using special activation tags if the model supports enabling/disabling thinking via prompt.
  - **By Header / Body Parameter**: Injection of parameters into the request body (YAML structure support) or headers, as well as exclusion of unnecessary parameters.
- **Timeouts**: Configuring response waiting time from the model (default 600 sec).
- **Limit and Queue Management**:
  - **Limits**: Setting global limits for the provider and individual limits for each model (RPM, TPM, RPD).
  - **Sequential Processing**: Sequential processing mode (waiting for a response before sending the next request). When disabled, requests are sent in parallel.
  - **Smart Delay**: Dynamic delay to prevent exceeding limits. The closer to the limit, the longer the pause between requests.
  - **Exponential Backoff**: Upon receiving a `429 RateLimitError`, the waiting time increases exponentially (up to 10 sec), and after success, it gradually decreases.
  - **[WIP] Limit Detection**: Experimental function for reading actual limits from API response headers (currently unstable).
  - **[WIP] Model Information**: Getting technical data about the model (context window, output token limit).
- **Launcher**:
  - Transition to the `uv` package manager for lightning-fast dependency installation.
  - Automatic environment "healing": recreating venv and downloading components on failure.
- **Interface (UI)**:
  - **Widgets**:
    - **Active Connection**: Quick selection of provider and model.
    - **Generation Parameters**: Configuration of temperature, top_p, penalties, etc.
    - **RPM Monitor**: Visualization of limit usage in real-time.
  - **Tabs and Windows**: New "Custom connections" tab and connection editing dialog.
  - **UX**: Animated notifications (Notification Banner), smooth field appearance, tooltips.
  - **[WIP] Loading Overlay**: Interface blocking with animation during heavy operations (loading/saving).
  - **Qt Designer**: Implemented `.ui` file loader to simplify form editing.
- **Localization and Developer Tools**:
  - Implemented translation system (`i18n`). Current language: English (En).
  - "Language" tab in settings.
  - **Developer Mode (Translation)**: Special debugging mode for translations:
    - Checking for missing and extra keys in JSON.
    - Copying key on `Ctrl + Right Click`.
    - Hot Reboot: Instant application of changes to localization files.
  - **Display modes**:
    - **Translated** - Shows translation, if translation is missing, shows the key.
    - **Key** - Shows only keys.
    - **Original** - When a translation language is selected, shows the original language (English).

### 🔄 Changed

- **Configuration**: Complete transition from `.json` to `.yaml` for storing settings and connection profiles.
- **Performance**: Transition to `QThreadPool` and `QRunnable`.
- **UI/UX**:
  - Input fields "shake" when validating incorrect data.
  - Settings grouped by tabs (API, Logging, Language).
  - Animations when deleting rows and on successful translation.
  - Automatic scrolling of the table to the last translated element.
  - Added "Delete all" button in the editing widget.
  - The model inspector now displays the name of the model being used.

### 🐛 Fixed

- Fixed interface freezing when waiting for an API response.
- Improved error handling for network and quota errors (Quota Exceeded) - now with detailed output to the log.
- Fixed UI behavior when switching tabs in the settings window.
- Fixed a bug in the editor where after deleting a row, it visually remained but the data was cleared.

### 🗑️ Removed

- Outdated `update.bat` script (replaced by the built-in update mechanism in the launcher and core).
- Hard code binding to Google GenAI (now it's just one of many providers).
- Removed unused placeholder tabs.

### Developer note

> This release contains many more internal changes and optimizations than described above. Version 0.2.0 is functionally equivalent to 0.1.0 but is built on a completely new codebase.
> Some features are marked as [WIP] - they may work unstably or will be changed in future updates. This release is necessary to stabilize the architecture and further develop the project.
