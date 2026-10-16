from app.config import settings

_embeddings = None


def get_huggingface_embeddings():
    """Lazy MiniLM embeddings for RAG; not created until first use."""
    global _embeddings
    if _embeddings is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(model_name=settings.SBERT_MODEL)
    return _embeddings
