"""HelloChusquis TUI v2 — better than opencode."""
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
    Input,
    Label,
    RichLog,
    Static,
)

from rich.markup import escape
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown

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

#command-palette {
    layer: overlay;
    width: 60;
    height: auto;
    max-height: 30;
    background: #0c0c0a;
    border: tall #1e1d1a;
    padding: 1 0;
    display: none;
    dock: top;
    margin-top: 5;
    margin-left: 5;
}

#command-palette.visible {
    display: block;
}

#palette-input {
    background: #0c0c0a;
    border: none;
    color: #e8e3d8;
    margin: 0 1;
}

#palette-list {
    background: #0c0c0a;
    height: auto;
    max-height: 20;
    overflow-y: auto;
}

.palette-item {
    padding: 0 1;
    height: 1;
    color: #a09a8e;
}

.palette-item.selected {
    background: #f5a623;
    color: #050504;
}

.palette-item-description {
    color: #7e7a70;
    padding-left: 2;
    height: 1;
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
    _processing = reactive(False)

    def render(self) -> Text:
        t = Text()
        t.append(" ⬡ ", style=f"bold {AMBER}")
        t.append("hellochusquis ", style="dim")
        if self._processing:
            t.append(" ● processing", style=f"bold {AMBER}")
        else:
            t.append(f"  {self._elapsed}", style="dim")
        t.append(f"  msgs:{self._msgs}  tools:{self._tools}", style="dim")
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
        t.append(" Ctrl+P commands", style="dim")
        t.append(" · ", style="dim")
        t.append("Ctrl+S status", style="dim")
        t.append(" · ", style="dim")
        t.append("Ctrl+L clear", style="dim")
        t.append(" · ", style="dim")
        t.append("exit quit", style="dim")
        return t


class CommandPalette(Widget):
    """Command palette overlay like opencode."""
    CSS = """
    CommandPalette {
        layer: overlay;
        width: 60;
        height: auto;
        max-height: 30;
        background: #0c0c0a;
        border: tall #1e1d1a;
        padding: 1 0;
        display: none;
        dock: top;
        margin-top: 5;
        margin-left: 5;
    }
    CommandPalette.visible {
        display: block;
    }
    """
    _visible = reactive(False)
    _selected = reactive(0)
    _filter = reactive("")
    _commands = reactive(list[tuple[str, str, str]]())  # (id, title, desc)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._commands = [
            ("status", "Provider Status", "Show provider status and latency"),
            ("clear", "Clear History", "Clear conversation history"),
            ("help", "Show Help", "Display available commands"),
            ("web", "Web UI", "Launch web interface on localhost:8000"),
            ("config", "Config", "Open configuration wizard"),
            ("plan", "Plan Task", "Generate execution plan for complex task"),
            ("feedback+", "Positive Feedback", "Mark last response as helpful"),
            ("feedback-", "Negative Feedback", "Mark last response as unhelpful"),
        ]
        self._filtered = list(self._commands)

    def render(self) -> Text:
        if not self._visible:
            return Text()

        t = Text()
        t.append(" Commands\n", style=f"bold {AMBER}")
        t.append(" ──────────────────────────────────\n", style="dim")

        for i, (cmd_id, title, desc) in enumerate(self._filtered):
            if i == self._selected:
                t.append(f" ▸ {title}\n", style=f"bold {AMBER}")
                t.append(f"   {desc}\n", style="dim")
            else:
                t.append(f"   {title}\n", style="dim")

        t.append("\n ", style="dim")
        t.append("↑↓ navigate", style="dim")
        t.append(" · ", style="dim")
        t.append("enter select", style="dim")
        t.append(" · ", style="dim")
        t.append("esc close", style="dim")

        return t

    def toggle(self):
        self._visible = not self._visible
        if self._visible:
            self._selected = 0
            self._filter = ""
            self._filtered = list(self._commands)
            self.add_class("visible")
        else:
            self.remove_class("visible")

    def move_up(self):
        if self._selected > 0:
            self._selected -= 1

    def move_down(self):
        if self._selected < len(self._filtered) - 1:
            self._selected += 1

    def get_selected(self) -> Optional[str]:
        if self._visible and self._filtered:
            return self._filtered[self._selected][0]
        return None

    def filter(self, query: str):
        self._filter = query.lower()
        self._filtered = [
            (cid, title, desc)
            for cid, title, desc in self._commands
            if self._filter in title.lower() or self._filter in desc.lower()
        ]
        self._selected = 0


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
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type a message...", id="input")


class HelloChusquisTUI(App):
    """Full-screen TUI app — better than opencode."""
    CSS = TUI_CSS
    TITLE = "HelloChusquis"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+s", "status", "Status", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+k", "command_palette", "Commands", show=False),
    ]

    def __init__(self, agent=None, config=None):
        super().__init__()
        self.agent = agent
        self.config = config
        self._t0 = time.time()
        self._msg_count = 0
        self._tool_count = 0
        self._processing = False
        self._palette_open = False

    def compose(self) -> ComposeResult:
        yield TopBar(id="top-bar")
        yield MessageLog(id="messages")
        yield InputArea(id="input-area")
        yield StatusBar(id="status-bar")
        yield CommandPalette(id="command-palette")

    def on_mount(self) -> None:
        self.query_one("#input").focus()
        self._update_topbar()
        self._add_system_msg("Type a message or Ctrl+P for commands.")

    def _update_topbar(self):
        bar = self.query_one("#top-bar")
        elapsed = int(time.time() - self._t0)
        m, s = divmod(elapsed, 60)
        bar._elapsed = f"{m}m{s}s" if m else f"{s}s"
        bar._msgs = self._msg_count
        bar._tools = self._tool_count
        bar._processing = self._processing
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

    def _add_agent_md(self, text: str):
        """Render agent response as markdown."""
        log = self.query_one("#log", RichLog)
        # Write the label
        t = Text()
        t.append(" │ ", style=f"bold {GREEN}")
        t.append("agent\n", style=f"bold {GREEN}")
        log.write(t)
        # Write markdown
        md = Markdown(text)
        log.write(md)
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
        icon = "✓" if success else "✗"
        t.append(f" {icon} ", style=GREEN if success else RED)
        truncated = output.strip()[:400]
        if len(output.strip()) > 400:
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

    # ─── Command Palette ───
    def action_command_palette(self):
        palette = self.query_one("#command-palette")
        palette.toggle()
        self._palette_open = palette._visible
        if self._palette_open:
            self.query_one("#input").disabled = True
        else:
            self.query_one("#input").disabled = False
            self.query_one("#input").focus()

    def _execute_palette_command(self, cmd_id: str):
        """Execute a command from the palette."""
        palette = self.query_one("#command-palette")
        palette.toggle()
        self._palette_open = False
        self.query_one("#input").disabled = False
        self.query_one("#input").focus()

        if cmd_id == "status":
            self._add_status()
        elif cmd_id == "clear":
            self.action_clear()
        elif cmd_id == "help":
            self._add_help()
        elif cmd_id == "web":
            self._add_system_msg("Starting web interface...")
            import threading
            def run_web():
                from web.server import app
                import uvicorn
                uvicorn.run(app, host="127.0.0.1", port=8000)
            threading.Thread(target=run_web, daemon=True).start()
        elif cmd_id == "config":
            self._add_system_msg("Run 'hellochusquis config' in another terminal.")
        elif cmd_id == "plan":
            self._add_system_msg("Type /plan <task> to generate a plan.")
        elif cmd_id == "feedback+":
            self._add_system_msg("👍 Feedback noted.")
        elif cmd_id == "feedback-":
            self._add_system_msg("👎 Feedback noted.")

    # ─── Input Handling ───
    @on(Input.Submitted, "#input")
    def handle_input(self, event: Input.Submitted) -> None:
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

        self._run_message(text)

    def on_key(self, event) -> None:
        """Handle key events for palette navigation."""
        if self._palette_open:
            palette = self.query_one("#command-palette")
            if event.key == "up":
                palette.move_up()
                event.stop()
            elif event.key == "down":
                palette.move_down()
                event.stop()
            elif event.key == "enter":
                cmd_id = palette.get_selected()
                if cmd_id:
                    self._execute_palette_command(cmd_id)
                event.stop()
            elif event.key == "escape":
                palette.toggle()
                self._palette_open = False
                self.query_one("#input").disabled = False
                self.query_one("#input").focus()
                event.stop()

    # ─── Agent Execution ───
    @work(thread=True)
    def _run_message(self, text: str):
        if not self.agent:
            self.call_from_thread(self._add_error, "No agent configured.")
            return

        self.call_from_thread(self._set_processing, True)
        try:
            from main import is_complex
            if is_complex(text):
                self.call_from_thread(self._add_agent_msg, "Complex task — generating plan...")
                from core.planner import generate_plan, execute_plan
                steps = generate_plan(text, self.agent.pool)
                if steps:
                    self.call_from_thread(self._add_plan, steps, text)
                    execute_plan(steps, self.agent)
                else:
                    respuesta = self.agent.run(text)
                    self.call_from_thread(self._add_agent_md, respuesta)
            else:
                respuesta = self.agent.run(text)
                self.call_from_thread(self._add_agent_md, respuesta)
        except RuntimeError as e:
            self.call_from_thread(self._add_error, str(e))
        except Exception as e:
            self.call_from_thread(self._add_error, f"Unexpected error: {e}")
        finally:
            self.call_from_thread(self._set_processing, False)

    @work(thread=True)
    def _run_plan(self, task: str):
        if not self.agent:
            self.call_from_thread(self._add_error, "No agent configured.")
            return

        self.call_from_thread(self._set_processing, True)
        try:
            from core.planner import generate_plan, execute_plan
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
        self._update_topbar()

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
