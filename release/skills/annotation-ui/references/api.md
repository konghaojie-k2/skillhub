# API 接口文档

## 基础URL

```
GET /api/health
```

## 案例管理 API

### 创建案例

```
POST /api/cases/
Query Parameters:
  - role: party_a | party_b (required)

Request Body:
{
  "title": string,
  "description"?: string,
  "feature_category": string,
  "point_names": string[],
  "devices": string[],
  "primary_device"?: string,
  "feature_types"?: string[],
  "time_range": { "start": string, "end": string },
  "tags"?: string[],
  "priority"?: string,
  "chart_data": Record<string, any>,
  "metadata": Record<string, any>
}

Response:
{
  "success": true,
  "message": "案例创建成功",
  "data": CaseDetail
}
```

### 获取案例列表

```
GET /api/cases/
Query Parameters:
  - status?: draft | active | resolved | archived
  - feature_category?: string
  - tags?: comma-separated string

Response:
{
  "success": true,
  "message": "获取案例列表成功",
  "data": CaseSnapshot[]
}
```

### 获取案例详情

```
GET /api/cases/{case_id}

Response:
{
  "success": true,
  "message": "获取案例详情成功",
  "data": CaseDetail
}
```

### 更新案例

```
PUT /api/cases/{case_id}
Request Body:
{
  "title"?: string,
  "description"?: string,
  "status"?: CaseStatus,
  "tags"?: string[],
  "priority"?: string,
  "feedbacks"?: Record<string, string>
}

Response:
{
  "success": true,
  "message": "案例更新成功",
  "data": CaseDetail
}
```

### 删除案例

```
DELETE /api/cases/{case_id}

Response:
{
  "success": true,
  "message": "案例删除成功"
}
```

## 标注管理 API

### 创建标注

```
POST /api/cases/{case_id}/annotations
Query Parameters:
  - role: party_a | party_b (required)

Request Body:
{
  "type": "point" | "range" | "drawing",
  "point_name": string,
  "position": any,
  "content": string,
  "color"?: string
}

Response:
{
  "success": true,
  "message": "标注创建成功",
  "data": Annotation
}
```

### 获取标注列表

```
GET /api/cases/{case_id}/annotations

Response:
{
  "success": true,
  "message": "获取标注列表成功",
  "data": Annotation[]
}
```

### 更新标注

```
PUT /api/cases/{case_id}/annotations/{annotation_id}
Request Body:
{
  "content": string
}

Response:
{
  "success": true,
  "message": "标注更新成功",
  "data": Annotation
}
```

### 删除标注

```
DELETE /api/cases/{case_id}/annotations/{annotation_id}

Response:
{
  "success": true,
  "message": "标注删除成功"
}
```

## 评论管理 API

### 创建评论

```
POST /api/cases/{case_id}/comments
Query Parameters:
  - role: party_a | party_b (required)

Request Body:
{
  "content": string,
  "annotation_id"?: string,
  "reply_to"?: string
}

Response:
{
  "success": true,
  "message": "评论创建成功",
  "data": DiscussionComment
}
```

### 获取评论列表

```
GET /api/cases/{case_id}/comments
Query Parameters:
  - annotation_id?: string

Response:
{
  "success": true,
  "message": "获取评论列表成功",
  "data": DiscussionComment[]
}
```

### 更新评论

```
PUT /api/cases/{case_id}/comments/{comment_id}
Request Body:
{
  "content": string
}

Response:
{
  "success": true,
  "message": "评论更新成功",
  "data": DiscussionComment
}
```

### 标记评论为已解决

```
POST /api/cases/{case_id}/comments/{comment_id}/resolve

Response:
{
  "success": true,
  "message": "评论已标记为已解决",
  "data": DiscussionComment
}
```
