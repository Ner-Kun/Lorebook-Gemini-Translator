# Guide: Model Selection

## 🎯 How to Select the Model to Use

### In the Endpoint Configuration Dialog

1. **File → Configure Endpoints**
2. Select your endpoint (e.g., lmstudio)
3. Click **"Test Connection"**
4. The list of available models appears automatically
5. **Click on a model in the list** to select it
6. Or manually type the name in **"Active Model"**
7. Save

### Configuration Structure

Each endpoint now stores:
- `models`: List of automatically detected models
- `active_model`: The currently selected model
- `additional_models`: Manually added models

### Example with LM Studio

1. Load a model in LM Studio
2. In the app, test the connection
3. You'll see all available models:
   - `amoral-gemma3-12b-v2-qat`
   - `dolphin-mistral-24b`
   - etc.
4. Click on the one you want to use
5. It appears in "Active Model"
6. Save

### Quick Model Change

To change models without restarting the app:
1. **File → Configure Endpoints**
2. Select another model
3. Save
4. The next translation batch will use this model

### Automatic Fallback

If no model is specified:
- For Gemini: Uses the default model from settings
- For OpenAI: Uses the first model in the list
- If list is empty: Uses "default-model"

## 🔧 Manual Configuration

In `endpoints_config.json`:

```json
{
  "endpoints": {
    "lmstudio": {
      "name": "LM Studio",
      "type": "openai",
      "base_url": "http://localhost:1234/v1",
      "models": ["model1", "model2"],
      "active_model": "model1",  // The selected model
      "auth_type": "none"
    }
  }
}
```

## 💡 Tips

- **LM Studio**: The model loaded in the UI is automatically available
- **Ollama**: Use `ollama list` to see your models
- **Text-gen-webui**: Only one active model at a time

## 🐛 Troubleshooting

**"No model selected"**
- Test the connection to load the list
- Make sure your local server is active

**"Model not found"**
- The model must be loaded in your server
- Check the exact spelling

**Change not applied**
- Save after selecting
- Jobs in progress use the old model
