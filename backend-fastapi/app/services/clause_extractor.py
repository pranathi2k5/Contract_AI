import re
from app.ml.legalbert_model import legalbert_model

class ClauseExtractor:
    @staticmethod
    def extract_clauses(text: str):
        # A simple regex based splitting for paragraphs as clauses
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 20]
        results = []
        for i, para in enumerate(paragraphs):
            cls_result = legalbert_model.classify_clause(para)
            results.append({
                "clause_text": para,
                "clause_type": cls_result["label"],
                "confidence": cls_result["confidence"],
                "section_number": str(i+1)
            })
        return results

clause_extractor = ClauseExtractor()
