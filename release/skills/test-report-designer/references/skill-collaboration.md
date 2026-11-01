# Skill 协作模式

本文档定义 test-report-designer 与 pdf skill 的协作模式。

---

## 协作架构

```
test-report-designer                          pdf skill
┌─────────────────────┐                      ┌─────────────────────┐
│  职责：             │                      │  职责：             │
│  - 读取分析测试数据  │   report_content.json │  - 接收报告内容      │
│  - LLM 深度分析     │ ──────────────────→  │  - PDF 排版渲染      │
│  - 生成报告内容     │                      │  - 中文字体支持      │
│  - 生成 generate_nb  │                      │                      │
└─────────────────────┘                      └─────────────────────┘
```

---

## 接口约定

### 输入：report_content.json

报告内容为 JSON 格式，由 test-report-designer 根据 meta-framework 动态生成。

**顶层结构**：
```json
{
  "title": "报告标题",
  "metadata": {
    "base_run_id": "基准ID",
    "test_run_id": "测试ID",
    "generated_at": "ISO时间戳",
    "tester": "测试人员",
    "test_purpose": "测试目的",
    "focus_metrics": "重点指标"
  },
  "sections": [...]
}
```

**sections 数组**：包含报告各章节内容，结构由 LLM 根据 meta-framework 动态生成。

---

## pdf skill 要求

1. **中文字体支持** - 自动注册系统字体
2. **通用 JSON 解析** - 支持任意结构的 sections
3. **专业排版** - 清晰的标题层级和视觉层次

---

## 调用方式

```
/pdf generate --input report_content.json --output test_report.pdf
```
