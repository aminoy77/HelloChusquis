from tools.base import BaseTool, ToolResult
import os


PLUGIN_NAME = "tts"
PLUGIN_DESCRIPTION = "Text-to-speech voice output"

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
            "required": ["action", "text"]
        }
    }
}


def run(action: str, text: str, voice: str = "", output_file: str = "", language: str = "en") -> str:
    """Text-to-speech output."""
    try:
        import subprocess
        import platform
        
        # Try using system TTS or a library
        if platform.system() == "Darwin":
            # macOS say command
            if output_file:
                cmd = ["say", "-o", output_file, text]
            else:
                cmd = ["say", text]
            subprocess.run(cmd, capture_output=True)
            return f"✓ Spoken: {text[:50]}..."
        
        elif platform.system() == "Linux":
            # Try espeak or festival
            try:
                cmd = ["espeak", text]
                subprocess.run(cmd, capture_output=True)
                return f"✓ Spoken: {text[:50]}..."
            except Exception:
                pass
        
        # Try gTTS (Google TTS)
        try:
            from gtts import gTTS
            tts = gTTS(text, lang=language.split("-")[0])
            
            if output_file:
                tts.save(output_file)
                return f"✓ Saved to: {output_file}"
            else:
                # Save to temp and play
                temp_file = "/tmp/hellochusquis_tts.mp3"
                tts.save(temp_file)
                # Would need to play - just save for now
                return f"✓ TTS generated: {temp_file}"
        
        except ImportError:
            return "Error: gTTS not installed. Run: pip install gtts"
        
        return "TTS not available on this system."
    
    except Exception as e:
        return f"Error: {str(e)}"


# Also add voice chat with streaming
PLUGIN_NAME2 = "voice_chat"


def voice_chat():
    """Real-time voice conversation."""
    # This would require a more complex setup with WebSocket
    # For now, return a placeholder
    return "Voice chat requires WebSocket server. Use hellochusquis web for UI."


if __name__ == "__main__":
    print("TTS plugin loaded.")