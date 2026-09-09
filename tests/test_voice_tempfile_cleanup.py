"""Regression tests for cleanup of failed local voice synthesis."""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from core.voice import PiperTTS


class TestVoiceTemporaryFileCleanup(unittest.TestCase):
    def test_piper_failure_removes_temporary_output(self):
        provider = PiperTTS()
        provider._piper_bin = "piper"
        created_paths: list[Path] = []
        original_named_temporary_file = tempfile.NamedTemporaryFile

        def record_temporary_file(*args, **kwargs):
            handle = original_named_temporary_file(*args, **kwargs)
            created_paths.append(Path(handle.name))
            return handle

        completed = SimpleNamespace(returncode=1, stderr=b"synthetic failure")
        with (
            patch("core.voice.tempfile.NamedTemporaryFile", side_effect=record_temporary_file),
            patch("core.voice.subprocess.run", return_value=completed),
        ):
            result = provider.synthesize("hello", language="en")

        self.assertFalse(result.success)
        self.assertEqual(len(created_paths), 1)
        self.assertFalse(created_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
