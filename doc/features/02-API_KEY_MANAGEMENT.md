# API Key Management

Secure storage and management of user API credentials for trading platforms with PGP encryption at rest.

## Overview

The API Key Management system allows users to securely store their exchange API credentials (Alpaca, Binance, Coinbase, Interactive Brokers) for automated trading. All credentials are encrypted using PGP symmetric encryption before storage.

### Key Features

- **Encryption at Rest**: PGP symmetric encryption using pgcrypto
- **Multiple Providers**: Support for Alpaca, Binance, Coinbase, Interactive Brokers
- **Environment Separation**: Separate keys for Paper and Live trading
- **Key Hints**: Display first 4 + last 4 characters for identification
- **Audit Logging**: Track all access to API keys
- **Hard Delete**: Secure permanent deletion with audit trail preservation
- **Row Level Security**: Users can only access their own keys

## Architecture

```
User → Profile Page (Vue)
         ↓ Enter API Key & Secret
Frontend encrypts display, sends plaintext to backend
         ↓ POST /api/keys/
Backend (FastAPI)
         ↓ encrypt_api_credential()
Database (PGP Encryption)
         ↓ Store encrypted + hint
PostgreSQL with pgcrypto extension
```

## Backend Implementation

### Files

- **[backend/api/routers/api_keys.py](../../backend/api/routers/api_keys.py)** - REST API endpoints
- **[backend/infrastructure/api_key_manager.py](../../backend/infrastructure/api_key_manager.py)** - Core service
- **[backend/scripts/generate_encryption_key.py](../../backend/scripts/generate_encryption_key.py)** - Key generator
- **[backend/scripts/check_env_security.py](../../backend/scripts/check_env_security.py)** - Security audit

### API Endpoints

#### List API Keys
```http
GET /api/keys/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "provider_id": "uuid",
    "provider_display_name": "Alpaca",
    "environment": "paper",
    "label": "My Trading Account",
    "api_key_hint": "APCA...xyz9",
    "api_secret_hint": "sk12...abc3",
    "last_used_at": "2025-01-19T10:30:00Z",
    "created_at": "2025-01-15T14:20:00Z"
  }
]
```

#### Create API Key
```http
POST /api/keys/
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider_id": "uuid",
  "environment": "paper",
  "api_key": "APCA1234567890abcdefg",
  "api_secret": "sk_1234567890abcdefghijklmnop",
  "label": "My Trading Account"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "API key stored successfully"
}
```

#### Update API Key
```http
PUT /api/keys/{api_key_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "api_key": "NEW_KEY",      // optional
  "api_secret": "NEW_SECRET", // optional
  "label": "Updated Label"    // optional
}
```

#### Delete API Key
```http
DELETE /api/keys/{api_key_id}
Authorization: Bearer <token>
```

**Note:** This is a **hard delete** - the encrypted key is permanently removed, but audit log is preserved.

### ApiKeyManager Service

#### Store API Key

```python
from infrastructure.api_key_manager import get_api_key_manager

mgr = get_api_key_manager()

api_key_id = mgr.store_api_key(
    user_id="user-uuid",
    provider_id="provider-uuid",
    environment="paper",  # or "live"
    api_key="APCA1234567890abcdefg",
    api_secret="sk_1234567890abcdefghijklmnop",
    label="My Trading Account",
    api_key_hint="APCA...defg",
    api_secret_hint="sk_1...mnop",
    additional_config={}  # Optional provider-specific config
)
```

**What it does:**
1. Encrypts API key using `encrypt_api_credential()` RPC
2. Encrypts API secret using `encrypt_api_credential()` RPC
3. Stores encrypted values in database
4. Logs action to audit trail
5. Returns UUID of stored credential

#### Retrieve API Credentials

```python
credentials = mgr.get_api_credentials(
    user_id="user-uuid",
    provider_id="provider-uuid",
    environment="paper",
    label="My Trading Account"  # Optional
)

if credentials:
    print(f"API Key: {credentials.api_key}")
    print(f"API Secret: {credentials.api_secret}")
    print(f"Provider: {credentials.provider}")
    print(f"Environment: {credentials.environment}")
```

**What it does:**
1. Queries database for encrypted credentials
2. Decrypts using `decrypt_api_credential()` RPC
3. Updates `last_used_at` timestamp
4. Logs access to audit trail
5. Returns `ApiKeyCredentials` dataclass or None

#### List User's API Keys

```python
keys = mgr.list_user_api_keys(user_id="user-uuid")

for key in keys:
    print(f"{key['provider_display_name']} ({key['environment']})")
    print(f"  Hint: {key['api_key_hint']}")
    print(f"  Last used: {key['last_used_at']}")
```

**Returns:** List of API key metadata (NO decryption, safe to display)

#### Delete API Key

```python
success = mgr.deactivate_api_key(
    user_id="user-uuid",
    api_key_id="key-uuid"
)
```

**What it does:**
1. Logs deletion to audit trail (with key still linked)
2. Hard deletes record from `user_api_keys` table
3. Audit log preserved with NULL api_key_id (ON DELETE SET NULL)

### Encryption Key Validation

The `ApiKeyManager` validates encryption key strength on initialization:

```python
def __init__(self):
    self.encryption_key = os.getenv('ENCRYPTION_KEY')

    # Must be set
    if not self.encryption_key:
        raise ValueError("ENCRYPTION_KEY must be set!")

    # Minimum 32 characters (256 bits)
    if len(self.encryption_key) < 32:
        raise ValueError("ENCRYPTION_KEY must be at least 32 characters")

    # No weak/placeholder patterns
    weak_patterns = ['test', 'example', 'generate_with', 'password', '12345']
    if any(pattern in self.encryption_key.lower() for pattern in weak_patterns):
        raise ValueError("ENCRYPTION_KEY appears to be a placeholder!")
```

### Generating Encryption Keys

Use the provided script to generate cryptographically secure keys:

```bash
cd backend
python scripts/generate_encryption_key.py
```

**Output:**
```
======================================================================
[*] ENCRYPTION KEY GENERATED
======================================================================

Your new encryption key:

  bZDyDAbCuG8B2mHBhBfTXNaO0iConMuqHIJM7dfiULq

======================================================================
[*] SETUP INSTRUCTIONS
======================================================================

1. Add to your .env file:
   ENCRYPTION_KEY=bZDyDAbCuG8B2mHBhBfTXNaO0iConMuqHIJM7dfiULq

2. SECURITY CHECKLIST:
   [x] Never commit .env to git
   [x] Use different keys for dev/staging/production
   [x] Store production key in platform environment variables
   [x] Rotate key every 90 days in production
```

## Frontend Implementation

### Files

- **[frontend/src/views/ProfileView.vue](../../frontend/src/views/ProfileView.vue)** - Main UI

### User Interface

The Profile page provides a full-width table for managing API keys:

```
┌─────────────────────────────────────────────────────────────────┐
│ API Keys                                                        │
│ Configure your trading platform credentials                    │
├──────────┬────────┬─────────────┬──────────────┬──────────────┤
│ Provider │ Env    │ API Key     │ API Secret   │ Actions      │
├──────────┼────────┼─────────────┼──────────────┼──────────────┤
│ Alpaca   │ Paper  │ [password]  │ [password]   │ Save Delete  │
│          │ Live   │ [password]  │ [password]   │ Save Delete  │
├──────────┼────────┼─────────────┼──────────────┼──────────────┤
│ Binance  │ Paper  │ [password]  │ [password]   │ Save         │
│          │ Live   │ [password]  │ [password]   │ Save         │
└──────────┴────────┴─────────────┴──────────────┴──────────────┘
```

### Key Features

#### Loading State
Shows spinner while fetching keys from backend:

```vue
<div v-if="loadingApiKeys" class="loading-container">
  <div class="spinner"></div>
  <p class="loading-text">Loading API keys...</p>
</div>
```

#### Hints as Placeholders
Existing key hints displayed as placeholder text:

```vue
<input
  v-model="ensureKeyInput(provider.id, 'paper').api_key"
  type="password"
  :placeholder="getKeyHint(provider.id, 'paper', 'api_key') || 'Enter API key'"
/>
```

If key exists, shows: `APCA...xyz9`
If no key, shows: `Enter API key`

#### Save Button States
```vue
<Button
  @click="saveKey(provider.id, 'paper')"
  size="sm"
  :disabled="!hasKeyInput(provider.id, 'paper') || savingKeys[keyId]"
>
  {{ savingKeys[keyId] ? 'Saving...' : 'Save' }}
</Button>
```

- Disabled when no input entered
- Shows "Saving..." during API call
- Re-enables after save completes

#### Delete Button States
```vue
<Button
  v-if="hasExistingKey(provider.id, 'paper')"
  @click="deleteKey(provider.id, 'paper')"
  variant="danger"
  size="sm"
  :disabled="deletingKeys[keyId]"
>
  {{ deletingKeys[keyId] ? 'Deleting...' : 'Delete' }}
</Button>
```

- Only shown if key exists
- Confirmation dialog before deletion
- Shows "Deleting..." during API call

### Component Logic

#### State Management
```typescript
const apiKeys = ref<any[]>([])
const providers = ref<any[]>([])
const loadingApiKeys = ref(true)
const keyInputs = reactive<Record<string, { api_key: string, api_secret: string }>>({})
const savingKeys = reactive<Record<string, boolean>>({})
const deletingKeys = reactive<Record<string, boolean>>({})
```

#### Load Providers and Keys in Parallel
```typescript
onMounted(async () => {
  loadProfile()  // Non-blocking

  // Parallel fetch for faster load
  await Promise.all([
    loadProviders(),
    loadApiKeys()
  ])
})
```

#### Save Key (Create or Update)
```typescript
async function saveKey(providerId: string, environment: string) {
  const keyId = getKeyId(providerId, environment)
  const input = keyInputs[keyId]

  savingKeys[keyId] = true

  try {
    const { data: { session } } = await supabase.auth.getSession()

    const existing = apiKeys.value.find(k =>
      k.provider_id === providerId && k.environment === environment
    )

    if (existing) {
      // Update existing key
      await axios.put(
        `${API_BASE_URL}/api/keys/${existing.id}`,
        { api_key: input?.api_key, api_secret: input?.api_secret },
        { headers: { Authorization: `Bearer ${session.access_token}` } }
      )
    } else {
      // Create new key
      await axios.post(
        `${API_BASE_URL}/api/keys/`,
        { provider_id: providerId, environment, api_key: input.api_key, api_secret: input.api_secret },
        { headers: { Authorization: `Bearer ${session.access_token}` } }
      )
    }

    keyInputs[keyId] = { api_key: '', api_secret: '' }  // Clear inputs
    await loadApiKeys()  // Refresh list
    alert('API key saved successfully')
  } catch (error) {
    alert('Failed to save API key')
  } finally {
    savingKeys[keyId] = false
  }
}
```

## Database Schema

### Migration File
**[supabase/migrations/20251118212000_create_user_api_keys_table.sql](../../supabase/migrations/20251118212000_create_user_api_keys_table.sql)**

### Tables

#### `user_api_key_providers`
Reference table for supported exchange providers.

```sql
CREATE TABLE public.user_api_key_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,  -- 'alpaca', 'binance', etc.
  display_name TEXT NOT NULL,  -- 'Alpaca', 'Binance', etc.
  supports_paper_trading BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed providers
INSERT INTO public.user_api_key_providers (name, display_name, supports_paper_trading) VALUES
  ('alpaca', 'Alpaca', true),
  ('binance', 'Binance', true),
  ('coinbase', 'Coinbase', false),
  ('interactive_brokers', 'Interactive Brokers', true);
```

#### `user_api_keys`
Stores encrypted API credentials per user.

```sql
CREATE TABLE public.user_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider_id UUID NOT NULL REFERENCES public.user_api_key_providers(id),
  environment TEXT NOT NULL CHECK (environment IN ('paper', 'live')),

  -- Encrypted credentials (stored as bytea)
  api_key_encrypted BYTEA NOT NULL,
  api_secret_encrypted BYTEA NOT NULL,

  -- Plaintext hints for UI (first 4 + last 4 chars)
  api_key_hint TEXT,
  api_secret_hint TEXT,

  -- Optional metadata
  label TEXT,
  additional_config JSONB DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,

  -- Ensure one key per user/provider/environment combo
  UNIQUE(user_id, provider_id, environment)
);

CREATE INDEX idx_user_api_keys_user_id ON public.user_api_keys(user_id);
```

#### `api_key_audit_log`
Tracks all access to API keys for compliance.

```sql
CREATE TABLE public.api_key_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  api_key_id UUID REFERENCES public.user_api_keys(id) ON DELETE SET NULL,  -- NULL after hard delete
  action TEXT NOT NULL CHECK (action IN ('created', 'used', 'updated', 'deleted', 'failed')),
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_key_audit_log_user_id ON public.api_key_audit_log(user_id);
CREATE INDEX idx_api_key_audit_log_api_key_id ON public.api_key_audit_log(api_key_id);
```

### Encryption Functions

#### `encrypt_api_credential(plaintext TEXT, encryption_key TEXT)`
```sql
CREATE OR REPLACE FUNCTION public.encrypt_api_credential(
  plaintext TEXT,
  encryption_key TEXT
)
RETURNS BYTEA AS $$
BEGIN
  RETURN pgp_sym_encrypt(plaintext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### `decrypt_api_credential(ciphertext BYTEA, encryption_key TEXT)`
```sql
CREATE OR REPLACE FUNCTION public.decrypt_api_credential(
  ciphertext BYTEA,
  encryption_key TEXT
)
RETURNS TEXT AS $$
BEGIN
  RETURN pgp_sym_decrypt(ciphertext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Row Level Security

```sql
ALTER TABLE public.user_api_keys ENABLE ROW LEVEL SECURITY;

-- Users can only see their own keys
CREATE POLICY "Users can read own API keys"
  ON public.user_api_keys
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert their own keys
CREATE POLICY "Users can insert own API keys"
  ON public.user_api_keys
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only update their own keys
CREATE POLICY "Users can update own API keys"
  ON public.user_api_keys
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can only delete their own keys
CREATE POLICY "Users can delete own API keys"
  ON public.user_api_keys
  FOR DELETE
  USING (auth.uid() = user_id);
```

## Security

### Encryption

**Algorithm:** PGP symmetric encryption (AES-128/256 via pgcrypto)

**Key Storage:**
- **Development:** `.env` file (ensure in `.gitignore`)
- **Production:** Platform environment variables (Heroku, AWS EB, Vercel, etc.)

**Key Strength:** Minimum 32 characters (256 bits of entropy)

### Are Hints Secure?

**Yes!** Showing first 4 + last 4 characters does NOT compromise encryption:

- AES is resistant to known-plaintext attacks
- Even with full plaintext + ciphertext, key derivation is infeasible
- 8 out of 32-64 characters provides minimal information
- Modern API keys have 62^24+ bits of entropy (middle portion unknown)

**Real risk:** Encryption key storage (NOT the hints)

### Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   echo ".env" >> .gitignore
   git rm --cached backend/.env  # Remove if accidentally committed
   ```

2. **Use strong encryption keys**
   ```bash
   openssl rand -base64 32  # Generate 256-bit key
   ```

3. **Different keys per environment**
   ```
   Development:   ENCRYPTION_KEY=dev_key_12345...
   Staging:       ENCRYPTION_KEY=staging_key_67890...
   Production:    ENCRYPTION_KEY=prod_key_abcdef...
   ```

4. **Rotate keys periodically**
   - Every 90 days in production
   - Implement key versioning for graceful rotation

5. **Monitor audit logs**
   ```sql
   -- Check for suspicious access
   SELECT * FROM api_key_audit_log
   WHERE action = 'failed'
     AND created_at > NOW() - INTERVAL '1 day';
   ```

6. **Use platform environment variables in production**
   ```bash
   # Heroku
   heroku config:set ENCRYPTION_KEY="your-key-here"

   # AWS Elastic Beanstalk
   eb setenv ENCRYPTION_KEY="your-key-here"

   # Vercel
   vercel env add ENCRYPTION_KEY
   ```

## Common Use Cases

### Using Stored Credentials in Trading

```python
from infrastructure.api_key_manager import get_api_key_manager
import alpaca_trade_api as tradeapi

mgr = get_api_key_manager()

# Get decrypted credentials
creds = mgr.get_api_credentials(
    user_id=user_id,
    provider_id=alpaca_provider_id,
    environment='paper'
)

if creds:
    # Initialize Alpaca API with decrypted keys
    api = tradeapi.REST(
        key_id=creds.api_key,
        secret_key=creds.api_secret,
        base_url=creds.additional_config.get('base_url', 'https://paper-api.alpaca.markets')
    )

    # Place order
    api.submit_order(
        symbol='AAPL',
        qty=1,
        side='buy',
        type='market',
        time_in_force='gtc'
    )
```

### Checking if User Has Configured Keys

```python
keys = mgr.list_user_api_keys(user_id=user_id)

# Check if user has Alpaca paper key
has_alpaca_paper = any(
    k['provider_id'] == alpaca_provider_id and k['environment'] == 'paper'
    for k in keys
)

if not has_alpaca_paper:
    return {"error": "Please configure Alpaca paper trading credentials"}
```

## Troubleshooting

### Common Issues

**1. "ENCRYPTION_KEY must be set" error**

Add to `backend/.env`:
```bash
ENCRYPTION_KEY=$(openssl rand -base64 32)
```

**2. "ENCRYPTION_KEY appears to be a placeholder" error**

You're using the example value. Run:
```bash
python backend/scripts/generate_encryption_key.py
```

**3. Keys not appearing in frontend after save**

Check browser console for CORS errors. Ensure backend CORS allows frontend origin:
```python
# backend/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**4. "Failed to decrypt key" error**

Encryption key changed. Old encrypted values cannot be decrypted with new key. Either:
- Restore old key
- Delete old keys and re-enter credentials

## Next Steps

- [Backtesting System](03-BACKTESTING.md) - Use stored keys for backtesting
- [Trading Strategies](06-TRADING_STRATEGIES.md) - Configure automated strategies
- [Security Documentation](../SECURITY.md) - In-depth security guide
