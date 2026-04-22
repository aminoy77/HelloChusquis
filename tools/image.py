from tools.base import BaseTool, ToolResult
import httpx
import base64
import os


PLUGIN_NAME = "image"
PLUGIN_DESCRIPTION = "Analyze images with AI"

IMAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "image",
        "description": "Analyze images, extract text (OCR), describe content",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["describe", "ocr", "extract_faces", "classify"],
                    "description": "Image analysis action"
                },
                "image_path": {"type": "string", "description": "Path to image file"},
                "prompt": {"type": "string", "description": "Custom prompt for analysis"},
            },
            "required": ["action", "image_path"]
        }
    }
}


def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def run(action: str, image_path: str, prompt: str = "") -> str:
    """Analyze images."""
    if not os.path.exists(image_path):
        return f"Error: Image not found: {image_path}"
    
    # Use Vision API if available, else use external service
    vision_api = os.getenv("VISION_API_KEY")
    
    if not prompt:
        if action == "describe":
            prompt = "Describe what's in this image in detail."
        elif action == "ocr":
            prompt = "Extract all text from this image."
        elif action == "extract_faces":
            prompt = "List all faces detected in this image."
        elif action == "classify":
            prompt = "What objects or categories are in this image?"
    
    # Try using free OCR.space API for OCR
    if action == "ocr":
        try:
            with open(image_path, "rb") as f:
                files = {"file": f}
                data = {"language": "eng", "isOverlayRequired": "False"}
                resp = httpx.post(
                    "https://api.ocr.space/parse/image",
                    files=files,
                    data=data,
                    timeout=30
                )
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get("ParsedResults", [{}])[0].get("ParsedText", "")
                    return f"Extracted text:\n{text}"
                return f"Error: {resp.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # For other actions, require API key
    if not vision_api:
        return "Error: VISION_API_KEY not set. Configure for image analysis."
    
    # Use vision API with base64 image
    b64_image = encode_image(image_path)
    
    try:
        # Claude Vision or OpenAI Vision
        headers = {
            "Authorization": f"Bearer {vision_api}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_image}}
                ]
            }],
            "max_tokens": 1024
        }
        
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if resp.status_code == 200:
            result = resp.json()
            return result.get("content", [{}])[0].get("text", "")
        return f"Error: {resp.status_code} - {resp.text[:200]}"
    
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Image analysis plugin loaded.")