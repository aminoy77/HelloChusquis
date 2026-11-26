"""Agent browser action map must honour every action its schema advertises.

The schema in core/agent.py lists upload_file, select_option, scroll_to_bottom,
scroll_to_top and close_current_tab, but the dispatch map had no entries for
the first four and mapped close_current_tab to "switch to page 0".
"""

import inspect
import unittest

from core import agent as agent_module


def _browser_schema_actions() -> set:
    for tool in agent_module._build_tools_schema([]):
        spec = tool.get("function", tool)
        if spec.get("name") == "browser":
            return set(spec["parameters"]["properties"]["action"]["enum"])
    return set()


class TestBrowserActionMapCoverage(unittest.TestCase):
    def test_schema_actions_are_all_dispatchable(self):
        schema_actions = _browser_schema_actions()
        self.assertTrue(schema_actions, "browser tool schema not found")

        source = inspect.getsource(agent_module.Agent._dispatch_tool)
        for action in schema_actions:
            self.assertIn(f'"{action}"', source, f"action {action} missing from dispatch map")

    def test_close_current_tab_is_not_aliased_to_switch_to_page(self):
        source = inspect.getsource(agent_module.Agent._dispatch_tool)
        self.assertNotIn(
            '"close_current_tab": lambda: browser_switch_to_page(index=0)',
            source,
            "close_current_tab must close the tab, not switch to the first one",
        )


if __name__ == "__main__":
    unittest.main()
