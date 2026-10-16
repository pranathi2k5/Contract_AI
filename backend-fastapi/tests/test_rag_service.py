from app.services.rag_service import LEGAL_DISCLAIMER, RAGService
from app.config import settings


SOURCE = {
    "act_name": "Verified Act title",
    "url": "https://www.indiacode.nic.in/verified-act.pdf",
    "version": "As published",
    "effective_date": "2024-01-01",
}
LAW_TEXT = (
    "1. Formation of agreements.—Agreements made with free consent and lawful "
    "consideration are contracts.\n"
    "2. Compensation for breach.—A party suffering loss from breach may seek "
    "compensation for that loss.\n"
)


class FakeCollection:
    def __init__(self):
        self.records = {}
        self.distance = 0.1
        self.metadata = {"embedding_model": settings.SBERT_MODEL}

    def count(self):
        return len(self.records)

    def upsert(self, ids, documents, metadatas, embeddings):
        for identifier, document, metadata, embedding in zip(
            ids, documents, metadatas, embeddings
        ):
            self.records[identifier] = {
                "document": document,
                "metadata": metadata,
                "embedding": embedding,
            }

    def get(self, where, include):
        return {
            "ids": [
                identifier for identifier, record in self.records.items()
                if record["metadata"]["source_url"] == where["source_url"]
            ]
        }

    def delete(self, ids):
        for identifier in ids:
            self.records.pop(identifier, None)

    def query(self, query_embeddings, n_results, include):
        records = list(self.records.values())[:n_results]
        return {
            "documents": [[record["document"] for record in records]],
            "metadatas": [[record["metadata"] for record in records]],
            "distances": [[self.distance for _ in records]],
        }


def make_service():
    service = RAGService()
    service._collection = FakeCollection()
    service._embeddings = lambda texts: [[0.1, 0.2] for _ in texts]
    return service


def test_empty_legal_corpus_reports_empty_not_fake_matches():
    service = make_service()

    result = service.query("indemnity and limitation of liability")

    assert service.status() == {"status": "empty", "sections": 0}
    assert result["status"] == "empty"
    assert result["matches"] == []
    assert result["disclaimer"] == LEGAL_DISCLAIMER


def test_ingestion_chunks_sections_and_is_repeatable():
    service = make_service()

    first_count = service.index_document(LAW_TEXT, SOURCE)
    first_ids = set(service._collection.records)
    second_count = service.index_document(LAW_TEXT, SOURCE)

    assert first_count == second_count == 2
    assert set(service._collection.records) == first_ids
    section = next(iter(service._collection.records.values()))
    assert section["metadata"]["act_name"] == SOURCE["act_name"]
    assert section["metadata"]["section_number"] == "1"
    assert section["metadata"]["source_url"] == SOURCE["url"]
    assert section["metadata"]["version"] == SOURCE["version"]
    assert section["metadata"]["effective_date"] == SOURCE["effective_date"]
    assert section["embedding"] == [0.1, 0.2]


def test_relevant_retrieval_returns_verified_citation_and_section_text():
    service = make_service()
    service.index_document(LAW_TEXT, SOURCE)

    result = service.query("agreements made with free consent")

    assert result["status"] == "ready"
    assert result["matches"][0]["act_name"] == SOURCE["act_name"]
    assert result["matches"][0]["section_number"] == "1"
    assert result["matches"][0]["source_url"] == SOURCE["url"]
    assert "free consent" in result["matches"][0]["retrieved_text"]
    assert result["matches"][0]["explanation_source"] == "retrieval"


def test_irrelevant_retrieval_is_rejected_by_relevance_threshold():
    service = make_service()
    service.index_document(LAW_TEXT, SOURCE)
    service._collection.distance = 0.8

    result = service.query("weather forecast and cricket score")

    assert result["status"] == "no_relevant_match"
    assert result["matches"] == []


def test_unreachable_chroma_corpus_reports_unavailable(monkeypatch):
    service = RAGService()
    monkeypatch.setattr(settings, "CHROMA_HOST", "unreachable-chroma")

    def connection_failure():
        raise ConnectionError("unavailable")

    monkeypatch.setattr(service, "_get_collection", connection_failure)

    assert service.status()["status"] == "unavailable"
    assert service.query("contract obligations")["status"] == "unavailable"


def test_non_official_or_non_https_source_is_rejected():
    service = make_service()

    try:
        service.index_document(LAW_TEXT, {**SOURCE, "url": "https://example.org/act.pdf"})
    except ValueError as exc:
        assert "indiacode.nic.in" in str(exc)
    else:
        raise AssertionError("The ingestion pipeline accepted a non-official source.")
