# **`llm/ollama_model.py`:**
# - Класс `OllamaModel(LLMModel)` - обертка над Ollama
# - В `__init__` принимает URL Ollama, имя модели
# - Реализует `generate()` используя Ollama API

from ml.app.models.base.llm_model import LLMModel
import ollama
import time


class OllamaModel(LLMModel):
    def __init__(self, base_url: str, model_name: str):
        """Initialize the Ollama model with the given base URL and model name.
        
        Args:
            base_url (str): The base URL of the Ollama server.
            model_name (str): The name of the model to use for text generation.
        """
        self.base_url = base_url
        self.model_name = model_name

    def generate(self, prompt: str, options: dict = None, max_generation_time: int = 2000) -> dict:
        """Generate text based on the given prompt using Ollama API.

        Args:
            prompt (str): The input prompt for text generation.
            max_generation_time (int): Maximum time allowed for generation in seconds.
        Returns:
            dict: A dictionary containing the generated text and any relevant metadata.
        """
        response_stream = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options= options if options is not None else {"temperature": 0.1},
        )

        start_time = time.time()
        result = ""

        for chunk in response_stream:
            if "message" in chunk and "content" in chunk["message"]:
                result += chunk["message"]["content"]

            if time.time() - start_time > max_generation_time:
                break

        return {
            "result_text": result,
            "generated_time": time.time() - start_time,
        }

