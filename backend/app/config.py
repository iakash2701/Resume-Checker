import os
from pydantic_settings import BaseSettings

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DEFAULT_DB_PATH = os.path.join(_BACKEND_DIR, "hireswift.db").replace("\\", "/")

class Settings(BaseSettings):
    PROJECT_NAME: str = "HireSwift"
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))

    class Config:
        env_file = ".env"

settings = Settings()
