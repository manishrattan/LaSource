import os
from pydantic_settings import BaseSettings
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class Settings(BaseSettings):
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://default.openai.azure.com/")
    azure_ad_tenant_id: str = os.getenv("AZURE_AD_TENANT_ID", "default-tenant")
    la_source_provider: str = os.getenv("LA_SOURCE_PROVIDER", "azure-openai")
    la_source_model: str = os.getenv("LA_SOURCE_MODEL", "gpt-4o")
    key_vault_url: str | None = os.getenv("KEY_VAULT_URL")

    def get_secret(self, secret_name: str) -> str | None:
        """Securely fetch API keys from Azure Key Vault or fallback to local env."""
        if self.key_vault_url:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            return client.get_secret(secret_name).value
        return os.getenv(secret_name.upper().replace("-", "_"))

    @property
    def anthropic_api_key(self) -> str | None:
        return self.get_secret("ANTHROPIC_API_KEY")

    @property
    def gemini_api_key(self) -> str | None:
        return self.get_secret("GEMINI_API_KEY")

    @property
    def cohere_api_key(self) -> str | None:
        return self.get_secret("COHERE_API_KEY")

settings = Settings()
