import logging

import requests
from app.config import settings

logger = logging.getLogger(__name__)


class ChatbotUnavailableError(RuntimeError):
    """Raised when the configured Ollama service cannot provide a chat response."""


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
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=15,
            )
            response.raise_for_status()
            response_body = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Ollama chat unavailable: %s", exc)
            raise ChatbotUnavailableError(
                "Chat service is unavailable. Configure OLLAMA_BASE_URL to point to a reachable Ollama service."
            ) from exc

        result = response_body.get("response") if isinstance(response_body, dict) else None
        if not isinstance(result, str) or not result.strip():
            raise ChatbotUnavailableError("Chat service returned an invalid response.")
        return result.strip()

chatbot_service = ChatbotService()
