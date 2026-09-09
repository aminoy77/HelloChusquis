import unittest
from unittest.mock import AsyncMock, patch

from tools.new_integrations import TodoistTool


class TestTodoistWrapperFix(unittest.TestCase):
    def test_list_tasks_delegates_to_real_todoist_module(self):
        expected = {"results": [{"id": "123", "content": "Buy milk"}]}
        with patch("tools.todoist.list_tasks", new=AsyncMock(return_value=expected)) as list_tasks:
            result = TodoistTool().run("list_tasks", token="secret", project_id="42")

        self.assertTrue(result.success)
        self.assertEqual(result.output, str(expected))
        list_tasks.assert_awaited_once_with("secret", "42")

    def test_unknown_action_is_reported_as_failure(self):
        result = TodoistTool().run("not_an_action", token="secret")

        self.assertFalse(result.success)
        self.assertIn("Unknown action", result.error)


if __name__ == "__main__":
    unittest.main()
