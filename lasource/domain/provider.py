from abc import ABC, abstractmethod

class AbstractProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generates a response from the AI model based on the prompt."""
        pass
