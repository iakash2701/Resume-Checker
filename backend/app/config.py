import os
from pydantic_settings import BaseSettings

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DEFAULT_DB_PATH = os.path.join(_BACKEND_DIR, "hireswift.db").replace("\\", "/")

# On Vercel serverless, SQLite DB file is read-only if placed in root unless copied to /tmp or read directly
_IS_VERCEL = "VERCEL" in os.environ
_VERCEL_DB = "/tmp/hireswift.db"

def _get_database_url():
    if _IS_VERCEL:
        import shutil
        if not os.path.exists(_VERCEL_DB):
            src_db = _DEFAULT_DB_PATH
            if not os.path.exists(src_db):
                src_db = os.path.abspath("backend/hireswift.db")
            if os.path.exists(src_db):
                try:
                    shutil.copyfile(src_db, _VERCEL_DB)
                except Exception:
                    pass
        return f"sqlite:///{_VERCEL_DB}"
    return f"sqlite:///{_DEFAULT_DB_PATH}"

class Settings(BaseSettings):
    PROJECT_NAME: str = "HireSwift"
    DATABASE_URL: str = _get_database_url()
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    UPLOAD_DIR: str = "/tmp/uploads" if _IS_VERCEL else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))

    class Config:
        env_file = ".env"

settings = Settings()
