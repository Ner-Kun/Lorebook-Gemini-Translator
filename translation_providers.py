"""
Translation Provider Interface
Abstract base class and implementations for different LLM providers
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
import requests

# Import Google Generative AI if available
try:
    import google.generativeai as genai
    from google.ai.generativelanguage_v1beta.types import GenerateContentResponse
    from google.api_core.exceptions import ResourceExhausted
    from google import errors
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    GenerateContentResponse = None
    ResourceExhausted = None
    errors = None

logger = logging.getLogger('Lorebook_Gemini_Translator')


class TranslationProvider(ABC):
    """Abstract base class for translation providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown Provider')
        self.type = config.get('type', 'unknown')
        self.base_url = config.get('base_url', '')
        self.auth_type = config.get('auth_type', 'none')
        self.headers = config.get('headers', {})
        self.default_params = config.get('default_params', {})
    
    @abstractmethod
    def list_models(self, api_key: Optional[str] = None) -> List[str]:
        """List available models from the provider"""
        pass
    
    @abstractmethod
    def translate(self, 
                  api_key: Optional[str],
                  model_name: str,
                  text: str,
                  source_lang: str,
                  target_lang: str,
                  context: Optional[str] = None,
                  enable_thinking: bool = True,
                  thinking_budget: int = -1) -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Translate text using the provider
        Returns: (prompt, translation, thinking_text, usage_metadata)
        """
        pass


class GeminiProvider(TranslationProvider):
    """Google Gemini implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library not installed. Run: pip install google-generativeai")
    
    def list_models(self, api_key: Optional[str] = None) -> List[str]:
        """List available Gemini models"""
        if not api_key:
            return self.config.get('models', [])
        
        try:
            client = genai.Client(api_key=api_key)
            models = [m.name.replace("models/", "") for m in client.models.list() 
                     if m.name.startswith("models/gemini")]
            return sorted(list(set(models)))
        except Exception as e:
            logger.error(f"Error fetching Gemini models: {e}")
            return self.config.get('models', [])
    
    def translate(self, 
                  api_key: Optional[str],
                  model_name: str,
                  text: str,
                  source_lang: str,
                  target_lang: str,
                  context: Optional[str] = None,
                  enable_thinking: bool = True,
                  thinking_budget: int = -1) -> Tuple[str, str, str, Dict[str, Any]]:
        """Translate using Gemini API"""
        
        # Build the prompt
        base_prompt = (
            f"You are a master linguist and loremaster specializing in video game localization. "
            f"Your task is to translate LORE keywords from {source_lang} into {target_lang}.\n\n"
            f"Instructions:\n"
            f"The translation MUST be concise, accurate, and function effectively as a search key or in-game display term.\n"
            f"Translate ONLY the text provided below.\n"
            f"Do NOT include explanations, commentary, or extraneous information.\n"
            f"If the text is already in {target_lang}, return it unchanged.\n"
            f"Use appropriate capitalization and formatting for {target_lang}.\n\n"
        )
        
        if context:
            base_prompt += f"Context (for reference only - DO NOT translate this):\n{context}\n\n"
        
        base_prompt += f"Text to translate:\n{text}\n\nTranslation:"
        
        # Prepare config
        config = genai.GenerationConfig(
            temperature=self.default_params.get('temperature', 0.7),
            max_output_tokens=self.default_params.get('max_tokens', 4096),
            candidate_count=1
        )
        
        if enable_thinking and thinking_budget > 0:
            config.thinking_config = {"thinking_budget": thinking_budget}
        
        # Make the API call
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=f"models/{model_name}",
                contents=base_prompt,
                config=config
            )
            
            # Extract response
            thinking_text = ""
            translation = ""
            usage_metadata = {}
            
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage_metadata = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                    'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0),
                    'thinking_tokens': getattr(response.usage_metadata, 'thinking_token_count', 0)
                }
            
            if response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    if hasattr(candidate.grounding_metadata, 'thinking_parts_text'):
                        thinking_text = candidate.grounding_metadata.thinking_parts_text or ""
                
                if candidate.content and candidate.content.parts:
                    translation = candidate.content.parts[0].text.strip()
            
            return base_prompt, translation, thinking_text, usage_metadata
            
        except Exception as e:
            logger.error(f"Gemini translation error: {e}")
            raise


class OpenAIProvider(TranslationProvider):
    """OpenAI-compatible API implementation (works with Ollama, LM Studio, etc.)"""
    
    def list_models(self, api_key: Optional[str] = None) -> List[str]:
        """List available models from OpenAI-compatible endpoint"""
        try:
            url = f"{self.base_url}/models"
            headers = self.headers.copy()
            
            if api_key and self.auth_type == 'api_key':
                headers['Authorization'] = f"Bearer {api_key}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            return sorted(models)
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI models from {self.base_url}: {e}")
            return self.config.get('models', [])
    
    def translate(self, 
                  api_key: Optional[str],
                  model_name: str,
                  text: str,
                  source_lang: str,
                  target_lang: str,
                  context: Optional[str] = None,
                  enable_thinking: bool = True,
                  thinking_budget: int = -1) -> Tuple[str, str, str, Dict[str, Any]]:
        """Translate using OpenAI-compatible API"""
        
        # Build the prompt
        system_prompt = (
            f"You are a master linguist and loremaster specializing in video game localization. "
            f"Your task is to translate LORE keywords from {source_lang} into {target_lang}. "
            f"The translation MUST be concise, accurate, and function effectively as a search key or in-game display term. "
            f"Translate ONLY the text provided. Do NOT include explanations or commentary. "
            f"If the text is already in {target_lang}, return it unchanged."
        )
        
        user_prompt = f"Text to translate:\n{text}"
        
        if context:
            user_prompt = f"Context (for reference only - DO NOT translate this):\n{context}\n\n{user_prompt}"
        
        # Prepare the request
        url = f"{self.base_url}/chat/completions"
        headers = self.headers.copy()
        
        if api_key and self.auth_type == 'api_key':
            headers['Authorization'] = f"Bearer {api_key}"
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.default_params.get('temperature', 0.7),
            "max_tokens": self.default_params.get('max_tokens', 4096)
        }
        
        # Make the API call
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response
            translation = ""
            thinking_text = ""  # OpenAI doesn't have thinking mode
            usage_metadata = {}
            
            if 'choices' in data and data['choices']:
                translation = data['choices'][0]['message']['content'].strip()
            
            if 'usage' in data:
                usage_metadata = {
                    'prompt_tokens': data['usage'].get('prompt_tokens', 0),
                    'completion_tokens': data['usage'].get('completion_tokens', 0),
                    'total_tokens': data['usage'].get('total_tokens', 0),
                    'thinking_tokens': 0
                }
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            return full_prompt, translation, thinking_text, usage_metadata
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Handle rate limiting
                raise ResourceExhausted(str(e))
            raise
        except Exception as e:
            logger.error(f"OpenAI translation error: {e}")
            raise


class ProviderFactory:
    """Factory class to create appropriate provider instances"""
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> TranslationProvider:
        """Create a provider instance based on the config type"""
        provider_type = config.get('type', '').lower()
        
        if provider_type == 'gemini':
            return GeminiProvider(config)
        elif provider_type == 'openai':
            return OpenAIProvider(config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def load_endpoints_config(config_path: str = "endpoints_config.json") -> Dict[str, Any]:
        """Load endpoints configuration from file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading endpoints config: {e}")
            # Return default config if file doesn't exist
            return {
                "endpoints": {
                    "gemini": {
                        "name": "Google Gemini",
                        "type": "gemini",
                        "models": ["gemini-2.5-flash-lite-preview-06-17"]
                    }
                },
                "active_endpoint": "gemini"
            }
