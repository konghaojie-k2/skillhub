#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Harness 初始化工具

创建项目 harness 目录结构，用于 AI-Agent 协作的项目管理。

Usage:
    uv run init_project.py --name "项目名称" --path ./项目目录
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


HARNESS_STRUCTURE = {
    ".project": {
        "subdirs": {
            "user-contexts": {},
            "memory": {
                "subdirs": {
                    "session-summaries": {}
                }
            }
        },
        "files": {
            "project-state.json": "project_state_template",
            "agent-checklist.md": "agent_checklist_template",
            "bootstrap.md": "bootstrap_template",
        }
    },
    "00-meta": {
        "subdirs": {
            "decisions": {},
            "queries": {}
        },
        "files": {
            "glossary.md": "glossary_template",
            "stakeholders.md": "stakeholders_template"
        }
    },
    "90-inbox": {},
    "99-archive": {},
}


def get_templates_dir() -> Path:
    """获取模板目录"""
    return Path(__file__).parent.parent / "assets" / "templates"


def create_structure(base_path: Path, structure: dict, templates_dir: Path):
    """递归创建目录结构"""
    for name, content in structure.items():
        path = base_path / name
        path.mkdir(parents=True, exist_ok=True)

        if "subdirs" in content:
            for subdir_name, subdir_content in content["subdirs"].items():
                create_structure(path, subdir_content, templates_dir)

        if "files" in content:
            for file_name, template_key in content["files"].items():
                template_file = templates_dir / f"{template_key}.json" if file_name.endswith('.json') else templates_dir / f"{template_key}.md"
                if template_file.exists():
                    shutil.copy2(template_file, path / file_name)
                else:
                    # 创建空文件
                    (path / file_name).touch()


def create_user_context_templates(base_path: Path, templates_dir: Path):
    """创建用户上下文模板"""
    uc_path = base_path / ".project" / "user-contexts"
    uc_path.mkdir(parents=True, exist_ok=True)

    template_files = [
        ("_template.json", "user_context_template"),
        ("index.json", "user_context_index")
    ]

    for file_name, template_key in template_files:
        template_file = templates_dir / f"{template_key}.json"
        if template_file.exists():
            shutil.copy2(template_file, uc_path / file_name)


def init_project(name: str, path: str, description: str = "", phases: list = None):
    """初始化项目"""
    project_path = Path(path)
    project_path.mkdir(parents=True, exist_ok=True)

    templates_dir = get_templates_dir()

    # 创建目录结构
    create_structure(project_path, HARNESS_STRUCTURE, templates_dir)

    # 创建用户上下文模板
    create_user_context_templates(project_path, templates_dir)

    # 更新 project-state.json
    state_file = project_path / ".project" / "project-state.json"
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        state["project"] = name
        state["project_cn"] = description
        state["last_update"] = datetime.now().strftime("%Y-%m-%d")

        if phases:
            for phase in phases:
                if phase in state["phases"]:
                    state["phases"][phase]["status"] = "in_progress"
                    state["current_phase"] = phase

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"Project harness initialized at: {project_path}")
    print(f"Next steps:")
    print(f"  1. Edit .project/bootstrap.md to customize the wizard")
    print(f"  2. Create CLAUDE.md in project root")
    print(f"  3. Start collaborating with AI Agent")


def main():
    parser = argparse.ArgumentParser(description="Initialize Project Harness")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--path", required=True, help="Project directory path")
    parser.add_argument("--description", default="", help="Project description (Chinese)")
    parser.add_argument("--phases", nargs="*", default=["presales"], help="Initial phases")

    args = parser.parse_args()
    init_project(args.name, args.path, args.description, args.phases)


if __name__ == "__main__":
    main()