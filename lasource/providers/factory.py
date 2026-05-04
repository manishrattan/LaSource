from lasource.domain.provider import AbstractProvider
from lasource.providers.azure_openai import AzureOpenAIProvider
from lasource.providers.anthropic_provider import AnthropicProvider
from lasource.config import settings

class ProviderFactory:
    @staticmethod
    def get_provider() -> AbstractProvider:
        provider_name = settings.la_source_provider.lower()
        
        if provider_name == "azure-openai":
            # Switch between gpt-4o, o1-preview, etc.
            model_name = settings.la_source_model
            return AzureOpenAIProvider(model_name=model_name)
            
        elif provider_name == "anthropic":
            return AnthropicProvider()
            
        elif provider_name == "gemini":
            raise NotImplementedError("Gemini provider is not yet implemented.")
            
        raise ValueError(f"Unknown provider: {provider_name}")
