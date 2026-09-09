"""Security regressions for the ephemeral Python code tool."""

import os
import unittest
from unittest.mock import patch

from tools.code import CodeTool


class TestCodeToolIsolation(unittest.TestCase):
    def test_code_does_not_inherit_process_secrets(self):
        tool = CodeTool()
        environment = {**os.environ, "HELLOCHUSQUIS_TEST_SECRET": "do-not-leak"}

        with patch.dict(os.environ, environment, clear=True):
            result = tool.run("import os; print(os.getenv('HELLOCHUSQUIS_TEST_SECRET', 'missing'))")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "missing")

    def test_code_output_is_bounded(self):
        tool = CodeTool()

        result = tool.run("print('x' * 200000)")

        self.assertTrue(result.success)
        self.assertLessEqual(len(result.output), tool.MAX_OUTPUT_CHARS)
        self.assertIn("truncated", result.output)


if __name__ == "__main__":
    unittest.main()
