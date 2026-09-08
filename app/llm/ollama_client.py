import os

import requests
from dotenv import load_dotenv

load_dotenv()


class OllamaClient:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.getenv(
            "OLLAMA_MODEL", "qwen2.5-coder:7b"
        )
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

    def is_reachable(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,
            )
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, prompt: str, timeout: int = 180) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=timeout,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]