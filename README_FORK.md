# Multi-Provider Fork for Lorebook-Gemini-Translator

## 🚀 New Features

This fork adds support for **multiple translation providers**, allowing you to use:
- Google Gemini (original)
- **Any OpenAI-compatible endpoint** (Ollama, LM Studio, text-generation-webui, etc.)
- Uncensored local models 😈

## 📋 Installation

1. Clone this fork or download the ZIP
2. Install dependencies: `pip install -r requirements.txt`
3. Run with `run_translator.bat`

## 🔧 Configuration

### Option 1: Via the Interface
1. **File → Configure Endpoints**
2. Select or add your endpoint
3. Test the connection
4. Save

### Option 2: Edit `endpoints_config.json`
```json
{
  "endpoints": {
    "lm_studio": {
      "name": "LM Studio Local",
      "type": "openai",
      "base_url": "http://localhost:1234/v1",
      "auth_type": "none"
    }
  },
  "active_endpoint": "lm_studio"
}
```

## 🎮 Using with LM Studio

1. Load your model in LM Studio
2. Enable the local server (port 1234)
3. In the app: **File → Configure Endpoints**
4. Select "Local OpenAI-Compatible"
5. URL: `http://localhost:1234/v1`
6. Test and save
7. Translate!

## 🐛 Known Issues & Solutions

### "No API keys" with local endpoint
- **Fixed**: Endpoints with `auth_type: "none"` no longer require API keys

### No model selector in main UI
- **Workaround**: The model loaded in LM Studio is automatically used
- **TODO**: Add a combo box for model selection

### Only translates "key", not "content"
- **Current limitation**: The original script only translates keys
- **TODO**: Add option to translate content as well

## 🔀 Contributing & Pull Requests

To contribute to the original project:

### Recommended strategy: **2 separate PRs**

1. **PR 1: Multi-Provider Support**
   - Modular architecture
   - OpenAI endpoint support
   - Configuration interface
   - Full backward compatibility

2. **PR 2: Content Translation** (if you implement it)
   - Option to translate content
   - Choice of key/content/both
   - Separate cache for content

### Why separate?
- Easier to review
- Owner can accept one feature without the other
- Better organized changes
- Cleaner Git history

### How to make a PR:
1. Fork the original repo on GitHub
2. Clone your fork
3. Create a branch: `git checkout -b feature/multi-provider`
4. Commit your changes
5. Push to your fork
6. Open a PR on the original repo

## 📝 Technical Changes

### Added Files:
- `translation_providers.py` - Modular provider system
- `endpoint_config_dialog.py` - Configuration UI
- `endpoints_config.json` - Endpoint configuration

### Modified Files:
- `Lorebook_Gemini_Translator.py` - Provider system integration

### Extension Points:
- New provider? Inherit from `TranslationProvider`
- New auth type? Add in `endpoint_config_dialog.py`

## 💡 Future Ideas

- [ ] Model selector in main UI
- [ ] Content translation in addition to keys
- [ ] Support for more providers (Claude API, Cohere, etc.)
- [ ] Translation profiles per endpoint
- [ ] Performance metrics per provider

## 🙏 Credits

- Original project: [Ner-Kun/Lorebook-Gemini-Translator](https://github.com/Ner-Kun/Lorebook-Gemini-Translator)
- Multi-provider fork: [your-username]

---

Enjoy your uncensored translations! 🎉
