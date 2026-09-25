from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return database_url


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/energy_optimization"
    app_name: str = "AI-Powered Energy Consumption Optimization & Cost Reduction System"
    reports_dir: str = "../reports"
    dataset_dir: str = "../dataset"
    models_dir: str = "./models"
    allowed_origins: str = "http://localhost:3000 || https://ai-powered-energy-optimization-cost-cetu.onrender.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
settings.database_url = normalize_database_url(settings.database_url)
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
