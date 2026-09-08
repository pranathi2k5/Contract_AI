from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

def get_huggingface_embeddings():
    return HuggingFaceEmbeddings(model_name=settings.SBERT_MODEL)
