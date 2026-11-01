# Living Technical Documents - Detailed Guide

## 1. What Makes a Document "Living"

A living document is one that is expected to evolve alongside the codebase. In software projects, these typically include:

- `docs/architecture.md` or `ARCHITECTURE.md`
- `docs/design-doc.md` or `DESIGN.md`
- `docs/requirements.md`
- `README.md` (for high-level project info)

These documents should always reflect the **current state** of the system, not a historical snapshot.

## 2. Versioning Strategy

Use an **in-document version table** at the top:

```markdown
| Version | Date | Author | Summary |
|---------|------|--------|---------|
| v2.2 | 2026-04-16 | @alice | Add multi-scenario test triggers |
| v2.1 | 2026-02-27 | @bob | Add annotation workflow |
| v2.0 | 2026-02-12 | @alice | Introduce 2-layer assertion |
```

This is preferable to file-level versioning because:
- It preserves a single file path that everyone bookmarks
- Git history already tracks line-by-line changes
- Readers immediately see the document's currency

## 3. The Draft-to-Master Workflow

### Step 1: Write the Draft
Create a file under `docs/plans/` or `docs/rfcs/` with a date-prefixed name:

```
docs/plans/
└── 2026-04-16-multi-scenario-test-trigger.md
```

### Step 2: Review
Discuss the proposal with stakeholders. Iterate on the draft.

### Step 3: Merge to Master
Once approved, do **not** simply link to the plan document. Instead:

1. Open the master document (e.g., `docs/architecture.md`)
2. Update the version table
3. Add a new section or appendix that captures the approved design
4. Ensure the master doc remains internally consistent

### Step 4: Clean Up
After merging, either:
- **Delete** the draft file, or
- **Move** it to `docs/plans/_archived/` if the team has a policy to keep proposals for audit purposes

Never leave the draft in its original location where it can be mistaken for the current design.

## 4. How to Add New Content Without Breaking Old Sections

### Preferred: Append New Sections

If the architecture gains a new module, add a new top-level section rather than rewriting the overview:

```markdown
## 5. 模块 5: 报告生成

... (new content)
```

This preserves all internal links and historical context.

### Preferred: Add Appendices for Cross-Cutting Changes

For changes that affect multiple chapters (e.g., a new data field used everywhere), add an appendix:

```markdown
## 9. 附录

### 9.1 数据模型扩展（v2.2 新增）
`TestRun` 新增 `trigger_type` 和 `trigger_metadata`...
```

### Avoid: Heavy Rewrites
Do not rewrite "Chapter 2: System Overview" every time a new feature is added. Instead, update only the parts that changed, or add a note box:

```markdown
> **v2.2 更新**: 系统新增 "配置验证" 和 "模型验证" 两个入口，详见第 6 章。
```

## 5. Deleting vs. Deprecating Content

**Delete obsolete content.** Do not do this:

```markdown
## Old Module (Deprecated)
~~This module was removed in v2.1.~~
```

If the information is truly no longer relevant, remove it. Git history preserves it for anyone who needs to look back.

Exception: If the removal itself is a significant design decision, briefly document it in the version history or a "Design Decisions" appendix.

## 6. When to Create a New Document vs. Update an Existing One

| Scenario | Action |
|---|---|
| New feature within existing architecture | Update master design doc |
| Entirely new subsystem that changes core assumptions | New doc in `docs/plans/`, then merge to master |
| Experiment that may be discarded | Keep in `docs/plans/` only |
| API reference that auto-generates | Do not maintain by hand; use OpenAPI / docstrings |
| Meeting notes or decision logs | Use `docs/decisions/` or ADR format, separate from design docs |

## 7. Common Mistakes

1. **The "plans drift" problem**: `docs/plans/2026-01-01-new-auth.md` was approved but never merged into `architecture.md`. Six months later, new developers read the outdated master doc and build features on the old architecture.

2. **The "version explosion" problem**: `design-doc.md`, `design-doc-v2.md`, `design-doc-final.md`, `design-doc-revised.md` all exist. No one knows which is correct.

3. **The "scattered deprecation" problem**: Every chapter has strike-through text from old versions. The document becomes unreadable.

## 8. Checklist for Document Updates

Before finishing a document update, verify:

- [ ] Version table is updated
- [ ] Date reflects the current day
- [ ] New content is in a dedicated section or appendix
- [ ] Obsolete content is removed (not just struck through)
- [ ] Any `docs/plans/` draft that was approved has been merged and cleaned up
- [ ] Internal links still work
- [ ] Table of contents (if any) is updated
