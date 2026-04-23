from httpx import AsyncClient


async def execute_query(host: str, port: int, database: str, query: str, user: str, password: str) -> dict:
    """Execute query on Cassandra."""
    url = f"http://{host}:{port}/cassandra"
    async with AsyncClient() as client:
        r = await client.post(url, json={"keyspace": database, "query": query}, auth=(user, password))
        return r.json()


async def create_keyspace(host: str, port: int, name: str, user: str, password: str) -> dict:
    """Create Cassandra keyspace."""
    url = f"http://{host}:{port}/cassandra/keyspace"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, auth=(user, password))
        return r.json()


async def create_table(host: str, port: int, keyspace: str, table: str, schema: dict, user: str, password: str) -> dict:
    """Create Cassandra table."""
    url = f"http://{host}:{port}/cassandra/table"
    async with AsyncClient() as client:
        r = await client.post(url, json={"keyspace": keyspace, "name": table, "schema": schema}, auth=(user, password))
        return r.json()


async def get_tables(host: str, port: int, keyspace: str, user: str, password: str) -> dict:
    """Get tables in keyspace."""
    url = f"http://{host}:{port}/cassandra/tables/{keyspace}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(user, password))
        return r.json()


async def truncate_table(host: str, port: int, keyspace: str, table: str, user: str, password: str) -> dict:
    """Truncate Cassandra table."""
    url = f"http://{host}:{port}/cassandra/truncate"
    async with AsyncClient() as client:
        r = await client.post(url, json={"keyspace": keyspace, "table": table}, auth=(user, password))
        return r.json()