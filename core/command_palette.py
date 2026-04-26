"""
Command Palette for HelloChusquis Terminal
Press Ctrl+P to open
"""

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
import readline
import sys
import os

console = Console()


class CommandPalette:
    """Interactive command palette for terminal."""

    def __init__(self, agent=None):
        self.agent = agent
        self.selected_index = 0
        self.filter = ""
        self.commands = self._get_commands()

    def _get_commands(self):
        """Get all available commands."""
        cmds = [
            # Session
            {"section": "Session", "icon": "💬", "title": "New Chat", "desc": "Start new conversation", "action": self._new_chat},
            {"section": "Session", "icon": "🗑️", "title": "Clear History", "desc": "Clear chat history", "action": self._clear_history},
            {"section": "Session", "icon": "💾", "title": "Show History", "desc": "View recent messages", "action": self._show_history},
            
            # Models
            {"section": "Models", "icon": "🤖", "title": "GPT-4o", "desc": "OpenAI GPT-4o", "action": lambda: self._set_model("openai", "gpt-4o")},
            {"section": "Models", "icon": "🤖", "title": "GPT-4o Mini", "desc": "OpenAI GPT-4o Mini", "action": lambda: self._set_model("openai", "gpt-4o-mini")},
            {"section": "Models", "icon": "🤖", "title": "Claude 3.5 Sonnet", "desc": "Anthropic Claude 3.5", "action": lambda: self._set_model("anthropic", "claude-3-5-sonnet")},
            {"section": "Models", "icon": "🤖", "title": "Claude 3.5 Haiku", "desc": "Anthropic Claude 3.5 Haiku", "action": lambda: self._set_model("anthropic", "claude-3-5-haiku")},
            {"section": "Models", "icon": "🤖", "title": "Gemini 2.0 Flash", "desc": "Google Gemini 2.0 Flash", "action": lambda: self._set_model("google", "gemini-2.0-flash")},
            {"section": "Models", "icon": "🤖", "title": "Ollama (Local)", "desc": "Local Ollama model", "action": lambda: self._set_model("ollama", "llama3")},
            
            # Tools
            {"section": "Tools", "icon": "🌐", "title": "Browser", "desc": "Open browser automation", "action": self._open_browser},
            {"section": "Tools", "icon": "📁", "title": "Plugins", "desc": "Manage plugins", "action": self._manage_plugins},
            {"section": "Tools", "icon": "🔍", "title": "Scan Security", "desc": "Scan for secrets", "action": self._security_scan},
            
            # Settings
            {"section": "Settings", "icon": "📝", "title": "System Prompt", "desc": "Edit system prompt", "action": self._edit_prompt},
            {"section": "Settings", "icon": "🔑", "title": "Manage API Keys", "desc": "Add/remove keys", "action": self._manage_keys},
            {"section": "Settings", "icon": "⚙️", "title": "Reconfigure", "desc": "Run setup wizard", "action": self._reconfigure},
        ]
        
        # Add models from configured providers
        if self.agent and hasattr(self.agent, 'pool'):
            try:
                for provider in self.agent.pool.providers:
                    provider_name = provider.get('name', '')
                    base_url = provider.get('base_url', '')
                    
                    # Determine models based on provider
                    models = []
                    if 'openai' in base_url.lower() or 'azure' in base_url.lower():
                        models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
                    elif 'anthropic' in base_url.lower():
                        models = ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"]
                    elif 'google' in base_url.lower() or 'gemini' in base_url.lower():
                        models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
                    elif 'ollama' in base_url.lower():
                        models = ["llama3", "llama3.1", "mistral", "codellama"]
                    elif 'openrouter' in base_url.lower():
                        models = ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash"]
                    
                    for model in models:
                        # Avoid duplicates
                        exists = any(c["title"] == model for c in cmds)
                        if not exists:
                            cmds.append({
                                "section": f"Models/{provider_name}",
                                "icon": "🤖",
                                "title": model,
                                "desc": f"{model} via {provider_name}",
                                "action": lambda m=model, p=provider_name: self._set_model(p, m)
                            })
            except:
                pass
        
        return cmds

    def _filter_commands(self):
        """Filter commands based on search query."""
        if not self.filter:
            return self.commands
        query = self.filter.lower()
        return [c for c in self.commands if 
                query in c["title"].lower() or 
                query in c["desc"].lower() or 
                query in c.get("section", "").lower()]

    def _new_chat(self):
        console.print("[green]✓ Starting new chat...[/green]")
        if self.agent:
            self.agent.history.clear()

    def _clear_history(self):
        console.print("[yellow]Clearing history...[/yellow]")
        if self.agent:
            self.agent.history.clear()

    def _show_history(self):
        if self.agent:
            msgs = self.agent.history.get()
            console.print(f"[dim]Messages in history: {len(msgs)}[/dim]")

    def _set_model(self, provider, model):
        if self.agent and hasattr(self.agent, 'pool'):
            self.agent.pool.set_default_provider(provider)
            console.print(f"[green]✓ Model set to {model} ({provider})[/green]")

    def _open_browser(self):
        console.print("[cyan]Opening browser...[/cyan]")
        console.print("Use: browse open https://example.com")

    def _manage_plugins(self):
        console.print("[cyan]Plugins: hellochusquis plugins[/cyan]")

    def _security_scan(self):
        console.print("[cyan]Running security scan...[/cyan]")

    def _edit_prompt(self):
        console.print("[cyan]Edit system prompt in config.yaml[/cyan]")

    def _manage_keys(self):
        console.print("[cyan]API keys managed in config.yaml[/cyan]")

    def _reconfigure(self):
        console.print("[cyan]Run: hellochusquis (without config)[/cyan]")

    def run(self):
        """Run the command palette."""
        filtered = self._filter_commands()
        
        while True:
            # Clear and redraw
            console.clear()
            
            # Header
            console.print("\n[bold #f5a623]┌─ Command Palette ──────────────────────────[/bold #f5a623]")
            
            # Search input
            console.print(f"[dim]│ [/dim]Filter: [bold]{self.filter}[/bold]")
            
            # Commands
            current_section = None
            for i, cmd in enumerate(filtered):
                if cmd["section"] != current_section:
                    current_section = cmd["section"]
                    console.print(f"[dim]│──────────────────────────────────────────────[/dim]")
                
                marker = "▶ " if i == self.selected_index else "  "
                icon = cmd["icon"]
                title = cmd["title"]
                desc = cmd["desc"]
                
                if i == self.selected_index:
                    console.print(f"[bold #f5a623]│{marker}{icon} {title}[/bold #f5a623] [dim]- {desc}[/dim]")
                else:
                    console.print(f"│{marker}{icon} {title} [dim]- {desc}[/dim]")
            
            # Footer
            console.print("[dim]└──────────────────────────────────────────────[/dim]")
            console.print("[dim]↑↓ Navigate · Enter Select · Esc Exit[/dim]\n")
            
            # Read key
            key = console.input("")
            
            if key == "\x1b":  # Escape
                return None
            elif key == "\n" or key == "\r":  # Enter
                if filtered:
                    cmd = filtered[self.selected_index]
                    console.print()
                    cmd["action"]()
                    return None
            elif key == "\x1b[A":  # Up arrow
                self.selected_index = max(0, self.selected_index - 1)
            elif key == "\x1b[B":  # Down arrow
                self.selected_index = min(len(filtered) - 1, self.selected_index + 1)
            elif key == "\x7f" or key == "\x08":  # Backspace
                self.filter = self.filter[:-1]
                self.selected_index = 0
            elif len(key) == 1 and key.isprintable():
                self.filter += key
                self.selected_index = 0
            
            filtered = self._filter_commands()


def open_palette(agent=None):
    """Open the command palette."""
    try:
        palette = CommandPalette(agent)
        palette.run()
    except KeyboardInterrupt:
        pass


def setup_readline():
    """Setup readline for better input handling."""
    readline.parse_and_bind('set editing-mode vi')
    readline.parse_and_bind('set show-all-if-ambiguous on')
    readline.parse_and_bind('set completion-ignore-case on')


if __name__ == "__main__":
    open_palette()