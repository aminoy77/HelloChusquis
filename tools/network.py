from httpx import AsyncClient


async def get_ip() -> dict:
    """Get public IP address."""
    async with AsyncClient() as client:
        r = await client.get("https://api.ipify.org?format=json")
        return r.json()


async def get_ip_info(ip: str) -> dict:
    """Get IP geolocation info."""
    async with AsyncClient() as client:
        r = await client.get(f"http://ip-api.com/json/{ip}")
        return r.json()


async def check_port(ip: str, port: int, timeout: int = 3) -> dict:
    """Check if port is open on IP."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return {"ip": ip, "port": port, "open": result == 0}
    except Exception as e:
        return {"ip": ip, "port": port, "error": str(e)}
    finally:
        sock.close()


async def check_ssl(domain: str, port: int = 443) -> dict:
    """Check SSL certificate."""
    import ssl, socket
    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return {"valid": True, "issuer": cert.get("issuer"), "subject": cert.get("subject")}
    except Exception as e:
        return {"valid": False, "error": str(e)}


async def lookup_domain(domain: str) -> dict:
    """DNS lookup."""
    import socket
    try:
        ip = socket.gethostbyname(domain)
        return {"domain": domain, "ip": ip}
    except Exception as e:
        return {"domain": domain, "error": str(e)}