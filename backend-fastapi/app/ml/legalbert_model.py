import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from app.config import settings

class LegalBERTModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(settings.LEGALBERT_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(settings.LEGALBERT_MODEL).to(self.device)
        self.pipeline = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer, device=0 if self.device=="cuda" else -1)
        
    def classify_clause(self, text: str):
        result = self.pipeline(text[:512], truncation=True, max_length=512)[0]
        return {"label": result["label"], "confidence": result["score"]}
        
    def extract_clauses(self, full_text: str):
        # Dummy sliding window implementation
        return [{"clause_text": full_text[:100], "clause_type": "Unknown", "confidence": 0.5}]

legalbert_model = LegalBERTModel()
