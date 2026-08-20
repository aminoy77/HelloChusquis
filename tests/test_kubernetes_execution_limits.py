"""Regression tests for bounded Kubernetes command execution."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import kubernetes


class TestKubernetesExecutionLimits(unittest.TestCase):
    def test_apply_uses_timeout_and_removes_temporary_manifest(self):
        completed = SimpleNamespace(stdout="applied", stderr="")
        captured_paths: list[Path] = []

        def record_run(command, **kwargs):
            manifest_index = command.index("-f") + 1
            captured_paths.append(Path(command[manifest_index]))
            self.assertTrue(captured_paths[-1].exists())
            self.assertEqual(kwargs["timeout"], kubernetes.KUBERNETES_TIMEOUT_SECONDS)
            return completed

        with patch("tools.kubernetes.subprocess.run", side_effect=record_run):
            result = kubernetes.run("apply", yaml="apiVersion: v1\nkind: ConfigMap")

        self.assertEqual(result, "applied")
        self.assertEqual(len(captured_paths), 1)
        self.assertFalse(captured_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
