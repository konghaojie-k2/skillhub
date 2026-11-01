# Gitignore Patterns by Project Type

## Python Project (with uv)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/
examples/*/.venv/

# Python cache
.pytest_cache/
.ruff_cache/
.mypy_cache/
examples/*/__pycache__/

# Coverage
.coverage
.coverage.*
htmlcov/
.tox/

# Environment
.env
.env.local
.env.*.local
```

## Frontend (React/Next.js)

```gitignore
# Dependencies
node_modules/
frontend/node_modules/

# Build
.next/
out/
build/
dist/

# Testing
coverage/
.nyc_output/

# Misc
.DS_Store
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.eslintcache
*.tsbuildinfo
```

## Local Data (model-eval tool)

```gitignore
# Generated local data
.model-eval/
examples/*/.model-eval/

# Databases
*.db
examples/*/*.db
```

## Claude/Agent Settings

```gitignore
# Claude settings
.claude/
.agent/

# AI chat files
agent_chat_file/
```

## Temporary Working Files

```gitignore
# Planning files
findings.md
progress.md
task_plan.md

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```
