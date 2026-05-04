from abc import ABC, abstractmethod

class AbstractProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generates a response from the AI model based on the prompt."""
        pass
        
    @abstractmethod
    def health_check(self) -> bool:
        """Checks if the provider is healthy and reachable."""
        pass
