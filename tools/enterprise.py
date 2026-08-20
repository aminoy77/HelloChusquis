import os
import re

import httpx


PLUGIN_NAME = "salesforce"
PLUGIN_DESCRIPTION = "Salesforce CRM integration"
SALESFORCE_HTTP_TIMEOUT_SECONDS = 30
_SALESFORCE_INSTANCE_RE = re.compile(r"^[A-Za-z0-9-]{1,63}$")
_SALESFORCE_OBJECTS = frozenset({"Account", "Contact", "Lead", "Opportunity"})
_SALESFORCE_FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)?$")
_SALESFORCE_DEFAULT_FIELDS = ("Id", "Name")

SALESFORCE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "salesforce",
        "description": "Salesforce operations",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["query", "create", "update", "list_objects"]},
                "sobject": {"type": "string", "description": "Object type (Account, Contact, Lead, Opportunity)"},
                "fields": {"type": "string", "description": "Fields to query"},
                "data": {"type": "string", "description": "Data as JSON"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, sobject: str = "", fields: str = "", data: str = "") -> str:
    """Salesforce operations."""
    token = os.getenv("SALESFORCE_TOKEN")
    instance = os.getenv("SALESFORCE_INSTANCE")
    
    if not token:
        return "Error: SALESFORCE_TOKEN not set"
    
    if not instance:
        return "Error: SALESFORCE_INSTANCE (yourdomain) not set"
    if not _SALESFORCE_INSTANCE_RE.fullmatch(instance):
        return "Error: SALESFORCE_INSTANCE is invalid"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base = f"https://{instance}.salesforce.com/services/data/v58.0"
    
    if action == "list_objects":
        try:
            resp = httpx.get(
                f"{base}/sobjects",
                headers=headers,
                timeout=SALESFORCE_HTTP_TIMEOUT_SECONDS,
                follow_redirects=False,
            )
        except httpx.HTTPError:
            return "Error: Salesforce request failed"
        if resp.status_code == 200:
            objs = resp.json().get("sobjects", [])[:15]
            return "Objects:\n" + "\n".join([f"• {obj['name']}" for obj in objs])
        return f"Error: {resp.status_code}"
    
    if action == "query":
        if not sobject:
            return "Error: sobject required"
        if sobject not in _SALESFORCE_OBJECTS:
            return "Error: invalid Salesforce object"
        requested_fields = [field.strip() for field in fields.split(",") if field.strip()]
        if not requested_fields:
            requested_fields = list(_SALESFORCE_DEFAULT_FIELDS)
        if len(requested_fields) > 20 or any(
            not _SALESFORCE_FIELD_RE.fullmatch(field) for field in requested_fields
        ):
            return "Error: invalid Salesforce fields"
        q = f"SELECT {', '.join(requested_fields)} FROM {sobject} LIMIT 10"
        try:
            resp = httpx.get(
                f"{base}/query",
                params={"q": q},
                headers=headers,
                timeout=SALESFORCE_HTTP_TIMEOUT_SECONDS,
                follow_redirects=False,
            )
        except httpx.HTTPError:
            return "Error: Salesforce request failed"
        if resp.status_code == 200:
            records = resp.json().get("records", [])
            return "\n".join([str(record) for record in records[:5]])
        return f"Error: {resp.status_code}"
    
    return f"Action {action} not fully implemented"


# HubSpot
def hubspot(action: str = "", object_type: str = "", properties: str = "") -> str:
    """HubSpot CRM."""
    token = os.getenv("HUBSPOT_TOKEN")
    if not token:
        return "Error: HUBSPOT_TOKEN not set"
    
    if action == "list":
        # Would list contacts, companies
        return "HubSpot integration - configure HUBSPOT_TOKEN"
    
    return "HubSpot: use SALESFORCE for full CRM"


# ServiceNow
def servicenow(action: str = "", table: str = "", data: str = "") -> str:
    """ServiceNow ITSM."""
    instance = os.getenv("SERVICENOW_INSTANCE")
    token = os.getenv("SERVICENOW_TOKEN")
    
    if not instance or not token:
        return "Error: SERVICENOW_INSTANCE and TOKEN not set"
    
    if action == "incidents":
        return "ServiceNow: would list incidents"
    
    return "ServiceNow: configure credentials"


# Snowflake
def snowflake(action: str = "", query: str = "") -> str:
    """Snowflake data warehouse."""
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    if not account:
        return "Error: SNOWFLAKE_ACCOUNT not set"
    
    if action == "execute":
        return "Would execute query via snowflake-connector"
    
    return "Snowflake: configure credentials"


if __name__ == "__main__":
    print("Enterprise: Salesforce, HubSpot, ServiceNow, Snowflake plugins loaded.")