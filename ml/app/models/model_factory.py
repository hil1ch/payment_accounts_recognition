"""Простая фабрика для создания моделей OCR и LLM по строковому типу."""

from models.base.ocr_model import OCRModel
from models.base.llm_model import LLMModel
from models.ocr.mock_ocr_model import MockOCRModel
from models.ocr.light_on_ocr_model import LightOnOCRModel
from models.llm.ollama_model import OllamaModel
from models.llm.mock_llm_model import MockLLMModel


def create_ocr_model(model_type: str, **kwargs) -> OCRModel:
    """Создает модель OCR по типу.

    Args:
        model_type: Тип модели ("easyocr", "lightonocr", "mock")
        **kwargs: Параметры для инициализации модели

    Returns:
        OCRModel: Экземпляр модели OCR

    Raises:
        ValueError: Если передан неизвестный тип модели
    """

    if model_type == "lightonocr":
        base_url = kwargs.get("base_url", "http://localhost:8001")
        model_name = kwargs.get("model_name", "lightonai/LightOnOCR-1B-1025")
        return LightOnOCRModel(base_url=base_url, model_name=model_name)

    elif model_type == "mock":
        mock_text = kwargs.get("mock_text", "Sample OCR Text\nLine 2\nLine 3")
        return MockOCRModel(mock_text=mock_text)

    else:
        raise ValueError(f"Unknown OCR model type: {model_type}. Available: easyocr, lightonocr, mock")


def create_llm_model(model_type: str, **kwargs) -> LLMModel:
    """Создает модель LLM по типу.

    Args:
        model_type: Тип модели ("ollama", "mock")
        **kwargs: Параметры для инициализации модели

    Returns:
        LLMModel: Экземпляр модели LLM

    Raises:
        ValueError: Если передан неизвестный тип модели
    """
    if model_type == "ollama":
        base_url = kwargs.get("base_url")
        model_name = kwargs.get("model_name", "gemma3:4b-it-qat")
        if not base_url:
            raise ValueError("base_url is required for ollama model")
        return OllamaModel(base_url=base_url, model_name=model_name)

    elif model_type == "mock":
        mock_response = kwargs.get("mock_response", '{"result": "mock", "data": {"field1": "value1"}}')
        return MockLLMModel(mock_response=mock_response)

    else:
        raise ValueError(f"Unknown LLM model type: {model_type}. Available: ollama, mock")