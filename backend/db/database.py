from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:Tan%40775873@localhost:5432/energy_optimization"
    app_name: str = "AI-Powered Energy Consumption Optimization & Cost Reduction System"
    reports_dir: str = "../reports"
    dataset_dir: str = "../dataset"
    models_dir: str = "./models"
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = (BASE_DIR / settings.reports_dir).resolve()
DATASET_DIR = (BASE_DIR / settings.dataset_dir).resolve()
MODELS_DIR = (BASE_DIR / settings.models_dir).resolve()

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
