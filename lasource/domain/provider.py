from abc import ABC, abstractmethod
from lasource.domain.exceptions import LaSourceProviderError


class AbstractProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All provider implementations must inherit from this class and implement
    the generate_response and health_check methods.
    
    This follows the Clean Architecture pattern where the domain layer
    defines interfaces that are implementation-agnostic.
    """
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the AI model based on the prompt.
        
        Args:
            prompt: The input prompt for the AI model.
            
        Returns:
            str: The generated response from the AI model.
            
        Raises:
            LaSourceProviderError: If there's an issue calling the provider.
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Performs a health check to verify the provider is reachable and responsive.
        
        Returns:
            bool: True if provider is healthy, False otherwise.
            
        Raises:
            LaSourceProviderError: If health check fails critically.
        """
        pass
