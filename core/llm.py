import os
from openai import OpenAI

def get_client(base_url=None, api_key = "local"):
    base_url = base_url or os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    return OpenAI(base_url=base_url, api_key=api_key)

def get_embed_client(base_url = None, api_key = "ollama"):
    """Embeddings stay on ollama - the vllm server only serves the chat model"""
    base_url = base_url or os.environ.get("EMBED_BASE_URL", "http://localhost:11434/v1")
    return OpenAI(base_url = base_url, api_key = api_key)
def get_model():
    return os.environ.get("QWEN_MODEL", "qwen3:8b")