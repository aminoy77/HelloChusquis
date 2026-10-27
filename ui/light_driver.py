"""Light input driver: fixes Textual's 100% CPU spin when stdin hits EOF.

Textual's LinuxDriver.run_input_thread() keeps calling select() after an
empty read (EOF). At EOF the fd is always "readable", so the loop spins at
~100% CPU forever. This happens whenever the app is launched with stdin
detached or piped (launchers, `open`, background jobs). Upstream 8.2.8
still has the bug, so we subclass and stop the loop on EOF instead.

Activated via TEXTUAL_DRIVER env var in ui.tui.run_tui().
"""
from __future__ import annotations

import os
import selectors
from codecs import getincrementaldecoder

from textual._loop import loop_last
from textual._xterm_parser import XTermParser
from textual.drivers.linux_driver import LinuxDriver


class LightInputDriver(LinuxDriver):
    """LinuxDriver that exits its input loop on stdin EOF instead of spinning."""

    def run_input_thread(self) -> None:
        """Wait for input and dispatch events; stop cleanly at EOF."""
        selector = selectors.SelectSelector()
        selector.register(self.fileno, selectors.EVENT_READ)

        fileno = self.fileno
        EVENT_READ = selectors.EVENT_READ

        parser = XTermParser(self._debug)
        feed = parser.feed
        tick = parser.tick

        utf8_decoder = getincrementaldecoder("utf-8")().decode
        decode = utf8_decoder
        read = os.read

        def process_selector_events(
            selector_events: list[tuple[selectors.SelectorKey, int]],
            final: bool = False,
        ) -> bool:
            """Process events from the selector.

            Returns False when stdin reached EOF (input thread must stop).
            """
            for last, (_selector_key, mask) in loop_last(selector_events):
                if mask & EVENT_READ:
                    unicode_data = decode(read(fileno, 1024 * 4), final=final and last)
                    if not unicode_data:
                        # EOF: stdin is closed/piped. Reading again would spin
                        # forever (EOF fds are always "readable"). Stop here.
                        return False
                    for event in feed(unicode_data):
                        self.process_message(event)
            for event in tick():
                self.process_message(event)
            return True

        try:
            while not self.exit_event.is_set():
                if not process_selector_events(selector.select(0.1)):
                    break
            selector.unregister(self.fileno)
            process_selector_events(selector.select(0.1), final=True)

        finally:
            selector.close()
            try:
                for event in feed(""):
                    pass
            except (EOFError, ParseError):
                pass
