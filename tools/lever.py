from httpx import AsyncClient


async def list_jobs(api_key: str) -> dict:
    """List Lever jobs."""
    url = f"https://api.lever.co/v0/posts"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def get_job(api_key: str, job_id: str) -> dict:
    """Get Lever job details."""
    url = f"https://api.lever.co/v0/posts/{job_id}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def list_stages(api_key: str, job_id: str) -> dict:
    """List Lever stages."""
    url = f"https://api.lever.co/v0/stages/{job_id}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def get_postings(api_key: str, mode: str = "embed") -> dict:
    """Get Lever postings."""
    url = f"https://api.lever.co/v0/postings?mode={mode}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()