import argparse
import hashlib
import json
import logging
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

from app.config import settings
from app.ml.sbert_model import SBERTModelUnavailableError, sbert_model

logger = logging.getLogger(__name__)

COLLECTION_NAME = "india_code_sections_v1"
RELEVANCE_THRESHOLD = 0.45
LEGAL_DISCLAIMER = (
    "Legal information only; not legal advice. Retrieved statutory text and semantic "
    "similarity do not determine whether a law applies to a particular contract."
)
INDIA_CODE_HOSTS = {"indiacode.nic.in", "www.indiacode.nic.in"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1
        elif tag in {"p", "div", "br", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._hidden_depth:
            self.parts.append(data)


class RAGService:
    def __init__(self):
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        import chromadb

        if settings.CHROMA_HOST.strip():
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST.strip(),
                port=settings.CHROMA_PORT,
            )
        else:
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY
            )
        collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": settings.SBERT_MODEL,
            },
        )
        stored_model = (collection.metadata or {}).get("embedding_model")
        if stored_model != settings.SBERT_MODEL:
            raise RuntimeError(
                "The legal corpus embedding model does not match SBERT_MODEL; "
                "rebuild the legal corpus with the configured model."
            )
        self._collection = collection
        return collection

    @staticmethod
    def _embeddings(texts):
        encoded = sbert_model.encode(texts)
        if encoded is None:
            raise SBERTModelUnavailableError(
                f"SBERT model {settings.SBERT_MODEL!r} is unavailable."
            )
        if hasattr(encoded, "detach"):
            encoded = encoded.detach().cpu()
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        return encoded

    @staticmethod
    def _is_official_india_code_url(url):
        parsed = urlparse(url)
        return parsed.scheme == "https" and parsed.hostname in INDIA_CODE_HOSTS

    @staticmethod
    def _read_source(url):
        if not RAGService._is_official_india_code_url(url):
            raise ValueError("Legal source URLs must use HTTPS on indiacode.nic.in.")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        final_url = response.url
        if not RAGService._is_official_india_code_url(final_url):
            raise ValueError("India Code source redirected outside the official domain.")
        content = response.content
        content_type = response.headers.get("Content-Type", "").lower()
        if content.startswith(b"%PDF") or "application/pdf" in content_type:
            import fitz

            with fitz.open(stream=content, filetype="pdf") as pdf:
                return "\n".join(page.get_text() for page in pdf)
        if "html" in content_type or b"<html" in content[:512].lower():
            parser = _HTMLTextExtractor()
            parser.feed(content.decode(response.encoding or "utf-8", errors="replace"))
            return "".join(parser.parts)
        return content.decode(response.encoding or "utf-8", errors="replace")

    @staticmethod
    def _section_chunks(text, source):
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        headings = list(re.finditer(
            r"(?m)^[ \t]*(\d+[A-Z]?)\.\s+([^\n]{4,})$",
            normalized,
        ))
        chunks = []
        for index, heading in enumerate(headings):
            body_start = heading.end()
            body_end = headings[index + 1].start() if index + 1 < len(headings) else len(normalized)
            heading_text = heading.group(2).strip()
            inline_body = ""
            title_match = re.search(r"[—–]", heading_text)
            if title_match:
                inline_body = heading_text[title_match.end():].strip()
                heading_text = heading_text[:title_match.start()]
            body = re.sub(
                r"\s+",
                " ",
                f"{inline_body} {normalized[body_start:body_end]}",
            ).strip()
            if not body:
                continue
            section_number = heading.group(1).strip()
            section_title = heading_text.strip().rstrip(".—- ")
            document = f"Section {section_number}: {section_title}\n{body}"
            identity = "\n".join((
                source["url"],
                source["act_name"],
                str(source.get("version") or ""),
                section_number,
                document,
            ))
            chunks.append({
                "id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                "document": document,
                "metadata": {
                    "act_name": source["act_name"],
                    "section_number": section_number,
                    "section_title": section_title,
                    "source_url": source["url"],
                    "version": str(source.get("version") or ""),
                    "effective_date": str(source.get("effective_date") or ""),
                },
            })
        return chunks

    def index_document(self, text, source):
        if not isinstance(source, dict) or not source.get("act_name") or not source.get("url"):
            raise ValueError("A legal source requires an act_name and official India Code URL.")
        if not isinstance(source["act_name"], str) or not isinstance(source["url"], str):
            raise ValueError("Legal source act_name and url values must be strings.")
        if not self._is_official_india_code_url(source["url"]):
            raise ValueError("Legal source URLs must use HTTPS on indiacode.nic.in.")
        chunks = self._section_chunks(text, source)
        if not chunks:
            raise ValueError(f"No numbered legislative sections were found in {source['url']}.")

        collection = self._get_collection()
        embeddings = self._embeddings([chunk["document"] for chunk in chunks])
        collection.upsert(
            ids=[chunk["id"] for chunk in chunks],
            documents=[chunk["document"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
            embeddings=embeddings,
        )
        current_ids = {chunk["id"] for chunk in chunks}
        existing = collection.get(
            where={"source_url": source["url"]},
            include=["metadatas"],
        )
        stale_ids = [
            chunk_id for chunk_id in existing.get("ids", [])
            if chunk_id not in current_ids
        ]
        if stale_ids:
            collection.delete(ids=stale_ids)
        return len(chunks)

    def ingest_sources(self, sources):
        if not isinstance(sources, list) or not sources:
            raise ValueError("INDIA_CODE_SOURCES_JSON must contain a non-empty JSON array.")
        indexed_sections = 0
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("Each India Code source must be a JSON object.")
            text = self._read_source(source.get("url", ""))
            indexed_sections += self.index_document(text, source)
        return {"status": "ready", "sources": len(sources), "sections_indexed": indexed_sections}

    def query(self, query, top_k=4):
        if not isinstance(query, str) or not query.strip():
            return {"status": "no_relevant_match", "matches": [], "disclaimer": LEGAL_DISCLAIMER}
        try:
            corpus_status = self.status()
            if corpus_status["status"] != "ready":
                return {
                    "status": corpus_status["status"],
                    "matches": [],
                    "disclaimer": LEGAL_DISCLAIMER,
                }
            collection = self._get_collection()
            embedding = self._embeddings([query])[0]
            results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except SBERTModelUnavailableError:
            logger.warning("Legal retrieval unavailable because the configured SBERT model is unavailable.")
            return {"status": "unavailable", "matches": [], "disclaimer": LEGAL_DISCLAIMER}
        except Exception as exc:
            logger.warning("Legal retrieval unavailable (%s).", type(exc).__name__)
            return {"status": "unavailable", "matches": [], "disclaimer": LEGAL_DISCLAIMER}

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        matches = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            score = max(0.0, min(1.0, 1.0 - float(distance)))
            if score < RELEVANCE_THRESHOLD:
                continue
            matches.append({
                **metadata,
                "retrieved_text": document,
                "relevance_score": round(score, 4),
                "explanation": (
                    "Retrieved because its section text is semantically relevant to the "
                    "contract passage; this is not a legal applicability determination."
                ),
                "explanation_source": "retrieval",
            })
        return {
            "status": "ready" if matches else "no_relevant_match",
            "matches": matches,
            "disclaimer": LEGAL_DISCLAIMER,
        }

    def status(self):
        if (
            self._collection is None
            and not settings.CHROMA_HOST.strip()
            and not os.path.isdir(settings.CHROMA_PERSIST_DIRECTORY)
        ):
            return {"status": "empty", "sections": 0}
        try:
            count = self._get_collection().count()
        except Exception as exc:
            logger.warning("Legal corpus status unavailable (%s).", type(exc).__name__)
            return {"status": "unavailable", "sections": None}
        return {"status": "ready" if count else "empty", "sections": count}


rag_service = RAGService()


def main():
    parser = argparse.ArgumentParser(description="Ingest official India Code legal sources into ChromaDB.")
    parser.add_argument("--ingest", action="store_true", help="Ingest sources configured in INDIA_CODE_SOURCES_JSON.")
    args = parser.parse_args()
    if not args.ingest:
        parser.error("Specify --ingest.")
    if not settings.INDIA_CODE_SOURCES_JSON.strip():
        parser.error("Set INDIA_CODE_SOURCES_JSON to a JSON array of official India Code sources.")
    sources = json.loads(settings.INDIA_CODE_SOURCES_JSON)
    print(json.dumps(rag_service.ingest_sources(sources), indent=2))


if __name__ == "__main__":
    main()
