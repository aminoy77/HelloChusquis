from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from core.voice import EdgeTTS


class TestEdgeVoiceCleanup(unittest.TestCase):
    def test_library_failure_removes_temporary_output(self):
        provider = EdgeTTS()
        created_paths: list[Path] = []
        original_named_temporary_file = tempfile.NamedTemporaryFile

        def record_temporary_file(*args, **kwargs):
            handle = original_named_temporary_file(*args, **kwargs)
            created_paths.append(Path(handle.name))
            return handle

        class _Communicate:
            def __init__(self, *args, **kwargs):
                pass

            async def save(self, path):
                raise RuntimeError("synthetic edge failure")

        fake_edge_tts = SimpleNamespace(Communicate=_Communicate)
        with (
            patch("core.voice.tempfile.NamedTemporaryFile", side_effect=record_temporary_file),
            patch.dict("sys.modules", {"edge_tts": fake_edge_tts}),
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic edge failure"):
                provider._synth_with_lib("hello", "en-US-Test", "+0%", "+0Hz", "mp3", 0.0)

        self.assertEqual(len(created_paths), 1)
        self.assertFalse(created_paths[0].exists())

    def test_cli_failure_removes_temporary_output(self):
        provider = EdgeTTS()
        created_paths: list[Path] = []
        original_named_temporary_file = tempfile.NamedTemporaryFile

        def record_temporary_file(*args, **kwargs):
            handle = original_named_temporary_file(*args, **kwargs)
            created_paths.append(Path(handle.name))
            return handle

        completed = SimpleNamespace(returncode=1, stderr=b"synthetic edge failure")
        with (
            patch("core.voice.tempfile.NamedTemporaryFile", side_effect=record_temporary_file),
            patch("core.voice.subprocess.run", return_value=completed),
            patch("core.voice.shutil.which", return_value="edge-tts"),
        ):
            result = provider._synth_with_cli("hello", "en-US-Test", "+0%", "+0Hz", "mp3", 0.0)

        self.assertFalse(result.success)
        self.assertEqual(len(created_paths), 1)
        self.assertFalse(created_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
