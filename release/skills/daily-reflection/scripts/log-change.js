#!/usr/bin/env node
// PostToolUse hook（Edit|Write|MultiEdit|NotebookEdit）：
// 把改动文件追加到 recent-changes.log；同一文件 10 分钟内改 5+ 次记一条打转警告。
// 项目未启用 daily-reflection 时静默退出。
const fs = require('fs');
const path = require('path');

const WINDOW_MS = 10 * 60 * 1000;
const THRASH_LIMIT = 5;
const MAX_LINES = 500;

function ts(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function main() {
  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const dir = path.join(root, '.daily_reflection');
  if (!fs.existsSync(path.join(dir, 'context-sync.json'))) process.exit(0);

  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const file = input.tool_input && input.tool_input.file_path;
  if (!file) process.exit(0);

  const rel = path.relative(root, file) || file;
  if (rel.startsWith('..')) process.exit(0); // 项目外的文件（如全局配置）不入项目日志
  const logPath = path.join(dir, 'recent-changes.log');
  const now = new Date();
  fs.appendFileSync(logPath, `[${ts(now)}] ${rel}\n`);

  const lines = fs.readFileSync(logPath, 'utf8').trim().split('\n');

  // 打转检测：时间窗内同文件出现次数达到上限，记一次警告（仅到达上限那次）
  const sameFile = lines.filter((l) => {
    const m = l.match(/^\[(.+?)\] (.*)$/);
    if (!m || m[2] !== rel) return false;
    return now - new Date(m[1].replace(' ', 'T')) <= WINDOW_MS;
  });
  if (sameFile.length === THRASH_LIMIT) {
    fs.appendFileSync(logPath, `[${ts(now)}] ⚠️ 打转：${rel} 10 分钟内改动 ${THRASH_LIMIT} 次\n`);
  }

  if (lines.length > MAX_LINES) {
    fs.writeFileSync(logPath, lines.slice(-400).join('\n') + '\n');
  }
}

try {
  main();
} catch {
  process.exit(0);
}
