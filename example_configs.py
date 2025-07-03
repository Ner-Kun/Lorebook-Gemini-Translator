"""
Example: How to use the Multi-Provider Translation System
"""

# Example 1: Using with Ollama
# 1. Start Ollama: ollama serve
# 2. Pull a model: ollama pull llama3.2
# 3. Configure in the app or modify endpoints_config.json:

ollama_config = {
    "name": "Ollama - Llama 3.2",
    "type": "openai",
    "base_url": "http://localhost:11434/v1",
    "models": ["llama3.2"],
    "auth_type": "none",
    "headers": {"Content-Type": "application/json"},
    "default_params": {
        "temperature": 0.7,
        "max_tokens": 4096
    }
}

# Example 2: Using with LM Studio
# 1. Load a model in LM Studio
# 2. Start the local server (usually port 1234)
# 3. Configure:

lm_studio_config = {
    "name": "LM Studio - Local Model",
    "type": "openai",
    "base_url": "http://localhost:1234/v1",
    "models": [],  # Will be auto-detected
    "auth_type": "none",
    "headers": {"Content-Type": "application/json"},
    "default_params": {
        "temperature": 0.5,
        "max_tokens": 2048
    }
}

# Example 3: Using with text-generation-webui
# 1. Start with --api flag
# 2. Configure:

textgen_config = {
    "name": "Text Generation WebUI",
    "type": "openai",
    "base_url": "http://localhost:5000/v1",
    "models": ["current_model"],
    "auth_type": "none",
    "headers": {"Content-Type": "application/json"},
    "default_params": {
        "temperature": 0.8,
        "max_tokens": 4096
    }
}

# Example 4: Using with a remote OpenAI-compatible API
remote_api_config = {
    "name": "Remote LLM Service",
    "type": "openai",
    "base_url": "https://api.example.com/v1",
    "models": ["model-1", "model-2"],
    "auth_type": "api_key",  # Requires API key
    "headers": {
        "Content-Type": "application/json"
    },
    "default_params": {
        "temperature": 0.7,
        "max_tokens": 4096
    }
}

# The complete configuration file would look like:
complete_config = {
    "endpoints": {
        "gemini": {
            "name": "Google Gemini",
            "type": "gemini",
            "base_url": "https://generativelanguage.googleapis.com",
            "models": ["gemini-2.5-flash-lite-preview-06-17"],
            "auth_type": "api_key"
        },
        "ollama": ollama_config,
        "lm_studio": lm_studio_config,
        "textgen": textgen_config,
        "remote_api": remote_api_config
    },
    "active_endpoint": "ollama"  # Set your preferred default
}

print("Example configurations created!")
print("\nTo use:")
print("1. Save the configuration to endpoints_config.json")
print("2. Start your chosen local LLM server")
print("3. Open the Lorebook Translator")
print("4. Go to File -> Configure Endpoints")
print("5. Select your endpoint and start translating!")
