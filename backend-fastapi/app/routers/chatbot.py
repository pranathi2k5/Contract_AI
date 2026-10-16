from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot_service import ChatbotUnavailableError, chatbot_service
from app.services.rag_service import LEGAL_DISCLAIMER, rag_service

router = APIRouter(prefix="/ai/chat", tags=["chat"])

@router.post("/", response_model=ChatMessageResponse)
def chat(req: ChatMessageRequest):
    contract_context = (req.contract_context or "").strip()
    if len(contract_context) > 24000:
        contract_context = contract_context[:24000] + "\n[Contract text truncated for context size.]"
    legal_result = rag_service.query(req.message)
    legal_matches = legal_result["matches"]
    legal_context = "\n\n".join(
        f"{match['act_name']}, section {match['section_number']} "
        f"({match['section_title']})\n{match['retrieved_text']}"
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
            "version": match.get("version", ""),
            "effective_date": match.get("effective_date", ""),
        }
        for match in legal_matches
    ]
    return ChatMessageResponse(
        role="assistant",
        content=f"{resp_text}\n\n{LEGAL_DISCLAIMER}",
        sources=sources,
    )

@router.get("/context/{contract_id}")
async def get_context(contract_id: str):
    return {"contract_id": contract_id, "context": None, "available": False}
