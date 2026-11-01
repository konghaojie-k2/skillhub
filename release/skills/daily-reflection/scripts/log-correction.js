#!/usr/bin/env node
// UserPromptSubmit hook：匹配纠正模式的用户消息原文追加到 corrections.log。
// 宁漏勿错——只抓明确的纠正信号，日常提问不记录。
// 项目未启用 daily-reflection 时静默退出。
const fs = require('fs');
const path = require('path');

const PATTERN = /不对|错了|搞错|弄错|重来|重新做|回退|撤销|不是这样|不是我要|返工|推倒/;
const MAX_LINES = 200;
const MAX_MSG = 200;

function ts(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function main() {
  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const dir = path.join(root, '.daily_reflection');
  if (!fs.existsSync(path.join(dir, 'context-sync.json'))) process.exit(0);

  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const prompt = (input.prompt || '').trim();
  if (!prompt || !PATTERN.test(prompt)) process.exit(0);

  const logPath = path.join(dir, 'corrections.log');
  const oneLine = prompt.replace(/\s+/g, ' ').slice(0, MAX_MSG);
  fs.appendFileSync(logPath, `[${ts(new Date())}] ${oneLine}\n`);

  const lines = fs.readFileSync(logPath, 'utf8').trim().split('\n');
  if (lines.length > MAX_LINES) {
    fs.writeFileSync(logPath, lines.slice(-150).join('\n') + '\n');
  }
}

try {
  main();
} catch {
  process.exit(0);
}
