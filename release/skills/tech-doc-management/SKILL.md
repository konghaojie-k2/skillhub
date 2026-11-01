---
name: tech-doc-management
description: Guide for managing living technical documents in software engineering projects. Use when the user asks about how to structure, version, or maintain technical docs (architecture.md, design-doc.md, requirements.md, docs/plans/, docs/rfcs/), or when deciding whether to edit an existing doc vs. create a new one.
---

# Technical Document Management

## Core Principle: Single Source of Truth

Technical documents like `architecture.md`, `design-doc.md`, and `requirements.md` must have **exactly one living version**. Never create multiple versioned copies of the same document (e.g., `design-doc-v1.md`, `design-doc-v2.md`).

## The Role of `docs/plans/` and `docs/rfcs/`

These directories are **draft spaces** for unapproved proposals only.

- Use `docs/plans/` to write a new design proposal that needs review before adoption.
- Once the proposal is finalized, **merge the conclusions back into the master document** (e.g., `architecture.md`).
- After merging, archive or remove the draft. Do not let `plans/` documents diverge permanently from master docs.

## Best Practices for Modifying Documents

When updating a living technical document:

1. **Update the version table** at the top of the document (version number, date, one-line change summary).
2. **Add new sections** rather than rewriting old structural descriptions.
3. **Delete obsolete content decisively** instead of keeping "deprecated" paragraphs scattered throughout.
4. **Append a changelog** for complex or cross-cutting changes if the project does not already maintain one.

## Workflow

```
Draft in docs/plans/  →  Review with user  →  Merge to master doc  →  Update version info  →  Remove/archive draft
```

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Is Bad |
|---|---|
| Multiple co-existing versions of the same doc | Creates confusion about which version is authoritative |
| Plans docs permanently diverging from master docs | Master doc becomes stale and misleading |
| Heavy rewrites of old structural sections | Destroys historical context and breaks deep links |
| Keeping "deprecated" paragraphs | Bloats the document and distracts readers |

## When to Use Which Approach

| Situation | Action |
|---|---|
| Minor incremental update to an existing design | Edit the master doc directly, update version |
| Large new feature that changes architecture | Draft in `docs/plans/`, then merge to master doc |
| User asks "should I update the design doc?" | Yes, update the living master doc; do not create a copy |

For detailed examples and decision criteria, see [references/living-docs-guide.md](references/living-docs-guide.md).
