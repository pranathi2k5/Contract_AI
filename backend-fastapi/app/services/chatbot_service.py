import requests
from app.config import settings

class ChatbotService:
    def chat(self, context, message):
        prompt = f"Context: {context}\nUser: {message}\nAssistant:"
        try:
            resp = requests.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            })
            if resp.status_code == 200:
                return resp.json().get("response", "No response generated.")
        except Exception as e:
            return f"Chatbot error: {e}"
        return "I am currently unavailable."

chatbot_service = ChatbotService()
