"""Text-to-speech helpers with bounded local process execution."""

import os
import platform
import subprocess
import tempfile


PLUGIN_NAME = "tts"
PLUGIN_DESCRIPTION = "Text-to-speech voice output"
TTS_PROCESS_TIMEOUT_SECONDS = 30
TTS_TEXT_MAX_CHARS = 10_000

TTS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "tts",
        "description": "Convert text to speech (TTS)",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["speak", "save"]},
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice ID"},
                "output_file": {"type": "string", "description": "Save to file"},
                "language": {"type": "string", "description": "Language code"},
            },
            "required": ["action", "text"],
        },
    },
}


def _run_local_tts(command: list[str]) -> str | None:
    """Run a system speech command with a fixed upper time limit."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TTS_PROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"TTS timed out after {TTS_PROCESS_TIMEOUT_SECONDS} seconds"
    if result.returncode != 0:
        return f"TTS failed: {(result.stderr or 'system speech command failed')[:500]}"
    return None


def _temporary_mp3_path() -> str:
    descriptor, path = tempfile.mkstemp(prefix="hellochusquis-tts-", suffix=".mp3")
    os.fchmod(descriptor, 0o600)
    os.close(descriptor)
    return path


def run(action: str, text: str, voice: str = "", output_file: str = "", language: str = "en") -> str:
    """Speak text locally or save synthesized speech to an explicit file."""
    if action not in {"speak", "save"}:
        return "Error: action must be 'speak' or 'save'."
    if not text:
        return "Error: text is required."
    if len(text) > TTS_TEXT_MAX_CHARS:
        return f"Error: text exceeds {TTS_TEXT_MAX_CHARS} characters."
    if action == "save" and not output_file:
        return "Error: output_file is required when action is 'save'."

    try:
        if platform.system() == "Darwin":
            command = ["say"]
            if voice:
                command.extend(["-v", voice])
            if action == "save":
                command.extend(["-o", output_file])
            command.append(text)
            error = _run_local_tts(command)
            if error:
                return f"Error: {error}"
            return f"✓ Saved to: {output_file}" if action == "save" else f"✓ Spoken: {text[:50]}..."

        if platform.system() == "Linux":
            command = ["espeak"]
            if voice:
                command.extend(["-v", voice])
            if action == "save":
                command.extend(["-w", output_file])
            command.append(text)
            error = _run_local_tts(command)
            if error:
                return f"Error: {error}"
            return f"✓ Saved to: {output_file}" if action == "save" else f"✓ Spoken: {text[:50]}..."

        try:
            from gtts import gTTS
        except ImportError:
            return "Error: gTTS not installed. Run: pip install gtts"
        destination = output_file if action == "save" else _temporary_mp3_path()
        gTTS(text, lang=language.split("-", 1)[0]).save(destination)
        return f"✓ Saved to: {destination}" if action == "save" else f"✓ TTS generated: {destination}"
    except OSError as exc:
        return f"Error: TTS execution failed: {exc}"
    except ValueError as exc:
        return f"Error: invalid TTS input: {exc}"


PLUGIN_NAME2 = "voice_chat"


def voice_chat() -> str:
    """Describe the currently available voice-chat entry point."""
    return "Voice chat requires WebSocket server. Use hellochusquis web for UI."


if __name__ == "__main__":
    print("TTS plugin loaded.")
