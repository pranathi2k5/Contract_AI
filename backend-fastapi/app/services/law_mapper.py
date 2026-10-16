from app.services.rag_service import LEGAL_DISCLAIMER, rag_service


class LawMapper:
    def map_laws_with_status(self, clauses):
        matches = []
        seen = set()
        corpus_status = rag_service.status()

        for clause in clauses or []:
            clause_text = str(clause.get("clause_text") or "").strip()
            if not clause_text:
                continue
            result = rag_service.query(clause_text)
            if result["status"] == "unavailable":
                corpus_status = {"status": "unavailable", "sections": corpus_status.get("sections")}
            elif result["status"] == "empty":
                corpus_status = {"status": "empty", "sections": 0}
            for section in result["matches"]:
                citation = (
                    section["source_url"],
                    section["section_number"],
                    clause_text,
                )
                if citation in seen:
                    continue
                seen.add(citation)
                matches.append({
                    "clause_text": clause_text,
                    "law_name": section["act_name"],
                    "act_name": section["act_name"],
                    "section_number": section["section_number"],
                    "section_title": section["section_title"],
                    "relevance_score": section["relevance_score"] * 100,
                    "reason": section["explanation"],
                    "source": section["source_url"],
                    "source_url": section["source_url"],
                    "version": section["version"],
                    "effective_date": section["effective_date"],
                    "retrieved_text": section["retrieved_text"],
                    "explanation_source": section["explanation_source"],
                })

        if matches:
            corpus_status = {
                "status": "ready",
                "sections": corpus_status.get("sections"),
            }
        elif corpus_status["status"] == "ready":
            corpus_status = {
                "status": "no_relevant_match",
                "sections": corpus_status.get("sections"),
            }
        return {
            "matches": matches,
            "legal_corpus_status": corpus_status,
            "legal_disclaimer": LEGAL_DISCLAIMER,
        }

    def map_laws(self, clauses):
        return self.map_laws_with_status(clauses)["matches"]


law_mapper = LawMapper()
