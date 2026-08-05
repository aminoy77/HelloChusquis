import sys

file_path = 'core/agent.py'

# The new _dispatch_tool method
new_dispatch_tool = """    def _dispatch_tool(self, name: str, args: dict) -> ToolResult:
        if name == "shell":
            cmd = args.get("command", "")
            unsafe_mode = os.getenv("HELLOCHUSQUIS_UNSAFE_MODE") == "1"
            profile = os.getenv("HELLOCHUSQUIS_PROFILE", "default")
            if not unsafe_mode and profile != "aggressive":
                safety_check = evaluate_command_safety(cmd, self.pool)
                if not safety_check.get("safe", True):
                    risk_msg = safety_check.get("reason", "Potentially unsafe command detected.")
                    logger.warning("Blocked unsafe command: %s — %s", cmd, risk_msg)
                    console.print(f"[bold red]⛔ Blocked unsafe command:[/bold red] {cmd}")
                    console.print(f"[dim]{risk_msg}[/dim]")
                    return ToolResult(success=False, output="", error=f"Safety check failed: {risk_msg}")
            return self.shell.run(**args)

        if name == "code":
            return self.code.run(**args)

        if name == "web_search":
            return self.websearch.run(**args)

        if name == "files":
            path = args.get("path", "")
            if not self.workspace.is_allowed(path):
                granted = self.workspace.request_access(path)
                if not granted:
                    return ToolResult(success=False, output="", error="Access denied by user")
                self.files.allow_dir(path)
            return self.files.run(**args)

        if name == "browser":
            try:
                action = args.get("action", "")
                if not action:
                    return ToolResult(success=False, output="", error="Action required for browser tool")

                from tools.browser import (
                    browser_open, browser_click, browser_double_click, browser_right_click,
                    browser_type, browser_scroll, browser_screenshot, browser_get_text,
                    browser_search, browser_find, browser_wait_for_element,
                    browser_execute_script, browser_get_url, browser_get_title,
                    browser_go_back, browser_go_forward, browser_reload,
                    browser_press_key, browser_scroll_to_element,
                    browser_open_new_tab, browser_switch_to_page,
                    browser_fill_form, browser_submit_form, browser_hover,
                    browser_get_visible_text, browser_get_cookies, browser_health,
                )

                action_map = {
                    "navigate": lambda: browser_open(args.get("url", "")),
                    "click": lambda: browser_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                        index=args.get("index", 0),
                    ),
                    "double_click": lambda: browser_double_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "right_click": lambda: browser_right_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "type": lambda: browser_type(
                        text=args.get("text", ""),
                        selector=args.get("selector"),
                        clear_first=args.get("clear_first", True),
                    ),
                    "scroll": lambda: browser_scroll(
                        direction=args.get("direction", "down"),
                        amount=args.get("amount", 3),
                    ),
                    "scroll_to_bottom": lambda: browser_scroll_to_element("body"),
                    "scroll_to_top": lambda: browser_scroll_to_element("header"),
                    "screenshot": lambda: browser_screenshot(
                        path=args.get("path"),
                        full_page=args.get("full_page", False),
                    ),
                    "get_text": lambda: browser_get_text(selector=args.get("selector")),
                    "get_visible_text": lambda: browser_get_visible_text(),
                    "search": lambda: browser_search(
                        query=args.get("query", args.get("text", "")),
                        engine=args.get("engine", "google"),
                    ),
                    "find": lambda: browser_find(pattern=args.get("pattern", args.get("text", ""))),
                    "wait_for_element": lambda: browser_wait_for_element(
                        selector=args.get("selector", ""),
                        timeout=args.get("timeout", 30),
                    ),
                    "hover": lambda: browser_hover(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "fill_form": lambda: browser_fill_form(form_data=args.get("form_data", {})),
                    "submit_form": lambda: browser_submit_form(selector=args.get("selector", "form")),
                    "execute_script": lambda: browser_execute_script(script=args.get("script", "")),
                    "press_key": lambda: browser_press_key(key=args.get("key", "")),
                    "go_back": lambda: browser_go_back(),
                    "go_forward": lambda: browser_go_forward(),
                    "reload": lambda: browser_reload(),
                    "get_url": lambda: browser_get_url(),
                    "get_title": lambda: browser_get_title(),
                    "get_cookies": lambda: browser_get_cookies(),
                    "open_new_tab": lambda: browser_open_new_tab(url=args.get("url")),
                    "switch_to_page": lambda: browser_switch_to_page(index=args.get("index", 0)),
                    "close_current_tab": lambda: browser_switch_to_page(index=0),
                    "health": lambda: browser_health(),
                }

                handler = action_map.get(action)
                if not handler:
                    return ToolResult(success=False, output="", error=f"Unknown browser action: {action}")

                result = handler()
                if isinstance(result, dict):
                    output = str(result)
                    success = result.get("success", False)
                    return ToolResult(success=success, output=output)
                return ToolResult(success=True, output=str(result))

            except Exception as e:
                logger.error("Browser tool error: %s", e)
                return ToolResult(success=False, output="", error=str(e))

        if name == "web_fetch":
            return self.web_fetch.run(**args)

        if name == "speak":
            if not self.voice_manager:
                return ToolResult(success=False, output="", error="Voice/TTS not available. Check provider config.")
            try:
                text = args.get("text", "")
                if not text:
                    return ToolResult(success=False, output="", error="text parameter required for speak")
                result = self.voice_manager.synthesize(
                    text=text,
                    voice_id=args.get("voice_id"),
                    language=args.get("language", ""),
                    speed=args.get("speed", 1.0),
                    provider_id=args.get("provider"),
                    output_format=args.get("output_format", "mp3"),
                )
                if result.success:
                    return ToolResult(success=True, output=f"Audio: {result.audio_path}")
                return ToolResult(success=False, output="", error=result.error or "TTS synthesis failed")
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "media":
            action = args.get("action", "")
            try:
                if action == "image_info":
                    from core.functions_advanced import image_info
                    result = image_info(args.get("path", ""))
                elif action == "image_resize":
                    from core.functions_advanced import image_resize
                    result = image_resize(
                        args.get("path", ""),
                        args.get("width", 0),
                        args.get("height", 0),
                    )
                elif action == "image_thumbnail":
                    from core.functions_advanced import image_thumbnail
                    result = image_thumbnail(
                        args.get("path", ""),
                        args.get("size", 128),
                    )
                elif action == "pdf_extract":
                    from core.functions_advanced import pdf_info
                    result = pdf_info(args.get("path", ""))
                elif action == "qr_generate":
                    from core.functions_advanced import qr_code
                    result = qr_code(
                        args.get("text", ""),
                        args.get("output_path"),
                    )
                else:
                    return ToolResult(success=False, output="", error=f"Unknown media action: {action}")
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "mcp":
            action = args.get("action", "")
            try:
                if action == "list_servers":
                    servers = list(self.mcp_client.servers.keys())
                    return ToolResult(success=True, output=str(servers))
                elif action == "list_tools":
                    tools = self.mcp_client.list_tools(args.get("server"))
                    return ToolResult(success=True, output=str(tools))
                elif action == "call_tool":
                    server = args.get("server", "")
                    tool = args.get("tool", "")
                    arguments = args.get("arguments", {})
                    import asyncio
                    result = asyncio.get_event_loop().run_until_complete(
                        self.mcp_client.call_tool(server, tool, arguments)
                    )
                    return ToolResult(
                        success=result.get("success", False),
                        output=str(result.get("data", result.get("error", ""))),
                        error=result.get("error") if not result.get("success") else None,
                    )
                else:
                    return ToolResult(success=False, output="", error=f"Unknown MCP action: {action}")
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        # External tool modules - call run() directly from module
        if name in self._external_tool_modules:
            try:
                module = self._external_tool_modules[name]
                result = module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        for plugin in self.plugins:
            if plugin["name"] == name:
                try:
                    result_text = plugin["run"](**args)
                    return ToolResult(success=True, output=str(result_text))
                except Exception as e:
                    return ToolResult(success=False, output="", error=str(e))

        return ToolResult(success=False, output="", error=f"Unknown tool: {name}. I can create this tool for you! Run `hellochusquis build` to create it with AI.")
"""

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find the start and end of the method
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "def _dispatch_tool(self, name: str, args: dict) -> ToolResult:" in line:
        start_idx = i
    if "return ToolResult(success=False, output=\"\", error=f\"Unknown tool: {name}. I can create this tool for you! Run `hellochusquis build` to create it with AI.\")" in line:
        # We want the LAST occurrence of this return statement in the method
        end_idx = i

# If we found multiple, we need to be careful. 
# But the method ends with this return.
# Let's check if there's another def after it.
if start_idx != -1 and end_idx != -1:
    print(f"Found _dispatch_tool from {start_idx+1} to {end_idx+1}")
    lines[start_idx : end_idx+1] = [line + '\n' for line in new_dispatch_tool.split('\n')]
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print("Successfully refactored core/agent.py")
else:
    print(f"Could not find _dispatch_tool. Start: {start_idx}, End: {end_idx}")
    sys.exit(1)
