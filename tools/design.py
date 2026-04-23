from tools.base import BaseTool, ToolResult
import httpx


class WebflowTool(BaseTool):
    name = "webflow"
    description = "Webflow - visual CMS"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Token required")
        headers = {"Authorization": token}
        try:
            if action == "list_sites":
                r = httpx.get("https://api.webflow.com/sites", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class FramerTool(BaseTool):
    name = "framer"
    description = "Framer - design tool"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(False, "", "Framer - configure at platform.framer.com")

class WebinyTool(BaseTool):
    name = "webiny"
    description = "Webiny - serverless CMS"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(False, "", "Webiny - configure at webiny.com")

class CanvaTool(BaseTool):
    name = "canva"
    description = "Canva - design tool"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(False, "", "Canva - configure at canva.com")

class FigmaTool(BaseTool):
    name = "figma"
    description = "Figma - design collaboration"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Figma token required")
        try:
            if action == "list_files":
                r = httpx.get("https://api.figma.com/v1/me/files", headers={"X-Figma-Token": token}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class MiroTool(BaseTool):
    name = "miro"
    description = "Miro - whiteboard"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Miro token required")
        try:
            if action == "list_boards":
                r = httpx.get("https://api.miro.com/v2/boards", headers={"Authorization": f"Bearer {token}"}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class LoomTool(BaseTool):
    name = "loom"
    description = "Loom - video messaging"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Loom token required")
        try:
            if action == "list_videos":
                r = httpx.get("https://api.loom.com/v1/videos", headers={"Authorization": token}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class VimeoTool(BaseTool):
    name = "vimeo"
    description = "Vimeo - video hosting"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Vimeo token required")
        try:
            if action == "list_videos":
                r = httpx.get("https://api.vimeo.com/me/videos", headers={"Authorization": f"Bearer {token}"}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class DailyTool(BaseTool):
    name = "daily"
    description = "Daily - video calls API"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        key = self.config.get("api_key")
        if not key:
            return ToolResult(False, "", "Daily API key required")
        try:
            if action == "list_rooms":
                r = httpx.get("https://api.daily.co/v1/rooms", headers={"Authorization": key}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

class GoogleDriveTool(BaseTool):
    name = "gdrive"
    description = "Google Drive - file storage"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(False, "", "Configure at console.cloud.google.com")

class OneDriveTool(BaseTool):
    name = "onedrive"
    description = "Microsoft OneDrive"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(False, "", "Configure at azure.com")

class CodaTool(BaseTool):
    name = "coda"
    description = "Coda - documents"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Coda token required")
        try:
            if action == "list_docs":
                r = httpx.get("https://api.coda.io/v1/docs", headers={"Authorization": f"Bearer {token}"}, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

def run(action: str = "list", **kwargs):
    return FigmaTool().run(action, **kwargs)