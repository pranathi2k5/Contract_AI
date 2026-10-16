import logging

import requests
from app.config import settings

logger = logging.getLogger(__name__)


class ChatbotService:
    def generate(self, prompt, output_format=None):
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
        if output_format:
            payload["format"] = output_format

        try:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            response_body = response.json()
            if not isinstance(response_body, dict):
                logger.warning("Ollama returned an invalid generated response.")
                return None
            result = response_body.get("response")
            if not isinstance(result, str) or not result.strip():
                logger.warning("Ollama returned an empty generated response.")
                return None
            return result.strip()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Ollama risk generation unavailable: %s", exc)
            return None

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
