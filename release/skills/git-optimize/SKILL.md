---
name: git-optimize
description: Git repository optimization including .gitignore review, removing tracked files from cache, and cleaning up local data. Use when: (1) User asks to review or optimize .gitignore, (2) Preparing to push a repository, (3) Removing locally generated files from git tracking, (4) Cleaning up a repository before commit/push.
---

# Git Optimize

Optimize git repositories by reviewing .gitignore and removing unwanted tracked files.

## Quick Check .gitignore

```bash
# 1. List all files in project root
ls -la

# 2. Check for common local data directories
ls -la .model-eval/ 2>/dev/null
ls -la examples/*/.model-eval/ 2>/dev/null
ls -la examples/*/*.db 2>/dev/null

# 3. Check git status
git status --short | head -30
```

## Standard .gitignore Patterns

Add these patterns if not present:

```gitignore
# Python cache
__pycache__/
*.py[oc]
.pytest_cache/
.ruff_cache/

# Virtual environments
.venv/
examples/*/.venv/

# Python compiled
examples/*/__pycache__/

# Environment files
.env
.env.example

# Local database
*.db
examples/*/*.db

# Test data and results (common in this project)
.model-eval/
examples/*/.model-eval/

# Agent/Claude settings
.claude/
.agent/

# Planning/temporary files
findings.md
progress.md
task_plan.md

# Node.js
node_modules/
frontend/node_modules/
frontend/.next/
*.tsbuildinfo

# Coverage
.coverage
htmlcov/
frontend/coverage/
```

## Remove Tracked Files from Cache

When files were previously tracked but should be ignored now:

```bash
# Remove specific file from tracking
git rm --cached <file-path>

# Remove entire directory from tracking
git rm --cached -r <directory-path>

# Common examples
git rm --cached -r .model-eval/
git rm --cached examples/*/.model-eval/
git rm --cached examples/*/*.db
git rm --cached .claude/settings.local.json
```

## Commit Process

1. Check git status: `git status --short`
2. Stage changes: `git add -A`
3. Review staged files
4. Create commit with descriptive message

```bash
git add .gitignore
git status --short
git commit -m "$(cat <<'EOF'
chore: update .gitignore and remove local data

- Add patterns for .model-eval/, .venv/, *.db, .claude/
- Remove tracked local data files from cache

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```
