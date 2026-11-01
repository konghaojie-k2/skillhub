# Backend Implementation

## Core Module: `myauth/dingtalk.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DingTalk OAuth Login Module"""

import secrets
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel, Field

from .models import User, TokenResponse
from .exceptions import Unauthorized


class DingTalkConfig(BaseModel):
    """DingTalk Configuration"""
    app_key: str = Field(..., description="DingTalk AppKey")
    app_secret: str = Field(..., description="DingTalk AppSecret")
    redirect_uri: str = Field(..., description="Callback URL")
    enabled: bool = Field(default=True, description="Enable DingTalk login")


class DingTalkUserInfo(BaseModel):
    """DingTalk User Info"""
    user_id: str
    name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    union_id: Optional[str] = None


class DingTalkLogin:
    """DingTalk Login Manager"""

    API_BASE = "https://oapi.dingtalk.com"
    API_V1_BASE = "https://api.dingtalk.com"  # New API

    def __init__(self, framework, config: DingTalkConfig):
        self.framework = framework
        self.config = config

    def generate_auth_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL for frontend redirect"""
        if not state:
            state = secrets.token_urlsafe(16)

        params = {
            "client_id": self.config.app_key,  # Use client_id, NOT appid
            "redirect_uri": self.config.redirect_uri,
            "state": state,
            "response_type": "code",
            "scope": "openid",
            "prompt": "consent"
        }

        query = urllib.parse.urlencode(params)
        return f"https://login.dingtalk.com/oauth2/auth?{query}"

    async def get_user_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for user token (New API)"""
        url = f"{self.API_V1_BASE}/v1.0/oauth2/userAccessToken"

        payload = {
            "clientId": self.config.app_key,
            "clientSecret": self.config.app_secret,
            "code": auth_code,
            "grantType": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()

        if "code" in data and data.get("code") != "0":
            raise Unauthorized(f"Failed to get user token: {data.get('message')}")

        return data

    async def _get_user_info_by_token(self, access_token: str) -> Dict[str, Any]:
        """Get user info using access token"""
        url = f"{self.API_V1_BASE}/v1.0/contact/users/me"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    # IMPORTANT: Use this header name, NOT Authorization: Bearer
                    "x-acs-dingtalk-access-token": access_token,
                    "Content-Type": "application/json"
                }
            )
            data = response.json()

        if "code" in data and data.get("code") != "0":
            raise Unauthorized(f"Failed to get user info: {data.get('message')}")

        return data

    async def login(self, auth_code: str) -> TokenResponse:
        """Complete login flow"""
        # 1. Get user token
        token_data = await self.get_user_token(auth_code)
        access_token = token_data.get("accessToken")

        # 2. Get user info
        user_info = await self._get_user_info_by_token(access_token)

        # 3. Find or create local user
        user = await self._find_or_create_user(DingTalkUserInfo(
            user_id=user_info.get("openId") or user_info.get("unionId"),
            name=user_info.get("nickName", "DingTalk User"),
            union_id=user_info.get("unionId")
        ))

        # 4. Generate JWT
        return self.framework.identity._create_tokens(user)

    async def _find_or_create_user(self, dingtalk_info: DingTalkUserInfo) -> User:
        """Find existing user or create new one"""
        # Check if user exists by dingtalk_id
        # If exists, return user
        # If not, create new user with:
        # - email: dingtalk_{user_id}@dingtalk.local
        # - password_hash: "" (empty for OAuth users)
        # - dingtalk_id: user_id
        # - role: "employee"
        # ... implementation depends on your database setup
        pass
```

## Router: `myauth/router.py`

Add these endpoints to your auth router:

```python
@router.get("/dingtalk/url")
async def get_dingtalk_auth_url():
    """Get DingTalk authorization URL"""
    if not auth_framework.dingtalk_login:
        raise HTTPException(400, "DingTalk login not enabled")
    
    auth_url = auth_framework.dingtalk_login.generate_auth_url()
    # Extract state from URL
    parsed = urllib.parse.urlparse(auth_url)
    params = urllib.parse.parse_qs(parsed.query)
    state = params.get("state", [""])[0]
    
    return {"auth_url": auth_url, "state": state}


@router.post("/dingtalk/callback", response_model=TokenResponse)
async def dingtalk_callback(data: DingTalkAuthRequest):
    """Handle DingTalk callback"""
    if not auth_framework.dingtalk_login:
        raise HTTPException(400, "DingTalk login not enabled")
    
    return await auth_framework.dingtalk_login.login(data.auth_code)
```

## Framework Integration: `myauth/framework.py`

```python
# In __init__:
self.dingtalk_config = None
self.dingtalk_login = None

# Read config from env or params:
dingtalk_app_key = dingtalk_app_key or os.getenv("DINGTALK_APP_KEY")
dingtalk_app_secret = dingtalk_app_secret or os.getenv("DINGTALK_APP_SECRET")
dingtalk_enabled = dingtalk_enabled or os.getenv("DINGTALK_ENABLED", "false").lower() == "true"

if dingtalk_enabled and dingtalk_app_key and dingtalk_app_secret:
    self.dingtalk_config = DingTalkConfig(
        app_key=dingtalk_app_key,
        app_secret=dingtalk_app_secret,
        redirect_uri=dingtalk_redirect_uri,
        enabled=True
    )

# In async def init():
if self.dingtalk_config:
    self.dingtalk_login = DingTalkLogin(self, self.dingtalk_config)
```

## Database Migration

```python
# In _init_db_sqlite():
await self.db_conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        ...
        password_hash VARCHAR(255),  -- Nullable for OAuth users
        dingtalk_id VARCHAR(100) UNIQUE,
        avatar TEXT
        ...
    )
""")

# Add columns if table exists:
try:
    await self.db_conn.execute("ALTER TABLE users ADD COLUMN dingtalk_id VARCHAR(100) UNIQUE")
except:
    pass
try:
    await self.db_conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
except:
    pass
```
