from httpx import AsyncClient


async def post_job(title: str, location: str, api_key: str, **kwargs) -> dict:
    """Post job on LinkedIn."""
    url = "https://api.linkedin.com/v2/jobs"
    async with AsyncClient() as client:
        r = await client.post(url, json={"title": title, "location": location, **kwargs}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def search_jobs(api_key: str, keywords: str) -> dict:
    """Search jobs on LinkedIn."""
    url = f"https://api.linkedin.com/v2/jobs?keywords={keywords}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_profile(api_key: str, person_id: str = "me") -> dict:
    """Get LinkedIn profile."""
    url = f"https://api.linkedin.com/v2/people/{person_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def share_post(api_key: str, comment: str, title: str = None) -> dict:
    """Share post on LinkedIn."""
    url = "https://api.linkedin.com/v2/ugcPosts"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "comment": comment,
            "content": {"title": {"text": title}} if title else None
        }, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def send_message(api_key: str, recipient: str, message: str) -> dict:
    """Send LinkedIn message."""
    url = "https://api.linkedin.com/v2/messages"
    async with AsyncClient() as client:
        r = await client.post(url, json={"recipients": [recipient], "message": {"body": message}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()