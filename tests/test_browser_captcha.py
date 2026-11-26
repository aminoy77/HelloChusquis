"""CAPTCHA detection: report it, never pretend to solve it."""

import asyncio

from core.browser_agent import BrowserAgent


class _FakePage:
    def __init__(self, answer):
        self.answer = answer
        self.scripts = []

    async def evaluate(self, script, arg=None):
        self.scripts.append(script)
        if callable(self.answer):
            return self.answer(script)
        return self.answer


def _agent(answer):
    agent = BrowserAgent.__new__(BrowserAgent)
    agent.page = _FakePage(answer)
    agent.config = type("C", (), {"headless": False})()
    return agent


def test_detect_captcha_returns_kind():
    agent = _agent("recaptcha")
    assert asyncio.run(agent.detect_captcha()) == "recaptcha"


def test_detect_captcha_none_when_clean():
    agent = _agent(None)
    assert asyncio.run(agent.detect_captcha()) is None


def test_detect_captcha_survives_evaluate_error():
    def boom(script):
        raise RuntimeError("execution context destroyed")

    agent = _agent(boom)
    assert asyncio.run(agent.detect_captcha()) is None


class _NavAgent:
    def __init__(self, captcha):
        self.state = type("S", (), {"url": "https://x.example/", "title": "X"})()
        self.captcha = captcha

    async def navigate(self, url):
        return True

    async def detect_captcha(self):
        return self.captcha

    async def page_report(self):
        return {"title": "X", "text": "hello"}


def test_navigate_reports_captcha_without_claiming_success():
    from tools.browser import PersistentBrowser

    pb = PersistentBrowser()
    pb._agent = _NavAgent("recaptcha")
    result = asyncio.run(pb._handle_navigate("https://x.example/"))

    assert result["captcha"] == "recaptcha"
    assert "solve it in the visible" in result["note"]


def test_navigate_stays_clean_without_captcha():
    from tools.browser import PersistentBrowser

    pb = PersistentBrowser()
    pb._agent = _NavAgent(None)
    result = asyncio.run(pb._handle_navigate("https://x.example/"))

    assert "captcha" not in result
    assert result["report"]["title"] == "X"
