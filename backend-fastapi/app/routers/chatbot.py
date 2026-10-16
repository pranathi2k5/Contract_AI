from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot_service import ChatbotUnavailableError, chatbot_service

router = APIRouter(prefix="/ai/chat", tags=["chat"])

@router.post("/", response_model=ChatMessageResponse)
async def chat(req: ChatMessageRequest):
    context = (
        "No contract-specific context is available. Answer general legal questions only; "
        "do not claim that a clause or fact appears in the user's contract."
    )
    try:
        resp_text = chatbot_service.chat(context, req.message)
    except ChatbotUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ChatMessageResponse(role="assistant", content=resp_text, sources=[])

@router.get("/context/{contract_id}")
async def get_context(contract_id: str):
    return {"contract_id": contract_id, "context": None, "available": False}
