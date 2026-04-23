from httpx import AsyncClient


async def chat_completion(model: str, messages: list, api_key: str, **kwargs) -> dict:
    """OpenAI Chat Completion."""
    url = "https://api.openai.com/v1/chat/completions"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "model": model,
            "messages": messages,
            **kwargs
        }, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        return r.json()


async def embeddings(text: str, model: str = "text-embedding-3-small", api_key: str) -> dict:
    """OpenAI Embeddings."""
    url = "https://api.openai.com/v1/embeddings"
    async with AsyncClient() as client:
        r = await client.post(url, json={"input": text, "model": model}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def image_edit(api_key: str, image: bytes, mask: bytes = None, prompt: str = "", n: int = 1) -> dict:
    """OpenAI Image Edit."""
    url = "https://api.openai.com/v1/images/edits"
    files = {"image": image}
    if mask:
        files["mask"] = mask
    async with AsyncClient() as client:
        r = await client.post(url, files=files, data={"prompt": prompt, "n": n}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def transcribe(api_key: str, file: bytes, model: str = "whisper-1") -> dict:
    """OpenAI Whisper Transcription."""
    url = "https://api.openai.com/v1/audio/transcriptions"
    async with AsyncClient() as client:
        r = await client.post(url, files={"file": file}, data={"model": model}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_models(api_key: str) -> dict:
    """List OpenAI models."""
    url = "https://api.openai.com/v1/models"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()