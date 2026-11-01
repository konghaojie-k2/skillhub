---
name: fix-python-utf8
description: Automatically configure Python UTF-8 encoding on Windows by creating and installing sitecustomize.py to virtual environment. Use when Python scripts display garbled Chinese characters or emoji in Windows console, or when user reports UnicodeEncodeError with non-ASCII output. Triggered by requests like "fix Chinese encoding", "configure UTF-8", or "emoji displays as garbled text".
---

# Python UTF-8 编码自动配置

## Overview

Automatically configure Python UTF-8 encoding support for Windows projects by installing `sitecustomize.py` to the virtual environment. This ensures all Python scripts correctly display Chinese characters and emoji output.

## Workflow

### Step 1: Check Current State

Verify the project structure and locate the virtual environment:

- Check for existing `sitecustomize.py` in project root
- Identify virtual environment location (usually `backend/.venv/` or `.venv/`)
- Check if `site-packages/sitecustomize.py` already exists

**If already configured**: Inform the user and skip to Step 5 (verification)

### Step 2: Create Configuration Files

Create two files in the project root:

#### 2.1 sitecustomize.py

The UTF-8 configuration file that Python auto-loads on startup. Use the bundled script from `scripts/sitecustomize.py`.

Content:
```python
import sys

# Force UTF-8 encoding for stdout/stderr (Windows compatible)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

#### 2.2 install_utf8_config.py

The installation script that copies `sitecustomize.py` to the virtual environment's `site-packages`. Use the bundled script from `scripts/install_utf8_config.py`.

Key features:
- Detects virtual environment automatically
- Backs up existing `sitecustomize.py` if present
- Installs to `{venv}/Lib/site-packages/sitecustomize.py`
- Provides success/failure feedback

### Step 3: Run Installation

Execute the installation script:

```bash
# If using uv (from backend directory)
cd backend && uv run python ../install_utf8_config.py

# Or with direct Python
python install_utf8_config.py
```

Expected output:
```
正在安装 UTF-8 全局配置...
--------------------------------------------------
✅ 成功安装 UTF-8 配置到: {path}/.venv/Lib/site-packages/sitecustomize.py
✅ 现在所有 Python 脚本将自动使用 UTF-8 编码
--------------------------------------------------
```

### Step 4: Verify Installation

Test UTF-8 support with Chinese and emoji:

```bash
python -c "print('测试中文和emoji: 🎉 🔥 ✅')"
```

Expected output: `测试中文和emoji: 🎉 🔥 ✅`

If successful, the encoding is configured correctly.

### Step 5: Clean Up (Optional)

Remove temporary files from project root:
- `install_utf8_config.py` (can be kept for reinstallation)
- Test files created during verification

**Keep**: `sitecustomize.py` in project root as reference/template

## How It Works

### sitecustomize.py Mechanism

Python automatically imports `sitecustomize.py` from `site-packages` on startup (if it exists). This is a standard Python mechanism for site-wide customizations.

By placing UTF-8 configuration in this file:
- ✅ All Python scripts automatically use UTF-8
- ✅ No code changes needed in user scripts
- ✅ Works with any Python framework or tool

### Virtual Environment Isolation

The installation targets the project's virtual environment:
- Only affects the current project
- Does not impact system Python or other projects
- Automatically activated when using the virtual environment

## Multi-Project Usage

To configure UTF-8 for other projects:

**Option A: Use this skill again**
- Trigger the skill for each project
- Repeat the workflow

**Option B: Manual setup**
1. Copy `sitecustomize.py` and `install_utf8_config.py` to the new project
2. Run the installation script

**Option C: Global configuration** (not recommended)
Install to system Python's `site-packages` (affects all projects globally)

## Troubleshooting

### Installation fails

**Problem**: Virtual environment not found

**Solution**:
- Check the project structure for `.venv/`, `venv/`, or `backend/.venv/`
- Verify the virtual environment is activated
- Manually specify the path in `install_utf8_config.py`

### Test still shows garbled text

**Problem**: Installation succeeded but output still garbled

**Solution**:
1. Verify the file was created: `ls {venv}/Lib/site-packages/sitecustomize.py`
2. Restart the IDE or terminal
3. Try running directly: `python -c "import sys; print(sys.stdout.encoding)"` (should show `utf-8`)
4. Check if the terminal/console supports UTF-8 (use Windows Terminal or PowerShell)

### Uninstallation

To remove UTF-8 configuration:

```bash
# Use the uninstall flag
python install_utf8_config.py --uninstall

# Or manually delete
rm {venv}/Lib/site-packages/sitecustomize.py
```

## Resources

### scripts/sitecustomize.py

The core UTF-8 configuration file. This file gets copied to the virtual environment's `site-packages` directory during installation.

**Do not modify** unless you understand the implications for all Python scripts in the project.

### scripts/install_utf8_config.py

Automated installation script that:
- Detects the virtual environment location
- Backs up existing configuration
- Copies `sitecustomize.py` to the correct location
- Provides installation feedback

**Can be modified** for custom installation paths or additional configuration steps.
