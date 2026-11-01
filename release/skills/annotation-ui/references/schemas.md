# Pydantic 数据模型

## Enums

```python
class CaseStatus(str, Enum):
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 讨论中
    RESOLVED = "resolved"     # 已解决
    ARCHIVED = "archived"     # 归档

class UserRole(str, Enum):
    PARTY_A = "party_a"       # 甲方
    PARTY_B = "party_b"       # 乙方

class AnnotationType(str, Enum):
    POINT = "point"           # 点标注
    RANGE = "range"           # 区间标注
    DRAWING = "drawing"       # 绘制标注
```

## CaseSnapshot

```python
class CaseSnapshot(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: CaseStatus = CaseStatus.ACTIVE
    
    # 设备信息
    devices: List[str] = []
    primary_device: Optional[str] = None
    
    # 数据快照
    feature_category: str
    point_names: List[str]
    feature_types: List[str] = []
    time_range: Dict[str, str]  # {start, end}
    
    # 数据内容
    chart_data: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    
    # 创建信息
    created_by: UserRole
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    # 标签
[str] = []
    tags: List    priority: Optional[str] = None
    
    # 反馈结果
    feedbacks: Optional[Dict[str, str]] = None
```

## Annotation

```python
class Annotation(BaseModel):
    id: str
    case_id: str
    type: AnnotationType
    point_name: str
    
    # 标注位置
    # point: {x, y}
    # range: {start_x, end_x}
    # drawing: {points: [{x, y}]}
    position: Dict[str, Any]
    
    # 标注内容
    content: str
    color: str = "#ff0000"
    
    # 创建信息
    created_by: UserRole
    created_at: datetime = datetime.now()
```

## DiscussionComment

```python
class DiscussionComment(BaseModel):
    id: str
    case_id: str
    annotation_id: Optional[str] = None
    
    # 评论内容
    content: str
    role: UserRole
    
    # 关联信息
    reply_to: Optional[str] = None
    mentions: List[str] = []
    
    # 状态
    is_resolved: bool = False
    
    # 时间戳
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
```

## Request Models

```python
class CreateCaseRequest(BaseModel):
    title: str
    description: Optional[str] = None
    feature_category: str
    point_names: List[str]
    devices: List[str]
    primary_device: Optional[str] = None
    feature_types: List[str] = []
    time_range: Dict[str, str]
    tags: List[str] = []
    priority: Optional[str] = None
    chart_data: Dict[str, Any]
    metadata: Dict[str, Any]

class UpdateCaseRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    feedbacks: Optional[Dict[str, str]] = None

class CreateAnnotationRequest(BaseModel):
    case_id: str
    type: AnnotationType
    point_name: str
    position: Dict[str, Any]
    content: str
    color: Optional[str] = "#ff0000"

class UpdateAnnotationRequest(BaseModel):
    content: str

class CreateCommentRequest(BaseModel):
    case_id: str
    content: str
    annotation_id: Optional[str] = None
    reply_to: Optional[str] = None

class UpdateCommentRequest(BaseModel):
    content: str
```

## ApiResponse

```python
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
```
