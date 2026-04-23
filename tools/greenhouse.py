from httpx import AsyncClient


async def list_jobs(api_key: str) -> dict:
    """ Greenhouse jobs."""
    url = "https://boards-api.greenhouse.io/v1/boards/jobs"
    async with AsyncClient() as client:
        r = await client.get(url, params={"api_key": api_key})
        return r.json()


async def get_job(api_key: str, job_id: str) -> dict:
    """Get Greenhouse job."""
    url = f"https://boards-api.greenhouse.io/v1/boards/jobs/{job_id}"
    async with AsyncClient() as client:
        r = await client.get(url, params={"api_key": api_key})
        return r.json()


async def list_candidates(api_key: str, job_id: str = None) -> dict:
    """List Greenhouse candidates."""
    url = f"https://harvest.greenhouse.io/v1/candidates"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"}, params={"job_id": job_id} if job_id else {})
        return r.json()


async def create_candidate(api_key: str, email: str, first_name: str, last_name: str) -> dict:
    """Create Greenhouse candidate."""
    url = "https://harvest.greenhouse.io/v1/candidates"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": email, "first_name": first_name, "last_name": last_name}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()