"""Security regressions for automated browser navigation."""

import unittest

from tools.browser import PersistentBrowser


class _State:
    url = ""
    title = ""


class _Agent:
    def __init__(self):
        self.state = _State()
        self.navigated = []

    async def navigate(self, url: str) -> bool:
        self.navigated.append(url)
        self.state.url = url
        return True


class TestBrowserNavigationSecurity(unittest.IsolatedAsyncioTestCase):
    async def test_private_and_credential_urls_are_blocked_before_navigation(self):
        browser = PersistentBrowser()
        agent = _Agent()
        browser._agent = agent

        private_result = await browser._handle_navigate("http://127.0.0.1:8080/admin")
        credential_result = await browser._handle_navigate("https://token@example.com/private")

        self.assertFalse(private_result["success"])
        self.assertFalse(credential_result["success"])
        self.assertEqual(agent.navigated, [])


if __name__ == "__main__":
    unittest.main()
