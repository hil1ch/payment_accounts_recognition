import time
from models.base.llm_model import LLMModel


class MockLLMModel(LLMModel):
    """Моковая модель LLM для разработки. Возвращает фиксированный JSON."""
    
    def __init__(self, mock_response: str = '{"result": "mock", "data": {"field1": "value1"}}'):
        """Initialize mock LLM model.
        
        Args:
            mock_response: JSON строка, которая будет возвращаться. 
                          По умолчанию возвращает простой пример JSON.
        """
        self.mock_response = mock_response
    
    def generate(self, prompt: str) -> dict:
        """Возвращает фиксированный ответ вместо реального LLM."""
        # Имитируем небольшую задержку для реалистичности
        time.sleep(0.1)
        
        return {
            "result_text": self.mock_response,
            "generated_time": 0.1,
        }
