from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from lasource.domain.provider import AbstractProvider
from lasource.config import settings
import logging

logger = logging.getLogger(__name__)

class AzureOpenAIProvider(AbstractProvider):
    def __init__(self, model_name: str = None):
        self.endpoint = settings.azure_openai_endpoint
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
            
        # DefaultAzureCredential supports Managed Identity dynamically
        self.credential = DefaultAzureCredential()
        
        # Targets Private Endpoint securely
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            azure_ad_token_provider=self._get_token,
            api_version="2024-02-15-preview"
        )
        self.model_name = model_name or settings.la_source_model

    def _get_token(self):
        token_info = self.credential.get_token("https://cognitiveservices.azure.com/.default")
        return token_info.token

    def generate_response(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        # Accommodates both 'gpt-4o' and 'o-series' models
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            raise
