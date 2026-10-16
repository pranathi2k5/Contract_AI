import json
from app.config import settings
from app.ml.sbert_model import sbert_model

class MissingClauseDetector:
    def __init__(self):
        self.templates = []
        try:
            with open(settings.STANDARD_CLAUSES_PATH, 'r') as f:
                self.templates = json.load(f)
        except Exception as e:
            print("Could not load standard clauses:", e)

    def detect(self, extracted_clauses: list, contract_type: str):
        if not self.templates:
            return []
            
        wanted = (contract_type or "").strip().lower()
        wanted = {
            "nda": "nda",
            "employee": "employment",
            "employment": "employment",
            "sla": "service",
            "service": "service",
            "sales": "sales",
            "vendor": "sales",
            "rental": "lease",
            "rental/lease": "lease",
            "lease": "lease",
        }.get(wanted, wanted)
        contract_templates = [
            t for t in self.templates
            if str(t.get("contract_type", "")).strip().lower() == wanted
        ]
        extracted_texts = [c["clause_text"] for c in extracted_clauses]

        missing = []
        for t in contract_templates:
            matches = sbert_model.find_similar(t["template_text"], extracted_texts, threshold=0.65) if extracted_texts else []
            if not matches:
                missing.append({
                    "clause_name": t["clause_name"],
                    "importance": t["importance"],
                    "description": t["description"],
                    "template_text": t["template_text"],
                    "max_similarity_score": 0.0
                })
            else:
                max_score = matches[0]["score"]
                if max_score < 0.65:
                    missing.append({
                        "clause_name": t["clause_name"],
                        "importance": t["importance"],
                        "description": t["description"],
                        "template_text": t["template_text"],
                        "max_similarity_score": max_score
                    })
                    
        return missing

missing_clause_detector = MissingClauseDetector()
