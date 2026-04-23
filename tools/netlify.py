from httpx import AsyncClient


async def create_site(name: str, api_key: str) -> dict:
    """Create Netlify site."""
    url = "https://api.netlify.com/api/v1/sites"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_site(site_id: str, api_key: str) -> dict:
    """Get Netlify site."""
    url = f"https://api.netlify.com/api/v1/sites/{site_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def deploy_site(site_id: str, api_key: str) -> dict:
    """Deploy Netlify site."""
    url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_deploys(site_id: str, api_key: str) -> dict:
    """Get Netlify deploys."""
    url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_hook(site_id: str, url: str, api_key: str) -> dict:
    """Create Netlify build hook."""
    hook_url = f"https://api.netlify.com/api/v1/sites/{site_id}/build_hooks"
    async with AsyncClient() as client:
        r = await client.post(hook_url, json={"url": url}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()