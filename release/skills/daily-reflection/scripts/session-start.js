#!/usr/bin/env node
// SessionStart hook：把 .daily_reflection 状态注入会话上下文。
// 项目未启用 daily-reflection（无 context-sync.json）时静默退出。
const fs = require('fs');
const path = require('path');

function main() {
  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const dir = path.join(root, '.daily_reflection');
  const syncPath = path.join(dir, 'context-sync.json');
  if (!fs.existsSync(syncPath)) process.exit(0);

  const sync = JSON.parse(fs.readFileSync(syncPath, 'utf8'));
  const pending = Array.isArray(sync.pending_tasks) ? sync.pending_tasks : [];
  const high = pending.filter((t) => t && t.priority === 'high');

  let inboxCount = 0;
  let stale = 0;
  const inbox = path.join(dir, 'inbox');
  if (fs.existsSync(inbox)) {
    const now = Date.now();
    for (const f of fs.readdirSync(inbox)) {
      const st = fs.statSync(path.join(inbox, f));
      if (st.isFile()) {
        inboxCount++;
        if (now - st.mtimeMs > 7 * 86400000) stale++;
      }
    }
  }

  const parts = [
    `[daily-reflection] 阶段 ${sync.phase || '?'} | 进度 ${sync.progress || '?'}`,
    `待办 ${pending.length} 项${high.length ? `（高优：${high.map((t) => t.title).join('；')}）` : ''}`,
  ];
  if (sync.next_focus) parts.push(`下一步：${sync.next_focus}`);
  if (inboxCount) parts.push(`inbox ${inboxCount} 个文件${stale ? `（${stale} 个超 7 天）` : ''}`);

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: parts.join(' | '),
      },
    })
  );
}

try {
  main();
} catch {
  process.exit(0);
}
