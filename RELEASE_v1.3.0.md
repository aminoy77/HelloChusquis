## HelloChusquis v1.3.0

### What's new
- **Quick Setup** - First run shows simple 60-second setup with just one question for API key
- **Setup Flags** - `hellochusquis setup --quick` for quick reset, `--full` for full wizard  
- Fixed multi-step plan execution (tools now persist across all steps)
- Fixed web search (switched to reliable DuckDuckGo lite)

### Quick Start
```bash
pip install hellochusquis
hellochusquis
```

### First Run
When you run `hellochusquis` for the first time:
1. You'll see a quick 60-second setup
2. Get a free API key from openrouter.ai
3. Paste it in
4. Start using HelloChusquis immediately!

### Setup Commands
- `hellochusquis` - Start (uses quick setup if no config)
- `hellochusquis setup --quick` - Quick reset (one question)
- `hellochusquis setup --full` - Full wizard with multiple providers
- `hellochusquis config` - Edit existing config