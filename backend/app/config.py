from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://leaf:leaf@localhost:5432/leaf"
    model_dir: str = "./model_cache"
    max_file_size: int = 10 * 1024 * 1024
    allowed_extensions: str = "jpg,jpeg,png,webp"
    default_lang: str = "vi"

    class Config:
        env_file = ".env"


settings = Settings()
