# HelloChusquis v1.1 - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Basic Commands](#basic-commands)
3. [Built-in Tools](#built-in-tools)
4. [Enterprise Integrations](#enterprise-integrations)
5. [API & Web Interface](#api--web-interface)
6. [Configuration](#configuration)

---

## Quick Start

```bash
# Install
pip install hellochusquis

# Run terminal agent
hellochusquis

# Run web interface
hellochusquis web

# Run API server
hellochusquis api --port 8080
```

---

## Basic Commands

| Command | Description |
|---------|------------|
| `hellochusquis` | Start terminal agent |
| `hellochusquis web` | Start web UI |
| `hellochusquis api` | Start REST API |
| `hellochusquis install <plugin>` | Install plugin |
| `hellochusquis uninstall <plugin>` | Remove plugin |
| `hellochusquis cache` | Clear response cache |
| 👍 / 👎 | Give feedback |

### Terminal Commands

```
You: /help          # Show commands
You: /status       # Provider status
You: /clear        # Clear history
You: /plan <task> # Force planning mode
You: exit         # Save and exit
```

---

## Built-in Tools

### 🎤 Voice Tools

```python
# Voice input (speech-to-text)
voice(action='listen', language='en')

# Text-to-speech output
tts(action='speak', text='Hello world')
```

### 🖼️ Image Analysis

```python
# Describe image with AI
image(action='describe', image_path='photo.jpg')

# Extract text from image (OCR)
image(action='ocr', image_path='screenshot.png')
```

### 📊 Data & Excel

```python
# Read Excel file
excel(action='read', file='data.xlsx', sheet='Sheet1')

# Write to Excel
excel(action='write', file='output.xlsx', cell='A1', value='Hello')

# List sheets
excel(action='list_sheets', file='data.xlsx')
```

### 📈 Visualization

```python
# Generate chart (saves to /tmp/chart.png)
visualize(type='bar', data='Q1:100,Q2:150,Q3:120,Q4:200', title='Sales 2024')

# Line chart
visualize(type='line', data='Jan:10,Feb:15,Mar:12', title='Growth')
```

### 🔐 Security

```python
# Scan for exposed secrets
secret_scanner(action='scan', path='./src')

# Scan specific file
secret_scanner(action='check_file', path='config.py')

# Check environment variables
secret_scanner(action='check_env')
```

### ☁️ Cloud & DevOps

```python
# Kubernetes - list pods
kubernetes(action='pods', namespace='default')

# Kubernetes - apply YAML
kubernetes(action='apply', yaml='apiVersion: v1...')

# Terraform - plan
terraform(action='plan', directory='./infra')

# Terraform - apply
terraform(action='apply', directory='./infra', auto_approve=True)

# GitHub Actions - list workflows
github_actions(action='list_workflows', owner='username', repo='myrepo')

# GitHub Actions - run workflow
github_actions(action='run_workflow', owner='username', repo='myrepo', workflow='ci.yml')

# Docker
docker(action='list_containers')
docker(action='container_logs', container='web-app', tail=50)
```

### 🗄️ Databases

```python
# PostgreSQL
postgresql(action='query', sql='SELECT * FROM users LIMIT 10')
postgresql(action='list_tables', database='mydb')

# MongoDB
mongodb(action='find', database='mydb', collection='users', filter='{"active": true}')

# Database migrations
db_migration(action='init')
db_migration(action='create', name='add_users_table')
db_migration(action='migrate')
```

### 📅 Productivity

```python
# Google Calendar
google_calendar(action='list_events')
google_calendar(action='create_event', title='Meeting', start_time='2024-01-15T10:00:00Z')

# Notion
notion(action='list_databases')
notion(action='create_page', database_id='...', title='New Task')

# Linear (Project Management)
linear(action='list_projects')
linear(action='create_issue', team_id='...', title='Fix bug', priority=1)

# Jira
jira(action='list_projects')
jira(action='create_issue', project='PROJ', summary='New feature', issue_type='Story')

# Meeting summarization
meeting(action='summarize', transcript='John: We need to...')
meeting(action='extract_actions', transcript='Meeting notes...')
```

### ✉️ Communication

```python
# Slack
slack(action='post_message', channel='general', text='Deploy complete!')
slack(action='list_channels')

# Discord (webhook)
discord(action='send_message', webhook_url='https://...', content='Server is up!')

# Gmail
gmail(action='send_email', to='user@example.com', subject='Update', body='Hello!')
gmail(action='search_emails', query='from:boss')

# Email draft (AI)
email_draft(to='client@example.com', subject='Project Update', context='Weekly progress report')
```

### 💻 Code & Development

```python
# GitHub
github(action='list_repos')
github(action='create_issue', owner='user', repo='project', title='Bug', body='Description')
github(action='list_issues', owner='user', repo='project')

# Code Analysis
code_analysis(action='lint', tool='eslint', path='./src')
code_analysis(action='format', tool='black', path='main.py')
code_analysis(action='check', tool='mypy', path='module/')

# GitHub Actions
github_actions(action='list_runs', owner='user', repo='project')
github_actions(action='run_workflow', owner='user', repo='project', workflow='ci.yml')
```

### 🤖 AI/ML

```-python
# RAG - Add documents for contextual knowledge
rag(action='add', file='document.pdf', collection='knowledge')
rag(action='query', query='What is our return policy?', collection='knowledge')

# Generate embeddings
embeddings(action='create', text='Hello world')
```

### 📊 Enterprise

```python
# Salesforce
salesforce(action='query', sobject='Account', fields='Name,Industry')
salesforce(action='list_objects')

# Snowflake
snowflake(action='execute', query='SELECT * FROM table LIMIT 10')
```

### 🌐 GraphQL

```python
graphql(action='query', endpoint='https://api.example.com/graphql', query='{ users { name } }')
```

### 🔄 Automation

```python
# Schedule tasks
scheduler(action='add', name='daily-report', command='python report.py', schedule='0 9 * * *')
scheduler(action='list')

# File watcher setup (requires external tool)
events(action='watch', watch_path='./src', command='npm test')
```

---

## API & Web Interface

### REST API

```bash
# Chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Status
curl http://localhost:8080/status

# Feedback
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{"type": "positive", "context": "Good response"}'

# Clear history
curl -X POST http://localhost:8080/clear
```

### Web Interface

Open http://localhost:8000 in your browser:

- 💬 Chat interface
- 📋 Copy button on responses
- 👍/👎 Feedback
- ⚙️ Configuration
- 📊 Status sidebar

---

## Configuration

### Environment Variables

```bash
# Core
export GITHUB_TOKEN="ghp_..."
export OPENAI_API_KEY="sk-..."

# Slack
export SLACK_BOT_TOKEN="xoxb-..."

# Discord  
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Database
export POSTGRES_DB="mydb"
export POSTGRES_USER="user"
export POSTGRES_PASSWORD="pass"

# AWS
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."

# Cloud
export NOTION_TOKEN="secret_..."
export GOOGLE_CALENDAR_TOKEN="..."
export SLACK_BOT_TOKEN="..."

# Security
export CLOUDFLARE_TOKEN="..."
export VERCEL_TOKEN="..."
export NETLIFY_TOKEN="..."

# Claude (for image analysis)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### CLI Options

```bash
# Security modes
hellochusquis --profile safe     # Enhanced security checks
hellochusquis --profile default # Normal
hellochusquis --profile aggressive  # No security checks

# API server
hellochusquis api --port 9000 --host 127.0.0.1
```

---

## Examples

### Example 1: Workflow

```
You: Create a new issue on GitHub for this bug
→ github(action='create_issue', owner='myorg', repo='myapp', title='Bug: Login fails', body='Steps to reproduce...')

You: Let me know when the CI pipeline finishes
→ github_actions(action='list_runs', owner='myorg', repo='myapp')

You: Send a message to #deployments
→ slack(action='post_message', channel='deployments', text='Deployment complete!')
```

### Example 2: Data Analysis

```
You: Read the sales data from Excel
→ excel(action='read', file='sales.xlsx', sheet='Q4')

You: Create a visualization
→ visualize(type='bar', data='Product A:500,Product B:300,Product C:200', title='Q4 Sales')

You: Save to PostgreSQL
→ postgresql(action='query', sql='INSERT INTO sales (product, amount) VALUES (...)')
```

### Example 3: Security Audit

```
You: Scan our codebase for secrets
→ secret_scanner(action='scan', path='./src')

You: Check Docker containers
→ docker(action='list_containers')

You: Check K8s pods
→ kubernetes(action='pods', namespace='production')
```

---

## Support

- GitHub: https://github.com/aminoy77/HelloChusquis
- Issues: https://github.com/aminoy77/HelloChusquis/issues
- Docs: https://aminoy77.github.io/HelloChusquis/