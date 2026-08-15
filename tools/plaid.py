from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "plaid"
PLUGIN_DESCRIPTION = "Plaid - banking and financial data"


def run(action: str, **kwargs) -> str:
    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    env = os.getenv("PLAID_ENV", "sandbox")
    if not client_id or not secret:
        return "Error: Plaid credentials not configured. Set PLAID_CLIENT_ID and PLAID_SECRET environment variables."

    base_url = f"https://{env}.plaid.com"
    headers = {"Content-Type": "application/json"}

    try:
        if action == "create_link_token":
            payload = {
                "client_id": client_id,
                "secret": secret,
                "client_name": "HelloChusquis",
                "country_codes": ["US"],
                "language": "en",
                "user": {"client_user_id": kwargs.get("user_id", "hellochusquis")},
                "products": ["transactions"],
            }
            r = httpx.post(f"{base_url}/link/token/create", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        elif action == "exchange_token":
            public_token = kwargs.get("public_token")
            if not public_token:
                return "Error: public_token required for exchange_token"
            payload = {"client_id": client_id, "secret": secret, "public_token": public_token}
            r = httpx.post(f"{base_url}/item/public_token/exchange", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        elif action == "get_transactions":
            access_token = kwargs.get("access_token")
            if not access_token:
                return "Error: access_token required for get_transactions"
            payload = {
                "client_id": client_id,
                "secret": secret,
                "access_token": access_token,
                "start_date": kwargs.get("start_date", "2024-01-01"),
                "end_date": kwargs.get("end_date", "2024-12-31"),
            }
            r = httpx.post(f"{base_url}/transactions/get", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        elif action == "get_balance":
            access_token = kwargs.get("access_token")
            if not access_token:
                return "Error: access_token required for get_balance"
            payload = {"client_id": client_id, "secret": secret, "access_token": access_token}
            r = httpx.post(f"{base_url}/accounts/balance/get", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: create_link_token, exchange_token, get_transactions, get_balance"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]