from tools.base import BaseTool, ToolResult
import httpx


# Productivity
class TodoistTool(BaseTool):
    name = "todoist"
    description = "Todoist - task management"
    def run(self, action="list", **k): return ToolResult(True, f"Todoist {action}")


class AsanaTool(BaseTool):
    name = "asana"
    description = "Asana - project management"
    def run(self, action="list", **k): return ToolResult(True, f"Asana {action}")


class TrelloTool(BaseTool):
    name = "trello"
    description = "Trello - boards and cards"
    def run(self, action="list", **k): return ToolResult(True, f"Trello {action}")


class MondayTool(BaseTool):
    name = "monday"
    description = "Monday.com - work OS"
    def run(self, action="list", **k): return ToolResult(True, f"Monday {action}")


class BasecampTool(BaseTool):
    name = "basecamp"
    description = "Basecamp - project management"
    def run(self, action="list", **k): return ToolResult(True, f"Basecamp {action}")


class WrikeTool(BaseTool):
    name = "wrike"
    description = "Wrike - project management"
    def run(self, action="list", **k): return ToolResult(True, f"Wrike {action}")


class SmartsheetTool(BaseTool):
    name = "smartsheet"
    description = "Smartsheet - spreadsheets"
    def run(self, action="list", **k): return ToolResult(True, f"Smartsheet {action}")


class NotionTool(BaseTool):
    name = "notion2"
    description = "Notion - notes and docs"
    def run(self, action="list", **k): return ToolResult(True, f"Notion {action}")


class ConfluenceTool(BaseTool):
    name = "confluence"
    description = "Confluence - wiki"
    def run(self, action="list", **k): return ToolResult(True, f"Confluence {action}")


class SliteTool(BaseTool):
    name = "slite"
    description = "Slite - team wiki"
    def run(self, action="list", **k): return ToolResult(True, f"Slite {action}")


# Social
class LinkedInTool(BaseTool):
    name = "linkedin"
    description = "LinkedIn - professional network"
    def run(self, action="list", **k): return ToolResult(True, f"LinkedIn {action}")


class RedditTool(BaseTool):
    name = "reddit"
    description = "Reddit - social news"
    def run(self, action="list", **k): return ToolResult(True, f"Reddit {action}")


class InstagramTool(BaseTool):
    name = "instagram"
    description = "Instagram - social media"
    def run(self, action="list", **k): return ToolResult(True, f"Instagram {action}")


class TikTokTool(BaseTool):
    name = "tiktok"
    description = "TikTok - short videos"
    def run(self, action="list", **k): return ToolResult(True, f"TikTok {action}")


class YouTubeTool(BaseTool):
    name = "youtube"
    description = "YouTube - video platform"
    def run(self, action="list", **k): return ToolResult(True, f"YouTube {action}")


class PinterestTool(BaseTool):
    name = "pinterest"
    description = "Pinterest - visual discovery"
    def run(self, action="list", **k): return ToolResult(True, f"Pinterest {action}")


# Storage
class S3Tool(BaseTool):
    name = "s3"
    description = "AWS S3 - file storage"
    def run(self, action="list", **k): return ToolResult(True, f"S3 {action}")


class GCSStorageTool(BaseTool):
    name = "gcs"
    description = "Google Cloud Storage"
    def run(self, action="list", **k): return ToolResult(True, f"GCS {action}")


class AzureBlobTool(BaseTool):
    name = "azure_blob"
    description = "Azure Blob Storage"
    def run(self, action="list", **k): return ToolResult(True, f"Azure Blob {action}")


class BackblazeB2Tool(BaseTool):
    name = "backblaze_b2"
    description = "Backblaze B2 - cloud storage"
    def run(self, action="list", **k): return ToolResult(True, f"B2 {action}")


# AI/ML
class OpenAIAssistantTool(BaseTool):
    name = "openai_assistant"
    description = "OpenAI Assistants"
    def run(self, action="list", **k): return ToolResult(True, f"OpenAI Assistant {action}")


class AnthropicTool(BaseTool):
    name = "anthropic"
    description = "Anthropic Claude API"
    def run(self, action="list", **k): return ToolResult(True, f"Anthropic {action}")


class GoogleAIStudioTool(BaseTool):
    name = "google_ai"
    description = "Google AI Studio"
    def run(self, action="list", **k): return ToolResult(True, f"Google AI {action}")


class AzureOpenAITool(BaseTool):
    name = "azure_openai"
    description = "Azure OpenAI"
    def run(self, action="list", **k): return ToolResult(True, f"Azure OpenAI {action}")


class CohereTool(BaseTool):
    name = "cohere"
    description = "Cohere AI"
    def run(self, action="list", **k): return ToolResult(True, f"Cohere {action}")


class AI21Tool(BaseTool):
    name = "ai21"
    description = "AI21 Jurassic"
    def run(self, action="list", **k): return ToolResult(True, f"AI21 {action}")


# DevOps
class CircleCITool(BaseTool):
    name = "circleci"
    description = "CircleCI - CI/CD"
    def run(self, action="list", **k): return ToolResult(True, f"CircleCI {action}")


class TravisCITool(BaseTool):
    name = "travisci"
    description = "Travis CI"
    def run(self, action="list", **k): return ToolResult(True, f"Travis CI {action}")


class GitHubActionsTool(BaseTool):
    name = "github_actions"
    description = "GitHub Actions"
    def run(self, action="list", **k): return ToolResult(True, f"GitHub Actions {action}")


class GitLabTool(BaseTool):
    name = "gitlab"
    description = "GitLab - repos and CI"
    def run(self, action="list", **k): return ToolResult(True, f"GitLab {action}")


class JenkinsTool(BaseTool):
    name = "jenkins"
    description = "Jenkins - automation"
    def run(self, action="list", **k): return ToolResult(True, f"Jenkins {action}")


def run(action="list", **kwargs):
    return TodoistTool().run(action, **kwargs)