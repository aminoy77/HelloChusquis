"""HelloChusquis TUI v3 — widget-per-message, auto-scroll, live streaming."""
from __future__ import annotations

import time
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Collapsible,
    Input,
    Markdown,
    Static,
    TextArea,
)

from rich.spinner import Spinner as RichSpinner
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
    padding: 0 1 1 1;
    overflow-y: auto;
    scrollbar-size: 0 0;
}

#bottom {
    height: auto;
    dock: bottom;
}

#input-area {
    height: 4;
    background: #0c0c0a;
    border-top: tall #1e1d1a;
    padding: 0 1;
}

#input-area ChatInput {
    background: #0c0c0a;
    border: none;
    color: #e8e3d8;
    height: 3;
}

#main {
    height: 1fr;
}

#sidebar {
    width: 34;
    min-width: 28;
    background: #0c0c0a;
    border-left: tall #1e1d1a;
    padding: 0 1;
    overflow-y: auto;
    scrollbar-size: 0 0;
}

#status-bar {
    height: 1;
    background: #0c0c0a;
    color: #7e7a70;
    padding: 0 1;
}

#command-palette {
    layer: overlay;
    width: 78;
    height: auto;
    max-height: 36;
    background: #0c0c0a;
    border: tall #f5a623;
    padding: 1 2;
    display: none;
    margin-top: 4;
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
    max-height: 24;
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


class SideBar(Widget):
    """Right info rail: session stats on top, live plan below."""
    _provider = reactive("–")
    _model = reactive("–")
    _msgs = reactive(0)
    _tokens = reactive("–")
    _tools = reactive(0)
    _plan_task = reactive("")
    _plan_steps = reactive(tuple())
    _plan_done = reactive(tuple())  # booleans per step

    def render(self) -> Text:
        t = Text()
        t.append(" session\n", style=f"bold {AMBER}")
        t.append(" ───────────────\n", style="dim")
        t.append(" provider  ", style="dim")
        t.append(f"{self._provider}\n", style=f"bold {GREEN}")
        t.append(" model     ", style="dim")
        t.append(f"{self._model}\n")
        t.append(" msgs      ", style="dim")
        t.append(f"{self._msgs}\n", style="bold")
        t.append(" tokens    ", style="dim")
        t.append(f"{self._tokens}\n", style="bold")
        t.append(" tools     ", style="dim")
        t.append(f"{self._tools}\n", style="bold")
        t.append("\n plan\n", style=f"bold {AMBER}")
        t.append(" ───────────────\n", style="dim")
        if not self._plan_steps:
            t.append(" No plan yet.\n", style="dim")
            t.append(" /plan <task>\n", style="dim")
        else:
            t.append(f" {self._plan_task[:28]}\n", style=f"bold {AMBER}")
            for i, step in enumerate(self._plan_steps):
                mark = "✓" if i < len(self._plan_done) and self._plan_done[i] else "·"
                style = GREEN if mark == "✓" else "dim"
                t.append(f" {mark} {i + 1}. {step[:28]}\n", style=style)
        return t

    def set_plan(self, task: str, steps: list[str]) -> None:
        self._plan_task = task or ""
        self._plan_steps = tuple(steps or [])
        self._plan_done = tuple()

    def mark_step(self, index: int) -> None:
        done = list(self._plan_done)
        while len(done) <= index:
            done.append(False)
        done[index] = True
        self._plan_done = tuple(done)


class CommandPalette(Widget):
    """Command palette overlay: real Input + filtered list."""
    CSS = """
    CommandPalette {
        layer: overlay;
        width: 78;
        height: auto;
        max-height: 36;
        background: #0c0c0a;
        border: tall #f5a623;
        padding: 1 2;
        display: none;
        margin-top: 4;
    }
    CommandPalette.visible {
        display: block;
    }
    """
    _visible = reactive(False)
    _selected = reactive(0)
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

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type to filter commands...", id="palette-input")
        yield Static(id="palette-list")

    def render(self) -> Text:
        return Text()

    def _refresh_list(self) -> None:
        lst = self.query_one("#palette-list", Static)
        t = Text()
        for i, (cmd_id, title, desc) in enumerate(self._filtered):
            if i == self._selected:
                t.append(f" ▸ {title}\n", style=f"bold {AMBER}")
                t.append(f"   {desc}\n", style="dim")
            else:
                t.append(f"   {title}\n", style="dim")
        if not self._filtered:
            t.append(" No matching commands.\n", style="dim")
        t.append("\n ", style="dim")
        t.append("↑↓ navigate", style="dim")
        t.append(" · ", style="dim")
        t.append("enter select", style="dim")
        t.append(" · ", style="dim")
        t.append("esc close", style="dim")
        lst.update(t)

    def on_mount(self) -> None:
        self._refresh_list()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.lower()
        self._filtered = [
            (cid, title, desc)
            for cid, title, desc in self._commands
            if query in title.lower() or query in desc.lower()
        ]
        self._selected = 0
        self._refresh_list()

    def toggle(self):
        self._visible = not self._visible
        if self._visible:
            self._selected = 0
            self._filtered = list(self._commands)
            self._refresh_list()
            self.add_class("visible")
            self.query_one("#palette-input", Input).focus()
        else:
            self.remove_class("visible")

    def move_up(self):
        if self._selected > 0:
            self._selected -= 1
            self._refresh_list()

    def move_down(self):
        if self._selected < len(self._filtered) - 1:
            self._selected += 1
            self._refresh_list()

    def get_selected(self) -> Optional[str]:
        if self._visible and self._filtered:
            return self._filtered[self._selected][0]
        return None


class CircularSpinner(Widget):
    """Small circular arc spinner shown next to the agent label while streaming."""

    DEFAULT_CSS = """
    CircularSpinner {
        width: 3;
        height: 1;
        color: #5eb97e;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._frames = RichSpinner("arc", text="").frames
        self._frame = 0
        self.set_interval(0.08, self.refresh)

    def render(self):
        self._frame += 1
        return Text(self._frames[self._frame % len(self._frames)],
                    style="bold #5eb97e")


class MessageLog(VerticalScroll):
    """Scrollable message area — one widget per message, auto-scrolls."""
    CSS = """
    MessageLog {
        height: 1fr;
        background: #050504;
        padding: 0 1;
        overflow-y: auto;
        scrollbar-size: 0 0;
    }
    """

    def add(self, widget: Widget) -> None:
        self.mount(widget)
        self.scroll_end(animate=False)


class ChatInput(TextArea):
    """Multiline chat box: wraps + scrolls, Enter sends, Shift+Enter newline."""
    # NOTE: Binding alone can't beat TextArea._on_key (it stop()s Enter),
    # so Enter is intercepted in _on_key below.

    def __init__(self, **kwargs):
        super().__init__(
            "",
            show_line_numbers=False,
            soft_wrap=True,
            placeholder="Type a message...  (Enter send · Shift+Enter newline · Ctrl+P commands)",
            **kwargs,
        )

    async def _on_key(self, event) -> None:
        if event.key == "enter":
            event.stop()
            event.prevent_default()
            submit = getattr(self.app, "submit_chat_text", None)
            if callable(submit):
                submit(self.text)
            return
        if event.key == "shift+enter":
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return
        await super()._on_key(event)


class InputArea(Widget):
    """Bottom input area — bigger box."""
    CSS = """
    InputArea {
        height: 4;
        background: #0c0c0a;
        border-top: tall #1e1d1a;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield ChatInput(id="input")


class HelloChusquisTUI(App):
    """Full-screen TUI app."""
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
        yield CommandPalette(id="command-palette")
        with Horizontal(id="main"):
            yield MessageLog(id="messages")
            yield SideBar(id="sidebar")
        with Vertical(id="bottom"):
            yield InputArea(id="input-area")
            yield StatusBar(id="status-bar")

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
        provider, model, tokens = "", "", "–"
        if self.agent:
            try:
                statuses = self.agent.pool.status()
                active = next((s for s in statuses if s["status"] == "ready"), None) or (statuses[0] if statuses else None)
                if active:
                    provider, model = active["name"], active["model"]
                    bar._provider = f"{provider} · {model}"
            except Exception:
                pass
            try:
                n = self.agent.history.get_token_count(self.agent.history.messages)
                tokens = f"{n / 1000:.1f}k" if n >= 1000 else str(n)
            except Exception:
                pass
        try:
            side = self.query_one("#sidebar", SideBar)
            side._provider = provider or "–"
            side._model = model or "–"
            side._msgs = self._msg_count
            side._tokens = tokens
            side._tools = self._tool_count
        except Exception:
            pass

    # ─── Message widgets ───
    def _label(self, name: str, color: str) -> Text:
        t = Text()
        t.append(" │ ", style=f"bold {color}")
        t.append(f"{name}\n", style=f"bold {color}")
        return t

    def _add_user_msg(self, text: str):
        self.query_one("#messages", MessageLog).add(
            Static(self._label("you", AMBER) + Text(text)))
        self._msg_count += 1
        self._update_topbar()

    def _add_agent_msg(self, text: str):
        self.query_one("#messages", MessageLog).add(
            Static(self._label("agent", GREEN) + Text(text)))
        self._msg_count += 1
        self._update_topbar()

    def _add_agent_md(self, text: str):
        log = self.query_one("#messages", MessageLog)
        log.add(Static(self._label("agent", GREEN)))
        log.add(Markdown(text))
        self._msg_count += 1
        self._update_topbar()

    def _add_tool_msg(self, tool: str, params: str):
        t = Text()
        t.append(" │ ", style="dim")
        t.append(f"{tool} ", style=f"bold {BLUE}")
        t.append(params, style="dim")
        self.query_one("#messages", MessageLog).add(Static(t))
        self._tool_count += 1
        self._update_topbar()

    def _add_tool_result(self, tool: str, success: bool, output: str):
        t = Text()
        t.append(" │ ", style="dim")
        t.append(f" {'✓' if success else '✗'} ", style=GREEN if success else RED)
        truncated = output.strip()[:400]
        if len(output.strip()) > 400:
            truncated += "..."
        t.append(truncated, style="dim")
        self.query_one("#messages", MessageLog).add(Static(t))

    def _add_system_msg(self, text: str):
        self.query_one("#messages", MessageLog).add(
            Static(Text(f" {text}", style="dim")))

    def _add_error(self, text: str):
        t = Text()
        t.append(" │ ", style=f"bold {RED}")
        t.append("error ", style=f"bold {RED}")
        t.append(text, style=RED)
        self.query_one("#messages", MessageLog).add(Static(t))

    def _add_help(self):
        t = Text()
        t.append(" Commands\n", style=f"bold {AMBER}")
        t.append(" │ /help      Show this help\n", style="dim")
        t.append(" │ /status    Provider status\n", style="dim")
        t.append(" │ /clear     Clear history\n", style="dim")
        t.append(" │ /plan      Force plan: /plan <task>\n", style="dim")
        t.append(" │ remember … Save a fact: remember my editor is vim\n", style="dim")
        t.append(" │ forget …   Drop memories matching a key\n", style="dim")
        t.append(" │ exit       Exit\n", style="dim")
        self.query_one("#messages", MessageLog).add(Static(t))

    def _add_status(self):
        if not self.agent:
            self._add_error("No agent configured.")
            return
        t = Text()
        t.append(" Provider Status\n", style=f"bold {AMBER}")
        try:
            statuses = self.agent.pool.status()
            for p in statuses:
                color = GREEN if p["status"] == "ready" else RED
                t.append(" │ ● ", style=color)
                t.append(f"{p['name']}", style="bold")
                t.append(f" — {p['model']}", style="dim")
                if p.get("avg_ms"):
                    t.append(f"  {p['avg_ms']}ms · {p.get('calls', 0)} calls", style="dim")
                t.append("\n")
        except Exception as e:
            t.append(f" │ Error: {e}\n", style=RED)
        self.query_one("#messages", MessageLog).add(Static(t))

    def _add_plan(self, steps: list[str], task: str):
        try:
            self.query_one("#sidebar", SideBar).set_plan(task, steps)
        except Exception:
            pass
        t = Text()
        t.append(" │ plan ", style=f"bold {AMBER}")
        t.append(f"{task} → sidebar ({len(steps)} steps)", style="dim")
        self.query_one("#messages", MessageLog).add(Static(t))
        self._msg_count += 1
        self._update_topbar()

    def _mark_plan_step(self, index: int):
        try:
            self.query_one("#sidebar", SideBar).mark_step(index)
        except Exception:
            pass

    # ─── Command Palette ───
    def action_command_palette(self):
        palette = self.query_one("#command-palette")
        palette.toggle()
        self._palette_open = palette._visible
        if not self._palette_open:
            self.query_one("#input").focus()

    def _close_palette(self):
        palette = self.query_one("#command-palette")
        if palette._visible:
            palette.toggle()
        self._palette_open = False
        self.query_one("#input").disabled = False
        self.query_one("#input").focus()

    def _execute_palette_command(self, cmd_id: str):
        self._close_palette()

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

    # ─── Input Handling (Enter sends, Shift+Enter newline via ChatInput) ───
    def submit_chat_text(self, raw: str) -> None:
        text = (raw or "").strip()
        try:
            self.query_one("#input", ChatInput).clear()
        except Exception:
            pass

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
                self._close_palette()
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
                self._run_plan_task(text)
                return
            # Streaming path: spinner → gray thinking box → live answer text.
            self.call_from_thread(self._start_stream_ui)
            full: list[str] = []
            think: list[str] = []
            last_flush = [time.time()]

            def flush(force=False):
                now = time.time()
                if force or now - last_flush[0] > 0.1:
                    last_flush[0] = now
                    self.call_from_thread(self._stream_set_text, "".join(full))

            for ev in self.agent.stream_run(text):
                etype = ev.get("type")
                if etype == "reasoning":
                    think.append(ev["content"])
                    self.call_from_thread(self._stream_set_thinking, "".join(think))
                elif etype == "chunk":
                    full.append(ev["content"])
                    flush()
                elif etype == "tool_call":
                    flush(force=True)
                    self.call_from_thread(self._add_tool_msg,
                                          ev.get("tool", "?"), str(ev.get("args", {})))
                elif etype == "tool_result":
                    self.call_from_thread(self._add_tool_result,
                                          ev.get("tool", "?"),
                                          ev.get("success", False),
                                          ev.get("output", ""))
            flush(force=True)
            self.call_from_thread(self._finish_stream_ui, "".join(full))
        except RuntimeError as e:
            self.call_from_thread(self._stream_cleanup)
            self.call_from_thread(self._add_error, str(e))
        except Exception as e:
            self.call_from_thread(self._stream_cleanup)
            self.call_from_thread(self._add_error, f"Unexpected error: {e}")
        finally:
            self.call_from_thread(self._set_processing, False)

    def _run_plan_task(self, task: str):
        """Shared plan path: generate + execute with visible progress."""
        self.call_from_thread(self._add_agent_msg, "Complex task — generating plan...")
        from core.planner import generate_plan, execute_plan
        # Spinner row stays up through plan generation + execution:
        # this path has no streaming, so without it the UI looks dead.
        self.call_from_thread(self._start_stream_ui)
        steps = generate_plan(task, self.agent.pool)
        if steps:
            self.call_from_thread(self._add_plan, steps, task)
            step_idx = [0]

            def notify(msg: str):
                # "Step N/M:" lines mark step completion in the sidebar.
                if msg.startswith("Step "):
                    try:
                        n = int(msg.split()[1].split("/")[0])
                        if n > 1:
                            self.call_from_thread(self._mark_plan_step, n - 2)
                    except Exception:
                        pass
                self.call_from_thread(self._add_agent_msg, msg)

            # notify → visible in TUI (execute_plan's stdout is invisible
            # here); quiet skips stdout prints that would corrupt the screen.
            execute_plan(steps, self.agent, notify=notify, quiet=True)
            if steps:
                self.call_from_thread(self._mark_plan_step, len(steps) - 1)
        else:
            self.call_from_thread(self._add_error, "Could not generate plan.")
        self.call_from_thread(self._finish_stream_ui, "")

    @work(thread=True)
    def _run_plan(self, task: str):
        if not self.agent:
            self.call_from_thread(self._add_error, "No agent configured.")
            return

        self.call_from_thread(self._set_processing, True)
        try:
            self._run_plan_task(task)
        except Exception as e:
            self.call_from_thread(self._stream_cleanup)
            self.call_from_thread(self._add_error, f"Plan error: {e}")
        finally:
            self.call_from_thread(self._set_processing, False)

    # ─── Streaming UI helpers (run on UI thread via call_from_thread) ───
    def _start_stream_ui(self):
        label = Text()
        label.append(" │ ", style=f"bold {GREEN}")
        label.append("agent ", style=f"bold {GREEN}")
        self.query_one("#messages", MessageLog).add(Horizontal(
            Static(label, id="stream-label"),
            CircularSpinner(id="stream-spinner"),
            id="stream-row"))

    def _stream_set_thinking(self, text: str):
        log = self.query_one("#messages", MessageLog)
        box = log.query("#think-box")
        if not box:
            # Mount carries the text: querying the child in the same tick
            # races AwaitMount (child not in DOM yet).
            log.add(Collapsible(
                Static(Text(text, style="grey50"), id="think-text"),
                title="💭 Thinking", collapsed=True, id="think-box"))
            return
        log.query("#think-text").first().update(Text(text, style="grey50"))
        log.scroll_end(animate=False)

    def _stream_set_text(self, text: str):
        log = self.query_one("#messages", MessageLog)
        for spinner in log.query("#stream-spinner"):
            spinner.remove()
        body = log.query("#stream-text")
        if not body:
            log.add(Static(text, id="stream-text"))
            return
        body.first().update(text)
        log.scroll_end(animate=False)

    def _finish_stream_ui(self, full_text: str):
        log = self.query_one("#messages", MessageLog)
        for wid in ("#stream-row", "#stream-text", "#think-box"):
            for w in log.query(wid):
                w.remove()
        if full_text.strip():
            self._add_agent_md(full_text)

    def _stream_cleanup(self):
        try:
            log = self.query_one("#messages", MessageLog)
            for wid in ("#stream-row", "#stream-text", "#think-box"):
                for w in log.query(wid):
                    w.remove()
        except Exception:
            pass

    def _set_processing(self, processing: bool):
        self._processing = processing
        inp = self.query_one("#input")
        if processing:
            inp.disabled = True
            inp.placeholder = "Processing..."
        else:
            inp.disabled = False
            inp.placeholder = "Type a message...  (Enter send · Ctrl+P commands)"
            inp.focus()
        self._update_topbar()

    def action_clear(self):
        log = self.query_one("#messages", MessageLog)
        for w in list(log.children):
            w.remove()
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
