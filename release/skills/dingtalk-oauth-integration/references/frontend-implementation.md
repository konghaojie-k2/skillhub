# Frontend Implementation

## Login Button Component

Add to your login page (`app/page.tsx`):

```tsx
// Add state for DingTalk loading
const [dingtalkLoading, setDingtalkLoading] = useState(false)

// Handler function
const handleDingTalkLogin = async () => {
  setDingtalkLoading(true)
  setError('')
  
  try {
    // 1. Get authorization URL from backend
    const res = await axios.get(`${API_URL}/auth/dingtalk/url`)
    const { auth_url, state } = res.data
    
    // 2. Save state for callback validation
    sessionStorage.setItem('dingtalk_state', state)
    
    // 3. Redirect to DingTalk
    window.location.href = auth_url
  } catch (err: any) {
    // Handle error - see error handling section below
    let errorMessage = 'DingTalk login failed'
    const detail = err.response?.data?.detail
    if (detail) {
      if (typeof detail === 'string') {
        errorMessage = detail
      } else if (typeof detail === 'object') {
        errorMessage = detail.detail || detail.error_code || JSON.stringify(detail)
      }
    }
    setError(errorMessage)
    setDingtalkLoading(false)
  }
}

// Button JSX (add after login form)
{isLogin && (
  <>
    <div style={{ /* divider styles */ }}>
      <span>or continue with</span>
    </div>
    
    <button
      onClick={handleDingTalkLogin}
      disabled={dingtalkLoading}
      style={{ /* button styles */ }}
    >
      {dingtalkLoading ? (
        <span>Loading...</span>
      ) : (
        <>
          {/* DingTalk Logo SVG */}
          <svg width="20" height="20" viewBox="0 0 24 24">
            <rect width="24" height="24" rx="4" fill="#3370FF"/>
            <path d="M7.5 8.5h2v7h-2zM11 8.5h2v7h-2z" fill="white"/>
          </svg>
          DingTalk Login
        </>
      )}
    </button>
  </>
)}
```

## Callback Page

Create `app/auth/dingtalk/callback/page.tsx`:

```tsx
'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function DingTalkCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    
    // Validate required params
    if (!code || !state) {
      setError('Missing authorization info')
      setLoading(false)
      return
    }

    // Validate state (CSRF protection)
    const savedState = sessionStorage.getItem('dingtalk_state')
    if (!savedState || savedState !== state) {
      setError('Invalid state, please try again')
      setLoading(false)
      return
    }

    // Exchange code for token
    handleLogin(code)
  }, [searchParams])

  const handleLogin = async (code: string) => {
    try {
      const res = await axios.post(`${API_URL}/auth/dingtalk/callback`, {
        auth_code: code
      })
      
      // Save tokens
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      
      // Cleanup
      sessionStorage.removeItem('dingtalk_state')
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (err: any) {
      // Handle error
      let errorMessage = 'DingTalk login failed'
      const detail = err.response?.data?.detail
      if (detail) {
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (typeof detail === 'object') {
          errorMessage = detail.detail || detail.error_code || JSON.stringify(detail)
        }
      }
      setError(errorMessage)
      setLoading(false)
    }
  }

  if (error) {
    return (
      <div>
        <h2>Login Failed</h2>
        <p>{error}</p>
        <button onClick={() => router.push('/')}>Back to Login</button>
      </div>
    )
  }

  return (
    <div>
      <h2>Logging in...</h2>
      <p>Please wait</p>
    </div>
  )
}

// Wrap with Suspense for Next.js App Router
export default function DingTalkCallbackPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DingTalkCallbackContent />
    </Suspense>
  )
}
```

## Directory Structure

```
frontend/app/
├── page.tsx                          # Login page with DingTalk button
└── auth/
    └── dingtalk/
        └── callback/
            └── page.tsx              # Callback handler
```

## Important Notes

1. **Suspense Boundary**: Next.js App Router requires `useSearchParams()` to be wrapped in `<Suspense>`

2. **State Validation**: Always validate `state` parameter to prevent CSRF attacks

3. **Error Handling**: DingTalk API returns objects like `{error_code, detail}`, not strings. Handle both formats.

4. **Token Storage**: Store tokens in localStorage for persistence across page refreshes

5. **Next.js Cache**: If you see 404 errors for static chunks, clear `.next` folder:
   ```bash
   rm -rf frontend/.next
   npm run dev
   ```
