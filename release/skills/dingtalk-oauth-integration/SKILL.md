---
name: dingtalk-oauth-integration
description: |
  Complete guide for integrating DingTalk (钉钉) OAuth2.0 login into FastAPI + Next.js applications.
  
  Use this skill when:
  - User asks to add DingTalk login to an existing authentication system
  - User wants to implement third-party OAuth login
  - User needs help with DingTalk API integration
  - User encounters issues with DingTalk login (signature errors, token errors, etc.)
  
  Covers: OAuth flow, frontend integration, backend API, database changes, configuration, and troubleshooting.
---

# DingTalk OAuth2.0 Login Integration

This skill provides a complete guide for integrating DingTalk OAuth2.0 login into existing FastAPI + Next.js authentication systems.

## Overview

DingTalk OAuth2.0 login flow:
1. Frontend redirects user to DingTalk authorization URL
2. User scans QR code or confirms in DingTalk app
3. DingTalk redirects back with authorization code
4. Backend exchanges code for user token via DingTalk API
5. Backend creates/finds local user and issues JWT

## API Endpoints Used

DingTalk provides two API versions. **Use the new unified API (recommended):**

| Endpoint | Purpose |
|:---|:---|
| `https://login.dingtalk.com/oauth2/auth` | Authorization URL (frontend) |
| `https://api.dingtalk.com/v1.0/oauth2/userAccessToken` | Exchange code for token |
| `https://api.dingtalk.com/v1.0/contact/users/me` | Get user info |

## Integration Steps

### Step 1: Configuration

Add to `.env`:
```bash
DINGTALK_ENABLED=true
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_REDIRECT_URI=http://localhost:3000/auth/dingtalk/callback
```

Add to `config.toml`:
```toml
[dingtalk]
enabled = true
redirect_uri = "http://localhost:3000/auth/dingtalk/callback"
```

### Step 2: Database Schema

Add columns to users table:
```sql
ALTER TABLE users ADD COLUMN dingtalk_id VARCHAR(100) UNIQUE;
ALTER TABLE users ADD COLUMN avatar TEXT;
-- Make password_hash nullable for OAuth users
ALTER TABLE users MODIFY password_hash VARCHAR(255) NULL;
```

### Step 3: Backend Implementation

See [references/backend-implementation.md](references/backend-implementation.md) for complete code.

Key components:
- `DingTalkConfig` - Configuration model
- `DingTalkLogin` - Login manager class
- API routes: `/auth/dingtalk/url`, `/auth/dingtalk/callback`

### Step 4: Frontend Implementation

See [references/frontend-implementation.md](references/frontend-implementation.md) for complete code.

Key components:
- Login button component
- Callback handler page
- Token storage and redirect

## Common Issues & Solutions

| Error | Cause | Solution |
|:---|:---|:---|
| `clientId is blank` | Wrong parameter name in auth URL | Use `client_id` not `appid` |
| `签名校验失败` | Signature calculation error | Sign with HmacSHA256 + base64 encode |
| `不存在的临时授权码` | Wrong API endpoint | Use `/sns/getuserinfo_bycode` for old API |
| `缺少参数：x-acs-dingtalk-access-token` | Wrong header name | Use `x-acs-dingtalk-access-token` header |
| `NOT NULL constraint failed: password_hash` | OAuth user has no password | Make `password_hash` nullable |

## Testing

1. Start backend: `uv run uvicorn backend.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to login page, click "DingTalk Login"
4. Scan QR code with DingTalk app
5. Verify redirect to dashboard

## Resources

- [DingTalk Open Platform](https://open.dingtalk.com/)
- [OAuth2.0 Documentation](https://open.dingtalk.com/document/app/dingtalk-account-login-isvapp)
- [API Reference](https://open.dingtalk.com/document/isvapp-server/obtain-user-token)
