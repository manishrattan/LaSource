from lasource.domain.provider import AbstractProvider

class AnthropicProvider(AbstractProvider):
    def __init__(self):
        # Stub for future implementation
        pass

    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Anthropic provider is not yet implemented.")
