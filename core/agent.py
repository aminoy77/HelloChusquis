import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Optional
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
    ToolPolicy, ToolLoopDetector, SecurityAuditor, ToolPolicyConfig, LoopDetectionConfig, SessionState as PolicySessionState,
    Severity,
)
from core.session import SessionManager
from core.voice import VoiceManager
from core.mcp import get_client as get_mcp_client
from core.approvals import ApprovalManager, approval_reason, redact_sensitive_data
from core.identity import ROLE_PERMISSIONS, Permission, Role
from ui.terminal import print_tool_call, print_tool_result, console
from core.logger import get_logger

logger = get_logger("agent")
MAX_PERSISTED_HTTP_SESSIONS = 200

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
from core.subagents import SUBAGENT_TOOL_SCHEMA, handle_subagent_tool, subagents_prompt_section
from core import skills as skills_module


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
                "description": "Search the internet with fallbacks (DuckDuckGo lite → HTML → browser). Returns titles, URLs, snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "number", "description": "Number of results (1-20, default 5)"},
                        "region": {"type": "string", "description": "Region code (e.g. es-es, en-us)"},
                        "time_filter": {"type": "string", "enum": ["day", "week", "month", "year"], "description": "Time filter for results"}
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
    schema.append(SUBAGENT_TOOL_SCHEMA)
    schema.append(skills_module.SKILL_TOOL_SCHEMA)
    return schema


def extract_memory_facts(text: str, max_facts: int = 2) -> list[tuple[str, str]]:
    """Deterministic fact patterns: explicit remember, 'my X is Y', 'I prefer X'."""
    facts: list[tuple[str, str]] = []
    for value in re.findall(r"\bremember\s+(.{1,120})", text or "", re.I):
        facts.append(("note", re.sub(r"\s+", " ", value.strip(" .;!?"))))
    for key, value in re.findall(
        r"\bmy\s+([\w ]{1,40}?)\s+is\s+([^.,;!?]{1,120})", text or "", re.I
    ):
        facts.append((re.sub(r"\s+", " ", key.strip().lower()), re.sub(r"\s+", " ", value.strip())))
    for value in re.findall(r"\bi\s+prefer\s+([^.,;!?]{1,120})", text or "", re.I):
        facts.append(("preference", re.sub(r"\s+", " ", value.strip())))
    seen = set()
    unique = [f for f in facts if f[1] and not (f in seen or seen.add(f))]
    return unique[:max(1, max_facts)]


def parse_memory_command(text: str) -> tuple[str, str] | None:
    """Parse 'remember <fact>' / 'forget <key>' chat commands."""
    stripped = (text or "").strip()
    lowered = stripped.lower()
    if lowered.startswith("remember ") and stripped[9:].strip():
        return ("remember", stripped[9:].strip()[:500])
    if lowered.startswith("forget ") and stripped[7:].strip():
        return ("forget", stripped[7:].strip()[:120])
    return None


def parse_fenced_tool_call(content: str) -> tuple[str, dict] | None:
    """Small models often emit ```json {"name": ..., "arguments": ...} text
    instead of a tool_calls payload. Return (name, args) or None."""
    if not content:
        return None
    stripped = content.strip()
    if stripped.startswith("{"):
        # Bare JSON object as the whole message (no fences at all).
        try:
            data, _ = json.JSONDecoder().raw_decode(stripped)
            if isinstance(data, dict) and isinstance(data.get("name"), str) and data.get("name"):
                args = data.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args)
                if isinstance(args, dict):
                    return data["name"], args
        except ValueError:
            pass
    if "```" not in content:
        return None
    start = content.find("```")
    fence = content[start:]
    newline = fence.find("\n")
    body = fence[newline + 1:] if newline != -1 else fence[3:]
    end = body.find("```")
    candidate = body[:end] if end != -1 else body
    candidate = candidate.strip()
    if candidate[:4].lower() == "json" and not candidate.startswith("{"):
        candidate = candidate[4:].strip()
    try:
        data, _ = json.JSONDecoder().raw_decode(candidate)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    args = data.get("arguments", {})
    if not isinstance(name, str) or not name:
        return None
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return None
    if not isinstance(args, dict):
        return None
    return name, args


def with_fenced_tools(message: dict) -> dict:
    """Inject synthetic tool_calls when content carries fenced tool JSON."""
    if not message.get("tool_calls"):
        fenced = parse_fenced_tool_call(message.get("content") or "")
        if fenced:
            fname, fargs = fenced
            return dict(message, tool_calls=[{
                "id": "fenced-%d" % abs(hash((fname, message.get("content", "")))),
                "function": {"name": fname, "arguments": json.dumps(fargs)},
            }])
    return message


class Agent:
    def __init__(
        self,
        config: dict,
        require_approval: bool = False,
        session_key: str | None = None,
        role: Role | str | None = None,
    ):
        self.pool = ProviderPool(config=config)
        self.require_approval = require_approval
        self.role = Role(role) if role is not None else None
        self.approval_manager = ApprovalManager()
        self._turn_lock = threading.Lock()
        self._audited_approval_ids: set[str] = set()
        self.history = History()
        self._pending_tool_results = []
        # Hand-made minimal configs (e.g. Ollama-only) may omit settings the
        # setup wizard always writes; fall back instead of KeyError.
        _settings = config.get("settings", {}) or {}
        _agent_cfg = config.get("agent", {}) or {}
        from pathlib import Path as _Path
        _workspace_dirs = _settings.get("workspace_dirs") or [
            str(_Path.home() / ".hellochusquis" / "workspace")]
        self.workspace = WorkspaceManager(_workspace_dirs)
        self.shell = ShellTool()
        self.files = FilesTool(_workspace_dirs)
        self.code = CodeTool()
        self.websearch = WebSearchTool()
        # External tool modules are used directly via run()
        self.system_prompt = _agent_cfg.get("system_prompt", "")
        self.workspace_dirs = _workspace_dirs

        # Memory (structured via SQLite now)
        summary = memory.load_summary()
        if summary:
            self.system_prompt += f"\n\nWhat you remember from past sessions:\n{summary}"

        # Learnings
        learnings = learning.load_learnings()
        learning_prompt = learning.build_learning_prompt(learnings)
        if learning_prompt:
            self.system_prompt += f"\n\n{learning_prompt}"

        # Reference knowledge base (repo MDknowledge + user overrides, best-effort)
        try:
            memory.load_knowledge()
        except Exception:
            pass

        # Universal SKILL.md skills (Fase 2, best-effort, prompt-only list/show)
        try:
            self.skills = skills_module.get_registry()
            skills_module.discover_skill_md(
                [
                    str(Path.home() / ".hellochusquis" / "skills"),
                    str(Path(__file__).resolve().parent.parent / ".agents" / "skills"),
                ],
                registry=self.skills,
            )
        except Exception:
            self.skills = skills_module.get_registry()
        self.system_prompt += "\n\n" + self.skills.skills_prompt_section()

        # Plugins — schema built once here, no global list mutated
        self.plugins = load_plugins()
        self.tools_schema = _build_tools_schema(self.plugins)

        # --- Core modules integration ---

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
        self._persistent_session = session_key is not None
        storage_session_id = (
            f"http_{hashlib.sha256(session_key.encode('utf-8')).hexdigest()}"
            if session_key
            else None
        )
        self._session_id = self.session_manager.create_session(
            agent_id="http" if storage_session_id else "main",
            model=config.get("model", "default"),
            session_id=storage_session_id,
        )
        if self._persistent_session:
            self._restore_persisted_history()

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

        self.system_prompt += "\n\n" + subagents_prompt_section()

        # Available integrations list for proposing new tools
        
        self._external_tool_modules = {
            "github": github_module, "slack": slack_module, "discord": discord_module,
            "docker": docker_module, "notion": notion_module, "aws": aws_module,
            "twitter": twitter_module, "gmail": gmail_module, "jira": jira_module,
            "postgresql": postgresql_module, "mongodb": mongodb_module,
            "google_calendar": google_calendar_module, "spotify": spotify_module,
            "stripe": stripe_module, "twilio": twilio_module, "sendgrid": sendgrid_module,
            "supabase": supabase_module, "vercel": vercel_module, "sentry": sentry_module,
            "pagerduty": pagerduty_module, "datadog": datadog_module, "intercom": intercom_module,
            "contentful": contentful_module, "sanity": sanity_module, "hubspot": hubspot_module,
            "shopify": shopify_module, "mailchimp": mailchimp_module, "airtable": airtable_module,
            "plaid": plaid_module, "square": square_module, "cloudinary": cloudinary_module,
            "algolia": algolia_module, "resend": resend_module, "brevo": brevo_module,
            "upstash": upstash_module, "clerk": clerk_module, "posthog": posthog_module,
            "launchdarkly": launchdarkly_module, "calendly": calendly_module,
            "zoom": zoom_module, "clickup": clickup_module, "raycast": raycast_module,
            "bitbucket": bitbucket_module, "n8n": n8n_module, "pipedream": pipedream_module,
            "retool": retool_module, "workato": workato_module, "make": make_module
        }

    def _restore_persisted_history(self) -> None:
        """Restore a bounded recent context for a stable HTTP session."""
        for message in self.session_manager.get_recent_history(self._session_id, limit=100):
            role = message.get("role", "")
            content = message.get("content", "")
            if role in {"user", "assistant", "tool", "system"} and isinstance(content, str):
                self.history.add(role, content)

    def try_acquire_turn(self) -> bool:
        """Acquire exclusive ownership of this conversation without waiting."""
        return self._turn_lock.acquire(blocking=False)

    def release_turn(self) -> None:
        """Release conversation ownership after a completed or cancelled HTTP turn."""
        if self._turn_lock.locked():
            self._turn_lock.release()

    def _audit(self, event_type: str, details: dict) -> None:
        """Best-effort audit persistence that must never interrupt an action."""
        try:
            self.session_manager.log_audit_event(self._session_id, event_type, details)
        except Exception:
            logger.exception("Failed to persist audit event: %s", event_type)

    def pending_approvals(self) -> list[dict]:
        """Return pending high-impact actions for this agent session only."""
        return self.approval_manager.list_requests()

    def decide_approval(self, request_id: str, approved: bool) -> dict:
        """Record one user decision for a high-impact action."""
        request = self.approval_manager.decide(request_id, approved)
        self._audit(
            "approval_decided",
            {
                "approval_id": request.id,
                "tool_name": request.tool_name,
                "approved": approved,
                "status": request.status.value,
            },
        )
        return request.to_public_dict()

    def execute_approved(self, request_id: str) -> ToolResult:
        """Consume an approved action and dispatch it exactly once."""
        request = self.approval_manager.claim_execution(request_id)
        denied = self._authorization_denied_result(request.tool_name, request.tool_args)
        if denied is not None:
            self.approval_manager.complete_execution(request_id, False, "Not authorized")
            return denied
        tool_policy = getattr(self, "tool_policy", None)
        if tool_policy is not None and not tool_policy.is_tool_allowed(request.tool_name):
            logger.warning("Approved tool denied by current policy: %s", request.tool_name)
            result = ToolResult(
                success=False,
                output="",
                error="Tool execution denied by current policy.",
            )
        else:
            result = self._safe_dispatch(
                request.tool_name,
                request.tool_args,
                approval_granted=True,
            )
        summary = "Action completed successfully" if result.success else "Action execution failed"
        completed = self.approval_manager.complete_execution(request_id, result.success, summary)
        self._audit(
            "approval_executed",
            {
                "approval_id": completed.id,
                "tool_name": completed.tool_name,
                "success": result.success,
            },
        )
        return result

    def _audit_cancelled_approvals(self, requests, reason: str) -> None:
        """Persist cancellation outcomes without retaining tool arguments or results."""
        for request in requests:
            self._audit(
                "approval_cancelled",
                {
                    "approval_id": request.id,
                    "tool_name": request.tool_name,
                    "reason": reason,
                },
            )

    def clear_conversation(self) -> dict[str, int]:
        """Remove session history and invalidate pending work for this agent."""
        self.history.clear()
        self._pending_tool_results = []
        self.session_manager.clear_history(self._session_id)
        cancelled_requests = self.approval_manager.cancel_pending_requests()
        self._audit_cancelled_approvals(cancelled_requests, "conversation_cleared")
        return {"cancelled_approvals": len(cancelled_requests)}

    def dispose_session(self) -> None:
        """Release this agent while retaining the audit trail for HTTP sessions."""
        self.history.clear()
        self._pending_tool_results = []
        cancelled_requests = self.approval_manager.cancel_pending_requests()
        self._audit_cancelled_approvals(cancelled_requests, "session_disposed")
        if self._persistent_session:
            self.session_manager.close_session(self._session_id)
            self.session_manager.prune_closed_sessions(
                "http", keep=MAX_PERSISTED_HTTP_SESSIONS
            )
            self.session_manager.close()
            return
        self.session_manager.delete_session(self._session_id)

    def audit_events(self, limit: int = 100) -> list[dict]:
        """Return the redacted persistent audit trail for this session."""
        return self.session_manager.list_audit_events(self._session_id, limit=limit)

    def role_has(self, permission: Permission) -> bool:
        """Whether the acting role grants a permission (unrestricted when unset)."""
        role = getattr(self, "role", None)
        if role is None:
            return True
        return permission in ROLE_PERMISSIONS[role]

    def _authorization_denied_result(self, tool_name: str, tool_args: dict) -> Optional[ToolResult]:
        """Deny high-impact calls the acting role may never perform.

        Routes already reject unauthorized requests, but tool calls are chosen
        by the model, so the decision is repeated here: a role that cannot run
        mutating tools cannot obtain one through prompting either.
        """
        role = getattr(self, "role", None)
        if role is None or self.role_has(Permission.MUTATING_TOOLS):
            return None
        if approval_reason(tool_name, tool_args) is None:
            return None
        self._audit("authorization_denied", {"tool_name": tool_name, "role": role.value})
        return ToolResult(
            success=False,
            output="",
            error=(
                f"Not authorized: role '{role.value}' cannot run '{tool_name}'. "
                "Ask an operator or owner to perform this action."
            ),
        )

    def _approval_required_result(self, tool_name: str, tool_args: dict) -> Optional[ToolResult]:
        """Return an actionable blocked result for unapproved high-impact calls."""
        if not self.require_approval:
            return None
        try:
            request = self.approval_manager.request_for(tool_name, tool_args)
        except RuntimeError as exc:
            return ToolResult(success=False, output="", error=f"Approval queue unavailable: {exc}")
        if request is None:
            return None
        if request.id not in self._audited_approval_ids:
            self._audited_approval_ids.add(request.id)
            self._audit(
                "approval_requested",
                {
                    "approval_id": request.id,
                    "tool_name": request.tool_name,
                    "tool_args": redact_sensitive_data(request.tool_args),
                    "reason": request.reason,
                    "expires_at": request.expires_at,
                },
            )
        return ToolResult(
            success=False,
            output="",
            error=(
                f"Approval required: {request.id}. {request.reason} "
                "Ask the user to approve or deny this action before execution."
            ),
        )

    def _safe_dispatch(self, tool_name: str, tool_args: dict,
                         approval_granted: bool = False) -> ToolResult:
        """Dispatch that never raises: malformed model args (missing params,
        wrong types) become an error result the model can self-correct from.
        Without this, one bad tool call crashes the turn — a 500 on web/API.
        """
        try:
            return self._dispatch_tool(tool_name, tool_args,
                                       approval_granted=approval_granted)
        except Exception as exc:
            logger.error("Tool dispatch failed (%s)", type(exc).__name__)
            return ToolResult(
                success=False, output="",
                error=f"{tool_name} call failed: missing or invalid arguments.",
            )

    def _known_tool_names(self) -> set:
        """Names the model may legally call: schema + external modules + plugins."""
        names = set()
        try:
            for fn in self.tools_schema or []:
                n = (fn.get("function") or {}).get("name")
                if n:
                    names.add(n)
        except Exception:
            pass
        try:
            names.update(getattr(self, "_external_tool_modules", {}) or {})
        except Exception:
            pass
        try:
            for p in getattr(self, "plugins", []) or []:
                if isinstance(p, dict) and p.get("name"):
                    names.add(p["name"])
        except Exception:
            pass
        return names

    def _unknown_tool_result(self, tool_name: str) -> ToolResult:
        return ToolResult(success=False, output="", error=(
            f"Unknown tool: {tool_name}. I can create this tool for you! "
            "Run `hellochusquis build` to create it with AI."))

    def _dispatch_tool(
        self,
        name: str,
        args: dict,
        approval_granted: bool = False,
    ) -> ToolResult:
        def safe_tool_result_failure(tool_name: str) -> ToolResult:
            logger.warning("%s tool returned a failure", tool_name)
            return ToolResult(
                success=False,
                output="",
                error=f"{tool_name} tool failed. Check server logs.",
            )

        def safe_tool_failure(tool_name: str, exc: Exception) -> ToolResult:
            logger.error("%s tool failed (%s)", tool_name, type(exc).__name__)
            return safe_tool_result_failure(tool_name)

        if name == "subagent":
            return handle_subagent_tool(self, args)

        if name == "skill":
            return skills_module.handle_skill_tool(self, args)

        if name == "shell":
            cmd = args.get("command", "")
            unsafe_mode = os.getenv("HELLOCHUSQUIS_UNSAFE_MODE") == "1"
            profile = os.getenv("HELLOCHUSQUIS_PROFILE", "default")
            if not unsafe_mode and profile != "aggressive":
                safety_check = evaluate_command_safety(cmd, self.pool)
                if not safety_check.get("safe", True):
                    risk_msg = safety_check.get("reason", "Potentially unsafe command detected.")
                    logger.warning("Blocked unsafe command: %s", risk_msg)
                    console.print("[bold red]⛔ Blocked unsafe command.[/bold red]")
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
                if approval_granted:
                    # The request owner has already approved this exact action
                    # through the authenticated HTTP approval flow. Do not block
                    # a server worker on a terminal prompt.
                    self.workspace.allowed.append(Path(path).expanduser().resolve())
                    self.files.allow_dir(path)
                else:
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

            except Exception as exc:
                return safe_tool_failure("Browser", exc)

        if name == "web_fetch":
            result = self.web_fetch.run(**args)
            if isinstance(result, ToolResult) and not result.success:
                return safe_tool_result_failure("Web fetch")
            return result

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
                return safe_tool_result_failure("Voice")
            except Exception as exc:
                return safe_tool_failure("Voice", exc)

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
            except Exception as exc:
                return safe_tool_failure("Media", exc)

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
                    if not result.get("success", False):
                        return safe_tool_result_failure("MCP")
                    return ToolResult(success=True, output=str(result.get("data", "")))
                else:
                    return ToolResult(success=False, output="", error=f"Unknown MCP action: {action}")
            except Exception as exc:
                return safe_tool_failure("MCP", exc)

        # External tool modules - call run() directly from module
        if name in self._external_tool_modules:
            try:
                module = self._external_tool_modules[name]
                result = module.run(**args)
                if isinstance(result, ToolResult):
                    # Some modules return ToolResult directly — preserve only safe failures.
                    return result if result.success else safe_tool_result_failure(name)
                text = str(result)
                # Treat "Error: ..." prefixed strings as failures so the LLM
                # sees accurate success flags instead of a success-wrapped error
                if isinstance(result, str) and result.lower().startswith("error"):
                    return safe_tool_result_failure(name)
                return ToolResult(success=True, output=text)
            except Exception as exc:
                return safe_tool_failure(name, exc)

        for plugin in self.plugins:
            if plugin["name"] == name:
                try:
                    result_text = plugin["run"](**args)
                    return ToolResult(success=True, output=str(result_text))
                except Exception as exc:
                    return safe_tool_failure(name, exc)

        return self._unknown_tool_result(name)


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
            "Answer directly in text when no tool is needed (greetings, small talk, "
            "questions you can already answer) — never call tools for those. "
            "A greeting gets one friendly sentence and nothing else. "
            "Use tools only when the task needs "
            "external action or information you don't have. "
            "For file operations, use the 'files' tool. "
            "For running commands, use the 'shell' tool. "
            "For executing code, use the 'code' tool. "
            "NEVER say 'I cannot' or 'I don't have' when a tool can do the work.\n\n"
            "You must follow this thought process for every turn:\n"
            "1. <thought>: Decide if a tool is needed; if not, answer directly.\n"
            "2. <call>: Execute the tool immediately (only when needed).\n"
            "3. <verify>: Check if the result solves the request.\n"
        )

        # Always inject CRITICAL file creation rules — even if old config lacks them
        if "CRITICAL: File Creation Rules" not in system:
            system += (
                "\n## CRITICAL: File Creation Rules\n\n"
                "When user asks you to create, write, or save a file:\n\n"
                "1. You MUST call the `files` tool with these exact parameters:\n"
                "   - `action`: \"write\"\n"
                "   - `path`: The FULL absolute path (e.g. /Users/name/Downloads/file.py)\n"
                "   - `content`: The COMPLETE file content as a string\n\n"
                "2. NEVER just show the code as text. Displaying code in a code block is NOT creating a file.\n\n"
                "3. If creating multiple files, call `files` tool ONCE PER FILE.\n\n"
                "4. After writing, confirm: \"File created at /path/to/file\"\n\n"
                "Example: Tool call: files(action=\"write\", path=\"/Users/name/Downloads/app.py\", content=\"print('hello')\")\n"
                "WRONG: Here's the code:\n```python\nprint('hello')\n```\n"
                "This is just displaying text, NOT creating a file!\n"
            )

        return [{"role": "system", "content": system}, *self.history.get()]

    def _handle_active_learning_trigger(self, tool_name: str, result):
        """Internal hook to trigger active learning on strategic failures."""
        import core.learning as learning
        if not result.success:
            # Strategic failures: Loops, Security, or repeated errors
            error_msg = result.error or ""
            is_strategic = any(kw in error_msg for kw in ["Loop detected", "Security audit", "denied by policy", "ERROR:"])
            
            if is_strategic:
                # The 'Analyst' loop: trigger analysis of current history
                import threading
                def analysis_task():
                    try:
                        learning.analyze_and_learn(self.history.get(), self.pool)
                    except Exception:
                        pass
                
                threading.Thread(target=analysis_task, daemon=True).start()

    def run(
        self,
        user_input: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tool_result_callback=None,
    ) -> str:
        """Run one agent turn, optionally observing tools for this request only."""
        self.history.add("user", user_input)
        self.session_manager.append_message(self._session_id, "user", user_input)

        # Memory commands short-circuit the LLM round-trip (best-effort store).
        command = parse_memory_command(user_input)
        if command:
            action, payload = command
            try:
                if action == "remember":
                    memory._get_store().add_entry(
                        key="note", value=payload, category="fact", importance=6
                    )
                    reply = f"Remembered: {payload}"
                else:
                    reply = f"Forgot {memory.forget_matching(payload)} memories matching '{payload}'."
            except Exception:
                reply = "Memory unavailable right now."
            self.history.add("assistant", reply)
            self.session_manager.append_message(self._session_id, "assistant", reply)
            return reply

        # A failed previous turn can leave tool messages whose assistant
        # tool_calls partner was never persisted — sending them first makes
        # strict providers 400 every following turn. Start each turn clean.
        self._pending_tool_results = []

        messages = self._build_messages()
        recall = memory.recall_context(user_input)
        if recall:
            messages.insert(1, {"role": "system", "content": recall})

        # Hard cap on LLM round-trips per turn: a model that keeps emitting
        # tool calls (or tools that fail instantly) must not spin forever —
        # this was burning ~100% CPU for hours in the field.
        max_tool_iterations = 30
        iterations = 0
        while True:
            iterations += 1
            if iterations > max_tool_iterations:
                self._pending_tool_results = []
                return ("Error: Turn stopped after 30 tool iterations without a final "
                        "answer. Try breaking the task into smaller steps.")
            response = self.pool.chat_with_retry(
                messages, tools=self.tools_schema, provider_name=provider, model=model
            )
            choices = response.get("choices", [])
            if not choices:
                return "Error: No response from AI provider"
            message = choices[0].get("message", {})
            message = with_fenced_tools(message)

            if not message.get("tool_calls"):
                content = message.get("content") or ""
                self.history.add("assistant", content)
                self.session_manager.append_message(self._session_id, "assistant", content)
                # Autolog: searchable turn + curated facts, never fails the turn.
                try:
                    memory.save_turn(user_input, content)
                    for key, value in extract_memory_facts(user_input):
                        memory._get_store().add_entry(
                            key=key, value=value, category="fact", importance=6
                        )
                except Exception:
                    logger.exception("Memory autolog failed")
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

                safe_tool_args = redact_sensitive_data(tool_args)
                if tool_name not in self._known_tool_names():
                    # Hallucinated tool: no UI event, no console noise — the
                    # model just gets the error back and self-corrects.
                    logger.debug("Unknown tool requested: %s", tool_name)
                    result = self._unknown_tool_result(tool_name)
                    self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)
                    self.loop_detector.record_outcome(
                        self._loop_session_state, tool_name, tool_args,
                        error=result.error,
                    )
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"ERROR: {result.error}"
                    }
                    messages.append(tool_msg)
                    step_tool_results.append(tool_msg)
                    continue
                print_tool_call(tool_name, safe_tool_args)
                logger.info(
                    "Tool call: %s(%s)",
                    tool_name,
                    json.dumps(safe_tool_args, default=str)[:200],
                )

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
                            approval_result = self._authorization_denied_result(
                                tool_name, tool_args
                            ) or self._approval_required_result(tool_name, tool_args)
                            if approval_result is not None:
                                result = approval_result
                            else:
                                # --- Plugin hooks: before_tool ---
                                for plugin in self.plugins:
                                    hook_fn = plugin.get("before_tool")
                                    if callable(hook_fn):
                                        try:
                                            hook_fn(tool_name, tool_args)
                                        except Exception:
                                            pass

                                result = self._safe_dispatch(tool_name, tool_args)

                                # --- Plugin hooks: after_tool ---
                                for plugin in self.plugins:
                                    hook_fn = plugin.get("after_tool")
                                    if callable(hook_fn):
                                        try:
                                            hook_fn(tool_name, tool_args, result)
                                        except Exception:
                                            pass
                if not result.success:
                    logger.error("Tool error: %s — %s", tool_name, result.error)
                    self._handle_active_learning_trigger(tool_name, result)

                # --- Loop detector: record call AND its outcome for every
                # path (denied/blocked calls included, so a model cannot
                # spam a denied tool; outcomes let polling tools progress).
                self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)
                self.loop_detector.record_outcome(
                    self._loop_session_state,
                    tool_name,
                    tool_args,
                    result=result.output if result.success else None,
                    error=None if result.success else result.error,
                )
                print_tool_result(result.success, result.output)
                if callable(tool_result_callback):
                    try:
                        tool_result_callback(tool_name, tool_args, result)
                    except Exception as exc:
                        logger.warning("Tool result callback failed: %s", exc)

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.output if result.success else f"ERROR: {result.error}"
                }
                messages.append(tool_msg)
                step_tool_results.append(tool_msg)
            
            # Keep all tool results for this turn for next turn
            self._pending_tool_results.extend(step_tool_results)

    def stream_run(self, user_input: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Yield SSE events instead of returning full string.
        Yields dict payloads: {"type": "chunk"|"tool_call"|"done", ...}
        """
        self.history.add("user", user_input)
        self.session_manager.append_message(self._session_id, "user", user_input)

        command = parse_memory_command(user_input)
        if command:
            action, payload = command
            try:
                if action == "remember":
                    memory._get_store().add_entry(
                        key="note", value=payload, category="fact", importance=6
                    )
                    reply = f"Remembered: {payload}"
                else:
                    reply = f"Forgot {memory.forget_matching(payload)} memories matching '{payload}'."
            except Exception:
                reply = "Memory unavailable right now."
            self.history.add("assistant", reply)
            self.session_manager.append_message(self._session_id, "assistant", reply)
            yield {"type": "chunk", "content": reply}
            yield {"type": "done"}
            return

        # Same rationale as run(): start each turn clean (audit #4).
        self._pending_tool_results = []

        messages = self._build_messages()
        recall = memory.recall_context(user_input)
        if recall:
            messages.insert(1, {"role": "system", "content": recall})

        if self.history.get_token_count(messages) > 8000:
            messages = self.history.optimize_context(max_tokens=4000)

        # Same hard cap as run(): bounded LLM round-trips per turn.
        max_tool_iterations = 30
        iterations = 0
        while True:
            iterations += 1
            if iterations > max_tool_iterations:
                self._pending_tool_results = []
                yield {"type": "chunk", "content": (
                    "Error: Turn stopped after 30 tool iterations without a final "
                    "answer. Try breaking the task into smaller steps.")}
                yield {"type": "done"}
                return
            content_parts: list[str] = []
            tool_calls: list[dict] = []
            stream_error = None
            for event in self.pool.chat_stream(
                messages, tools=self.tools_schema, provider_name=provider, model=model
            ):
                etype = event.get("type")
                if etype == "reasoning":
                    yield {"type": "reasoning", "content": event["content"]}
                elif etype == "chunk":
                    content_parts.append(event["content"])
                    yield {"type": "chunk", "content": event["content"]}
                elif etype == "tool_calls":
                    tool_calls = event["tool_calls"]
                elif etype == "error":
                    stream_error = event.get("message", "stream failed")

            if stream_error and not content_parts and not tool_calls:
                yield {"type": "chunk", "content": f"Error: {stream_error}"}
                yield {"type": "done"}
                return

            if stream_error:
                # Mid-stream drop with partial output: surface it instead of
                # silently saving a truncated answer as a complete turn.
                yield {"type": "error", "message": stream_error}
                yield {"type": "chunk", "content": f"\n\n⚠ Error: {stream_error}"}
                yield {"type": "done"}
                return

            if not tool_calls:
                content = "".join(content_parts)
                self.history.add("assistant", content)
                self.session_manager.append_message(self._session_id, "assistant", content)
                self._pending_tool_results = []
                try:
                    memory.save_turn(user_input, content)
                    for key, value in extract_memory_facts(user_input):
                        memory._get_store().add_entry(
                            key=key, value=value, category="fact", importance=6
                        )
                except Exception:
                    logger.exception("Memory autolog failed")
                yield {"type": "done"}
                return

            message = {
                "role": "assistant",
                "content": "".join(content_parts) or None,
                "tool_calls": [
                    {"id": tc.get("id") or f"call_{i}", "type": "function",
                     "function": tc.get("function", {})}
                    for i, tc in enumerate(tool_calls)
                ],
            }
            message = with_fenced_tools(message)

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
                safe_tool_args = redact_sensitive_data(tool_args)
                if tool_name not in self._known_tool_names():
                    logger.debug("Unknown tool requested: %s", tool_name)
                    result = self._unknown_tool_result(tool_name)
                    self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)
                    self.loop_detector.record_outcome(
                        self._loop_session_state, tool_name, tool_args,
                        error=result.error,
                    )
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"ERROR: {result.error}"
                    }
                    messages.append(tool_msg)
                    step_tool_results.append(tool_msg)
                    continue
                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": safe_tool_args,
                }
                print_tool_call(tool_name, safe_tool_args)
                logger.info(
                    "Stream tool call: %s(%s)",
                    tool_name,
                    json.dumps(safe_tool_args, default=str)[:200],
                )


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
                            approval_result = self._authorization_denied_result(
                                tool_name, tool_args
                            ) or self._approval_required_result(tool_name, tool_args)
                            if approval_result is not None:
                                result = approval_result
                                approval_match = re.search(r"Approval required: (apr_[A-Za-z0-9_-]+)\.", result.error)
                                if approval_match:
                                    approval_id = approval_match.group(1)
                                    pending = next(
                                        (
                                            item for item in self.pending_approvals()
                                            if item["id"] == approval_id
                                        ),
                                        None,
                                    )
                                    if pending is not None:
                                        yield {"type": "approval_required", "approval": pending}
                            else:
                                # --- Plugin hooks: before_tool ---
                                for plugin in self.plugins:
                                    hook_fn = plugin.get("before_tool")
                                    if callable(hook_fn):
                                        try:
                                            hook_fn(tool_name, tool_args)
                                        except Exception:
                                            pass
                                result = self._safe_dispatch(tool_name, tool_args)
                                # --- Plugin hooks: after_tool ---
                                for plugin in self.plugins:
                                    hook_fn = plugin.get("after_tool")
                                    if callable(hook_fn):
                                        try:
                                            hook_fn(tool_name, tool_args, result)
                                        except Exception:
                                            pass
                    # --- Record tool call AND outcome for loop detector ---
                    self.loop_detector.record_call(self._loop_session_state, tool_name, tool_args)
                    self.loop_detector.record_outcome(
                        self._loop_session_state,
                        tool_name,
                        tool_args,
                        result=result.output if result.success else None,
                        error=None if result.success else result.error,
                    )
                if not result.success:
                    logger.error("Stream tool error: %s — %s", tool_name, result.error)
                    self._handle_active_learning_trigger(tool_name, result)

                # TUI consumes this; stdout print would corrupt the textual screen.
                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.output if result.success else result.error,
                }

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
        # Apply retention on shutdown so turn entries don't grow unbounded
        # (audit #7: memory.db hit 200 MB with no TTL).
        try:
            memory.prune_sessions_older_than(retention_days)
        except Exception:
            logger.exception("Memory retention prune failed")
        if len(messages) < 2:
            try:
                self.session_manager.close_session(self._session_id)
            except Exception:
                logger.exception("Session close failed")
            return

        summary_prompt = (
            "Summarize the key facts, tasks completed, and important context "
            "from this conversation in 3-5 bullet points. Be very concise.\n\n"
            + "\n".join(f"{m['role']}: {m['content'][:200]}" for m in messages)
        )

        # Learnings run alongside summarization (independent stores) halve exit cost.
        learn_thread = threading.Thread(
            target=lambda: learning.analyze_and_learn(messages, self.pool, max_retries=1),
            daemon=True,
        )
        learn_thread.start()
        try:
            # ponytail: single attempt — shutdown must not hang on LLM retries.
            response = self.pool.chat_with_retry([
                {"role": "user", "content": summary_prompt}
            ], max_retries=1)
            choices = response.get("choices", [])
            if choices:
                summary = choices[0].get("message", {}).get("content", "")
                memory.save_summary(summary)
        except Exception:
            logger.exception("Summary save failed")
        finally:
            learn_thread.join(timeout=90)

        # Close session
        try:
            self.session_manager.close_session(self._session_id)
        except Exception:
            logger.exception("Session close failed")
