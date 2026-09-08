import json
from app.config import settings
from app.ml.sbert_model import sbert_model

class LawMapper:
    def __init__(self):
        self.laws = []
        try:
            with open(settings.INDIAN_LAWS_PATH, 'r') as f:
                self.laws = json.load(f)
        except Exception as e:
            print("Could not load Indian laws:", e)

    def map_laws(self, clauses: list):
        mapped = []
        if not self.laws:
            return mapped
            
        law_texts = [f"{l['act_name']} - {l['section_title']}: {l['description']}" for l in self.laws]
        
        for c in clauses:
            matches = sbert_model.find_similar(c["clause_text"], law_texts, threshold=0.60)
            if matches:
                top_match_text = matches[0]["text"]
                # Find corresponding law
                law = next((l for l in self.laws if f"{l['act_name']} - {l['section_title']}: {l['description']}" == top_match_text), None)
                if law:
                    mapped.append({
                        "clause_text": c["clause_text"],
                        "law_name": law["act_name"],
                        "act_name": law["act_name"],
                        "section_number": law["section_number"],
                        "section_title": law["section_title"],
                        "relevance_score": matches[0]["score"] * 100,
                        "reason": f"The clause relates to {law['section_title']}, making the manner of operation legally relevant.",
                        "source": "indian_laws.json"
                    })
        return mapped

law_mapper = LawMapper()
