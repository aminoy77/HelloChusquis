import json
import os
import time
import core.db_memory as memory
import core.learning as learning
from core.provider import ProviderPool
from core.history import History
from tools.shell import ShellTool
from tools.files import FilesTool
from tools.code import CodeTool
from tools.websearch import WebSearchTool
from tools.base import ToolResult
from tools.web_fetch import WebFetchTool
from workspace.manager import WorkspaceManager
from core.plugins import load_plugins
from core.security_evaluator import evaluate_command_safety
from core.tool_policy import (
    ToolPolicy, ToolLoopDetector, SecurityAuditor, DangerousToolDetector,
    ToolPolicyConfig, LoopDetectionConfig, SessionState as PolicySessionState,
    Severity,
)
from core.session import SessionManager
from core.voice import VoiceManager
from core.mcp import get_client as get_mcp_client, MCPTransport
from ui.terminal import print_tool_call, print_tool_result, console
from core.logger import get_logger

logger = get_logger("agent")

# Import tool modules directly (they provide run functions)
import tools.github as github_module
import tools.slack as slack_module
import tools.discord as discord_module
import tools.docker as docker_module
import tools.notion as notion_module
import tools.aws as aws_module
import tools.twitter as twitter_module
import tools.gmail as gmail_module
import tools.jira as jira_module
import tools.postgresql as postgresql_module
import tools.mongodb as mongodb_module
import tools.google_calendar as google_calendar_module
import tools.spotify as spotify_module
import tools.stripe as stripe_module
import tools.twilio as twilio_module
import tools.sendgrid as sendgrid_module
import tools.supabase as supabase_module
import tools.vercel as vercel_module
import tools.sentry as sentry_module
import tools.pagerduty as pagerduty_module
import tools.datadog as datadog_module
import tools.intercom as intercom_module
import tools.contentful as contentful_module
import tools.sanity as sanity_module
import tools.hubspot as hubspot_module
import tools.shopify as shopify_module
import tools.mailchimp as mailchimp_module
import tools.airtable as airtable_module
import tools.plaid as plaid_module
import tools.square as square_module
import tools.cloudinary as cloudinary_module
import tools.algolia as algolia_module
import tools.resend as resend_module
import tools.brevo as brevo_module
import tools.upstash as upstash_module
import tools.clerk as clerk_module
import tools.posthog as posthog_module
import tools.launchdarkly as launchdarkly_module
import tools.calendly as calendly_module
import tools.zoom as zoom_module
import tools.clickup as clickup_module
import tools.raycast as raycast_module
import tools.bitbucket as bitbucket_module
import tools.n8n as n8n_module
import tools.pipedream as pipedream_module
import tools.retool as retool_module
import tools.workato as workato_module
import tools.make as make_module


def _build_tools_schema(plugins: list) -> list:
    """Construye el schema de tools cada vez — evita duplicados en TOOLS_SCHEMA global."""
    schema = [
        {
            "type": "function",
            "function": {
                "name": "browser",
                "description": "Full browser automation via Playwright. Navigate to URLs, click elements, type text, take screenshots, extract content, fill forms, scroll, and more. Human-like mouse movements enabled. Anti-detection active.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "navigate", "click", "double_click", "right_click",
                                "type", "scroll", "scroll_to_bottom", "scroll_to_top",
                                "screenshot", "get_text", "get_visible_text",
                                "search", "find", "wait_for_element",
                                "fill_form", "submit_form", "hover",
                                "execute_script", "press_key",
                                "go_back", "go_forward", "reload",
                                "get_url", "get_title", "get_cookies",
                                "open_new_tab", "switch_to_page", "close_current_tab",
                                "upload_file", "select_option",
                            ],
                            "description": "The browser action to perform"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL for navigate or open_new_tab actions"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for the target element"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type, text to click, or search query"
                        },
                        "xpath": {
                            "type": "string",
                            "description": "XPath selector for the target element"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query for browser_search"
                        },
                        "engine": {
                            "type": "string",
                            "enum": ["google", "duckduckgo", "bing", "brave"],
                            "description": "Search engine for browser_search"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["down", "up"],
                            "description": "Scroll direction"
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Number of scroll steps (each ~300-600px)"
                        },
                        "path": {
                            "type": "string",
                            "description": "File path to save screenshot"
                        },
                        "full_page": {
                            "type": "boolean",
                            "description": "Capture full page screenshot"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Text pattern to find elements"
                        },
                        "index": {
                            "type": "integer",
                            "description": "Element index if multiple match"
                        },
                        "key": {
                            "type": "string",
                            "description": "Keyboard key to press (Enter, Tab, Escape, etc)"
                        },
                        "form_data": {
                            "type": "object",
                            "description": "Key-value pairs for form fields",
                            "additionalProperties": {"type": "string"}
                        },
                        "script": {
                            "type": "string",
                            "description": "JavaScript code to execute"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path for upload"
                        },
                        "clear_first": {
                            "type": "boolean",
                            "description": "Clear field before typing"
                        }
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "shell",
                "description": "Execute a terminal command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command to run"}
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "code",
                "description": "Execute Python code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the internet via DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "github",
                "description": "Interact with GitHub API - manage repos, issues, PRs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_repos", "get_repo", "list_issues", "create_issue", "list_pulls", "create_pr", "get_user", "search_repos"]},
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "state": {"type": "string"},
                        "base": {"type": "string"},
                        "head": {"type": "string"},
                        "query": {"type": "string"},
                        "per_page": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "slack",
                "description": "Send messages to Slack channels and users",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["post_message", "list_channels", "get_channel", "list_users"]},
                        "channel": {"type": "string"},
                        "user": {"type": "string"},
                        "text": {"type": "string"},
                        "username": {"type": "string"},
                        "icon_emoji": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "discord",
                "description": "Send messages to Discord via webhooks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_message", "send_embed"]},
                        "webhook_url": {"type": "string"},
                        "channel_id": {"type": "string"},
                        "content": {"type": "string"},
                        "username": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "color": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "docker",
                "description": "Manage Docker containers, images, and volumes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_containers", "list_images", "list_volumes", "start_container", "stop_container", "remove_container", "container_logs", "docker_info"]},
                        "container": {"type": "string"},
                        "all": {"type": "boolean"},
                        "tail": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "notion",
                "description": "Interact with Notion workspaces",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_page", "update_page", "query_database", "list_databases", "get_page"]},
                        "page_id": {"type": "string"},
                        "database_id": {"type": "string"},
                        "title": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "aws",
                "description": "Interact with AWS services - EC2, S3, Lambda",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_ec2", "list_s3", "list_lambda", "invoke_lambda", "list_iam", "sts_caller"]},
                        "resource": {"type": "string"},
                        "region": {"type": "string"},
                        "payload": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "twitter",
                "description": "Post tweets and interact with Twitter/X",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["post_tweet", "get_user", "search_tweets", "get_timeline", "get_mentions"]},
                        "text": {"type": "string"},
                        "username": {"type": "string"},
                        "query": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gmail",
                "description": "Send emails and manage Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_email", "list_emails", "search_emails", "get_labels"]},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "jira",
                "description": "Create and manage Jira issues",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_issue", "search_issues", "get_issue", "assign_issue", "list_projects"]},
                        "project": {"type": "string"},
                        "issue_key": {"type": "string"},
                        "summary": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "postgresql",
                "description": "Execute SQL queries on PostgreSQL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["query", "execute", "list_tables"]},
                        "sql": {"type": "string"},
                        "database": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mongodb",
                "description": "Query and manipulate MongoDB",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["find", "insert", "update", "delete"]},
                        "database": {"type": "string"},
                        "collection": {"type": "string"},
                        "filter": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "google_calendar",
                "description": "Manage Google Calendar events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_events", "create_event"]},
                        "title": {"type": "string"},
                        "start_time": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "spotify",
                "description": "Control Spotify playback",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["play", "pause", "next", "search"]},
                        "query": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "stripe",
                "description": "Stripe payment processing - customers, charges, subscriptions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_customers", "create_customer", "create_charge", "list_invoices", "list_subscriptions"]},
                        "email": {"type": "string"},
                        "amount": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "twilio",
                "description": "Twilio SMS, voice calls, and messaging",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_sms", "list_messages", "make_call"]},
                        "to": {"type": "string"},
                        "message": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sendgrid",
                "description": "SendGrid transactional email",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_email", "list_contacts", "get_stats"]},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "supabase",
                "description": "Supabase PostgreSQL database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["select", "insert", "update", "delete", "list_tables"]},
                        "table": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "vercel",
                "description": "Vercel deployments and projects",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_deployments", "get_deployment", "list_projects", "get_project"]},
                        "id": {"type": "string"},
                        "name": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sentry",
                "description": "Sentry error tracking",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_issues", "get_issue", "list_projects", "get_stats"]},
                        "id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pagerduty",
                "description": "PagerDuty incident management",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_incidents", "get_incident", "list_services", "list_on_calls", "trigger_incident"]},
                        "id": {"type": "string"},
                        "title": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "datadog",
                "description": "Datadog monitoring and metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["query_metrics", "list_hosts", "get_services", "list_monitors"]},
                        "query": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "intercom",
                "description": "Intercom customer messaging",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_conversations", "get_conversation", "list_contacts", "send_message"]},
                        "id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "message": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "contentful",
                "description": "Contentful CMS content management",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_entries", "get_entry", "list_assets", "list_content_types"]},
                        "id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sanity",
                "description": "Sanity CMS structured content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["fetch", "mutate"]},
                        "query": {"type": "string"},
                        "mutations": {"type": "array"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "hubspot",
                "description": "HubSpot CRM contacts and deals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_contacts", "create_contact", "list_deals", "list_companies"]},
                        "email": {"type": "string"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "shopify",
                "description": "Shopify e-commerce products and orders",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_products", "get_product", "list_orders", "list_customers"]},
                        "id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mailchimp",
                "description": "Mailchimp email marketing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_campaigns", "create_campaign", "send_campaign", "list_lists"]},
                        "id": {"type": "string"},
                        "subject": {"type": "string"},
                        "list_id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "airtable",
                "description": "Airtable collaborative bases",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_records", "create_record", "update_record", "delete_record"]},
                        "table": {"type": "string"},
                        "id": {"type": "string"},
                        "fields": {"type": "object"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "plaid",
                "description": "Plaid banking and financial data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_link_token", "exchange_token", "get_transactions", "get_balance"]},
                        "public_token": {"type": "string"},
                        "access_token": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "square",
                "description": "Square payments and orders",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_payments", "create_payment", "list_orders", "list_locations"]},
                        "amount": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cloudinary",
                "description": "Cloudinary image and video management",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["upload", "list_resources", "delete_resource", "transform"]},
                        "file": {"type": "string"},
                        "public_id": {"type": "string"},
                        "transformations": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "algolia",
                "description": "Algolia search and analytics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["search", "add_object", "delete_object", "search_settings"]},
                        "query": {"type": "string"},
                        "data": {"type": "object"},
                        "id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "resend",
                "description": "Resend modern email delivery",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send", "batch", "list"]},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "html": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "brevo",
                "description": "Brevo email marketing and SMS",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_email", "list_contacts", "create_contact", "list_campaigns"]},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "upstash",
                "description": "Upstash Redis serverless database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["get", "set", "incr", "del"]},
                        "key": {"type": "string"},
                        "value": {"type": "string"},
                        "ttl": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "clerk",
                "description": "Clerk authentication and user management",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_users", "get_user", "create_user", "list_organizations"]},
                        "id": {"type": "string"},
                        "email": {"type": "string"},
                        "password": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "posthog",
                "description": "PostHog product analytics and feature flags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["capture", "list_feature_flags", "get_flag", "list_insights"]},
                        "event": {"type": "string"},
                        "properties": {"type": "object"},
                        "key": {"type": "string"},
                        "distinct_id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "launchdarkly",
                "description": "LaunchDarkly feature flags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_flags", "get_flag", "toggle_flag", "list_environments"]},
                        "flag": {"type": "string"},
                        "state": {"type": "boolean"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calendly",
                "description": "Calendly meeting scheduling",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_events", "list_event_types", "get_event", "list_users"]},
                        "id": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "zoom",
                "description": "Zoom video meetings and recordings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list_meetings", "create_meeting", "get_meeting", "list_recordings"]},
                        "id": {"type": "string"},
                        "topic": {"type": "string"},
                        "duration": {"type": "number"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "files",
                "description": "Read, write, delete, list files in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "delete", "list", "create_dir"]
                        },
                        "path": {"type": "string"},
                        "content": {"type": "string", "description": "Required for write"}
                    },
                    "required": ["action", "path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Fetch URL content with SSRF protection, caching, and markdown/text extraction. Lightweight alternative to browser.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "HTTP(S) URL to fetch"},
                        "extract_mode": {
                            "type": "string",
                            "enum": ["markdown", "text"],
                            "description": "Output format (default: markdown)"
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Max chars returned (default: 20000)"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "speak",
                "description": "Text-to-speech synthesis. Convert text to audio using available TTS providers (Edge, OpenAI, ElevenLabs, Piper).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to synthesize to speech"},
                        "voice_id": {"type": "string", "description": "Specific voice ID (optional)"},
                        "language": {"type": "string", "description": "Language code (e.g. en, es)"},
                        "speed": {"type": "number", "description": "Speech speed multiplier (default: 1.0)"},
                        "provider": {"type": "string", "description": "TTS provider (edge, openai, elevenlabs, piper)"},
                        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "description": "Audio format"}
                    },
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "media",
                "description": "Media processing: image operations (resize, thumbnail, info, convert), PDF text extraction, and QR code generation. Uses ImageMagick/ffmpeg.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["image_info", "image_resize", "image_thumbnail", "image_convert", "pdf_extract", "qr_generate"],
                            "description": "Media operation to perform"
                        },
                        "path": {"type": "string", "description": "Input file path"},
                        "output_path": {"type": "string", "description": "Output file path (optional)"},
                        "width": {"type": "integer", "description": "Target width for resize"},
                        "height": {"type": "integer", "description": "Target height for resize"},
                        "size": {"type": "integer", "description": "Thumbnail size in px"},
                        "text": {"type": "string", "description": "Text content for QR code"},
                        "format": {"type": "string", "description": "Output format (e.g. png, webp)"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mcp",
                "description": "Route tool calls to Model Context Protocol (MCP) servers. Connect, list tools, and call tools on external MCP servers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list_servers", "list_tools", "call_tool"],
                            "description": "MCP operation"
                        },
                        "server": {"type": "string", "description": "MCP server name"},
                        "tool": {"type": "string", "description": "Tool name on the MCP server"},
                        "arguments": {"type": "object", "description": "Arguments for the MCP tool"}
                    },
                    "required": ["action"]
                }
            }
        }
    ]
    for plugin in plugins:
        schema.append(plugin["schema"])
    return schema


class Agent:
    def __init__(self, config: dict):
        self.pool = ProviderPool()
        self.history = History()
        self._pending_tool_results = []
        self.workspace = WorkspaceManager(config["settings"]["workspace_dirs"])
        self.shell = ShellTool()
        self.files = FilesTool(config["settings"]["workspace_dirs"])
        self.code = CodeTool()
        self.websearch = WebSearchTool()
        # Los módulos de herramientas externos se usan directamente via run()
        self.system_prompt = config["agent"]["system_prompt"]
        self.workspace_dirs = config["settings"]["workspace_dirs"]

        # Memoria (estructurada vía SQLite ahora)
        summary = memory.load_summary()
        if summary:
            self.system_prompt += f"\n\nWhat you remember from past sessions:\n{summary}"

        # Learnings
        learnings = learning.load_learnings()
        learning_prompt = learning.build_learning_prompt(learnings)
        if learning_prompt:
            self.system_prompt += f"\n\n{learning_prompt}"

        # Plugins — schema se construye una vez aquí, no se modifica una lista global
        self.plugins = load_plugins()
        self.tools_schema = _build_tools_schema(self.plugins)

        # --- OpenClaw modules integration ---

        # WebFetch tool instance
        self.web_fetch = WebFetchTool()

        # Tool policy (allow/deny enforcement)
        policy_cfg = ToolPolicyConfig(
            allow=config.get("tool_policy", {}).get("allow"),
            deny=config.get("tool_policy", {}).get("deny"),
        )
        self.tool_policy = ToolPolicy(allow=policy_cfg.allow, deny=policy_cfg.deny)

        # Loop detection
        loop_cfg = LoopDetectionConfig()
        self.loop_detector = ToolLoopDetector(config=loop_cfg)
        self._loop_session_state = PolicySessionState()

        # Security auditor
        self.security_auditor = SecurityAuditor(policy=self.tool_policy)

        # Session persistence
        sessions_db = os.path.join(
            os.path.expanduser("~"), ".hellochusquis", "sessions.db"
        )
        os.makedirs(os.path.dirname(sessions_db), exist_ok=True)
        self.session_manager = SessionManager(sessions_db)
        self._session_id = self.session_manager.create_session(
            agent_id="main",
            model=config.get("model", "default"),
        )

        # Voice/TTS
        try:
            self.voice_manager = VoiceManager()
        except Exception:
            self.voice_manager = None

        # MCP client
        self.mcp_client = get_mcp_client()

        logger.info("Agent initialized — %d providers, %d tools", len(self.pool.providers), len(self.tools_schema))

        if self.plugins:
            plugin_names = ", ".join(p["name"] for p in self.plugins)
            self.system_prompt += (
                f"\n\nInstalled plugins available as tools: {plugin_names}. "
                "Use them directly without asking the user to install anything."
            )

        # Available integrations list for proposing new tools
        available_integrations = [
            "stripe", "square", "plaid",  # Payments
            "twilio", "sendgrid", "resend", "brevo",  # Communication
            "vercel", "supabase", "sentry", "datadog", "pagerduty",  # DevOps
            "shopify", "hubspot", "mailchimp", "airtable", "clerk",  # CRM/Marketing
            "contentful", "sanity",  # CMS
            "algolia", "cloudinary", "posthog", "launchdarkly", "upstash",  # Tools
            "clickup", "raycast", "bitbucket", "n8n", "pipedream", "retool", "workato", "make",  # Automation
            "calendly", "zoom"  # Meetings
        ]
        
        self.system_prompt += f"\n\nIf user requests an integration not in available tools ({', '.join(available_integrations)}), offer to build it using the /tool command or suggest it as a feature request."

    def _dispatch_tool(self, name: str, args: dict) -> ToolResult:
        if name == "shell":
            cmd = args.get("command", "")
            
            # Skip security checks if disabled via CLI
            unsafe_mode = os.getenv("HELLOCHUSQUIS_UNSAFE_MODE") == "1"
            profile = os.getenv("HELLOCHUSQUIS_PROFILE", "default")

            # En modo agresivo o deshabilitado por CLI, saltarse las revisiones
            if not unsafe_mode and profile != "aggressive":
                safety_check = evaluate_command_safety(cmd, self.pool)
                if not safety_check.get("safe", True):
                    risk_msg = safety_check.get("reason", "Potentially unsafe command detected.")
                    logger.warning("Blocked unsafe command: %s — %s", cmd, risk_msg)
                    console.print(f"[bold red]⛔ Blocked unsafe command:[/bold red] {cmd}")
                    console.print(f"[dim]{risk_msg}[/dim]")
                    return ToolResult(success=False, output="", error=f"Safety check failed: {risk_msg}")

            return self.shell.run(**args)

        if name == "code":
            return self.code.run(**args)

        if name == "web_search":
            return self.websearch.run(**args)

        if name == "files":
            path = args.get("path", "")
            if not self.workspace.is_allowed(path):
                granted = self.workspace.request_access(path)
                if not granted:
                    return ToolResult(success=False, output="", error="Access denied by user")
                self.files.allow_dir(path)
            return self.files.run(**args)

        if name == "browser":
            try:
                action = args.get("action", "")
                if not action:
                    return ToolResult(success=False, output="", error="Action required for browser tool")

                from tools.browser import (
                    browser_open, browser_click, browser_double_click, browser_right_click,
                    browser_type, browser_scroll, browser_screenshot, browser_get_text,
                    browser_search, browser_find, browser_wait_for_element,
                    browser_execute_script, browser_get_url, browser_get_title,
                    browser_go_back, browser_go_forward, browser_reload,
                    browser_press_key, browser_scroll_to_element,
                    browser_open_new_tab, browser_switch_to_page,
                    browser_fill_form, browser_submit_form, browser_hover,
                    browser_get_visible_text, browser_get_cookies, browser_health,
                )

                action_map = {
                    "navigate": lambda: browser_open(args.get("url", "")),
                    "click": lambda: browser_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                        index=args.get("index", 0),
                    ),
                    "double_click": lambda: browser_double_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "right_click": lambda: browser_right_click(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "type": lambda: browser_type(
                        text=args.get("text", ""),
                        selector=args.get("selector"),
                        clear_first=args.get("clear_first", True),
                    ),
                    "scroll": lambda: browser_scroll(
                        direction=args.get("direction", "down"),
                        amount=args.get("amount", 3),
                    ),
                    "scroll_to_bottom": lambda: browser_scroll_to_element("body"),
                    "scroll_to_top": lambda: browser_scroll_to_element("header"),
                    "screenshot": lambda: browser_screenshot(
                        path=args.get("path"),
                        full_page=args.get("full_page", False),
                    ),
                    "get_text": lambda: browser_get_text(selector=args.get("selector")),
                    "get_visible_text": lambda: browser_get_visible_text(),
                    "search": lambda: browser_search(
                        query=args.get("query", args.get("text", "")),
                        engine=args.get("engine", "google"),
                    ),
                    "find": lambda: browser_find(pattern=args.get("pattern", args.get("text", ""))),
                    "wait_for_element": lambda: browser_wait_for_element(
                        selector=args.get("selector", ""),
                        timeout=args.get("timeout", 30),
                    ),
                    "hover": lambda: browser_hover(
                        selector=args.get("selector"),
                        text=args.get("text"),
                        xpath=args.get("xpath"),
                    ),
                    "fill_form": lambda: browser_fill_form(form_data=args.get("form_data", {})),
                    "submit_form": lambda: browser_submit_form(selector=args.get("selector", "form")),
                    "execute_script": lambda: browser_execute_script(script=args.get("script", "")),
                    "press_key": lambda: browser_press_key(key=args.get("key", "")),
                    "go_back": lambda: browser_go_back(),
                    "go_forward": lambda: browser_go_forward(),
                    "reload": lambda: browser_reload(),
                    "get_url": lambda: browser_get_url(),
                    "get_title": lambda: browser_get_title(),
                    "get_cookies": lambda: browser_get_cookies(),
                    "open_new_tab": lambda: browser_open_new_tab(url=args.get("url")),
                    "switch_to_page": lambda: browser_switch_to_page(index=args.get("index", 0)),
                    "close_current_tab": lambda: browser_switch_to_page(index=0),
                    "health": lambda: browser_health(),
                }

                handler = action_map.get(action)
                if not handler:
                    return ToolResult(success=False, output="", error=f"Unknown browser action: {action}")

                result = handler()
                if isinstance(result, dict):
                    output = str(result)
                    success = result.get("success", False)
                    return ToolResult(success=success, output=output)
                return ToolResult(success=True, output=str(result))

            except Exception as e:
                logger.error("Browser tool error: %s", e)
                return ToolResult(success=False, output="", error=str(e))

        if name == "web_fetch":
            return self.web_fetch.run(**args)

        if name == "speak":
            if not self.voice_manager:
                return ToolResult(success=False, output="", error="Voice/TTS not available. Check provider config.")
            try:
                text = args.get("text", "")
                if not text:
                    return ToolResult(success=False, output="", error="text parameter required for speak")
                result = self.voice_manager.synthesize(
                    text=text,
                    voice_id=args.get("voice_id"),
                    language=args.get("language", ""),
                    speed=args.get("speed", 1.0),
                    provider_id=args.get("provider"),
                    output_format=args.get("output_format", "mp3"),
                )
                if result.success:
                    return ToolResult(success=True, output=f"Audio: {result.audio_path}")
                return ToolResult(success=False, output="", error=result.error or "TTS synthesis failed")
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "media":
            action = args.get("action", "")
            try:
                if action == "image_info":
                    from core.functions_advanced import image_info
                    result = image_info(args.get("path", ""))
                elif action == "image_resize":
                    from core.functions_advanced import image_resize
                    result = image_resize(
                        args.get("path", ""),
                        args.get("width", 0),
                        args.get("height", 0),
                    )
                elif action == "image_thumbnail":
                    from core.functions_advanced import image_thumbnail
                    result = image_thumbnail(
                        args.get("path", ""),
                        args.get("size", 128),
                    )
                elif action == "pdf_extract":
                    from core.functions_advanced import pdf_info
                    result = pdf_info(args.get("path", ""))
                elif action == "qr_generate":
                    from core.functions_advanced import qr_code
                    result = qr_code(
                        args.get("text", ""),
                        args.get("output_path"),
                    )
                else:
                    return ToolResult(success=False, output="", error=f"Unknown media action: {action}")
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "mcp":
            action = args.get("action", "")
            try:
                if action == "list_servers":
                    servers = list(self.mcp_client.servers.keys())
                    return ToolResult(success=True, output=str(servers))
                elif action == "list_tools":
                    tools = self.mcp_client.list_tools(args.get("server"))
                    return ToolResult(success=True, output=str(tools))
                elif action == "call_tool":
                    server = args.get("server", "")
                    tool = args.get("tool", "")
                    arguments = args.get("arguments", {})
                    import asyncio
                    result = asyncio.get_event_loop().run_until_complete(
                        self.mcp_client.call_tool(server, tool, arguments)
                    )
                    return ToolResult(
                        success=result.get("success", False),
                        output=str(result.get("data", result.get("error", ""))),
                        error=result.get("error") if not result.get("success") else None,
                    )
                else:
                    return ToolResult(success=False, output="", error=f"Unknown MCP action: {action}")
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        # External tool modules - call run() directly from module
        if name == "github":
            try:
                result = github_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "slack":
            try:
                result = slack_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "discord":
            try:
                result = discord_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "docker":
            try:
                result = docker_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "notion":
            try:
                result = notion_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "aws":
            try:
                result = aws_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "twitter":
            try:
                result = twitter_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "gmail":
            try:
                result = gmail_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "jira":
            try:
                result = jira_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "postgresql":
            try:
                result = postgresql_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "mongodb":
            try:
                result = mongodb_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "google_calendar":
            try:
                result = google_calendar_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "spotify":
            try:
                result = spotify_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        # New tool integrations
        if name == "stripe":
            try:
                result = stripe_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "twilio":
            try:
                result = twilio_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "sendgrid":
            try:
                result = sendgrid_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "supabase":
            try:
                result = supabase_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "vercel":
            try:
                result = vercel_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "sentry":
            try:
                result = sentry_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "pagerduty":
            try:
                result = pagerduty_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "datadog":
            try:
                result = datadog_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "intercom":
            try:
                result = intercom_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "contentful":
            try:
                result = contentful_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "sanity":
            try:
                result = sanity_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "hubspot":
            try:
                result = hubspot_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "shopify":
            try:
                result = shopify_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "mailchimp":
            try:
                result = mailchimp_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "airtable":
            try:
                result = airtable_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "plaid":
            try:
                result = plaid_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "square":
            try:
                result = square_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "cloudinary":
            try:
                result = cloudinary_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "algolia":
            try:
                result = algolia_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "resend":
            try:
                result = resend_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "brevo":
            try:
                result = brevo_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "upstash":
            try:
                result = upstash_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "clerk":
            try:
                result = clerk_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "posthog":
            try:
                result = posthog_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "launchdarkly":
            try:
                result = launchdarkly_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "calendly":
            try:
                result = calendly_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "zoom":
            try:
                result = zoom_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "clickup":
            try:
                result = clickup_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "raycast":
            try:
                result = raycast_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "bitbucket":
            try:
                result = bitbucket_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "n8n":
            try:
                result = n8n_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "pipedream":
            try:
                result = pipedream_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "retool":
            try:
                result = retool_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "workato":
            try:
                result = workato_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        if name == "make":
            try:
                result = make_module.run(**args)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        for plugin in self.plugins:
            if plugin["name"] == name:
                try:
                    result_text = plugin["run"](**args)
                    return ToolResult(success=True, output=str(result_text))
                except Exception as e:
                    return ToolResult(success=False, output="", error=str(e))

        return ToolResult(success=False, output="", error=f"Unknown tool: {name}. I can create this tool for you! Run `hellochusquis build` to create it with AI.")

    def _propose_tool_creation(self, tool_name: str, args: dict) -> str:
        """Propose creating a new tool when one doesn't exist."""
        return (
            f"I don't have a '{tool_name}' tool configured yet. I can create it for you!\n\n"
            f"Options:\n"
            f"1. Run `hellochusquis build` to build it with AI\n"
            f"2. Describe the integration you need and I'll create it\n"
            f"3. Submit a feature request at github.com/aminoy77/HelloChusquis/issues\n\n"
            f"Supported integrations I can build: Stripe, Twilio, SendGrid, Square, Plaid, "
            f"Vercel, Supabase, Sentry, PagerDuty, Datadog, Shopify, HubSpot, "
            f"Contentful, Sanity, Algolia, Cloudinary, n8n, Pipedream, Retool, and more."
        )

    def _build_messages(self) -> list[dict]:
        system = (
            self.system_prompt
            + f"\n\nWorkspace directories: {', '.join(self.workspace_dirs)}. "
            "ALWAYS use the available tools to complete tasks - do NOT respond with text explanations when tools can do the work. "
            "For file operations, use the 'files' tool. "
            "For running commands, use the 'shell' tool. "
            "For executing code, use the 'code' tool. "
            "NEVER say 'I cannot' or 'I don't have' - use the tools instead.\n\n"
            "You must follow this thought process for every turn:\n"
            "1. <thought>: Analyze what tool is needed.\n"
            "2. <call>: Execute the tool immediately.\n"
            "3. <verify>: Check if the result solves the request.\n"
        )
        return [{"role": "system", "content": system}, *self.history.get()]

    def run(self, user_input: str) -> str:
        self.history.add("user", user_input)
        self.session_manager.append_message(self._session_id, "user", user_input)
        messages = self._build_messages()

        # Preserve tool results across turns - don't optimize history during execution
        # This ensures tool responses from previous steps remain available
        self._pending_tool_results = getattr(self, '_pending_tool_results', [])
        
        # Add any pending tool results to the messages
        for tr in self._pending_tool_results:
            messages.append(tr)
        
        # Only optimize if we have too many messages (not during multi-step execution)
        if self.history.get_token_count(messages) > 4000:
            messages = self.history.optimize_context(max_tokens=4000)
            # Re-add tool results after optimization
            for tr in self._pending_tool_results:
                messages.append(tr)

        while True:
            response = self.pool.chat_with_retry(messages, tools=self.tools_schema)
            choices = response.get("choices", [])
            if not choices:
                return "Error: No response from AI provider"
            message = choices[0].get("message", {})

            if not message.get("tool_calls"):
                content = message.get("content") or ""
                self.history.add("assistant", content)
                self.session_manager.append_message(self._session_id, "assistant", content)
                # Clear pending tool results on successful completion
                self._pending_tool_results = []
                return content

            messages.append(message)
            step_tool_results = []

            for tc in message.get("tool_calls", []):
                func = tc.get("function", {})
                tool_name = func.get("name", "unknown")
                try:
                    tool_args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_args = {}

                print_tool_call(tool_name, tool_args)
                logger.info("Tool call: %s(%s)", tool_name, json.dumps(tool_args, default=str)[:200])

                # --- ToolPolicy enforcement ---
                if not self.tool_policy.is_tool_allowed(tool_name):
                    logger.warning("Tool denied by policy: %s", tool_name)
                    result = ToolResult(success=False, output="", error=f"Tool '{tool_name}' denied by policy")
                else:
                    # --- SecurityAuditor pre-check ---
                    audit_findings = self.security_auditor.audit_tool_call(tool_name, tool_args)
                    critical_findings = [f for f in audit_findings if f.severity == Severity.CRITICAL]
                    if critical_findings:
                        msg = "; ".join(f.title for f in critical_findings)
                        logger.warning("Security audit blocked %s: %s", tool_name, msg)
                        result = ToolResult(success=False, output="", error=f"Security audit: {msg}")
                    else:
                        # --- ToolLoopDetector check ---
                        loop_result = self.loop_detector.detect(self._loop_session_state, tool_name, tool_args)
                        if loop_result.stuck:
                            logger.warning("Loop detected for %s: %s", tool_name, loop_result.message)
                            result = ToolResult(success=False, output="", error=f"Loop detected: {loop_result.message}")
                        else:
                            # --- Plugin hooks: before_tool ---
                            for plugin in self.plugins:
                                hook_fn = plugin.get("before_tool")
                                if callable(hook_fn):
                                    try:
                                        hook_fn(tool_name, tool_args)
                                    except Exception:
                                        pass

                            result = self._dispatch_tool(tool_name, tool_args)

                            # --- Plugin hooks: after_tool ---
                            for plugin in self.plugins:
                                hook_fn = plugin.get("after_tool")
                                if callable(hook_fn):
                                    try:
                                        hook_fn(tool_name, tool_args, result)
                                    except Exception:
                                        pass

                    # --- Record tool call for loop detector ---
                    self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)

                if not result.success:
                    logger.error("Tool error: %s — %s", tool_name, result.error)
                print_tool_result(result.success, result.output)

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.output if result.success else f"ERROR: {result.error}"
                }
                messages.append(tool_msg)
                step_tool_results.append(tool_msg)
            
            # Keep all tool results for this turn for next turn
            self._pending_tool_results.extend(step_tool_results)

    def stream_run(self, user_input: str):
        """Yield SSE events instead of returning full string.
        Yields dict payloads: {"type": "chunk"|"tool_call"|"done", ...}
        """
        self.history.add("user", user_input)
        self.session_manager.append_message(self._session_id, "user", user_input)
        messages = self._build_messages()

        self._pending_tool_results = getattr(self, '_pending_tool_results', [])
        for tr in self._pending_tool_results:
            messages.append(tr)

        if self.history.get_token_count(messages) > 4000:
            messages = self.history.optimize_context(max_tokens=4000)
            for tr in self._pending_tool_results:
                messages.append(tr)

        while True:
            response = self.pool.chat_with_retry(messages, tools=self.tools_schema)
            choices = response.get("choices", [])
            if not choices:
                yield {"type": "chunk", "content": "Error: No response from AI provider"}
                yield {"type": "done"}
                return
            message = choices[0].get("message", {})

            if not message.get("tool_calls"):
                content = message.get("content") or ""
                self.history.add("assistant", content)
                self.session_manager.append_message(self._session_id, "assistant", content)
                self._pending_tool_results = []

                # Yield content in ~50 char chunks to simulate streaming
                chunk_size = 50
                for i in range(0, len(content), chunk_size):
                    yield {"type": "chunk", "content": content[i:i + chunk_size]}
                yield {"type": "done"}
                return

            messages.append(message)
            step_tool_results = []

            for tc in message.get("tool_calls", []):
                func = tc.get("function", {})
                tool_name = func.get("name", "unknown")
                try:
                    tool_args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_args = {}

                # Yield tool call status event
                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": tool_args,
                }

                print_tool_call(tool_name, tool_args)
                logger.info("Stream tool call: %s(%s)", tool_name, json.dumps(tool_args, default=str)[:200])

                # --- ToolPolicy enforcement ---
                if not self.tool_policy.is_tool_allowed(tool_name):
                    logger.warning("Stream tool denied by policy: %s", tool_name)
                    result = ToolResult(success=False, output="", error=f"Tool '{tool_name}' denied by policy")
                else:
                    # --- SecurityAuditor pre-check ---
                    audit_findings = self.security_auditor.audit_tool_call(tool_name, tool_args)
                    critical_findings = [f for f in audit_findings if f.severity == Severity.CRITICAL]
                    if critical_findings:
                        msg = "; ".join(f.title for f in critical_findings)
                        result = ToolResult(success=False, output="", error=f"Security audit: {msg}")
                    else:
                        # --- ToolLoopDetector check ---
                        loop_result = self.loop_detector.detect(self._loop_session_state, tool_name, tool_args)
                        if loop_result.stuck:
                            result = ToolResult(success=False, output="", error=f"Loop detected: {loop_result.message}")
                        else:
                            # --- Plugin hooks: before_tool ---
                            for plugin in self.plugins:
                                hook_fn = plugin.get("before_tool")
                                if callable(hook_fn):
                                    try:
                                        hook_fn(tool_name, tool_args)
                                    except Exception:
                                        pass

                            result = self._dispatch_tool(tool_name, tool_args)

                            # --- Plugin hooks: after_tool ---
                            for plugin in self.plugins:
                                hook_fn = plugin.get("after_tool")
                                if callable(hook_fn):
                                    try:
                                        hook_fn(tool_name, tool_args, result)
                                    except Exception:
                                        pass

                    # --- Record tool call for loop detector ---
                    self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)

                if not result.success:
                    logger.error("Stream tool error: %s — %s", tool_name, result.error)
                print_tool_result(result.success, result.output)

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.output if result.success else f"ERROR: {result.error}"
                }
                messages.append(tool_msg)
                step_tool_results.append(tool_msg)

            self._pending_tool_results.extend(step_tool_results)

    def summarize_and_save(self, retention_days: int = 30):
        messages = self.history.get()
        if not messages:
            return

        memory.save_session(messages)

        summary_prompt = (
            "Summarize the key facts, tasks completed, and important context "
            "from this conversation in 3-5 bullet points. Be very concise.\n\n"
            + "\n".join(f"{m['role']}: {m['content'][:200]}" for m in messages)
        )

        try:
            response = self.pool.chat_with_retry([
                {"role": "user", "content": summary_prompt}
            ])
            choices = response.get("choices", [])
            if not choices:
                return
            summary = choices[0].get("message", {}).get("content", "")
            memory.save_summary(summary)
        except Exception:
            pass

        learning.analyze_and_learn(messages, self.pool)
        # Ya no limpiamos viejos porque SQLite permite gestionarlo mejor internamente

        # Close session
        try:
            self.session_manager.close_session(self._session_id)
        except Exception:
            pass
