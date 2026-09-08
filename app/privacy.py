def privacy_flags(local_model: str) -> dict:
    return {
        "privacy_mode": True,
        "local_llm": "Ollama",
        "local_model": local_model,
        "documents_processed_locally": True,
        "external_verification": False,
    }
