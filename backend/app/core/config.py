from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str 
    rabbit_url: str 
    exchange_name: str 
    queue_name: str 
    routing_key: str 
    shared_dir: str

    model_config = SettingsConfigDict(env_file = ".env")

settings = Settings()
