from httpx import AsyncClient


async def track_event(api_key: str, name: str, properties: dict = {}) -> dict:
    """Track event in Mixpanel."""
    url = "https://api.mixpanel.com/track"
    async with AsyncClient() as client:
        r = await client.post(url, json=[{
            "event": name,
            "properties": {**properties, "token": api_key}
        }])
        return {"status": "ok"}


async def update_profile(api_key: str, distinct_id: str, **properties) -> dict:
    """Update user profile in Mixpanel."""
    url = "https://api.mixpanel.com/engage"
    async with AsyncClient() as client:
        r = await client.post(url, json=[{
            "$set": properties,
            "$token": api_key,
            "$distinct_id": distinct_id
        }])
        return {"status": "ok"}


async def get_people(api_key: str, expression: str = "") -> dict:
    """Get people from Mixpanel."""
    url = f"https://api.mixpanel.com/engage?api_key={api_key}&expression={expression}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def get_events(api_key: str, from_date: str, to_date: str) -> dict:
    """Get events from Mixpanel."""
    url = f"https://api.mixpanel.com/funnels?api_key={api_key}&from_date={from_date}&to_date={to_date}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def create_annotation(api_key: str, project_id: str, date: str, text: str) -> dict:
    """Create annotation in Mixpanel."""
    url = f"https://api.mixpanel.com/projects/{project_id}/annotations"
    async with AsyncClient() as client:
        r = await client.post(url, json={"date": date, "text": text}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()