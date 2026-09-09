"""Offline structural checks for bundled integration modules.

These checks deliberately do not authenticate, call external APIs, or execute
integration actions. They verify the minimum local contract advertised by the
agent: an importable module with a callable ``run`` entry point.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from typing import Iterable


# Kept in one place for the doctor command. The names mirror the modules that
# Agent exposes through its external-tool registry.
EXTERNAL_INTEGRATIONS = (
    "github", "slack", "discord", "docker", "notion", "aws", "twitter",
    "gmail", "jira", "postgresql", "mongodb", "google_calendar", "spotify",
    "stripe", "twilio", "sendgrid", "supabase", "vercel", "sentry",
    "pagerduty", "datadog", "intercom", "contentful", "sanity", "hubspot",
    "shopify", "mailchimp", "airtable", "plaid", "square", "cloudinary",
    "algolia", "resend", "brevo", "upstash", "clerk", "posthog",
    "launchdarkly", "calendly", "zoom", "clickup", "raycast", "bitbucket",
    "n8n", "pipedream", "retool", "workato", "make",
)


@dataclass(frozen=True)
class IntegrationContractResult:
    name: str
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def check_integration_contract(name: str) -> IntegrationContractResult:
    """Check one tool module without invoking any external service."""
    try:
        module = importlib.import_module(f"tools.{name}")
    except Exception as exc:
        return IntegrationContractResult(name, False, f"import failed: {type(exc).__name__}: {exc}")
    if not callable(getattr(module, "run", None)):
        return IntegrationContractResult(name, False, "missing callable run entry point")
    return IntegrationContractResult(name, True, "imported with callable run entry point")


def check_integration_contracts(
    names: Iterable[str] = EXTERNAL_INTEGRATIONS,
) -> list[IntegrationContractResult]:
    """Return deterministic structural results for the selected integrations."""
    return [check_integration_contract(name) for name in names]


def contract_summary(results: Iterable[IntegrationContractResult]) -> dict[str, int]:
    """Return a compact summary for CLI or health reporting."""
    result_list = list(results)
    passed = sum(result.ok for result in result_list)
    return {"total": len(result_list), "passed": passed, "failed": len(result_list) - passed}
