from tools.base import BaseTool, ToolResult
import os


PLUGIN_NAME = "meeting"
PLUGIN_DESCRIPTION = "Summarize meetings, transcribe, and extract action items"

MEETING_SCHEMA = {
    "type": "function",
    "function": {
        "name": "meeting",
        "description": "Process meeting transcripts and extract insights",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summarize", "extract_actions", "extract_decisions", "extract_topics"],
                    "description": "Meeting action"
                },
                "transcript": {"type": "string", "description": "Meeting transcript text"},
                "file": {"type": "string", "description": "Path to transcript file"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, transcript: str = "", file: str = "") -> str:
    """Meeting transcription and analysis."""
    
    # Get transcript from file or direct input
    if file:
        if not os.path.exists(file):
            return f"Error: File not found: {file}"
        with open(file, "r") as f:
            transcript = f.read()
    
    if not transcript:
        return "Error: transcript or file required"
    
    # For now, use LLM to process
    # In production, would use dedicated meeting AI APIs
    
    try:
        from core.provider import ProviderPool
        pool = ProviderPool()
        
        if action == "summarize":
            prompt = f"""Summarize this meeting transcript in bullet points:

{transcript[:3000]}

Provide:
- Key topics discussed
- Main decisions made
- Any important announcements"""
        
        elif action == "extract_actions":
            prompt = f"""Extract action items from this meeting:

{transcript[:3000]}

List each action with:
- Who is responsible
- What needs to be done
- When it's due (if mentioned)"""
        
        elif action == "extract_decisions":
            prompt = f"""Extract decisions made in this meeting:

{transcript[:3000]}

List each decision clearly."""
        
        elif action == "extract_topics":
            prompt = f"""Extract key topics from this meeting:

{transcript[:3000]}

List the main topics discussed."""
        
        else:
            return f"Error: Unknown action {action}"
        
        response = pool.chat_with_retry([{"role": "user", "content": prompt}])
        choices = response.get("choices", [])
        if not choices:
            return "Error: No response from AI provider"
        return choices[0].get("message", {}).get("content", "") or ""
    
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Meeting AI plugin loaded.")