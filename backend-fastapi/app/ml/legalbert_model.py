from app.config import settings


class LegalBERTModel:
    def __init__(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(settings.LEGALBERT_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(settings.LEGALBERT_MODEL).to(self.device)
        self.pipeline = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1,
        )

    def classify_clause(self, text: str):
        result = self.pipeline(text[:512], truncation=True, max_length=512)[0]
        return {"label": result["label"], "confidence": result["score"]}

    def extract_clauses(self, full_text: str):
        return [{"clause_text": full_text[:100], "clause_type": "Unknown", "confidence": 0.5}]


_legalbert_model = None


def get_legalbert_model():
    """Load LegalBERT only when ENABLE_LEGALBERT is true. Returns None otherwise."""
    global _legalbert_model
    if not settings.ENABLE_LEGALBERT:
        return None
    if _legalbert_model is None:
        _legalbert_model = LegalBERTModel()
    return _legalbert_model


class _LazyLegalBERT:
    def _resolved(self):
        model = get_legalbert_model()
        if model is None:
            raise RuntimeError(
                "LegalBERT is disabled. Set ENABLE_LEGALBERT=true to load it."
            )
        return model

    def __getattr__(self, name):
        return getattr(self._resolved(), name)


# Backward-compatible handle; does not load the model at import time.
import os

LEGALBERT_ENABLED = os.getenv("LEGALBERT_ENABLED", "false").lower() == "true"

legalbert_model = None

if LEGALBERT_ENABLED:
    legalbert_model = LegalBERTModel()
