from sentence_transformers import SentenceTransformer, util
from app.config import settings

class SBERTModel:
    def __init__(self):
        self.model = SentenceTransformer(settings.SBERT_MODEL)
        
    def encode(self, texts):
        return self.model.encode(texts, convert_to_tensor=True)
        
    def compute_similarity(self, text1: str, text2: str):
        emb1 = self.encode([text1])
        emb2 = self.encode([text2])
        return util.cos_sim(emb1, emb2).item()
        
    def find_similar(self, query: str, candidates: list, threshold: float = 0.65):
        query_emb = self.encode([query])
        candidate_embs = self.encode(candidates)
        scores = util.cos_sim(query_emb, candidate_embs)[0]
        
        results = []
        for i, score in enumerate(scores):
            if score >= threshold:
                results.append({"text": candidates[i], "score": score.item()})
        return sorted(results, key=lambda x: x["score"], reverse=True)

sbert_model = SBERTModel()
