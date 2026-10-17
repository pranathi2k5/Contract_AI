from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot_service import ChatbotUnavailableError, chatbot_service
from app.services.rag_service import LEGAL_DISCLAIMER, rag_service

router = APIRouter(prefix="/ai/chat", tags=["chat"])
MIN_LEGAL_RELEVANCE = 0.45
OFFICIAL_INDIA_CODE_HOSTS = {"indiacode.nic.in", "www.indiacode.nic.in"}


def _verified_legal_matches(legal_result):
    if not isinstance(legal_result, dict) or legal_result.get("status") != "ready":
        return []
    matches = legal_result.get("matches")
    if not isinstance(matches, list):
        return []

    verified = []
    for match in matches:
        if not isinstance(match, dict):
            continue
        required_text = ("act_name", "section_number", "section_title", "retrieved_text")
        if not all(
            isinstance(match.get(field), str) and match[field].strip()
            for field in required_text
        ):
            continue
        source_url = match.get("source_url")
        if not isinstance(source_url, str):
            continue
        parsed_url = urlparse(source_url)
        if parsed_url.scheme != "https" or parsed_url.hostname not in OFFICIAL_INDIA_CODE_HOSTS:
            continue
        score = match.get("relevance_score")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or score < MIN_LEGAL_RELEVANCE
        ):
            continue
        verified.append(match)
    return verified


def _evidence_status(sources):
    if not sources:
        return (
            "Retrieved statutory evidence: No relevant official India Code passage "
            "with verifiable source metadata was retrieved. The answer may still provide "
            "general legal information, but does not quote or cite a statute."
        )
    return (
        "Retrieved statutory evidence: Official India Code passages and their citations "
        "are listed under Sources. The assistant's explanation is AI-generated and is "
        "not itself statutory text."
    )

@router.post("/", response_model=ChatMessageResponse)
def chat(req: ChatMessageRequest):
    contract_context = (req.contract_context or "").strip()
    if len(contract_context) > 24000:
        contract_context = contract_context[:24000] + "\n[Contract text truncated for context size.]"
    legal_result = rag_service.query(req.message)
    legal_matches = _verified_legal_matches(legal_result)
    legal_context = "\n\n".join(
        f"Act: {match['act_name']}\n"
        f"Section: {match['section_number']} — {match['section_title']}\n"
        f"Official source: {match['source_url']}\n"
        f"Retrieved statutory text:\n{match['retrieved_text']}"
        for match in legal_matches
    )
    try:
        resp_text = chatbot_service.chat(contract_context, legal_context, req.message)
    except ChatbotUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    sources = [
        {
            "act_name": match["act_name"],
            "section_number": match["section_number"],
            "section_title": match["section_title"],
            "source_url": match["source_url"],
            "relevance_score": match["relevance_score"],
            "retrieved_text": match["retrieved_text"],
            "version": match.get("version", ""),
            "effective_date": match.get("effective_date", ""),
        }
        for match in legal_matches
    ]
    return ChatMessageResponse(
        role="assistant",
        content=(
            "AI-generated explanation (general legal information and/or contract-specific "
            f"analysis):\n{resp_text}\n\n{_evidence_status(sources)}\n\n{LEGAL_DISCLAIMER}"
        ),
        sources=sources,
    )

@router.get("/context/{contract_id}")
async def get_context(contract_id: str):
    return {"contract_id": contract_id, "context": None, "available": False}
