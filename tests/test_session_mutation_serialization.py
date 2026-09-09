"""HTTP regression tests for session-mutating operations during active turns."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import main as api_main
from web import server as web_server


class _SessionMutationAgent:
    def __init__(self, turn_available=True):
        self.turn_available = turn_available
        self.clear_calls = 0
        self.approval_calls = 0
        self.releases = 0

    def try_acquire_turn(self):
        if not self.turn_available:
            return False
        self.turn_available = False
        return True

    def release_turn(self):
        self.turn_available = True
        self.releases += 1

    def clear_conversation(self):
        self.clear_calls += 1
        return {"cancelled_approvals": 0}

    def decide_approval(self, _request_id, _approved):
        self.approval_calls += 1
        return {"id": "approval-id", "status": "rejected"}


class TestSessionMutationSerialization(unittest.TestCase):
    @staticmethod
    def _headers(module):
        return {
            "Authorization": f"Bearer {module.REQUIRED_API_KEY}",
            "X-HelloChusquis-Session": "session-mutation",
        }

    def test_clear_is_rejected_without_mutation_during_active_turn(self):
        for module in (api_main, web_server):
            agent = _SessionMutationAgent(turn_available=False)
            with self.subTest(module=module.__name__), patch.object(
                module, "_require_agent", return_value=agent
            ):
                response = TestClient(module.app).post("/clear", headers=self._headers(module))

            self.assertEqual(response.status_code, 409)
            self.assertEqual(agent.clear_calls, 0)
            self.assertEqual(agent.releases, 0)

    def test_rejected_approval_is_rejected_without_mutation_during_active_turn(self):
        for module in (api_main, web_server):
            agent = _SessionMutationAgent(turn_available=False)
            with self.subTest(module=module.__name__), patch.object(
                module, "_require_agent", return_value=agent
            ):
                response = TestClient(module.app).post(
                    "/approvals/approval-id",
                    json={"approve": False},
                    headers=self._headers(module),
                )

            self.assertEqual(response.status_code, 409)
            self.assertEqual(agent.approval_calls, 0)
            self.assertEqual(agent.releases, 0)

    def test_clear_owns_and_releases_turn_when_idle(self):
        for module in (api_main, web_server):
            agent = _SessionMutationAgent()
            with self.subTest(module=module.__name__), patch.object(
                module, "_require_agent", return_value=agent
            ):
                response = TestClient(module.app).post("/clear", headers=self._headers(module))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(agent.clear_calls, 1)
            self.assertEqual(agent.releases, 1)
            self.assertTrue(agent.turn_available)

    def test_web_chat_clear_is_rejected_without_mutation_during_active_turn(self):
        for path in ("/chat", "/chat/stream"):
            agent = _SessionMutationAgent(turn_available=False)
            with self.subTest(path=path), patch.object(
                web_server, "_require_agent", return_value=agent
            ):
                response = TestClient(web_server.app).post(
                    path,
                    json={"message": "/clear"},
                    headers=self._headers(web_server),
                )

            self.assertEqual(response.status_code, 409)
            self.assertEqual(agent.clear_calls, 0)
            self.assertEqual(agent.releases, 0)

    def test_web_chat_clear_owns_and_releases_turn_when_idle(self):
        agent = _SessionMutationAgent()
        with patch.object(web_server, "_require_agent", return_value=agent):
            response = TestClient(web_server.app).post(
                "/chat",
                json={"message": "/clear"},
                headers=self._headers(web_server),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(agent.clear_calls, 1)
        self.assertEqual(agent.releases, 1)
        self.assertTrue(agent.turn_available)


if __name__ == "__main__":
    unittest.main()
