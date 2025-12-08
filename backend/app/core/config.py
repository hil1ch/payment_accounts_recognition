from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str 
    rabbit_url: str 
    exchange_name: str 
    queue_name: str 
    routing_key: str 
    shared_dir: str
    redis_host: str 
    redis_port: int
    redis_password: str

    model_config = SettingsConfigDict(env_file = ".env")

settings = Settings()
