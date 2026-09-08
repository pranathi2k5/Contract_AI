from fastapi import APIRouter, Depends
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot_service import chatbot_service

router = APIRouter(prefix="/ai/chat", tags=["chat"])

@router.post("/", response_model=ChatMessageResponse)
async def chat(req: ChatMessageRequest):
    # Retrieve context from DB/RAG
    context = "Sample contract context here."
    resp_text = chatbot_service.chat(context, req.message)
    return ChatMessageResponse(role="assistant", content=resp_text, sources=[])

@router.get("/context/{contract_id}")
async def get_context(contract_id: str):
    return {"contract_id": contract_id, "context": "Retrieved contract context chunks"}
