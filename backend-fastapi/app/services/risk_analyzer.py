import json
from app.config import settings
from app.ml.sbert_model import sbert_model

class RiskAnalyzer:
    def __init__(self):
        self.risk_keywords = {}
        try:
            with open(settings.RISK_KEYWORDS_PATH, 'r') as f:
                self.risk_keywords = json.load(f)
        except:
            self.risk_keywords = {
                "unlimited liability": {"category": "FINANCIAL", "severity": "CRITICAL"},
                "irrevocable": {"category": "LEGAL", "severity": "HIGH"},
                "waive all rights": {"category": "LEGAL", "severity": "CRITICAL"}
            }

    def analyze(self, clauses):
        risk_clauses = []
        total_score = 0
        
        for clause in clauses:
            text = clause["clause_text"].lower()
            keyword_score = 0
            category = "OPERATIONAL"
            severity = "LOW"
            
            for kw, meta in self.risk_keywords.items():
                if kw in text:
                    keyword_score += 0.4
                    category = meta["category"]
                    severity = meta["severity"]
                    
            confidence_score = (1.0 - clause["confidence"]) * 0.35
            
            # Simple simulation for SBERT risk templates
            sbert_score = 0.25 if keyword_score > 0 else 0
            
            combined = min(1.0, keyword_score + confidence_score + sbert_score)
            
            if combined > 0.4:
                risk_clauses.append({
                    "clause_text": clause["clause_text"],
                    "clause_type": clause["clause_type"],
                    "risk_score": combined * 100,
                    "risk_category": category,
                    "severity": severity,
                    "explanation": f"Detected risky terms or low confidence.",
                    "suggestion": "Consider reviewing and revising this clause."
                })
                total_score += combined * 100
                
        avg_score = total_score / max(1, len(clauses)) if total_score > 0 else 0
        risk_level = "LOW"
        if avg_score > 75:
            risk_level = "CRITICAL"
        elif avg_score > 50:
            risk_level = "HIGH"
        elif avg_score > 25:
            risk_level = "MEDIUM"
            
        return {
            "overall_risk_score": avg_score,
            "risk_level": risk_level,
            "risk_clauses": risk_clauses
        }

risk_analyzer = RiskAnalyzer()
