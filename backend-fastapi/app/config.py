import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/contractai")
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LEGALBERT_MODEL: str = "nlpaueb/legal-bert-base-uncased"
    SBERT_MODEL: str = "all-MiniLM-L6-v2"
    INDIAN_LAWS_PATH: str = "knowledge_base/indian_laws.json"
    STANDARD_CLAUSES_PATH: str = "knowledge_base/standard_clauses.json"
    RISK_KEYWORDS_PATH: str = "knowledge_base/risk_keywords.json"

    class Config:
        env_file = ".env"

settings = Settings()
