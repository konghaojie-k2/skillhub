#!/usr/bin/env bash
# 初始化 .daily_reflection/ 目录结构（幂等，不覆盖已有文件）
set -euo pipefail

mkdir -p .daily_reflection/inbox .daily_reflection/archive

create_if_absent() {
  local path="$1"
  if [ ! -f "$path" ]; then
    cat > "$path"
    echo "created: $path"
  else
    echo "exists, skip: $path"
  fi
}

create_if_absent .daily_reflection/context-sync.json <<'EOF'
{
  "last_session": "",
  "phase": "",
  "progress": "0%",
  "pending_tasks": [],
  "active_findings": [],
  "recent_changes": [],
  "next_focus": ""
}
EOF

create_if_absent .daily_reflection/decisions.md <<'EOF'
# 决策记录

> 活跃决策（仍影响当前行为）在前，归档（已完结）在后，以 `---` 分隔。

---
EOF

create_if_absent .daily_reflection/daily-status.md <<'EOF'
# 每日流程

> 强制每日检查清单，不存具体业务数据。

## 早省
- [ ] 读取 context-sync.json，确认阶段、进度、待办
- [ ] `gh issue list`，新 issue 是否纳入今日任务
- [ ] 检查 inbox/ 是否有新文件
- [ ] 确认今日主攻方向（参考 next_focus）

## 晚省
- [ ] 更新 context-sync.json
- [ ] active_findings > 8 条则归档 3 条
- [ ] 新决策追加到 decisions.md（按状态归位）
- [ ] 完成任务从 pending_tasks 移除
EOF

create_if_absent .daily_reflection/archive/findings-history.md <<'EOF'
# 陷阱归档
EOF

create_if_absent .daily_reflection/archive/decisions-history.md <<'EOF'
# 决策归档
EOF

create_if_absent .daily_reflection/archive/tasks-history.md <<'EOF'
# 任务归档
EOF

echo "done."
