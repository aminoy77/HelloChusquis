from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Supabase API actions."""
    api_key = kwargs.get("api_key") or os.getenv("SUPABASE_API_KEY")
    if not api_key:
        return "Error: No Supabase API key found. Set SUPABASE_API_KEY environment variable."

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # Event loop running — schedule async on it
        import concurrent.futures
        fut = asyncio.run_coroutine_threadsafe(_run_async(action, api_key, kwargs), loop)
        return fut.result(timeout=30)
    except RuntimeError:
        # No event loop — use sync httpx
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Supabase operations."""
    if action == "create_project":
        return str(await create_project(kwargs.get("name", ""), kwargs.get("slug", ""), api_key))[:2000]
    elif action == "get_project":
        return str(await get_project(kwargs.get("ref", ""), api_key))[:2000]
    elif action == "query_table":
        return str(await query_table(kwargs.get("ref", ""), kwargs.get("table", ""), api_key))[:2000]
    elif action == "insert_row":
        return str(await insert_row(kwargs.get("ref", ""), kwargs.get("table", ""), kwargs.get("data", {}), api_key))[:2000]
    elif action == "run_sql":
        return str(await run_sql(kwargs.get("ref", ""), kwargs.get("sql", ""), api_key))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: create_project, get_project, query_table, insert_row, run_sql"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    try:
        client = httpx.Client(timeout=30)
        if action == "create_project":
            r = client.post("https://api.supabase.com/v1/projects",
                           json={"name": kwargs.get("name", ""), "slug": kwargs.get("slug", "")},
                           headers={"Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "get_project":
            r = client.get(f"https://api.supabase.com/v1/projects/{kwargs.get('ref', '')}",
                          headers={"Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "query_table":
            ref = kwargs.get("ref", "")
            table = kwargs.get("table", "")
            r = client.get(f"https://{ref}.supabase.co/rest/v1/{table}",
                          headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "insert_row":
            ref = kwargs.get("ref", "")
            table = kwargs.get("table", "")
            r = client.post(f"https://{ref}.supabase.co/rest/v1/{table}",
                           json=kwargs.get("data", {}),
                           headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "run_sql":
            ref = kwargs.get("ref", "")
            r = client.post(f"https://{ref}.supabase.co/rest/v1/rpc/exec_sql",
                           json={"query": kwargs.get("sql", "")},
                           headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_project, get_project, query_table, insert_row, run_sql"
    except Exception as e:
        return f"Error: {str(e)}"


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