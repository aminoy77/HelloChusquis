import json
import core.memory as memory
import core.learning as learning
from core.provider import ProviderPool
from core.history import History
from tools.shell import ShellTool
from tools.files import FilesTool
from tools.code import CodeTool
from tools.base import ToolResult
from workspace.manager import WorkspaceManager
from core.plugins import load_plugins
from ui.terminal import print_tool_call, print_tool_result


def _build_tools_schema(plugins: list) -> list:
    """Construye el schema de tools cada vez — evita duplicados en TOOLS_SCHEMA global."""
    schema = [
        {
            "type": "function",
            "function": {
                "name": "shell",
                "description": "Execute a terminal command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command to run"}
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "code",
                "description": "Execute Python code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "files",
                "description": "Read, write, delete, list files in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "delete", "list", "create_dir"]
                        },
                        "path": {"type": "string"},
                        "content": {"type": "string", "description": "Required for write"}
                    },
                    "required": ["action", "path"]
                }
            }
        }
    ]
    for plugin in plugins:
        schema.append(plugin["schema"])
    return schema


class Agent:
    def __init__(self, config: dict):
        self.pool = ProviderPool()
        self.history = History()
        self.workspace = WorkspaceManager(config["settings"]["workspace_dirs"])
        self.shell = ShellTool()
        self.files = FilesTool(config["settings"]["workspace_dirs"])
        self.code = CodeTool()
        self.system_prompt = config["agent"]["system_prompt"]
        self.workspace_dirs = config["settings"]["workspace_dirs"]

        # Memoria
        summary = memory.load_summary()
        if summary:
            self.system_prompt += f"\n\nWhat you remember from past sessions:\n{summary}"

        # Learnings
        learnings = learning.load_learnings()
        learning_prompt = learning.build_learning_prompt(learnings)
        if learning_prompt:
            self.system_prompt += f"\n\n{learning_prompt}"

        # Plugins — schema se construye una vez aquí, no se modifica una lista global
        self.plugins = load_plugins()
        self.tools_schema = _build_tools_schema(self.plugins)

        if self.plugins:
            plugin_names = ", ".join(p["name"] for p in self.plugins)
            self.system_prompt += (
                f"\n\nInstalled plugins available as tools: {plugin_names}. "
                "Use them directly without asking the user to install anything."
            )

    def _dispatch_tool(self, name: str, args: dict) -> ToolResult:
        if name == "shell":
            return self.shell.run(**args)

        if name == "code":
            return self.code.run(**args)

        if name == "files":
            path = args.get("path", "")
            if not self.workspace.is_allowed(path):
                granted = self.workspace.request_access(path)
                if not granted:
                    return ToolResult(success=False, output="", error="Access denied by user")
                self.files.allow_dir(path)
            return self.files.run(**args)

        for plugin in self.plugins:
            if plugin["name"] == name:
                try:
                    result_text = plugin["run"](**args)
                    return ToolResult(success=True, output=str(result_text))
                except Exception as e:
                    return ToolResult(success=False, output="", error=str(e))

        return ToolResult(success=False, output="", error=f"Unknown tool: {name}")

    def _build_messages(self) -> list[dict]:
                   self.system_prompt
            + f"\n\nWorkspace directories: {', '.join(self.workspace_dirs)}. "
            "Always use absolute paths when calling file tools. "       "Only use tools when strictly necessary. "
            "Never use shell or code tools just to print or display text.\n\n"
            "You must follow this thought process for every turn:\n"
            "1. <thought>: Analyze the current state and decide the next best action.\n"
            "2. <call>: Execute the tool if needed.\n"
            "3. <verify>: Check if the tool output solves the user\'s request.\n"
        )
        return [{"role": "system", "content": system}, *self.history.get()]

    def run(self, user_input: str) -> str:
        self.history.add("user", user_input)
        messages = self._build_messages()
        messages = self.history.optimize_context(messages)

        while True:
            response = self.pool.chat_with_retry(messages, tools=self.tools_schema)
            message = response["choices"][0]["message"]

            if not message.get("tool_calls"):
                content = message.get("content") or ""
                self.history.add("assistant", content)
                return content

            messages.append(message)

            for tc in message["tool_calls"]:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])

                print_tool_call(tool_name, tool_args)
                result = self._dispatch_tool(tool_name, tool_args)
                print_tool_result(result.success, result.output)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.output if result.success else f"ERROR: {result.error}"
                })

    def summarize_and_save(self, retention_days: int = 30):
        messages = self.history.get()
        if not messages:
            return

        memory.save_session(messages)

        summary_prompt = (
            "Summarize the key facts, tasks completed, and important context "
            "from this conversation in 3-5 bullet points. Be very concise.\n\n"
            + "\n".join(f"{m['role']}: {m['content'][:200]}" for m in messages)
        )

        try:
            response = self.pool.chat_with_retry([
                {"role": "user", "content": summary_prompt}
            ])
            summary = response["choices"][0]["message"]["content"]
            memory.save_summary(summary)
        except Exception:
            pass

        learning.analyze_and_learn(messages, self.pool)
        memory.cleanup_old_sessions(retention_days)
