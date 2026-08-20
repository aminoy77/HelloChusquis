import os
import subprocess

import httpx


TERRAFORM_TIMEOUT_SECONDS = 120
INFRASTRUCTURE_HTTP_TIMEOUT_SECONDS = 30


PLUGIN_NAME = "terraform"
PLUGIN_DESCRIPTION = "Infrastructure as Code with Terraform"

TERRAFORM_SCHEMA = {
    "type": "function",
    "function": {
        "name": "terraform",
        "description": "Terraform operations",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["init", "plan", "apply", "destroy", "validate", "show"]},
                "directory": {"type": "string", "description": "Terraform directory"},
                "var": {"type": "string", "description": "Variables"},
                "auto_approve": {"type": "boolean", "description": "Auto-approve"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, directory: str = "", var: str = "", auto_approve: bool = False) -> str:
    """Terraform operations."""
    cmd = ["terraform"]
    
    if action == "init":
        cmd.extend(["init"])
    elif action == "plan":
        cmd.extend(["plan"])
    elif action == "apply":
        cmd.append("apply")
        if auto_approve:
            cmd.append("-auto-approve")
    elif action == "destroy":
        cmd.append("destroy")
        if auto_approve:
            cmd.append("-auto-approve")
    elif action == "validate":
        cmd.append("validate")
    elif action == "show":
        cmd.append("show")
    else:
        return f"Unknown action: {action}"
    
    if directory:
        cwd = directory
    else:
        cwd = "."
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TERRAFORM_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Terraform timed out after {TERRAFORM_TIMEOUT_SECONDS} seconds"
    return result.stdout + result.stderr


# Cloudflare tool
PLUGIN_NAME2 = "cloudflare"


def cloudflare(action: str = "", zone: str = "", record: str = "", value: str = "", record_type: str = "A") -> str:
    """Cloudflare operations."""
    token = os.getenv("CLOUDFLARE_TOKEN")
    if not token:
        return "Error: CLOUDFLARE_TOKEN not set"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if action == "list_zones":
        resp = httpx.get(
            "https://api.cloudflare.com/client/v4/zones",
            headers=headers,
            timeout=INFRASTRUCTURE_HTTP_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
        if resp.status_code == 200:
            zones = resp.json().get("result", [])
            return "\n".join([f"• {z['name']} ({z['id']})" for z in zones[:10]])
        return f"Error: {resp.status_code}"
    
    elif action == "create_record":
        if not zone or not record or not value:
            return "Error: zone, record, value required"
        
        # Would need zone ID
        return "Error: Implementation requires zone ID lookup"


# Vercel tool
PLUGIN_NAME3 = "vercel"


def vercel(action: str = "", project: str = "", env: str = "") -> str:
    """Vercel deployment."""
    token = os.getenv("VERCEL_TOKEN")
    if not token:
        return "Error: VERCEL_TOKEN not set"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if action == "list":
        resp = httpx.get(
            "https://api.vercel.com/v6/deployments",
            headers=headers,
            timeout=INFRASTRUCTURE_HTTP_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
        if resp.status_code == 200:
            deps = resp.json().get("deployments", [])
            return "\n".join([f"• {d['name']} - {d['state']}" for d in deps[:10]])
        return f"Error: {resp.status_code}"
    
    elif action == "deploy":
        return "Use 'vercel --yes' in project directory"


# Netlify tool
PLUGIN_NAME4 = "netlify"


def netlify(action: str = "", site: str = "") -> str:
    """Netlify deployment."""
    token = os.getenv("NETLIFY_TOKEN")
    if not token:
        return "Error: NETLIFY_TOKEN not set"
    
    if action == "list":
        return "Netlify sites: use netlify CLI"


if __name__ == "__main__":
    print("Terraform, Cloudflare, Vercel, Netlify plugins loaded.")