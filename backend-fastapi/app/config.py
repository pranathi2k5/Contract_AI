import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/contractai")
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    # Lightweight sentence-transformer used for embeddings, RAG, similarity, and risk scoring.
    SBERT_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # LegalBERT is optional and is not loaded unless explicitly enabled.
    ENABLE_LEGALBERT: bool = False
    LEGALBERT_MODEL: str = "nlpaueb/legal-bert-base-uncased"
    INDIAN_LAWS_PATH: str = "knowledge_base/indian_laws.json"
    STANDARD_CLAUSES_PATH: str = "knowledge_base/standard_clauses.json"
    RISK_KEYWORDS_PATH: str = "knowledge_base/risk_keywords.json"
    RISK_PATTERNS_PATH: str = "knowledge_base/risk_patterns.json"

    class Config:
        env_file = ".env"


settings = Settings()
