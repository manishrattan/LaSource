from lasource.domain.provider import AbstractProvider
from lasource.providers.azure_openai import AzureOpenAIProvider
from lasource.providers.anthropic_provider import AnthropicProvider
from lasource.domain.exceptions import LaSourceConfigError, LaSourceProviderError
import logging
import os

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory class for creating and managing AI provider instances.
    
    Uses the Factory design pattern to abstract provider instantiation.
    Supports dynamic provider switching via LA_SOURCE_PROVIDER environment variable.
    """
    
    SUPPORTED_PROVIDERS = {
        "azure-openai": AzureOpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    
    @staticmethod
    def get_provider() -> AbstractProvider:
        """
        Factory method to retrieve the configured AI provider.
        
        Environment Variables:
            LA_SOURCE_PROVIDER: The provider to use (azure-openai, anthropic).
            LA_SOURCE_MODEL: The model name within the provider.
            
        Returns:
            AbstractProvider: An instance of the configured provider.
            
        Raises:
            LaSourceConfigError: If provider name is not set or invalid.
            LaSourceProviderError: If provider instantiation fails.
        """
        try:
            provider_name = os.getenv("LA_SOURCE_PROVIDER", "").lower().strip()
            
            if not provider_name:
                raise LaSourceConfigError(
                    "LA_SOURCE_PROVIDER environment variable is not set. "
                    f"Supported providers: {', '.join(ProviderFactory.SUPPORTED_PROVIDERS.keys())}"
                )
            
            if provider_name not in ProviderFactory.SUPPORTED_PROVIDERS:
                raise LaSourceConfigError(
                    f"Unknown provider: '{provider_name}'. "
                    f"Supported providers: {', '.join(ProviderFactory.SUPPORTED_PROVIDERS.keys())}"
                )
            
            provider_class = ProviderFactory.SUPPORTED_PROVIDERS[provider_name]
            logger.info(f"Instantiating provider: {provider_name}")
            
            if provider_name == "azure-openai":
                model_name = os.getenv("LA_SOURCE_MODEL", "gpt-4o")
                return provider_class(model_name=model_name)
            else:
                return provider_class()
                
        except LaSourceConfigError:
            raise
        except Exception as e:
            logger.error(f"Failed to instantiate provider: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Failed to instantiate provider: {str(e)}",
                provider_name=provider_name if 'provider_name' in locals() else "unknown"
            )
