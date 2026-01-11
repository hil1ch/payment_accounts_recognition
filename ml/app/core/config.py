# OCR_TYPE=easyocr
# OCR_LANGUAGES=["en", "ru"]
# OCR_GPU=false
# OCR_MODEL_STORAGE_DIRECTORY=/models/easyocr
# 
# OCR_TYPE=lightonocr
# LIGHTONAI_HOST=http://localhost
# LIGHTONAI_PORT=8001

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str 
    rabbit_url: str 
    queue_name: str 
    routing_key: str 
    shared_dir: str
    redis_host: str 
    redis_port: int
    redis_password: str
    ollama_host: str
    max_generation_time: int = 200
    redis_expire_seconds: int 


    # Типы моделей: "easyocr", "lightonocr" или "mock" для OCR, "ollama" или "mock" для LLM
    ocr_model_type: str = "easyocr"
    llm_model_type: str = "ollama"
    
    # Параметры для OCR (опционально)
    # Параметры для easyocr
    ocr_languages: str | None = None  # = "en,ru"  # Список языков через запятую
    ocr_gpu: bool | None = None # = False
    
    # Параметры для lightonocr (API к vLLM серверу)
    lightonai_host: str = "http://localhost"  # URL хоста (например, http://lightonai или http://localhost)
    lightonai_port: int = 8001  # Порт vLLM сервера
    lightonai_model_name: str = "lightonai/LightOnOCR-1B-1025"  # Имя модели
    lightonai_api_key: str | None = None  # Опциональный API ключ
    
    # Параметры для LLM (опционально, используются только для ollama)
    ollama_model_name: str | None = None # = "gemma3:4b-it-qat"
    
    @property
    def lightonai_base_url(self) -> str:
        """Формирует полный URL для lightonai сервера."""
        return f"{self.lightonai_host}:{self.lightonai_port}".replace("::8001", ":8001")  # Защита от http://localhost::8001
    
    model_config = SettingsConfigDict(env_file = ".env")

settings = Settings()
