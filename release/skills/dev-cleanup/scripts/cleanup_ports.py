#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理开发环境中被占用的端口进程。

适用于 Windows 环境，可清理前后端开发服务器的默认端口（3000, 8000等），
并自动删除 Next.js 遗留的 dev lock 文件。
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def find_pid_by_port(port: int) -> Optional[int]:
    """通过 netstat 查找占用指定端口的 PID。"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if parts:
                    pid_str = parts[-1]
                    return int(pid_str)
    except Exception:
        pass
    return None


def kill_process(pid: int) -> bool:
    """使用 taskkill 强制终止指定 PID 的进程。"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def remove_next_lock(project_root: Path) -> None:
    """删除 Next.js 遗留的 dev lock 文件。"""
    lock_file = project_root / ".next" / "dev" / "lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
            print(f"已删除遗留 lock 文件: {lock_file}")
        except Exception as e:
            print(f"无法删除 lock 文件: {e}")


def main():
    parser = argparse.ArgumentParser(description="清理开发端口占用")
    parser.add_argument(
        "--ports",
        nargs="+",
        type=int,
        default=[3000, 8000],
        help="要清理的端口列表（默认: 3000 8000）",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="项目根目录，用于清理 Next.js lock 文件",
    )
    args = parser.parse_args()

    cleaned = 0
    for port in args.ports:
        pid = find_pid_by_port(port)
        if pid:
            print(f"端口 {port} 被 PID {pid} 占用，正在终止...")
            if kill_process(pid):
                print(f"  成功终止 PID {pid}，端口 {port} 已释放。")
                cleaned += 1
            else:
                print(f"  终止 PID {pid} 失败，请手动检查。")
        else:
            print(f"端口 {port} 未被占用。")

    remove_next_lock(args.project_root)

    if cleaned:
        print(f"\n共清理 {cleaned} 个端口进程。")
    else:
        print("\n没有需要清理的端口进程。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
