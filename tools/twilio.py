from httpx import AsyncClient
import os
import httpx


async def send_message(auth: str, to: str, message: str) -> dict:
    """Send SMS via Twilio."""
    url = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    async with AsyncClient() as client:
        r = await client.post(url, data={"To": to, "Body": message}, 
            headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def list_messages(auth: str, to: str = None) -> dict:
    """List Twilio messages."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{{account_sid}}/Messages.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def make_call(auth: str, to: str, url: str) -> dict:
    """Make Twilio call."""
    call_url = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    async with AsyncClient() as client:
        r = await client.post(call_url, data={"To": to, "Url": url}, 
            headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def get_call_log(auth: str, sid: str) -> dict:
    """Get Twilio call log."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{{account_sid}}/Calls/{sid}.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def lookup_phone(auth: str, phone: str) -> dict:
    """Lookup phone number."""
    url = f"https://api.twilio.com/2010-04-01/Addresses/{phone}/Lookup.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Twilio API actions."""
    auth = kwargs.get("auth") or os.getenv("TWILIO_AUTH_TOKEN")
    if not auth:
        return "Error: No Twilio auth token found. Set TWILIO_AUTH_TOKEN environment variable."
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, auth, kwargs)
        return loop.run_until_complete(_run_async(action, auth, kwargs))
    except RuntimeError:
        return _run_sync(action, auth, kwargs)


async def _run_async(action: str, auth: str, kwargs: dict) -> str:
    """Async dispatcher for Twilio operations."""
    if action == "send_message":
        return str(await send_message(auth, kwargs.get("to", ""), kwargs.get("message", "")))
    elif action == "list_messages":
        return str(await list_messages(auth, kwargs.get("to")))
    elif action == "make_call":
        return str(await make_call(auth, kwargs.get("to", ""), kwargs.get("url", "")))
    elif action == "get_call_log":
        return str(await get_call_log(auth, kwargs.get("sid", "")))
    elif action == "lookup_phone":
        return str(await lookup_phone(auth, kwargs.get("phone", "")))
    else:
        return f"Error: Unknown action '{action}'. Available: send_message, list_messages, make_call, get_call_log, lookup_phone"


def _run_sync(action: str, auth: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    try:
        client = httpx.Client(timeout=30)
        headers = {"Authorization": f"Bearer {auth}"}
        if action == "send_message":
            r = client.post("https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                           data={"To": kwargs.get("to", ""), "Body": kwargs.get("message", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "list_messages":
            r = client.get("https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json", headers=headers)
            return str(r.json())[:2000]
        elif action == "make_call":
            r = client.post("https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
                           data={"To": kwargs.get("to", ""), "Url": kwargs.get("url", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_call_log":
            r = client.get(f"https://api.twilio.com/2010-04-01/Accounts/{{account_sid}}/Calls/{kwargs.get('sid', '')}.json", headers=headers)
            return str(r.json())[:2000]
        elif action == "lookup_phone":
            r = client.get(f"https://api.twilio.com/2010-04-01/Addresses/{kwargs.get('phone', '')}/Lookup.json", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: send_message, list_messages, make_call, get_call_log, lookup_phone"
    except Exception as e:
        return f"Error: {str(e)}"