from azure.identity import DefaultAzureCredential, ClientAuthenticationError
from openai import AzureOpenAI, APIConnectionError, APITimeoutError
from lasource.domain.provider import AbstractProvider
from lasource.domain.exceptions import (
    LaSourceConfigError,
    LaSourceProviderError,
    LaSourceHealthCheckError,
    LaSourceValidationError
)
import logging
import os

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(AbstractProvider):
    """
    Azure OpenAI provider implementation.
    
    Handles authentication via Azure Managed Identity and communicates
    with Azure OpenAI through Private Endpoints for secure, compliant access.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            model_name: The model to use (e.g., 'gpt-4o', 'gpt-35-turbo').
                       Defaults to environment variable or 'gpt-4o'.
                       
        Raises:
            LaSourceConfigError: If AZURE_OPENAI_ENDPOINT is not set.
            LaSourceProviderError: If Azure authentication fails.
        """
        try:
            self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
            if not self.endpoint:
                raise LaSourceConfigError(
                    "AZURE_OPENAI_ENDPOINT environment variable is required. "
                    "Please set it to your Azure OpenAI endpoint URL."
                )
            
            # DefaultAzureCredential supports Managed Identity, environment variables, and local development
            try:
                self.credential = DefaultAzureCredential()
                logger.info("Azure credentials initialized successfully")
            except ClientAuthenticationError as e:
                raise LaSourceProviderError(
                    f"Failed to authenticate with Azure: {str(e)}. "
                    "Ensure Managed Identity is configured or Azure CLI is authenticated.",
                    provider_name="azure-openai"
                )
            
            # Create Azure OpenAI client targeting Private Endpoint securely
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                azure_ad_token_provider=self._get_token,
                api_version="2024-02-15-preview"
            )
            self.model_name = model_name or os.getenv("LA_SOURCE_MODEL", "gpt-4o")
            logger.info(f"Azure OpenAI provider initialized with model: {self.model_name}")
            
        except LaSourceConfigError:
            raise
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI provider: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Failed to initialize Azure OpenAI provider: {str(e)}",
                provider_name="azure-openai"
            )

    def _get_token(self):
        """
        Retrieves Azure authentication token for API calls.
        
        Returns:
            str: Valid Azure authentication token.
            
        Raises:
            LaSourceProviderError: If token retrieval fails.
        """
        try:
            token_info = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            return token_info.token
        except ClientAuthenticationError as e:
            logger.error(f"Failed to get Azure token: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Failed to retrieve Azure authentication token: {str(e)}",
                provider_name="azure-openai"
            )

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from Azure OpenAI.
        
        Args:
            prompt: The user prompt to send to the model.
            
        Returns:
            str: The generated response from the model.
            
        Raises:
            LaSourceProviderError: If API call fails.
        """
        if not prompt or not prompt.strip():
            raise LaSourceValidationError("Prompt cannot be empty")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            logger.debug(f"Calling Azure OpenAI with model {self.model_name}")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise LaSourceProviderError(
                    "Received empty response from Azure OpenAI",
                    provider_name="azure-openai"
                )
            
            return response.choices[0].message.content
            
        except APIConnectionError as e:
            logger.error(f"Connection error with Azure OpenAI: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Failed to connect to Azure OpenAI: {str(e)}",
                provider_name="azure-openai"
            )
        except APITimeoutError as e:
            logger.error(f"Timeout calling Azure OpenAI: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Azure OpenAI request timed out: {str(e)}",
                provider_name="azure-openai"
            )
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {str(e)}", exc_info=True)
            raise LaSourceProviderError(
                f"Error calling Azure OpenAI: {str(e)}",
                provider_name="azure-openai"
            )

    def health_check(self) -> bool:
        """
        Verify Azure OpenAI provider is reachable and responsive.
        
        Returns:
            bool: True if provider is healthy.
            
        Raises:
            LaSourceHealthCheckError: If health check fails.
        """
        try:
            # Simple test call to verify connectivity
            messages = [{"role": "user", "content": "Health check"}]
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=5
            )
            logger.info("Azure OpenAI health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Azure OpenAI health check failed: {str(e)}", exc_info=True)
            raise LaSourceHealthCheckError(
                f"Azure OpenAI health check failed: {str(e)}",
                provider_name="azure-openai"
            )
