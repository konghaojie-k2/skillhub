# 类型定义

## CaseStatus

```typescript
type CaseStatus = 'draft' | 'active' | 'resolved' | 'archived';
```

## UserRole

```typescript
type UserRole = 'party_a' | 'party_b';
```

## AnnotationType

```typescript
type AnnotationType = 'point' | 'range' | 'drawing';
```

## CaseSnapshot

```typescript
interface CaseSnapshot {
  id: string;
  title: string;
  description?: string;
  status: CaseStatus;
  
  // 设备信息
  devices: string[];
  primary_device?: string;
  
  // 数据快照
  feature_category: string;
  point_names: string[];
  feature_types: string[];
  time_range: { start: string; end: string };
  chart_data: Record<string, any>;
  metadata: Record<string, any>;
  
  created_by: UserRole;
  created_at: string;
  updated_at: string;
  tags: string[];
  priority?: string;
  
  // 反馈结果
  feedbacks?: Record<string, string>;
}
```

## CaseDetail

```typescript
interface CaseDetail extends CaseSnapshot {
  annotations: Annotation[];
  comments: DiscussionComment[];
}
```

## Annotation

```typescript
interface Annotation {
  id: string;
  case_id: string;
  type: AnnotationType;
  point_name: string;
  position: any; // point: {x, y} | range: {start_x, end_x} | drawing: {points: [{x, y}]}
  content: string;
  color?: string;
  created_by: UserRole;
  created_at: string;
}
```

## DiscussionComment

```typescript
interface DiscussionComment {
  id: string;
  case_id: string;
  annotation_id?: string;
  content: string;
  role: UserRole;
  reply_to?: string;
  mentions: string[];
  is_resolved: boolean;
  created_at: string;
  updated_at?: string;
}
```

## CompareConfig

```typescript
interface CompareConfig {
  mode: string;
  distinguish_field: string;
  distinguish_conditions: Array<{
    label: string;
    start?: string;
    end?: string;
    values?: string[];
    min?: number;
    max?: number;
  }>;
  time_filter?: { start?: string; end?: string };
  change_point?: string;
  context_component?: string;
  context_components?: string[];
}
```

## ComparisonRange

```typescript
interface ComparisonRange {
  label: string;
  start?: string;
  end?: string;
  statistics: {
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
    count: number;
  };
  time_series: { time: string; value: number | null }[];
}
```

## 标签映射

```typescript
const CaseStatusLabels: Record<CaseStatus, string> = {
  draft: '草稿',
  active: '讨论中',
  resolved: '已解决',
  archived: '已归档',
};

const AnnotationTypeLabels: Record<AnnotationType, string> = {
  point: '点标注',
  range: '区间标注',
  drawing: '绘制标注',
};
```
