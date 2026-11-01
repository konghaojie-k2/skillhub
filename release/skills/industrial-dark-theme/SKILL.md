---
name: industrial-dark-theme
description: Create industrial monitoring dashboards with dark theme, neon accents, and gradient backgrounds. Use when building monitoring interfaces, data dashboards, or control panels for industrial applications.
author: konghaojie
version: 1.0.0
tags: [dark-theme, industrial, monitoring, dashboard, neon, tailwind]
---

# Industrial Dark Theme

Design system for electrolytic aluminum monitoring interfaces.

## Core Colors

```css
--bg-primary: #0a0f1a      /* Main background */
--bg-secondary: #151c2e    /* Card background */
--bg-tertiary: #1a2238     /* Hover state */
--border-color: #232d42    /* Borders */
--text-primary: #ffffff    /* Headings */
--text-secondary: #e4e9f2  /* Body text */
--text-muted: #8b97b0      /* Labels */
--text-slate: #64748b      /* Small text */

/* Neon accents */
--neon-blue: #00d4ff
--neon-emerald: #00ff88
--neon-amber: #ff6b35
--neon-purple: #a855f7
--neon-red: #ef4444
--neon-yellow: #eab308
```

## Layout Patterns

### Hero Section

```tsx
<div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#0d1421] via-[#151c2e] to-[#0d1421] border border-[#232d42] p-8">
  <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
  <div className="absolute bottom-0 left-0 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
  
  <div className="relative z-10">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
        <svg className="w-6 h-6 text-white">...</svg>
      </div>
      <h1 className="text-3xl font-bold text-white">Title</h1>
    </div>
  </div>
</div>
```

### Tab Navigation

```tsx
<div className="flex gap-2 mb-6 overflow-x-auto pb-2">
  {tabs.map(tab => (
    <button
      key={tab.id}
      onClick={() => setActiveTab(tab.id)}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-all ${
        activeTab === tab.id
          ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
          : "text-slate-400 hover:text-white hover:bg-[#151c2e]"
      }`}
    >
      <svg className="w-5 h-5">...</svg>
      <span className="font-medium">{tab.label}</span>
    </button>
  ))}
</div>
```

### Card Component

```tsx
<Card padding="none">
  <div className="panel-header">
    <h2 className="text-lg font-semibold text-white">Section Title</h2>
    <span className="text-sm text-slate-500">subtitle</span>
  </div>
  <div className="panel-content">
    {/* content */}
  </div>
</Card>
```

### List Item

```tsx
<div className="workflow-step cursor-pointer hover:bg-[#1a2238]">
  <div className="flex items-center gap-3 flex-1">
    <span className="font-mono text-sm text-slate-500">#{id}</span>
    <Badge variant="warning">高优先</Badge>
    <span className="text-xs text-slate-500">{date}</span>
  </div>
  <svg className="w-4 h-4 text-slate-600">...</svg>
</div>
```

### Stat Card

```tsx
<div className="relative overflow-hidden rounded-xl bg-[#151c2e] border border-[#232d42] p-4">
  <div className="flex items-center justify-between">
    <div>
      <div className="text-sm text-slate-400 mb-1">Label</div>
      <div className="text-2xl font-mono font-bold text-amber-400">{value}</div>
    </div>
    <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
      <svg className="w-5 h-5 text-amber-400">...</svg>
    </div>
  </div>
</div>
```

## Badge Variants

```tsx
<Badge variant="success">已标注</Badge>   // emerald-400
<Badge variant="warning">高优先</Badge>   // amber-400
<Badge variant="error">预测异常</Badge>    // red-400
<Badge variant="secondary">普通</Badge>    // slate-400
```

## Progress Bar

```tsx
<div className="progress-track">
  <div className="progress-fill success" style={{ width: `${percent}%` }} />
</div>
```

## Button Variants

```tsx
<Button variant="primary" size="lg">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost" size="sm">Ghost</Button>
<Button variant="outline">Outline</Button>
```

## Spinner

```tsx
<div className="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
```

## Loading Skeleton

```tsx
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-[#232d42] rounded w-1/4" />
  <div className="h-[250px] bg-[#232d42] rounded" />
</div>
```

## Empty State

```tsx
<div className="text-center py-8 text-slate-500">
  暂无数据
</div>
```

## File Structure

```
frontend/
├── app/
│   └── page.tsx              // Homepage with hero + tabs
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Badge.tsx
│   │   └── Card.tsx
│   └── samples/
│       └── TimeSeriesChart.tsx
└── globals.css               // CSS variables
```
