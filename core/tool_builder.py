# DEPRECATED: This module is not used. Consider removing.
from __future__ import annotations

import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table


console = Console()


def build_tool(tool_name: str = None):
    """Interactive tool builder."""
    console.print("\n[bold cyan]🔧 HelloChusquis Tool Builder[/bold cyan]\n")

    if not tool_name:
        show_available_integrations()
        tool_name = Prompt.ask("\n[cyan]Tool name[/cyan] (or 'custom' for new)", default="")
        if not tool_name:
            return

    tool_name = tool_name.lower().replace(" ", "_")

    # Check if tool already exists
    tool_file = Path(f"tools/{tool_name}.py")
    if tool_file.exists():
        console.print(f"[yellow]⚠ Tool '{tool_name}' already exists at {tool_file}[/yellow]")
        return

    console.print(f"\n[green]Creating new tool: {tool_name}[/green]\n")

    # Gather tool information
    description = Prompt.ask("[cyan]Description[/cyan]", default="")

    # API selection
    console.print("\n[cyan]API/Service:[/cyan]")
    console.print("1. REST API (generic)")
    console.print("2. Stripe")
    console.print("3. GraphQL")
    console.print("4. Custom")
    api_type = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")

    actions = []
    while True:
        action = Prompt.ask("\n[cyan]Action name[/cyan] (or 'done')", default="")
        if not action or action.lower() == "done":
            break
        actions.append(action)

    # Generate tool code
    code = generate_tool_code(tool_name, description, actions, api_type)

    # Save tool
    tool_file.write_text(code)
    console.print(f"\n[green]✓ Tool saved to {tool_file}[/green]")
    console.print(f"[dim]Run: hellochusquis to use '{tool_name}'[/dim]")


def show_available_integrations():
    """Show available integrations that can be built."""
    table = Table(title="Available Integrations")
    table.add_column("Category", style="cyan")
    table.add_column("Integrations")

    table.add_row("Payments", "Stripe, Square, Plaid, PayPal")
    table.add_row("Communication", "Twilio, SendGrid, Resend, Brevo")
    table.add_row("DevOps", "Vercel, Supabase, Sentry, Datadog, PagerDuty")
    table.add_row("CRM", "HubSpot, Salesforce, Close, Pipedrive")
    table.add_row("CMS", "Contentful, Sanity, Strapi")
    table.add_row("Marketing", "Mailchimp, ConvertKit, Klaviyo")
    table.add_row("Automation", "n8n, Pipedream, Make, Zapier")
    table.add_row("Analytics", "PostHog, Mixpanel, Amplitude")
    table.add_row("Logging", "Cloudinary, Algolia, Upstash")

    console.print(table)


def generate_tool_code(name: str, description: str, actions: list, api_type: str) -> str:
    """Generate tool code from template."""

    if api_type == "1":
        base_url = "https://api.example.com/v1"
    elif api_type == "2":
        base_url = "https://api.stripe.com/v1"
    elif api_type == "3":
        base_url = "https://api.example.com/graphql"
    else:
        base_url = "https://api.example.com/v1"

    actions_enum = ", ".join([f'"{a}"' for a in actions]) if actions else '"action"'
    actions_code = "\n".join([f'            elif action == "{a}":\n                pass' for a in actions]) or "pass"

    return f'''from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class {name.title().replace("_", "")}Tool(Tool):
    name = "{name}"
    description = "{description}"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error="{name.title()} API key not configured")

        base_url = "{base_url}"
        headers = {{"Authorization": f"Bearer {{api_key}}"}}

        try:
            if action == "list":
                r = httpx.get(f"{{base_url}}", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data)

            elif action == "get":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="ID required")
                r = httpx.get(f"{{base_url}}/{{id}}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "create":
                data = kwargs.get("data", {{}})
                if not data:
                    return ToolResult(success=False, error="Data required")
                r = httpx.post(f"{{base_url}}", headers=headers, json=data, timeout=30)
                return ToolResult(success=True, data=r.json())

            {actions_code}

            else:
                return ToolResult(success=False, error=f"Unknown action: {{action}}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def run(action: str = "list", **kwargs):
    """Entry point for the tool."""
    tool = {name.title().replace("_", "")}Tool()
    return tool.run(action, **kwargs)
'''