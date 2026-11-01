# My-Auth 配置详解

## 初始化参数

```python
AuthFramework(
    db_url: str,              # 数据库连接字符串
    secret: str,               # JWT 密钥（至少32字符）
    admin_email: str,          # 管理员邮箱
    admin_password: str,       # 管理员密码
    dingtalk_enabled: bool,   # 启用钉钉登录
    dingtalk_app_key: str,    # 钉钉 AppKey
    dingtalk_app_secret: str, # 钉钉 AppSecret
    dingtalk_redirect_uri: str, # 回调地址
)
```

## 环境变量配置

| 变量 | 说明 | 必填 |
|------|------|------|
| JWT_SECRET | JWT 签名密钥 | 是 |
| DATABASE_URL | 数据库连接 | 否 |
| ADMIN_EMAIL | 管理员邮箱 | 否 |
| ADMIN_PASSWORD | 管理员密码 | 否 |
| DINGTALK_ENABLED | 启用钉钉 | 否 |
| DINGTALK_APP_KEY | 钉钉 AppKey | 否 |
| DINGTALK_APP_SECRET | 钉钉 AppSecret | 否 |

## 数据库支持

- SQLite: `sqlite:///myauth.db`
- PostgreSQL: `postgresql://user:pass@localhost:5432/myauth`

## 角色权限

| 角色 | 权限 |
|------|------|
| admin | *:* (所有权限) |
| finance | finance:* |
| employee | 仅访问自己的资源 |
