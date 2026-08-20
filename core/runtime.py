"""Runtime lifecycle helpers for interfaces that host a HelloChusquis agent.

The terminal client intentionally guides a first-time user through setup. HTTP
interfaces must not do that at import time: a process supervisor cannot answer
interactive prompts. ``AgentRuntime`` therefore exposes explicit readiness,
keeps the process alive before setup, and owns request-session agent instances
so that one user's conversation never becomes another user's context.
"""

from __future__ import annotations

from collections import OrderedDict
import logging
import threading
from typing import Callable, Optional

from core.agent import Agent
from core.setup import ensure_config

logger = logging.getLogger(__name__)


class AgentNotReadyError(RuntimeError):
    """Raised when an HTTP request needs an agent that is not configured."""


class AgentRuntime:
    """Own configured agents with bounded, request-session isolation.

    Each session receives a distinct agent with independent in-memory history,
    loop detection, and pending tool results. The configured number of cached
    sessions is bounded with LRU eviction so a public process cannot grow
    without limit solely through new session identifiers.
    """

    def __init__(
        self,
        config_loader: Callable[..., dict] = ensure_config,
        agent_factory: Callable[..., Agent] = Agent,
        max_sessions: int = 32,
        require_approval: bool = True,
    ) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        self._config_loader = config_loader
        self._agent_factory = agent_factory
        self._max_sessions = max_sessions
        self._require_approval = require_approval
        self._lock = threading.RLock()
        self._config: Optional[dict] = None
        self._agent: Optional[Agent] = None
        self._session_agents: OrderedDict[str, Agent] = OrderedDict()
        self._error: Optional[str] = None
        self.refresh()

    def refresh(self) -> bool:
        """Reload configuration non-interactively and invalidate old sessions."""
        with self._lock:
            stale_agents = [agent for agent in [self._agent, *self._session_agents.values()] if agent]
            self._session_agents.clear()
            self._agent = None
            try:
                config = self._config_loader(interactive=False)
                agent = self._new_agent(config)
                self._config = config
                self._agent = agent
                self._error = None
                logger.info("Agent runtime initialized")
                return True
            except Exception as exc:  # Keep HTTP service alive for recovery.
                self._config = None
                self._error = str(exc)
                logger.warning("Agent runtime is not ready: %s", exc)
                return False
            finally:
                for stale_agent in stale_agents:
                    self._dispose_agent(stale_agent)

    @property
    def is_ready(self) -> bool:
        """Whether an initialized agent is currently available."""
        with self._lock:
            return self._agent is not None

    @property
    def error(self) -> Optional[str]:
        """A non-sensitive description of the latest initialization failure."""
        with self._lock:
            return self._error

    @property
    def session_count(self) -> int:
        """Number of non-default in-memory sessions currently retained."""
        with self._lock:
            return len(self._session_agents)

    def get(self, session_id: Optional[str] = None) -> Agent:
        """Return the default or a session-isolated agent.

        The default agent is kept for backward-compatible callers that do not
        have a session concept (for example health inspection). HTTP chat
        handlers should always supply a validated session identifier.
        """
        with self._lock:
            if self._agent is None:
                detail = self._error or "No provider configuration is available."
                raise AgentNotReadyError(
                    "HelloChusquis is not configured. Run 'hellochusquis setup' and retry. "
                    f"Details: {detail}"
                )
            if not session_id:
                return self._agent

            cached = self._session_agents.pop(session_id, None)
            if cached is not None:
                self._session_agents[session_id] = cached
                return cached

            # Tests and integrations may inject a ready base agent without a
            # reloadable config. In that case retain backward compatibility.
            if self._config is None:
                return self._agent

            agent = self._new_agent(self._config, session_key=session_id)
            self._session_agents[session_id] = agent
            if len(self._session_agents) > self._max_sessions:
                evicted_session, evicted_agent = self._session_agents.popitem(last=False)
                self._dispose_agent(evicted_agent)
                logger.info("Evicted inactive agent session %s", evicted_session)
            return agent

    @staticmethod
    def _dispose_agent(agent: Agent) -> None:
        """Release optional persistent resources without making eviction fail."""
        dispose = getattr(agent, "dispose_session", None)
        if callable(dispose):
            try:
                dispose()
            except Exception as exc:
                logger.warning("Failed to dispose an evicted agent session: %s", exc)

    def _new_agent(self, config: dict, session_key: str | None = None) -> Agent:
        """Construct an agent with the runtime's approval policy and session identity."""
        return self._agent_factory(
            config,
            require_approval=self._require_approval,
            session_key=session_key,
        )

    def provider_status(self) -> list[dict]:
        """Return provider status without failing a health endpoint."""
        with self._lock:
            if self._agent is None:
                return []
            return self._agent.pool.status()

    def readiness(self) -> dict:
        """Return machine-readable readiness information for HTTP endpoints."""
        with self._lock:
            if self._agent is None:
                return {"ready": False, "error": self._error or "Agent is not configured"}
            providers = self._agent.pool.status()
            return {
                "ready": any(provider.get("status") == "ready" for provider in providers),
                "providers": providers,
            }
