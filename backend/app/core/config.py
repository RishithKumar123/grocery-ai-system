import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Grocery Inventory System API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "grocery_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    CACHE_TTL_SECONDS: int = 300
    RATE_LIMIT_PER_MINUTE: int = 120

    # JWT Config
    JWT_SECRET: str = "supersecretjwtkeyforgroceryinventorysystem"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Storage Config
    STORAGE_PROVIDER: str = "local"  # "local", "s3", "supabase"
    LOCAL_STORAGE_DIR: str = "/app/local_storage"

    # AWS Settings
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: str = ""

    # Supabase Settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = ""

    # AI Configurations (custom grocery model only — never generic COCO weights)
    YOLO_MODEL_PATH: str = ""
    YOLO_BASE_MODEL: str = "yolo11m.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    YOLO_IOU_THRESHOLD: float = 0.70
    ML_DATASET_ROOT: str = ""
    ML_RUNS_DIR: str = ""
    OCR_LANGUAGES: str = "en,hi"

    # CORS Origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings
settings = Settings()
