# Authentication & User Management

Secure JWT-based authentication system with role-based access control and multi-tenant isolation.

## Overview

The authentication system provides:
- User signup and login via Supabase Auth
- JWT token-based authentication for API requests
- Role-based access control (Admin/User roles)
- Row Level Security (RLS) for multi-tenant data isolation
- Session management with automatic token refresh

## Architecture

```
Frontend (Vue 3)
    ↓ Login with email/password
Supabase Auth
    ↓ Issues JWT token
Backend (FastAPI)
    ↓ Validates JWT + extracts user_id
    ↓ Checks admin role via database
Database (PostgreSQL + RLS)
    ↓ Enforces row-level access
```

## Backend Implementation

### Files

- **[backend/api/auth.py](../../backend/api/auth.py)** - Authentication utilities
- **[backend/infrastructure/supabase_client.py](../../backend/infrastructure/supabase_client.py)** - Supabase client setup

### Core Functions

#### `get_current_user_id()`
Extracts and validates the user ID from JWT Bearer token.

```python
from api.auth import get_current_user_id
from fastapi import Depends

@router.get("/my-data")
async def get_data(user_id: str = Depends(get_current_user_id)):
    # user_id is automatically extracted from Authorization header
    return {"user_id": user_id}
```

**How it works:**
1. Reads `Authorization: Bearer <token>` header
2. Verifies JWT token with Supabase
3. Extracts `sub` (subject) claim = user UUID
4. Returns user_id or raises HTTPException(401)

#### `get_current_user_id_optional()`
Same as above but allows unauthenticated requests.

```python
@router.get("/public-data")
async def get_data(user_id: Optional[str] = Depends(get_current_user_id_optional)):
    if user_id:
        # Return personalized data
    else:
        # Return public data
```

#### `get_current_user()`
Returns full user info including admin status.

```python
from api.auth import get_current_user, UserInfo

@router.get("/profile")
async def profile(user: UserInfo = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "is_admin": user.is_admin
    }
```

**UserInfo dataclass:**
```python
@dataclass
class UserInfo:
    user_id: str      # User UUID
    is_admin: bool    # True if user has admin role
```

### Database Functions

#### `is_user_admin(user_uuid UUID)`
Database function to check if user has admin role.

```sql
-- Called from Python
supabase.rpc('is_user_admin', {'user_uuid': user_id}).execute()
```

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.is_user_admin(user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.user_role_assignments ura
    JOIN public.user_roles ur ON ura.role_id = ur.id
    WHERE ura.user_id = user_uuid
      AND ur.name = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Frontend Implementation

### Files

- **[frontend/src/views/LoginView.vue](../../frontend/src/views/LoginView.vue)** - Login page
- **[frontend/src/views/SignupView.vue](../../frontend/src/views/SignupView.vue)** - Signup page
- **[frontend/src/composables/useAuth.ts](../../frontend/src/composables/useAuth.ts)** - Auth composable
- **[frontend/src/lib/supabase.ts](../../frontend/src/lib/supabase.ts)** - Supabase client
- **[frontend/src/router/index.ts](../../frontend/src/router/index.ts)** - Route guards

### Login Flow

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/lib/supabase'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

async function handleLogin() {
  loading.value = true
  error.value = ''

  const { data, error: authError } = await supabase.auth.signInWithPassword({
    email: email.value,
    password: password.value,
  })

  if (authError) {
    error.value = authError.message
    loading.value = false
    return
  }

  // Redirect to dashboard
  router.push('/dashboard')
}
</script>
```

### Signup Flow

```vue
<script setup lang="ts">
async function handleSignup() {
  const { data, error } = await supabase.auth.signUp({
    email: email.value,
    password: password.value,
  })

  if (error) {
    // Handle error
  } else {
    // Success - check email for confirmation
  }
}
</script>
```

### useAuth Composable

Provides reactive authentication state across the app.

```typescript
// frontend/src/composables/useAuth.ts
import { ref, onMounted } from 'vue'
import { supabase } from '@/lib/supabase'

const user = ref(null)
const loading = ref(true)

export function useAuth() {
  onMounted(async () => {
    // Get current session
    const { data: { session } } = await supabase.auth.getSession()
    user.value = session?.user ?? null
    loading.value = false

    // Listen for auth changes
    supabase.auth.onAuthStateChange((_event, session) => {
      user.value = session?.user ?? null
    })
  })

  return {
    user,
    loading,
  }
}
```

**Usage in components:**
```vue
<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'

const { user, loading } = useAuth()
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="user">
    Welcome, {{ user.email }}
  </div>
  <div v-else>
    Please log in
  </div>
</template>
```

### Route Guards

Protect authenticated routes using router guards.

```typescript
// frontend/src/router/index.ts
router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    const { data: { session } } = await supabase.auth.getSession()

    if (!session) {
      // Redirect to login
      next({ name: 'login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  } else {
    next()
  }
})
```

**Route configuration:**
```typescript
{
  path: '/dashboard',
  name: 'dashboard',
  component: DashboardView,
  meta: { requiresAuth: true }
}
```

## Database Schema

### Tables

#### `user_roles`
Reference table for available roles.

```sql
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,  -- 'admin' or 'user'
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed data
INSERT INTO public.user_roles (name, description) VALUES
  ('admin', 'Administrator with full system access'),
  ('user', 'Regular user with standard permissions');
```

#### `user_role_assignments`
Maps users to roles (many-to-many).

```sql
CREATE TABLE public.user_role_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES public.user_roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  assigned_by UUID REFERENCES auth.users(id),

  UNIQUE(user_id, role_id)
);

-- Index for fast lookups
CREATE INDEX idx_user_role_assignments_user_id
  ON public.user_role_assignments(user_id);
```

### Row Level Security (RLS)

RLS policies ensure users can only access their own data.

```sql
-- Enable RLS on user_role_assignments
ALTER TABLE public.user_role_assignments ENABLE ROW LEVEL SECURITY;

-- Users can read their own role assignments
CREATE POLICY "Users can read own roles"
  ON public.user_role_assignments
  FOR SELECT
  USING (auth.uid() = user_id);

-- Only admins can manage role assignments
CREATE POLICY "Admins can manage all roles"
  ON public.user_role_assignments
  FOR ALL
  USING (is_user_admin(auth.uid()));
```

## API Endpoints

### Authentication via Frontend

All authentication is handled by Supabase Auth SDK on the frontend. The backend only validates tokens.

**Frontend Login:**
```typescript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword'
})
```

**Frontend Signup:**
```typescript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'securepassword'
})
```

**Frontend Logout:**
```typescript
const { error } = await supabase.auth.signOut()
```

### Making Authenticated API Requests

```typescript
// Get current session token
const { data: { session } } = await supabase.auth.getSession()

// Make API request with Bearer token
const response = await axios.get('/api/backtests/', {
  headers: {
    Authorization: `Bearer ${session.access_token}`
  }
})
```

## Security Considerations

### Token Expiry

Supabase JWT tokens expire after 1 hour by default. The frontend automatically refreshes tokens using the refresh token.

**Manual refresh:**
```typescript
const { data, error } = await supabase.auth.refreshSession()
```

### Token Validation

The backend validates every request:
1. Checks token signature
2. Verifies expiration
3. Confirms token issued by Supabase
4. Extracts user_id

### Password Requirements

Enforce strong passwords on signup:
```typescript
// Minimum 8 characters, at least one uppercase, one lowercase, one number
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/
```

### Admin Role Assignment

Only existing admins can assign admin role to other users:

```sql
-- Admin-only insert policy
CREATE POLICY "Only admins can assign roles"
  ON public.user_role_assignments
  FOR INSERT
  WITH CHECK (
    is_user_admin(auth.uid())  -- Caller must be admin
  );
```

## Common Patterns

### Admin-Only Endpoints

```python
@router.get("/admin/users")
async def list_users(user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Admin-only logic
    return {"users": [...]}
```

### User-Scoped Data Access

```python
@router.get("/backtests/")
async def list_backtests(user_id: str = Depends(get_current_user_id)):
    # Automatically filtered by user_id via RLS
    supabase = get_client()
    result = supabase.table('backtests').select('*').eq('user_id', user_id).execute()
    return result.data
```

### Optional Authentication

```python
@router.get("/public/strategies")
async def list_strategies(user_id: Optional[str] = Depends(get_current_user_id_optional)):
    # Different behavior based on authentication
    if user_id:
        # Return user's custom strategies + public
    else:
        # Return only public strategies
```

## Troubleshooting

### Common Issues

**1. "Invalid token" errors**
- Token expired (> 1 hour old)
- Token from wrong Supabase project
- Frontend and backend using different Supabase configs

**Solution:** Ensure `SUPABASE_URL` and `SUPABASE_ANON_KEY` match in both frontend and backend.

**2. "Unauthorized" (401) on all requests**
- Authorization header not sent
- Token in wrong format (should be `Bearer <token>`)

**Solution:** Check axios interceptor or add header manually:
```typescript
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
```

**3. RLS blocking valid requests**
- Policy too restrictive
- Missing auth.uid() in query context

**Solution:** Check RLS policies in Supabase dashboard, ensure policies use `auth.uid()` correctly.

## Testing

### Unit Tests

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_protected_endpoint_requires_auth():
    client = TestClient(app)
    response = client.get("/api/backtests/")
    assert response.status_code == 401

def test_valid_token_grants_access():
    client = TestClient(app)
    token = generate_test_token()
    response = client.get(
        "/api/backtests/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### Integration Tests

```python
def test_admin_can_access_admin_endpoint():
    admin_token = get_admin_token()
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

def test_regular_user_cannot_access_admin_endpoint():
    user_token = get_user_token()
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
```

## Next Steps

- [API Key Management](02-API_KEY_MANAGEMENT.md) - Securely store exchange credentials
- [Backtesting](03-BACKTESTING.md) - Run strategy backtests
- [System Monitoring](08-SYSTEM_MONITORING.md) - Track tasks and resources
