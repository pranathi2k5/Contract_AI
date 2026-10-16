import logging
from threading import Lock

from app.config import settings

logger = logging.getLogger(__name__)


class SBERTModelUnavailableError(RuntimeError):
    """Raised when semantic scoring cannot run because SBERT is unavailable."""


class SBERTModel:
    """Lazy-loaded lightweight sentence transformer (all-MiniLM-L6-v2 by default)."""

    def __init__(self):
        self._model = None
        self._load_failed = False
        self._load_error = None
        self._embedding_cache = {}
        self._cache_lock = Lock()

    def _get_model(self):
        if self._model is not None or self._load_failed:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.SBERT_MODEL, device="cpu")
        except Exception as exc:
            logger.warning("SBERT model could not be loaded (%s): %s", settings.SBERT_MODEL, exc)
            self._load_failed = True
            self._load_error = exc
            self._model = None
        return self._model

    def semantic_scores(self, texts, concepts):
        if not texts or not concepts:
            return []

        model = self._get_model()
        if model is None:
            raise SBERTModelUnavailableError(
                f"SBERT model {settings.SBERT_MODEL!r} is unavailable; risk scoring cannot continue."
            ) from self._load_error

        from sentence_transformers import util

        cache_key = tuple(concepts)
        with self._cache_lock:
            concept_embeddings = self._embedding_cache.get(cache_key)
            if concept_embeddings is None:
                concept_embeddings = model.encode(
                    concepts,
                    batch_size=32,
                    convert_to_tensor=True,
                    show_progress_bar=False,
                )
                self._embedding_cache[cache_key] = concept_embeddings

        text_embeddings = model.encode(
            texts,
            batch_size=32,
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        similarities = util.cos_sim(text_embeddings, concept_embeddings)
        return similarities.cpu().tolist()

    def encode(self, texts):
        model = self._get_model()
        if model is None:
            return None
        return model.encode(texts, convert_to_tensor=True)

    def compute_similarity(self, text1: str, text2: str):
        from sentence_transformers import util
        emb1 = self.encode([text1])
        emb2 = self.encode([text2])
        if emb1 is None or emb2 is None:
            return self._lexical_score(text1, text2)
        return util.cos_sim(emb1, emb2).item()

    def find_similar(self, query: str, candidates: list, threshold: float = 0.65):
        if not candidates:
            return []

        model = self._get_model()
        if model is None:
            return self._lexical_matches(query, candidates, threshold)

        from sentence_transformers import util
        query_emb = model.encode([query], convert_to_tensor=True)
        candidate_embs = model.encode(candidates, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, candidate_embs)[0]

        results = []
        for i, score in enumerate(scores):
            if score >= threshold:
                results.append({"text": candidates[i], "score": score.item()})
        return sorted(results, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _tokenize(text: str):
        return set(word for word in text.lower().split() if len(word) > 2)

    def _lexical_score(self, text1: str, text2: str) -> float:
        a = self._tokenize(text1)
        b = self._tokenize(text2)
        if not a or not b:
            return 0.0
        return len(a & b) / max(1, len(a | b))

    def _lexical_matches(self, query: str, candidates: list, threshold: float):
        results = []
        for candidate in candidates:
            score = self._lexical_score(query, candidate)
            if score >= min(threshold, 0.25):
                results.append({"text": candidate, "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)


sbert_model = SBERTModel()
