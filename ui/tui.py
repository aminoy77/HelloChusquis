"""HelloChusquis TUI — full-screen opencode-style interface."""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    Markdown,
    RichLog,
    Static,
)

from rich.markup import escape
from rich.text import Text

# ─── Palette ───
AMBER = "#f5a623"
GREEN = "#5eb97e"
BLUE = "#7eb8d4"
RED = "#e85d5d"
DIM = "#7e7a70"
MUTED = "#a09a8e"
SURFACE = "#0c0c0a"
BG = "#050504"
BORDER = "#1e1d1a"


# ─── CSS ───
TUI_CSS = """
Screen {
    background: #050504;
}

#top-bar {
    height: 1;
    background: #0c0c0a;
    dock: top;
    padding: 0 1;
    color: #a09a8e;
}

#messages {
    height: 1fr;
    background: #050504;
    padding: 0 1;
    overflow-y: auto;
    scrollbar-size: 0 0;
}

#messages RichLog {
    background: #050504;
}

#input-area {
    height: 3;
    dock: bottom;
    background: #0c0c0a;
    border-top: tall #1e1d1a;
    padding: 0 1;
}

#input-area Input {
    background: #0c0c0a;
    border: none;
    color: #e8e3d8;
}

#status-bar {
    height: 1;
    dock: bottom;
    background: #0c0c0a;
    color: #7e7a70;
    padding: 0 1;
}

.user-msg {
    color: #e8e3d8;
    margin: 0 0 1 0;
}

.agent-msg {
    color: #e8e3d8;
    margin: 0 0 1 0;
}

.tool-msg {
    color: #a09a8e;
    margin: 0 0 0 0;
}

.tool-result {
    color: #a09a8e;
    margin: 0 0 1 0;
}

.separator {
    color: #1e1d1a;
}
"""


class TopBar(Widget):
    """Session info bar."""
    CSS = """
    TopBar {
        height: 1;
        dock: top;
        background: #0c0c0a;
        color: #a09a8e;
        padding: 0 1;
    }
    """
    _elapsed = reactive("0s")
    _msgs = reactive(0)
    _tools = reactive(0)
    _provider = reactive("")

    def render(self) -> Text:
        t = Text()
        t.append(" ⬡ ", style=f"bold {AMBER}")
        t.append("hellochusquis ", style="dim")
        t.append(f"  {self._elapsed}  msgs:{self._msgs}  tools:{self._tools}", style="dim")
        if self._provider:
            t.append(f"  {self._provider}", style=f"bold {GREEN}")
        return t


class StatusBar(Widget):
    """Bottom status bar."""
    CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: #0c0c0a;
        color: #7e7a70;
        padding: 0 1;
    }
    """

    def render(self) -> Text:
        t = Text()
        t.append(" ↑↓ history", style="dim")
        t.append(" · ", style="dim")
        t.append("Tab autocomplete", style="dim")
        t.append(" · ", style="dim")
        t.append("/help commands", style="dim")
        t.append(" · ", style="dim")
        t.append("exit quit", style="dim")
        return t


class MessageLog(VerticalScroll):
    """Scrollable message area."""
    CSS = """
    MessageLog {
        height: 1fr;
        background: #050504;
        padding: 0 1;
        overflow-y: auto;
        scrollbar-size: 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", markup=True, wrap=True, highlight=False)


class InputArea(Widget):
    """Bottom input area."""
    CSS = """
    InputArea {
        height: 3;
        dock: bottom;
        background: #0c0c0a;
        border-top: tall #1e1d1a;
        padding: 0 1;
    }
    Input {
        background: #0c0c0a;
        border: none;
        color: #e8e3d8;
    }
    """

    def compose(self) -> ComposeResult:
        from textual.widgets import Input
        yield Input(placeholder="Type a message...", id="input", classes="input")


class HelloChusquisTUI(App):
    """Full-screen TUI app."""
    CSS = TUI_CSS
    TITLE = "HelloChusquis"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+s", "status", "Status", show=True),
    ]

    def __init__(self, agent=None, config=None):
        super().__init__()
        self.agent = agent
        self.config = config
        self._t0 = time.time()
        self._msg_count = 0
        self._tool_count = 0
        self._processing = False

    def compose(self) -> ComposeResult:
        yield TopBar(id="top-bar")
        yield MessageLog(id="messages")
        yield InputArea(id="input-area")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """Initialize on mount."""
        self.query_one("#input").focus()
        self._update_topbar()
        self._add_system_msg("Type a message or /help for commands.")

    def _update_topbar(self):
        bar = self.query_one("#top-bar")
        elapsed = int(time.time() - self._t0)
        m, s = divmod(elapsed, 60)
        bar._elapsed = f"{m}m{s}s" if m else f"{s}s"
        bar._msgs = self._msg_count
        bar._tools = self._tool_count
        if self.agent:
            try:
                statuses = self.agent.pool.status()
                active = next((s for s in statuses if s["status"] == "ready"), None)
                if active:
                    bar._provider = f"{active['name']} · {active['model']}"
            except Exception:
                pass

    def _add_user_msg(self, text: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" │ ", style=f"bold {AMBER}")
        t.append("you\n", style=f"bold {AMBER}")
        t.append(" │ ", style=f"bold {AMBER}")
        t.append(text)
        log.write(t)
        self._msg_count += 1
        self._update_topbar()

    def _add_agent_msg(self, text: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" │ ", style=f"bold {GREEN}")
        t.append("agent\n", style=f"bold {GREEN}")
        t.append(" │ ", style=f"bold {GREEN}")
        t.append(text)
        log.write(t)
        self._msg_count += 1
        self._update_topbar()

    def _add_tool_msg(self, tool: str, params: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" │ ", style="dim")
        t.append(f"{tool} ", style=f"bold {BLUE}")
        t.append(params, style="dim")
        log.write(t)
        self._tool_count += 1
        self._update_topbar()

    def _add_tool_result(self, success: bool, output: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" │ ", style="dim")
        icon = f"[{GREEN}]✓[/{GREEN}]" if success else f"[{RED}]✗[/{RED}]"
        t.append(f" ✓ ", style=GREEN if success else RED)
        truncated = output.strip()[:300]
        if len(output.strip()) > 300:
            truncated += "..."
        t.append(truncated, style="dim")
        log.write(t)

    def _add_system_msg(self, text: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(f" {text}", style="dim")
        log.write(t)

    def _add_error(self, text: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" │ ", style=f"bold {RED}")
        t.append("error ", style=f"bold {RED}")
        t.append(text, style=RED)
        log.write(t)

    def _add_help(self):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" Commands\n", style=f"bold {AMBER}")
        t.append(" │ /help      Show this help\n", style="dim")
        t.append(" │ /status    Provider status\n", style="dim")
        t.append(" │ /clear     Clear history\n", style="dim")
        t.append(" │ /plan      Force plan: /plan <task>\n", style="dim")
        t.append(" │ exit       Exit\n", style="dim")
        log.write(t)

    def _add_status(self):
        if not self.agent:
            self._add_error("No agent configured.")
            return
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(" Provider Status\n", style=f"bold {AMBER}")
        try:
            statuses = self.agent.pool.status()
            for p in statuses:
                color = GREEN if p["status"] == "ready" else RED
                icon = "●"
                t.append(f" │ {icon} ", style=color)
                t.append(f"{p['name']}", style="bold")
                t.append(f" — {p['model']}", style="dim")
                if p.get("avg_ms"):
                    t.append(f"  {p['avg_ms']}ms · {p.get('calls', 0)} calls", style="dim")
                t.append("\n")
        except Exception as e:
            t.append(f" │ Error: {e}\n", style=RED)
        log.write(t)

    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted) -> None:
        """Handle user input."""
        text = event.value.strip()
        event.control.value = ""

        if not text:
            return

        self._add_user_msg(text)

        if text in ("exit", "quit"):
            self.action_quit()
            return

        if text == "/help":
            self._add_help()
            return

        if text == "/status":
            self._add_status()
            return

        if text == "/clear":
            if self.agent:
                self.agent.history.clear()
            self._add_system_msg("History cleared.")
            return

        if text.startswith("/plan "):
            task = text[6:].strip()
            self._run_plan(task)
            return

        # Normal message
        self._run_message(text)

    @work(thread=True)
    def _run_message(self, text: str):
        """Run agent message in background thread."""
        if not self.agent:
            self.call_from_thread(self._add_error, "No agent configured.")
            return

        self.call_from_thread(self._set_processing, True)
        try:
            # Check if complex
            from main import is_complex
            if is_complex(text):
                self.call_from_thread(self._add_agent_msg, "Complex task — generating plan...")
                from core.planner import generate_plan, confirm_plan, execute_plan
                steps = generate_plan(text, self.agent.pool)
                if steps:
                    self.call_from_thread(self._add_plan, steps, text)
                    # Execute plan
                    from core.planner import execute_plan
                    execute_plan(steps, self.agent)
                else:
                    respuesta = self.agent.run(text)
                    self.call_from_thread(self._add_agent_msg, respuesta)
            else:
                respuesta = self.agent.run(text)
                self.call_from_thread(self._add_agent_msg, respuesta)
        except RuntimeError as e:
            self.call_from_thread(self._add_error, str(e))
        except Exception as e:
            self.call_from_thread(self._add_error, f"Unexpected error: {e}")
        finally:
            self.call_from_thread(self._set_processing, False)

    @work(thread=True)
    def _run_plan(self, task: str):
        """Run plan generation in background thread."""
        if not self.agent:
            self.call_from_thread(self._add_error, "No agent configured.")
            return

        self.call_from_thread(self._set_processing, True)
        try:
            from core.planner import generate_plan, confirm_plan, execute_plan
            steps = generate_plan(task, self.agent.pool)
            if steps:
                self.call_from_thread(self._add_plan, steps, task)
                execute_plan(steps, self.agent)
            else:
                self.call_from_thread(self._add_error, "Could not generate plan.")
        except Exception as e:
            self.call_from_thread(self._add_error, f"Plan error: {e}")
        finally:
            self.call_from_thread(self._set_processing, False)

    def _add_plan(self, steps: list[str], task: str):
        log = self.query_one("#log", RichLog)
        t = Text()
        t.append(f" │ plan ", style=f"bold {AMBER}")
        t.append(task, style=f"bold {AMBER}")
        t.append("\n")
        for i, step in enumerate(steps, 1):
            t.append(f" │  {i}. {step}\n", style="dim")
        log.write(t)
        self._msg_count += 1
        self._update_topbar()

    def _set_processing(self, processing: bool):
        self._processing = processing
        inp = self.query_one("#input")
        if processing:
            inp.disabled = True
            inp.placeholder = "Processing..."
        else:
            inp.disabled = False
            inp.placeholder = "Type a message..."
            inp.focus()

    def action_clear(self):
        log = self.query_one("#log", RichLog)
        log.clear()
        self._msg_count = 0
        self._tool_count = 0
        self._update_topbar()

    def action_status(self):
        self._add_status()

    def action_quit(self):
        self._cleanup()
        self.exit()

    def _cleanup(self):
        """Save session data on exit."""
        if self.agent:
            try:
                from core.learning import save_learnings
                save_learnings(self.agent.history)
            except Exception:
                pass


def run_tui(agent=None, config=None):
    """Launch the TUI."""
    app = HelloChusquisTUI(agent=agent, config=config)
    app.run()
