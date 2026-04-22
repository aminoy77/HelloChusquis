# HelloChusquis v0.9.1 Release Notes

**Release Date:** April 2026  
**Version:** v0.9.1  
**Status:** Stable

---

## 🎉 What's New

### 🔗 GitHub Integration
- List repositories and search
- Get repository details (stars, forks, language)
- List and create issues
- List and create pull requests
- Get user information

### 💬 Slack Integration
- Send messages to channels
- List channels and users
- Get channel information
- Custom bot username and emoji

### 🎮 Discord Integration
- Send messages via webhooks
- Send embed messages
- Custom username and avatar

### 🐳 Docker Integration
- List containers and images
- Start/stop/remove containers
- View container logs
- Docker system info

### 📓 Notion Integration
- Create and update pages
- Query databases
- List databases
- Append blocks

### ☁️ AWS Integration
- List EC2 instances
- List S3 buckets
- List and invoke Lambda functions
- List IAM users
- Get caller identity

---

## 🛠️ Environment Variables Required

### GitHub
```bash
export GITHUB_TOKEN="your_github_token"
```

### Slack
```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
```

### Discord
```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### Notion
```bash
export NOTION_TOKEN="secret_your_notion_token"
```

### AWS
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

---

## 📦 New Files Added

| File | Description |
|------|-------------|
| `tools/github.py` | GitHub API integration |
| `tools/slack.py` | Slack API integration |
| `tools/discord.py` | Discord webhook integration |
| `tools/docker.py` | Docker API integration |
| `tools/notion.py` | Notion API integration |
| `tools/aws.py` | AWS CLI integration |

---

## 🐛 Bug Fixes

- Fixed various indentation errors
- Fixed config parsing issues

---

## 🚀 Upgrading

```bash
# If you already have HelloChusquis installed
pip install --upgrade hellochusquis

# Or if running from source
git pull origin main
```

---

## 📋 Breaking Changes

- None. This release is fully backward compatible.

---

## ❤️ Thanks

Thanks to all contributors and users!

---

**License:** MIT  
**Repository:** https://github.com/aminoy77/HelloChusquis  
**PyPI:** https://pypi.org/project/hellochusquis/