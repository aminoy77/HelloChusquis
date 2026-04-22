# HelloChusquis Usage Examples

## Basic Usage

### Start the agent
```bash
hellochusquis
```

### Send a message
```
You: Hola, cómo estás?
HelloChusquis: ¡Hola! Estoy listo para ayudarte...
```

## Terminal Commands

### List files
```
You: Lista los archivos en la carpeta actual
→ files(action='list', path='.')
```

### Run a shell command
```
You: Ejecuta ls -la
→ shell(command='ls -la')
```

## Web Interface

### Start web UI
```bash
hellochusquis web
# Opens http://localhost:8000
```

### Features in Web UI
- 💬 Real-time chat
- 📋 Copy button on each response
- 👍/👎 Feedback buttons
- ⚙️ Configuration panel
- 📊 Provider status sidebar

## REST API

### Start API server
```bash
hellochusquis api --port 8080
```

### Chat via API
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}'
```

### Get status
```bash
curl http://localhost:8080/status
```

## GitHub Integration

### List repositories
```
You: Lista mis repositorios de GitHub
→ github(action='list_repos')
```

### Create issue
```
You: Crea un issue en mi repositorio
→ github(action='create_issue', owner='username', repo='myrepo', title='Bug found', body='Description')
```

### Search repositories
```
You: Busca repositorios sobre python
→ github(action='search_repos', query='python language:python')
```

## Slack Integration

### Send message to channel
```
You: Envía un mensaje a #general
→ slack(action='post_message', channel='general', text='Hola equipo!')
```

### List channels
```
You: Lista los canales de Slack
→ slack(action='list_channels')
```

## Docker Integration

### List containers
```
You: Lista los contenedores Docker
→ docker(action='list_containers')
```

### View logs
```
You: Ver los logs de mi contenedor web
→ docker(action='container_logs', container='my-web-container', tail=50)
```

## AWS Integration

### List EC2 instances
```
You: Lista mis instancias EC2
→ aws(action='list_ec2')
```

### Invoke Lambda
```
You: Ejecuta mi función Lambda
→ aws(action='invoke_lambda', resource='my-function', payload='{}')
```

## Database Integration

### PostgreSQL - Query
```
You: Ejecuta SELECT * FROM users LIMIT 5
→ postgresql(action='query', sql='SELECT * FROM users LIMIT 5')
```

### PostgreSQL - List tables
```
You: Lista las tablas
→ postgresql(action='list_tables', database='mydb')
```

### MongoDB - Find
```
You: Busca documentos en usuarios
→ mongodb(action='find', database='mydb', collection='users', filter='{"active": true}')
```

## Jira Integration

### Create issue
```
You: Crea un issue en Jira
→ jira(action='create_issue', project='PROJ', summary='Fix bug', description='Description', issue_type='Bug')
```

### List projects
```
You: Lista los proyectos
→ jira(action='list_projects')
```

## Code Analysis

### Run ESLint
```
You: Analiza el código con ESLint
→ code_analysis(action='lint', tool='eslint', path='./src')
```

### Format with Black
```
You: Formatea el código Python
→ code_analysis(action='format', tool='black', path='./main.py')
```

### Run MyPy
```
You: Verifica tipos con MyPy
→ code_analysis(action='check', tool='mypy', path='./module')
```

## Notion Integration

### Create page
```
You: Crea una página en Notion
→ notion(action='create_page', database_id='..., title='My Task', content='Description')
```

### Query database
```
You: Consulta la base de datos de Notion
→ notion(action='query_database', database_id='...')
```

## Calendar Integration

### Create event
```
You: Crea un evento para mañana
→ google_calendar(action='create_event', title='Meeting', start_time='2024-01-15T10:00:00Z')
```

### List events
```
You: Lista mis eventos
→ google_calendar(action='list_events')
```

## Configuration

### Safe mode (security enabled)
```bash
hellochusquis --profile safe
```

### Aggressive mode (no security)
```bash
hellochusquis --profile aggressive
```

### Custom port for API
```bash
hellochusquis api --port 9000 --host localhost
```

## Plugins

### Install plugin
```bash
hellochusquis install weather
```

### Uninstall plugin
```bash
hellochusquis uninstall weather
```

### List plugins
```bash
hellochusquis plugins
```

## Feedback

### Positive feedback
```
You: 👍
# or
You: +
```

### Negative feedback
```
You: 👎
# or
You: -
```

## Planning Mode

### Force planning
```
You: /plan crear un informe mensual de ventas
```

## Help

### Show commands
```
You: /help
```

### Provider status
```
You: /status
```

### Clear history
```
You: /clear
```

### Exit
```
You: exit
```