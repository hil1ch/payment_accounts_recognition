# OCR_TYPE=easyocr
# OCR_LANGUAGES=["en", "ru"]
# OCR_GPU=false
# OCR_MODEL_STORAGE_DIRECTORY=/models/easyocr



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


    # Типы моделей: "easyocr" или "mock" для OCR, "ollama" или "mock" для LLM
    ocr_model_type: str = "easyocr"
    llm_model_type: str = "ollama"
    
    # Параметры для OCR (опционально, используются только для easyocr)
    ocr_languages: str | None = None  # = "en,ru"  # Список языков через запятую
    ocr_gpu: bool | None = None # = False
    
    # Параметры для LLM (опционально, используются только для ollama)
    ollama_model_name: str | None = None # = "gemma3:4b-it-qat"
    model_config = SettingsConfigDict(env_file = ".env")

settings = Settings()
