# Multi-Provider Translation Support

This fork of Lorebook-Gemini-Translator adds support for multiple translation providers, including any OpenAI-compatible endpoint.

## New Features

- **Multiple Translation Providers**: Support for Google Gemini and any OpenAI-compatible API
- **Modular Architecture**: Easy to add new providers
- **Endpoint Configuration UI**: User-friendly interface to manage translation endpoints
- **Local LLM Support**: Works with Ollama, LM Studio, text-generation-webui, etc.

## Configuration

### Using the Endpoint Configuration Dialog

1. Go to **File → Configure Endpoints** in the menu
2. Select or add a new endpoint
3. Configure the endpoint settings:
   - **Name**: Display name for the endpoint
   - **Type**: Either `gemini` or `openai`
   - **Base URL**: API endpoint URL
   - **Authentication**: None, API key, or custom
   - **Models**: Available models (can be auto-detected)

### Supported Endpoints

#### Google Gemini (Default)
- Type: `gemini`
- Base URL: `https://generativelanguage.googleapis.com`
- Authentication: API key required

#### Local OpenAI-Compatible
- Type: `openai`
- Base URL: `http://localhost:11434/v1` (for Ollama)
- Authentication: None

#### Custom OpenAI Endpoints
- Type: `openai`
- Base URL: Your custom endpoint
- Authentication: As required by your provider

## Manual Configuration

You can also edit `endpoints_config.json` directly:

```json
{
  "endpoints": {
    "gemini": {
      "name": "Google Gemini",
      "type": "gemini",
      "base_url": "https://generativelanguage.googleapis.com",
      "models": ["gemini-2.5-flash-lite-preview-06-17"],
      "auth_type": "api_key"
    },
    "ollama": {
      "name": "Ollama Local",
      "type": "openai",
      "base_url": "http://localhost:11434/v1",
      "models": ["llama3.2", "mistral"],
      "auth_type": "none"
    }
  },
  "active_endpoint": "gemini"
}
```

## Adding New Providers

To add support for a new provider type:

1. Create a new class in `translation_providers.py` that inherits from `TranslationProvider`
2. Implement the required methods:
   - `list_models()`: List available models
   - `translate()`: Perform translation
3. Update `ProviderFactory.create_provider()` to handle your new type

## Example: Using with Ollama

1. Install and run Ollama
2. Pull a model: `ollama pull llama3.2`
3. In the app, go to File → Configure Endpoints
4. Select "Local OpenAI-Compatible"
5. Set Base URL to `http://localhost:11434/v1`
6. Add your model name(s)
7. Save and start translating!

## Example: Using with LM Studio

1. Run LM Studio with a loaded model
2. Enable the local server (usually on port 1234)
3. Configure endpoint with Base URL: `http://localhost:1234/v1`
4. The app will auto-detect available models

## Troubleshooting

- **Connection Failed**: Check that your local server is running
- **No Models Found**: Some providers require manual model entry
- **Authentication Error**: Verify your API key or authentication settings
