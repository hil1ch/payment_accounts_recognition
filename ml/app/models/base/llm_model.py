from abc import ABC, abstractmethod

class LLMModel(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> dict:
        """Generate text based on the given prompt.

        Args:
            prompt (str): The input prompt for text generation.

        Returns:
            dict: A dictionary containing the generated text and any relevant metadata.
        """
        pass