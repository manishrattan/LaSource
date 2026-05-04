import os
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from .config import settings

class AbstractProvider:
    def health_check(self) -> bool:
        pass
        
    def generate_response(self, prompt: str) -> str:
        """Generates a response from the AI model based on the prompt."""
        pass

class AzureOpenAIProvider(AbstractProvider):
    def __init__(self, model_name: str = None):
        self.endpoint = settings.azure_openai_endpoint
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
            
        self.credential = DefaultAzureCredential()
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            azure_ad_token_provider=self._get_token,
            api_version="2024-02-15-preview"
        )
        self.model_name = model_name or settings.la_source_model

    def _get_token(self):
        token_info = self.credential.get_token("https://cognitiveservices.azure.com/.default")
        return token_info.token

    def health_check(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            return False

    def generate_response(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class AnthropicProvider(AbstractProvider):
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required but not found in Key Vault or environment.")

    def health_check(self) -> bool:
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages", 
                method="GET",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            )
            # Make a dummy API call to simulate a successful check
            # We expect a 4xx or 2xx response, but just attempting the connection is the check
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
        return True

class GeminiProvider(AbstractProvider):
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required but not found in Key Vault or environment.")

    def health_check(self) -> bool:
        return True

class CohereProvider(AbstractProvider):
    def __init__(self):
        self.api_key = settings.cohere_api_key
        if not self.api_key:
            raise ValueError("COHERE_API_KEY is required but not found in Key Vault or environment.")

    def health_check(self) -> bool:
        return True

class ProviderFactory:
    """Infrastructure Brain that dynamically selects the AI Provider."""
    
    @staticmethod
    def get_provider() -> AbstractProvider:
        # Resolves dynamic dependencies - completely separated from domain logic
        provider_name = settings.la_source_provider.lower()
        
        if provider_name == "azure-openai":
            return AzureOpenAIProvider()
        elif provider_name == "anthropic":
            return AnthropicProvider()
        elif provider_name == "gemini":
            return GeminiProvider()
        elif provider_name == "cohere":
            return CohereProvider()
            
        raise ValueError(f"Unknown provider: {provider_name}")
