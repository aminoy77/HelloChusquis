from httpx import AsyncClient


async def complete(prompt: str, model: str = "claude-3-5-sonnet-20241022", max_tokens: int = 1024, api_key: str = None, **kwargs) -> dict:
    """Anthropic Claude Completion."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": api_key or "", "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }, headers=headers)
        return r.json()


async def vision_complete(api_key: str, model: str, prompt: str, image_urls: list, **kwargs) -> dict:
    """Anthropic Claude Vision."""
    url = "https://api.anthropic.com/v1/messages"
    content = [{"type": "text", "text": prompt}]
    for url in image_urls:
        content.append({"type": "image", "source": {"type": "url", "url": url}})
    
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    async with AsyncClient() as client:
        r = await client.post(url, json={"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": content}]}, headers=headers)
        return r.json()


async def embeddings(api_key: str, input: str, model: str = "claude-embedding-3", **kwargs) -> dict:
    """Anthropic Claude Embeddings."""
    url = "https://api.anthropic.com/v1/embeddings"
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    async with AsyncClient() as client:
        r = await client.post(url, json={"model": model, "input": input, **kwargs}, headers=headers)
        return r.json()