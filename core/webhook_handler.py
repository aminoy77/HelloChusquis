from __future__ import annotations
import json
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Awaitable
from datetime import datetime


@dataclass
class WebhookEvent:
    id: str
    source: str
    event_type: str
    payload: dict
    received_at: str
    processed: bool = False


class WebhookHandler:
    """Handle incoming webhooks and events."""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._events: list[WebhookEvent] = []
        self._filters: dict[str, Callable] = {}

    def register(self, event_type: str, handler: Callable[[dict], Awaitable[None]]):
        """Register a handler for an event type."""
        self._handlers[event_type] = handler

    def add_filter(self, event_type: str, filter_fn: Callable[[dict], bool]):
        """Add a filter for an event type."""
        self._filters[event_type] = filter_fn

    async def handle(self, event_type: str, payload: dict, source: str = "unknown") -> WebhookEvent:
        """Handle an incoming webhook event."""
        event = WebhookEvent(
            id=f"{datetime.now().timestamp()}",
            source=source,
            event_type=event_type,
            payload=payload,
            received_at=datetime.now().isoformat()
        )

        # Apply filter if exists
        if event_type in self._filters:
            if not self._filters[event_type](payload):
                return event

        # Process handler if exists
        if event_type in self._handlers:
            try:
                await self._handlers[event_type](payload)
                event.processed = True
            except Exception as e:
                event.error = str(e)

        self._events.append(event)
        return event

    def get_events(self, event_type: str = None, limit: int = 50) -> list[WebhookEvent]:
        """Get recent events."""
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear_events(self):
        """Clear event history."""
        self._events.clear()


# Built-in handlers for common events
async def handle_github_push(payload: dict):
    """Handle GitHub push events."""
    commits = payload.get("commits", [])
    print(f"Received push with {len(commits)} commits")

async def handle_github_pr(payload: dict):
    """Handle GitHub pull request events."""
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    print(f"PR action: {action}, title: {pr.get('title')}")

async def handle_slack_event(payload: dict):
    """Handle Slack events."""
    event = payload.get("event", {})
    print(f"Slack event: {event.get('type')}")

async def handle_stripe_event(payload: dict):
    """Handle Stripe webhook events."""
    event_type = payload.get("type")
    data = payload.get("data", {}).get("object", {})
    print(f"Stripe event: {event_type}")


# Webhook verification helpers
def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    import hmac
    expected = hmac.new(secret.encode(), payload, "sha256").hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

def verify_slack_request(token: str, verification_token: str) -> bool:
    """Verify Slack request token."""
    return token == verification_token


def create_webhook_response(message: str, response_type: str = "text") -> dict:
    """Create a webhook response."""
    return {"response_type": response_type, "text": message}


# Event bus for internal events
class EventBus:
    """Simple event bus for agent events."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        """Subscribe to an event."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def publish(self, event: str, data: any = None):
        """Publish an event to all subscribers."""
        for callback in self._subscribers.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Event handler error: {e}")


def get_webhook_handler() -> WebhookHandler:
    return WebhookHandler()


def get_event_bus() -> EventBus:
    return EventBus()