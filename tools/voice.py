from tools.base import BaseTool, ToolResult
import speech_recognition as sr
import io


PLUGIN_NAME = "voice"
PLUGIN_DESCRIPTION = "Voice input and speech-to-text"

VOICE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "voice",
        "description": "Convert speech to text or record voice input",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["listen", "transcribe_file"],
                    "description": "Voice action"
                },
                "language": {"type": "string", "description": "Language code (default: en)"},
                "duration": {"type": "number", "description": "Recording duration in seconds"},
                "audio_file": {"type": "string", "description": "Path to audio file to transcribe"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, language: str = "en", duration: int = 5, audio_file: str = "") -> str:
    """Voice input and speech recognition."""
    try:
        if action == "listen":
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=duration)
            
            try:
                text = recognizer.recognize_google(audio, language=language)
                return f"Transcribed: {text}"
            except sr.UnknownValueError:
                return "Could not understand audio. Please speak more clearly."
            except sr.RequestError as e:
                return f"Error: {e}"
        
        elif action == "transcribe_file":
            if not audio_file:
                return "Error: audio_file path required"
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio, language=language)
                return f"Transcribed: {text}"
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                return f"Error: {e}"
        
        else:
            return f"Error: Unknown action {action}"
    
    except ImportError:
        return "Error: speech_recognition not installed. Run: pip install SpeechRecognition"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Voice plugin loaded. Say 'hellochusquis voice listen' to use.")