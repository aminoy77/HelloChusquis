import yaml
import httpx
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

console = Console()
CONFIG_PATH = Path("config.yaml")

KNOWN_PROVIDERS = [
    # ============ Major Providers ============
    {"name": "OpenAI",             "base_url": "https://api.openai.com/v1",                    "docs": "platform.openai.com/api-keys",             "category": "Major", "requires_key": True, "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini", "o4-mini"]},
    {"name": "Anthropic Claude",   "base_url": "https://api.anthropic.com/v1",                 "docs": "console.anthropic.com",                    "category": "Major", "requires_key": True, "models": ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest", "claude-sonnet-4-20250514"]},
    {"name": "Google Gemini",      "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "docs": "aistudio.google.com/apikey",      "category": "Major", "requires_key": True, "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]},
    {"name": "xAI (Grok)",         "base_url": "https://api.x.ai/v1",                          "docs": "console.x.ai",                             "category": "Major", "requires_key": True, "models": ["grok-4", "grok-3", "grok-3-mini", "grok-2", "grok-2-mini", "grok-beta"]},
    {"name": "Groq",               "base_url": "https://api.groq.com/openai/v1",               "docs": "console.groq.com/keys",                    "category": "Major", "requires_key": True, "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.2-90b-text-preview", "llama-3.2-11b-vision-preview", "llama-3.2-3b-preview", "llama-3.2-1b-preview", "gemma2-9b-it", "mixtral-8x7b-32768", "qwen-2.5-32b"]},
    {"name": "OpenRouter",         "base_url": "https://openrouter.ai/api/v1",                 "docs": "openrouter.ai/keys",                       "category": "Major", "requires_key": True, "models": ["openrouter/auto", "meta-llama/llama-3.3-70b-instruct:free", "nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-3-27b-it:free", "microsoft/phi-4:free", "mistralai/mistral-small-3.1-24b-instruct:free", "qwen/qwen2.5-coder-7b-instruct:free", "deepseek/deepseek-r1:free", "nousresearch/hermes-3-llama-3.1-405b:free"]},
    {"name": "Perplexity",         "base_url": "https://api.perplexity.ai",                    "docs": "perplexity.ai/settings/api",               "category": "Major", "requires_key": True, "models": ["sonar", "sonar-pro", "sonar-reasoning", "sonar-reasoning-pro", "llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online"]},

    # ============ European Providers ============
    {"name": "Mistral",            "base_url": "https://api.mistral.ai/v1",                    "docs": "console.mistral.ai/api-keys",              "category": "European", "requires_key": True, "models": ["mistral-large-latest", "mistral-small-latest", "mistral-medium-latest", "open-mistral-nemo", "codestral-latest", "pixtral-large-latest"]},
    {"name": "DeepSeek",           "base_url": "https://api.deepseek.com/v1",                  "docs": "platform.deepseek.com/api_keys",            "category": "European", "requires_key": True, "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"name": "Cohere",             "base_url": "https://api.cohere.com/v1",                    "docs": "dashboard.cohere.com/api-keys",             "category": "European", "requires_key": True, "models": ["command-r-plus", "command-r", "command-r7b-02-2025", "command-a"]},
    {"name": "Aleph Alpha",        "base_url": "https://api.aleph-alpha.com/v1",               "docs": "aleph-alpha.com",                          "category": "European", "requires_key": True, "models": ["luminous-supreme-control", "luminous-base-control"]},
    {"name": "Writer",             "base_url": "https://api.writer.com/v1",                    "docs": "writer.com",                               "category": "European", "requires_key": True, "models": ["palmyra-x-004", "palmyra-medical-70b-004", "palmyra-fin-70b-004"]},

    # ============ Chinese Providers ============
    {"name": "Qwen / Alibaba",     "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "docs": "dashscope.aliyuncs.com",      "category": "Chinese", "requires_key": True, "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct", "qwen2.5-7b-instruct", "qwen2.5-coder-32b-instruct"]},
    {"name": "MiniMax",            "base_url": "https://api.minimax.chat/v1",                  "docs": "platform.minimax.io",                      "category": "Chinese", "requires_key": True, "models": ["MiniMax-Text-01", "abab6.5s-chat", "abab6.5-chat", "MiniMax-M1"]},
    {"name": "Baichuan",           "base_url": "https://api.baichuan-ai.com/v1",               "docs": "platform.baichuan-ai.com",                  "category": "Chinese", "requires_key": True, "models": ["Baichuan4", "Baichuan3-Turbo", "Baichuan2-Turbo"]},
    {"name": "Zhipu (ChatGLM)",    "base_url": "https://open.bigmodel.cn/api/paas/v4",         "docs": "open.bigmodel.cn",                         "category": "Chinese", "requires_key": True, "models": ["glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4-long", "glm-4-0520", "glm-4v-plus", "glm-4v-flash"]},
    {"name": "Moonshot",           "base_url": "https://api.moonshot.cn/v1",                   "docs": "platform.moonshot.cn",                     "category": "Chinese", "requires_key": True, "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k", "kimi-latest"]},
    {"name": "StepFun",            "base_url": "https://api.stepfun.com/v1",                   "docs": "platform.stepfun.com",                     "category": "Chinese", "requires_key": True, "models": ["step-2-16k", "step-1-8k", "step-1-32k", "step-1-128k", "step-1v-8k", "step-1o-32k"]},
    {"name": "SiliconFlow",        "base_url": "https://api.siliconflow.cn/v1",                "docs": "cloud.siliconflow.cn",                     "category": "Chinese", "requires_key": True, "models": ["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen2.5-72B-Instruct", "Qwen/QwQ-32B-Preview", "THUDM/glm-4-9b-chat", "meta-llama/Llama-3.3-70B-Instruct"]},
    {"name": "Volcengine (Doubao)", "base_url": "https://ark.cn-beijing.volces.com/api/v3",    "docs": "console.volcengine.com/ark",               "category": "Chinese", "requires_key": True, "models": ["doubao-pro-32k", "doubao-pro-128k", "doubao-lite-32k", "doubao-1.5-pro-32k", "doubao-1.5-lite-32k"]},
    {"name": "Baidu Qianfan",      "base_url": "https://qianfan.baidubce.com/v2",              "docs": "console.bce.baidu.com/qianfan",            "category": "Chinese", "requires_key": True, "models": ["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k", "ernie-speed-8k", "ernie-lite-8k"]},
    {"name": "Tencent Hunyuan",    "base_url": "https://api.hunyuan.cloud.tencent.com/v1",     "docs": "cloud.tencent.com/product/hunyuan",        "category": "Chinese", "requires_key": True, "models": ["hunyuan-turbos-latest", "hunyuan-turbo-latest", "hunyuan-pro", "hunyuan-lite", "hunyuan-standard"]},

    # ============ AI Platforms ============
    {"name": "Together AI",        "base_url": "https://api.together.xyz/v1",                  "docs": "api.together.ai/settings/api-keys",         "category": "AI Platforms", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.1-405B-Instruct-Turbo", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"]},
    {"name": "Fireworks AI",       "base_url": "https://api.fireworks.ai/inference/v1",        "docs": "fireworks.ai/account/api-keys",            "category": "AI Platforms", "requires_key": True, "models": ["accounts/fireworks/models/llama-v3p3-70b-instruct", "accounts/fireworks/models/llama-v3p1-70b-instruct", "accounts/fireworks/models/qwen2p5-72b-instruct", "accounts/fireworks/models/deepseek-v3", "accounts/fireworks/models/mixtral-8x7b-instruct"]},
    {"name": "Novita AI",          "base_url": "https://api.novita.ai/v3/openai",              "docs": "novita.ai/settings/key-management",         "category": "AI Platforms", "requires_key": True, "models": ["meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-v3", "qwen/qwen2.5-72b-instruct", "mistralai/mixtral-8x7b-instruct"]},
    {"name": "Lepton AI",          "base_url": "https://api.lepton.ai/httpapi/v1",             "docs": "dashboard.lepton.ai",                      "category": "AI Platforms", "requires_key": True, "models": ["llama3-3-70b", "llama3-1-70b", "qwen2-72b", "mixtral-8x7b"]},
    {"name": "Hyperbolic",         "base_url": "https://api.hyperbolic.xyz/v1",                "docs": "hyperbolic.xyz/dashboard",                 "category": "AI Platforms", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.1-405B-Instruct", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]},
    {"name": "SambaNova",          "base_url": "https://api.sambanova.ai/v1",                  "docs": "cloud.sambanova.ai",                       "category": "AI Platforms", "requires_key": True, "models": ["Meta-Llama-3.3-70B-Instruct", "Meta-Llama-3.1-8B-Instruct", "Qwen2.5-72B-Instruct", "DeepSeek-R1-Distill-Llama-70B"]},
    {"name": "Cerebras",           "base_url": "https://api.cerebras.ai/v1",                   "docs": "cloud.cerebras.ai",                        "category": "AI Platforms", "requires_key": True, "models": ["llama-3.3-70b", "llama-3.1-8b", "llama-3.1-70b"]},
    {"name": "NVIDIA NIM",         "base_url": "https://integrate.api.nvidia.com/v1",          "docs": "build.nvidia.com",                         "category": "AI Platforms", "requires_key": True, "models": ["meta/llama-3.3-70b-instruct", "deepseek-ai/deepseek-r1", "nvidia/llama-3.1-nemotron-70b-instruct", "qwen/qwen2.5-72b-instruct"]},
    {"name": "DeepInfra",          "base_url": "https://api.deepinfra.com/v1/openai",          "docs": "deepinfra.com/dash/api_keys",              "category": "AI Platforms", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"]},
    {"name": "FriendliAI",         "base_url": "https://api.friendli.ai/server/v1",            "docs": "friendli.ai/console",                      "category": "AI Platforms", "requires_key": True, "models": ["meta-llama-3.3-70b-instruct", "deepseek-r1", "qwen2.5-72b-instruct"]},
    {"name": "Jina AI",            "base_url": "https://api.jina.ai/v1",                       "docs": "jina.ai",                                  "category": "AI Platforms", "requires_key": True, "models": ["jina-chat-v3", "jina-embeddings-v3", "reader-latest"]},
    {"name": "Baseten",            "base_url": "https://model-{id}.api.baseten.co/v1",         "docs": "baseten.co",                               "category": "AI Platforms", "requires_key": True, "models": ["meta-llama-3.3-70b-instruct", "deepseek-r1"]},
    {"name": "Modal",              "base_url": "https://api.modal.com/v1",                     "docs": "modal.com",                                "category": "AI Platforms", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct", "deepseek-ai/DeepSeek-R1"]},

    # ============ Open Source Focused ============
    {"name": "Blackbox AI",        "base_url": "https://api.blackbox.ai/v1",                   "docs": "blackbox.ai",                              "category": "Open Source", "requires_key": True, "models": ["blackbox-pro", "blackbox-mini", "llama-3.1-70b"]},
    {"name": "Xiaomi (MiMo)",      "base_url": "https://api.mimo.xiaomi.com/v1",               "docs": "mimo.xiaomi.com",                          "category": "Open Source", "requires_key": True, "models": ["MiMo-7B-RL", "MiMo-7B-SFT"]},
    {"name": "Replicate",          "base_url": "https://api.replicate.com/v1",                 "docs": "replicate.com/account/tokens",             "category": "Open Source", "requires_key": True, "models": ["meta/meta-llama-3-70b-instruct", "meta/meta-llama-3.1-405b-instruct", "deepseek-ai/deepseek-r1"]},
    {"name": "HuggingFace",        "base_url": "https://api-inference.huggingface.co/v1",      "docs": "huggingface.co/settings/tokens",           "category": "Open Source", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.1-70B", "Qwen/Qwen2.5-72B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"]},
    {"name": "Anyscale",           "base_url": "https://api.endpoints.anyscale.com/v1",        "docs": "anyscale.com",                             "category": "Open Source", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.1-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"]},
    {"name": "Beam",               "base_url": "https://api.beam.cloud/v1",                    "docs": "beam.cloud/dashboard",                     "category": "Open Source", "requires_key": True, "models": ["meta-llama/Llama-3.3-70B-Instruct"]},

    # ============ Local Models ============
    {"name": "Ollama (local)",     "base_url": "http://localhost:11434/v1",                    "docs": "ollama.ai — runs locally, no API key needed", "category": "Local", "requires_key": False, "models": ["llama3.2", "llama3.1", "qwen2.5-coder", "codellama", "mistral", "phi3", "gemma2", "deepseek-r1"]},
    {"name": "LM Studio (local)",  "base_url": "http://localhost:1234/v1",                     "docs": "lmstudio.ai — local, no API key needed",    "category": "Local", "requires_key": False, "models": ["local-model", "llama-3.3-70b-instruct", "qwen2.5-72b-instruct"]},
    {"name": "vLLM (local)",       "base_url": "http://localhost:8000/v1",                     "docs": "docs.vllm.ai — local, no API key needed",   "category": "Local", "requires_key": False, "models": ["local-model"]},
    {"name": "Jan (local)",        "base_url": "http://localhost:1337/v1",                     "docs": "jan.ai — local, no API key needed",         "category": "Local", "requires_key": False, "models": ["local-model"]},
    {"name": "TextGen WebUI (local)", "base_url": "http://localhost:5000/v1",                  "docs": "github.com/oobabooga/text-generation-webui — local", "category": "Local", "requires_key": False, "models": ["local-model"]},
    {"name": "LocalAI (local)",    "base_url": "http://localhost:8080/v1",                     "docs": "localai.io — local, no API key needed",     "category": "Local", "requires_key": False, "models": ["local-model"]},

    # ============ Enterprise ============
    {"name": "Azure OpenAI",       "base_url": "https://YOUR_RESOURCE.openai.azure.com/openai/v1", "docs": "azure.com",                            "category": "Enterprise", "requires_key": True, "models": ["gpt-4o", "gpt-4o-mini", "gpt-35-turbo"]},
    {"name": "AWS Bedrock",        "base_url": "https://bedrock-runtime.{region}.amazonaws.com", "docs": "aws.amazon.com/bedrock",                "category": "Enterprise", "requires_key": True, "models": ["anthropic.claude-v2", "meta.llama3-70b-instruct-v1", "amazon.titan-text-express-v1"]},
    {"name": "Vertex AI",          "base_url": "https://{location}-aiplatform.googleapis.com/v1", "docs": "cloud.google.com/vertex-ai",             "category": "Enterprise", "requires_key": True, "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro"]},

    # ============ Specialized ============
    {"name": "Nomic",              "base_url": "https://api-atlas.nomic.ai/v1",                "docs": "nomic.ai",                               "category": "Specialized", "requires_key": True, "models": ["nomic-embed-text-v1.5", "nomic-embed-text-v1"]},
    {"name": "AI21 (Jamba)",       "base_url": "https://api.ai21.com/studio/v1",               "docs": "ai21.com",                               "category": "Specialized", "requires_key": True, "models": ["jamba-1.5-large", "jamba-1.5-mini", "jamba-instruct-preview"]},
    {"name": "TextCortex",         "base_url": "https://api.textcortex.com/v1",                "docs": "textcortex.com",                         "category": "Specialized", "requires_key": True, "models": ["sophos-2", "hermes-2-pro"]},

    # ============ Custom ============
    {"name": "Custom / Other",     "base_url": "",                                             "docs": "",                                       "category": "Custom", "requires_key": True, "models": []},
]

VERIFIED_OPENROUTER_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-3-27b-it:free",
    "microsoft/phi-4:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen2.5-coder-7b-instruct:free",
    "deepseek/deepseek-r1:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]

VERIFIED_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

VERIFIED_OLLAMA_MODELS = [
    "llama3.2",
    "llama3.1",
    "qwen2.5-coder",
    "codellama",
    "mistral",
    "phi3",
]

SYSTEM_PROMPT = """You are HelloChusquis — a brilliant AI assistant who lives in the terminal. You're friendly, slightly witty, and genuinely helpful. Think of yourself as a genius friend who happens to have superpowers.

Your name is Chusquis (or HelloChusquis). You speak naturally. You don't overthink. You just get things done.

## Your Superpowers

You have serious tools. Use them freely:

- **Shell** — Run any terminal command: git, npm, pip, brew, system ops, compilation, scripting. Full system access.
- **Python** — Execute code instantly. Data processing, math, algorithms, JSON, testing, anything.
- **Files** — Read, write, create, delete, list directories. Full filesystem control.
- **Web Search** — DuckDuckGo search with browser fallback. Find anything online.
- **Web Fetch** — Extract content from any URL. Scrape, read, analyze.
- **Browser** — Full Playwright automation. Navigate, click, type, screenshot, fill forms, scroll. Anti-detection enabled.
- **Documents** — Generate real PDF and DOCX files. Not fake text — actual downloadable documents.
- **Voice** — Text-to-speech generation.
- **40+ Integrations** — GitHub, Slack, Discord, Docker, Notion, Gmail, Jira, and more.
- **Image Processing** — Manipulate and generate images.
- **Utilities** — Weather, stocks, crypto, calculator, world clocks, currency conversion.

## How You Work

**Act, don't narrate.** Never say "I would do X." Just do X. Show results, not process.

**End-to-end execution.** Complete the full task in one response when possible. Generate a plan for complex tasks, execute every step, summarize what got done.

**Absolute paths always.** `/Users/name/file.txt` not `./file.txt`. Never ambiguous.

**Real outputs only.** Never fake file contents, command results, or API responses. If you can't do it, say so.

**Fail loudly.** If something breaks, say exactly what failed and why. Then suggest the next step.

## Response Style

- **Be helpful and thorough.** Give complete answers, not half-answers.
- **Show results clearly.** Use formatting: code blocks, lists, sections.
- **When searching**, show multiple results with titles and URLs.
- **When running code**, show the output clearly.
- **When creating files**, confirm what was done and show the path.
- **Explain what you're doing** briefly — don't leave users guessing.
- **Be concise but complete.** No rambling, no missing info.

## Output Formatting

- Use emojis sparingly 🎯 for visual clarity, not decoration.
- Structure responses with clear sections and headers.
- Show URLs as clickable links.
- Code always in fenced blocks with language tag.
- Long outputs: summarize, offer to show full output.
- Errors: exact message + what you tried + next step.

## Language

- **Default to English.**
- **Switch to Spanish** when the user writes in Spanish. Match their language naturally.

## Tool Usage

- Use tools immediately — don't ask unnecessary questions.
- Show tool results in readable format.
- For web searches: nice list with titles + URLs.
- For code: show output clearly.
- For files: confirm path and what was saved.

## CRITICAL: File Creation Rules

When user asks you to create, write, or save a file:

1. **You MUST call the `files` tool** with these exact parameters:
   - `action`: "write"
   - `path`: The FULL absolute path (e.g. `/Users/name/Downloads/file.py`)
   - `content`: The COMPLETE file content as a string

2. **NEVER just show the code as text.** Displaying code in a code block is NOT creating a file. The user wants the file on disk.

3. **If creating multiple files**, call `files` tool ONCE PER FILE.

4. **If creating a directory first**, call `files` with `action: "create_dir"`, then call `files` with `action: "write"` for each file.

5. **After writing**, confirm: "File created at /path/to/file"

Example of CORRECT behavior:
```
Tool call: files(action="create_dir", path="/Users/name/Downloads/myapp")
Tool call: files(action="write", path="/Users/name/Downloads/myapp/main.py", content="print('hello')")
Tool call: files(action="write", path="/Users/name/Downloads/myapp/README.md", content="# My App")
Response: Created project at /Users/name/Downloads/myapp with 2 files.
```

Example of WRONG behavior (DO NOT DO THIS):
```
Response: Here's the code:
```python
print('hello')
```
```
This is just displaying text, NOT creating a file!

## Decision Framework

1. Does this need a tool? → Use it. Don't describe using it.
2. Multi-step task? → Plan it, execute fully, summarize.
3. Step failed? → Try alternative before giving up.
4. User asks for a file? → Call `files` tool with `action: "write"`. NEVER just show content as text.
5. Plugin missing? → "I don't have a [X] plugin installed. Want me to build one?" Then build it.

## Memory

You have access to conversation history summaries. Use them. Never ask for information you already have. Reference past context naturally."""

def fetch_available_models(base_url: str, api_key: str, provider_name: str = "") -> list[str]:
    """Fetch ALL models for a provider.

    Strategy: hit the live ``/models`` endpoint first; merge in the known
    catalog models for that provider so the list is never empty. Falls back
    to the catalog entirely if the endpoint fails.
    """
    base = base_url.rstrip("/")

    # Known models from the catalog (per-provider defaults)
    known: list[str] = []
    for p in KNOWN_PROVIDERS:
        if p["name"].lower() == provider_name.lower() or (
            p["base_url"] and p["base_url"].rstrip("/") == base
        ):
            known = list(p.get("models", []))
            break
    if not known:
        if "openrouter.ai" in base:
            known = list(VERIFIED_OPENROUTER_MODELS)
        elif "groq.com" in base:
            known = list(VERIFIED_GROQ_MODELS)
        elif "localhost:11434" in base:
            known = list(VERIFIED_OLLAMA_MODELS)

    live: list[str] = []
    try:
        with httpx.Client(timeout=10) as client:
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            r = client.get(f"{base}/models", headers=headers)
            r.raise_for_status()
            data = r.json()
            live = [m["id"] for m in data.get("data", data.get("models", []))]
    except Exception:
        live = []

    # Merge: known first (stable defaults), then live models not already present.
    seen = set(known)
    merged = list(known)
    for m in live:
        if m not in seen:
            seen.add(m)
            merged.append(m)
    return merged


def pick_provider() -> dict:
    """Show ALL providers grouped by category; user picks any one."""
    console.print(Panel(
        "[bold]Choose a provider from the full list[/bold]\n"
        "[dim]All available providers are shown below, grouped by category.[/dim]",
        expand=False,
    ))

    rows: list[tuple[str, dict]] = []
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(width=4)
    table.add_column(width=24)
    table.add_column()
    current_category = None
    for i, p in enumerate(KNOWN_PROVIDERS):
        cat = p.get("category", "Other")
        if cat != current_category:
            table.add_row("", f"[bold yellow]{cat.upper()}[/bold yellow]", "")
            current_category = cat
        local_tag = " [dim](no key needed)[/dim]" if not p.get("requires_key", True) else ""
        table.add_row(
            f"[cyan]{i+1}[/cyan]",
            f"[bold]{p['name']}[/bold]{local_tag}",
            f"[dim]{p['docs']}[/dim]",
        )
        rows.append((i + 1, p))
    console.print(table)

    while True:
        choice = Prompt.ask("  Pick a provider (number)", default="1")
        try:
            num = int(choice)
        except ValueError:
            console.print("[red]Enter a valid number.[/red]")
            continue
        if 1 <= num <= len(rows):
            break
        console.print(f"[red]Number must be between 1 and {len(rows)}.[/red]")

    selected = rows[num - 1][1]

    if selected["name"] == "Custom / Other":
        base_url = Prompt.ask("  Base URL")
    else:
        base_url = selected["base_url"]
        console.print(f"  [dim]Get your API key at: {selected['docs']}[/dim]")

    return {"name": selected["name"], "base_url": base_url, "requires_key": selected.get("requires_key", True), "models": selected.get("models", [])}


def pick_model(base_url: str, api_key: str, provider_name: str = "", known_models: list = None) -> str:
    console.print("\n  [dim]Fetching available models...[/dim]")
    models = fetch_available_models(base_url, api_key, provider_name=provider_name)

    if not models and known_models:
        models = list(known_models)
    if not models:
        # Last resort: manual entry
        console.print("  [yellow]Could not fetch models. Enter manually:[/yellow]")
        return Prompt.ask("  Model name", default="llama-3.3-70b-versatile")

    console.print(f"  [dim]({len(models)} models available)[/dim]")
    # Paginate: show all, let user type a number OR search text
    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, m in enumerate(models):
        table.add_row(f"[cyan]{i+1}[/cyan]", m)
    console.print(table)

    while True:
        choice = Prompt.ask("  Pick a model (number or type to search)", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]
            console.print(f"[red]Number must be between 1 and {len(models)}.[/red]")
        except ValueError:
            # text search
            matches = [m for m in models if choice.strip().lower() in m.lower()]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                console.print("  [dim]Multiple matches:[/dim]")
                for j, m in enumerate(matches):
                    console.print(f"    [cyan]{j+1}[/cyan] {m}")
                sub = Prompt.ask("  Pick one (number)", default="1")
                try:
                    return matches[int(sub) - 1]
                except (ValueError, IndexError):
                    console.print("[red]Invalid choice, using first match.[/red]")
                    return matches[0]
            else:
                console.print("[red]No matching model. Try again.[/red]")


def _validate_api_key(api_key: str) -> bool:
    """Return True if api_key is non-empty after stripping whitespace."""
    return bool(api_key and api_key.strip())


def _prompt_api_key(provider_name: str, existing_key: str = "") -> str:
    """Prompt for API key with validation loop. Keeps existing key if user blanks out."""
    while True:
        f"  API Key [{existing_key[:4]}***]" if existing_key else "  API Key"
        api_key = Prompt.ask(f"[bold]Paste your API key for {provider_name}[/bold]", password=True)
        if not api_key or not api_key.strip():
            if existing_key:
                console.print("  [dim]Keeping existing key.[/dim]")
                return existing_key
            console.print("[red]API key cannot be empty. Try again or press Ctrl+C to cancel.[/red]")
            continue
        return api_key.strip()


def _check_providers_valid(config: dict) -> None:
    """Warn if config has no valid providers configured."""
    providers = config.get("providers", [])
    has_ollama = any(
        "ollama" in p.get("base_url", "").lower() or p.get("api_key") == "ollama"
        for p in providers
    )
    has_valid_key = any(
        p.get("api_key") and p["api_key"] != "ollama" and len(p["api_key"].strip()) > 0
        for p in providers
    )
    if not has_ollama and not has_valid_key:
        console.print("\n[bold yellow]⚠ No valid providers configured.[/bold yellow]")
        console.print("[yellow]Chat will fail until you add an API key.[/yellow]")
        console.print("[dim]Run: hellochusquis config[/dim]\n")


def run_setup():
    console.print(Panel(
        "[bold #f5a623]HelloChusquis Setup[/bold #f5a623]\n"
        "[dim]Configure your AI providers[/dim]\n\n"
        "[yellow]⚠ Recommended: add at least 2 providers for fallback.[/yellow]",
        expand=False
    ))

    console.print("\n[dim]Tip: Start with Groq (fastest, free) then OpenRouter as fallback.[/dim]\n")

    providers = []
    priority = 1

    while True:
        console.print(f"\n[bold]Provider #{priority}[/bold]")
        provider_info = pick_provider()
        if provider_info.get("requires_key"):
            api_key = _prompt_api_key(provider_info["name"])
        else:
            api_key = "ollama" if "ollama" in provider_info["name"].lower() else ""
            console.print(f"  [dim]✓ {provider_info['name']} runs locally — no API key needed.[/dim]")
        model = pick_model(
            provider_info["base_url"],
            api_key,
            provider_name=provider_info["name"],
            known_models=provider_info.get("models", []),
        )

        providers.append({
            "name": f"{provider_info['name']}-{priority}",
            "base_url": provider_info["base_url"],
            "api_key": api_key,
            "model": model,
            "priority": priority,
        })

        console.print(f"  [#5eb97e]✓[/#5eb97e] Added: [bold]{provider_info['name']}[/bold] → [cyan]{model}[/cyan]")
        priority += 1

        if priority == 2:
            add_more = Confirm.ask("\n  Add another provider? [yellow](recommended)[/yellow]", default=True)
        else:
            add_more = Confirm.ask("\n  Add another provider?", default=False)

        if not add_more:
            if priority == 2:
                console.print("  [yellow]⚠ Only one provider. If it fails, HelloChusquis will stop.[/yellow]")
            break

    reset_hours = IntPrompt.ask(
        "\nReset exhausted providers after how many hours?",
        default=1
    )

    retention_days = IntPrompt.ask(
        "Delete old sessions after how many days?",
        default=30
    )

    workspace = Prompt.ask(
        "Default workspace directory",
        default=str(Path.home() / "workspace")
    )

    config = {
        "providers": providers,
        "settings": {
            "provider_reset_hours": reset_hours,
            "max_retries": 3,
            "timeout_seconds": 15,
            "workspace_dirs": [workspace],
            "memory_retention_days": retention_days,
        },
        "agent": {
            "system_prompt": SYSTEM_PROMPT
        }
    }

    config_dir = Path.home() / ".hellochusquis"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[#5eb97e]✓ Config saved to {config_path}[/#5eb97e]")
    _check_providers_valid(config)
    return config


def run_quick_setup() -> dict:
    """First-run setup: choose 1 provider from the ENTIRE list, then a model."""
    from rich.console import Console

    console = Console()

    console.print(Panel(
        "[bold #f5a623]Welcome to HelloChusquis![/bold #f5a623]\n"
        "[dim]One-time setup — pick any provider, add your key, choose a model.[/dim]",
        expand=False,
    ))

    # Step 1: pick a provider from the full catalog
    provider_info = pick_provider()

    # Step 2: local providers skip the key; others must have one
    if not provider_info["requires_key"]:
        api_key = "ollama" if "ollama" in provider_info["name"].lower() else ""
        console.print(f"  [dim]✓ {provider_info['name']} runs locally — no API key needed.[/dim]")
    else:
        api_key = _prompt_api_key(provider_info["name"])

    # Step 3: pick a model from ALL available models
    model = pick_model(
        provider_info["base_url"],
        api_key,
        provider_name=provider_info["name"],
        known_models=provider_info.get("models", []),
    )

    config = {
        "providers": [{
            "name": provider_info["name"],
            "base_url": provider_info["base_url"],
            "api_key": api_key,
            "model": model,
            "priority": 1,
        }],
        "settings": {
            "provider_reset_hours": 1,
            "max_retries": 3,
            "timeout_seconds": 15,
            "workspace_dirs": [str(Path.home() / ".hellochusquis" / "workspace")],
            "memory_retention_days": 30,
        },
        "agent": {
            "system_prompt": SYSTEM_PROMPT
        }
    }

    config_dir = Path.home() / ".hellochusquis"
    config_dir.mkdir(parents=True, exist_ok=True)
    workspace_path = config_dir / "workspace"
    workspace_path.mkdir(parents=True, exist_ok=True)
    config["settings"]["workspace_dirs"] = [str(workspace_path)]

    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print("\n[#5eb97e]✓ Ready. Starting HelloChusquis...[/#5eb97e]")
    console.print(f"[dim]Config saved to: {config_path}[/dim]")
    console.print(f"[dim]Provider: {provider_info['name']} → {model}[/dim]")
    _check_providers_valid(config)
    return config


def ensure_config(
    quick: bool = False, full: bool = False, interactive: bool = True
) -> dict:
    """Load configuration, optionally starting the terminal setup wizard.

    Interactive clients may guide a first-time user through setup. Services
    such as the REST API and web UI must pass ``interactive=False`` so that a
    missing configuration becomes a recoverable readiness state rather than an
    input prompt that blocks process startup.
    """
    # Busca config en varias ubicaciones posibles
    possible_paths = [
        Path("config.yaml"),
        Path.home() / "config.yaml",
        Path.home() / ".hellochusquis" / "config.yaml",
    ]

    for path in possible_paths:
        if path.exists():
            with open(path) as f:
                config = yaml.safe_load(f) or {}
            # Actualiza system prompt si es viejo
            if "agent" not in config:
                config["agent"] = {"system_prompt": SYSTEM_PROMPT}
            elif len(config["agent"].get("system_prompt", "")) < 100:
                config["agent"]["system_prompt"] = SYSTEM_PROMPT
            return config

    if not interactive:
        searched = ", ".join(str(path) for path in possible_paths)
        raise FileNotFoundError(
            "No provider configuration found. Run 'hellochusquis setup' first. "
            f"Searched: {searched}"
        )

    # No config found - use quick setup by default, or full if requested
    if full:
        console.print("[yellow]No config found. Running full setup...[/yellow]\n")
        return run_setup()
    console.print("[yellow]No config found. Running quick setup...[/yellow]\n")
    return run_quick_setup()


def edit_config(section: str = None):
    """Edit configuration interactively."""
    config = ensure_config()
    
    console.print(Panel(
        "[bold #f5a623]HelloChusquis Config[/bold #f5a623]\n"
        "[dim]Update your configuration[/dim]",
        expand=False
    ))
    
    if section == "providers" or section is None:
        console.print("\n[bold cyan]Providers Configuration[/bold cyan]")
        providers = config.get("providers", [])
        
        # Edit each provider
        for i, p in enumerate(providers):
            console.print(f"\n[bold]Provider #{i+1}: {p['name']}[/bold]")
            
            name = Prompt.ask(f"  Name [{p.get('name', '')}]", default=p.get("name", ""))
            base_url = Prompt.ask(f"  Base URL [{p.get('base_url', '')}]", default=p.get("base_url", ""))
            current_key = p.get("api_key", "")
            api_key_label = "***" + current_key[-4:] if current_key else ""
            api_key = Prompt.ask(f"  API Key [{api_key_label}]", default="")
            if not api_key:
                api_key = current_key
            model = Prompt.ask(f"  Model [{p.get('model', '')}]", default=p.get("model", ""))
            
            providers[i] = {
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "priority": p.get("priority", i + 1),
            }
        
        # Add new provider
        add_new = Confirm.ask("\n  Add another provider?", default=False)
        priority = len(providers) + 1
        while add_new:
            provider_info = pick_provider()
            if provider_info.get("requires_key"):
                api_key = _prompt_api_key(provider_info["name"])
            else:
                api_key = "ollama" if "ollama" in provider_info["name"].lower() else ""
                console.print(f"  [dim]✓ {provider_info['name']} runs locally — no API key needed.[/dim]")
            model = pick_model(
                provider_info["base_url"],
                api_key,
                provider_name=provider_info["name"],
                known_models=provider_info.get("models", []),
            )
            providers.append({
                "name": f"{provider_info['name']}-{priority}",
                "base_url": provider_info["base_url"],
                "api_key": api_key,
                "model": model,
                "priority": priority,
            })
            priority += 1
            add_new = Confirm.ask("  Add another?", default=False)
        
        config["providers"] = providers
    
    if section == "api-keys" or section is None:
        console.print("\n[bold cyan]API Keys[/bold cyan]")
        providers = config.get("providers", [])
        for i, p in enumerate(providers):
            current_key = p.get("api_key", "")
            api_key_label = "***" + current_key[-4:] if current_key else ""
            console.print(f"  {p['name']}: [{api_key_label}]")
            try:
                new_key = input(f"  Enter new key for {p['name']} (press Enter to keep current): ")
            except EOFError:
                new_key = ""
            if new_key:
                providers[i]["api_key"] = new_key
                console.print("    ✓ Updated")
            else:
                console.print("    ✓ Kept existing")
        config["providers"] = providers
    
    if section == "settings" or section is None:
        console.print("\n[bold cyan]Settings[/bold cyan]")
        settings = config.get("settings", {})
        
        reset_hours = IntPrompt.ask(
            "  Reset exhausted providers after how many hours?",
            default=settings.get("provider_reset_hours", 1)
        )
        
        retention_days = IntPrompt.ask(
            "  Delete old sessions after how many days?",
            default=settings.get("memory_retention_days", 30)
        )
        
        workspace = Prompt.ask(
            "  Default workspace directory",
            default=settings.get("workspace_dirs", [str(Path.home() / "workspace")])[0]
        )
        
        config["settings"] = {
            "provider_reset_hours": reset_hours,
            "max_retries": 3,
            "timeout_seconds": 15,
            "workspace_dirs": [workspace],
            "memory_retention_days": retention_days,
        }
    
    config_dir = Path.home() / ".hellochusquis"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[#5eb97e]✓ Config saved to {config_path}[/#5eb97e]")
    _check_providers_valid(config)
    return config


def show_config():
    """Show current configuration with masked API keys without prompting."""
    try:
        config = ensure_config(interactive=False)
    except FileNotFoundError:
        console.print("[yellow]No configuration found. Run: hellochusquis setup[/yellow]")
        return None

    console.print(Panel(
        "[bold #f5a623]HelloChusquis Configuration[/bold #f5a623]",
        expand=False
    ))
    
    providers = config.get("providers", [])
    console.print("\n[bold cyan]Providers:[/bold cyan]")
    for p in providers:
        api_key = p.get("api_key", "")
        masked_key = "***" + api_key[-4:] if len(api_key) > 4 else "***"
        console.print(f"  • {p.get('name', 'Unknown')}")
        console.print(f"    Model: {p.get('model', 'N/A')}")
        console.print(f"    API Key: {masked_key}")
    
    settings = config.get("settings", {})
    console.print("\n[bold cyan]Settings:[/bold cyan]")
    console.print(f"  • Reset after: {settings.get('provider_reset_hours', 1)} hours")
    console.print(f"  • Memory retention: {settings.get('memory_retention_days', 30)} days")
    console.print(f"  • Workspace: {settings.get('workspace_dirs', ['N/A'])[0]}")
    console.print(f"  • Timeout: {settings.get('timeout_seconds', 15)} seconds")
