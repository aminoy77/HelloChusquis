from httpx import AsyncClient


async def create_project(name: str, slug: str, api_key: str) -> dict:
    """Create Supabase project."""
    url = "https://api.supabase.com/v1/projects"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "slug": slug}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_project(ref: str, api_key: str) -> dict:
    """Get Supabase project."""
    url = f"https://api.supabase.com/v1/projects/{ref}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def query_table(ref: str, table: str, api_key: str) -> dict:
    """Query Supabase table."""
    url = f"https://{ref}.supabase.co/rest/v1/{table}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
        return r.json()


async def insert_row(ref: str, table: str, data: dict, api_key: str) -> dict:
    """Insert row to Supabase."""
    url = f"https://{ref}.supabase.co/rest/v1/{table}"
    async with AsyncClient() as client:
        r = await client.post(url, json=data, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
        return r.json()


async def run_sql(ref: str, sql: str, api_key: str) -> dict:
    """Run SQL in Supabase."""
    url = f"https://{ref}.supabase.co/rest/v1/rpc/exec_sql"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": sql}, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
        return r.json()