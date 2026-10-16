import re
from app.ml.legalbert_model import get_legalbert_model

CLAUSE_HINTS = [
    ("non-compete", "NON_COMPETE"),
    ("restraint of trade", "NON_COMPETE"),
    ("indemnif", "INDEMNITY"),
    ("hold harmless", "INDEMNITY"),
    ("confidential", "CONFIDENTIALITY"),
    ("non-disclosure", "CONFIDENTIALITY"),
    ("terminat", "TERMINATION"),
    ("notice period", "TERMINATION"),
    ("governing law", "GOVERNING_LAW"),
    ("jurisdiction", "DISPUTE_RESOLUTION"),
    ("arbitration", "DISPUTE_RESOLUTION"),
    ("intellectual property", "IP"),
    ("payment", "PAYMENT"),
    ("invoice", "PAYMENT"),
    ("deadline", "DEADLINE"),
    ("time is of the essence", "DEADLINE"),
    ("liability", "LIABILITY"),
    ("limitation of liability", "LIABILITY"),
    ("auto-renew", "RENEWAL"),
    ("automatic renewal", "RENEWAL"),
]


def classify_clause_heuristic(text: str):
    lowered = text.lower()
    for hint, label in CLAUSE_HINTS:
        if hint in lowered:
            return {"label": label, "confidence": 0.78}
    return {"label": "GENERAL", "confidence": 0.55}


class ClauseExtractor:
    @staticmethod
    def extract_clauses(text: str):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 20]
        if not paragraphs and text.strip():
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
            paragraphs = sentences or [text.strip()]

        legalbert = get_legalbert_model()
        results = []
        for i, para in enumerate(paragraphs):
            if legalbert is not None:
                cls_result = legalbert.classify_clause(para)
            else:
                cls_result = classify_clause_heuristic(para)
            results.append({
                "clause_text": para,
                "clause_type": cls_result["label"],
                "confidence": cls_result["confidence"],
                "section_number": str(i + 1),
            })
        return results


clause_extractor = ClauseExtractor()
