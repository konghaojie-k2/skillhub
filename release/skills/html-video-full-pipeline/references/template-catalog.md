# Template catalog

The html-video repo ships with 22+ templates in `templates/`. Run `node packages/cli/dist/bin.js search-templates --intent "<keywords>"` for the live list with scores. This file is a quick reference for which template fits which use case.

## By use case

### Section dividers / chapter openers
- **`frame-bold-signal`** — dark gradient bg, big section number rolls in, orange card slides in from right, title rises. 3-6s.
- **`frame-bold-poster`** — 1970s editorial poster, warm white bg, giant red Shrikhand figure rotates in, 3-line headline. 4-6s. Best for "manifesto" / "vision" statements.

### Title cards / hero
- **`frame-build-minimal`** — premium minimal, single word, elegant. 4-7s. Best for product launches.
- **`frame-play-mode`** — multi-composition. Multiple sub-scenes stitched via `data-composition-src`. 8-12s. Use when you need several distinct visuals in one video.

### Data / metrics
- **`frame-huashu-pentagram`** — Pentagram-inspired editorial, data-viz friendly (only fill in: title, subtitle, big number, unit, chart).
- **`frame-huashu-build`** — Build studio-inspired, 95.7/73.8 style stat hero.
- **`frame-huashu-takram`** — Takram radar aesthetic.

### Social / shareable
- **`frame-soft-radar`** — gentle, friendly, pastel.
- **`frame-editorial-anchor`** — magazine anchor style, deep serif.
- **`frame-luxe-minimal`** — luxury minimal, gold accent.

## By variable complexity

### Minimal (just a title)
- `frame-build-minimal` — `{ title }`
- `frame-bold-signal` — `{ section, nav, card_label, title, duration_sec }`

### Medium
- `frame-bold-poster` — `{ kicker, date, figure, headline[3], standfirst, footer_* }`
- `frame-soft-radar` — radar chart inputs

### Complex
- `frame-play-mode` — multi-composition, needs content-graph

## Picking a default

If unsure, start with `frame-bold-signal`. It's the most flexible and works for almost any "section divider with a punchy line" use case.

For a "this is what we believe" opener, use `frame-bold-poster`.

For data/metrics, pick from the huashu-* family.

## How to read a template's input schema

```bash
node packages/cli/dist/bin.js inspect-template <id>
```

Look at `inputs.schema.properties` for the variable names. Required fields are listed in `inputs.schema.required`. Examples are in `inputs.examples` — copy one and adapt.

## Authoring new templates

Out of scope for this skill. But the pattern is:
1. Create `templates/<id>/source/index.html` with HTML + CSS keyframes (or GSAP)
2. Create `templates/<id>/template.html-video.yaml` with metadata, engine, schema
3. Create `templates/<id>/preview.png` (optional static poster)
4. Run `node packages/cli/dist/bin.js search-templates --intent "test"` — your template should appear
