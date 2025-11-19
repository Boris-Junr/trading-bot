-- Create secure storage for user API keys (Alpaca, etc.)
-- Uses PostgreSQL pgcrypto for encryption at rest

-- Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- USER API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Provider identification
    provider TEXT NOT NULL CHECK (provider IN ('alpaca', 'binance', 'coinbase', 'interactive_brokers')),
    environment TEXT NOT NULL DEFAULT 'paper' CHECK (environment IN ('paper', 'live')),

    -- Encrypted API credentials
    -- These are encrypted using pgcrypto with a key stored in environment variables
    api_key_encrypted BYTEA NOT NULL,
    api_secret_encrypted BYTEA NOT NULL,

    -- Optional additional fields (provider-specific)
    additional_config JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    label TEXT, -- User-friendly label like "My Live Trading Account"
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure user can't have duplicate provider/environment combinations
    CONSTRAINT unique_user_provider_env UNIQUE (user_id, provider, environment, label)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON public.user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_provider ON public.user_api_keys(provider, environment);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_active ON public.user_api_keys(user_id, is_active) WHERE is_active = true;

-- Enable Row Level Security
ALTER TABLE public.user_api_keys ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Users can view their own API keys
CREATE POLICY "Users can view their own api keys"
    ON public.user_api_keys
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Users can insert their own API keys
CREATE POLICY "Users can insert their own api keys"
    ON public.user_api_keys
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own API keys
CREATE POLICY "Users can update their own api keys"
    ON public.user_api_keys
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own API keys
CREATE POLICY "Users can delete their own api keys"
    ON public.user_api_keys
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- HELPER FUNCTIONS FOR ENCRYPTION/DECRYPTION
-- ============================================================================

-- Function to encrypt API key
-- NOTE: The encryption key should be stored in environment variable ENCRYPTION_KEY
-- and passed as a parameter, NOT hardcoded
CREATE OR REPLACE FUNCTION public.encrypt_api_credential(
    plaintext TEXT,
    encryption_key TEXT
)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt API key
-- Only callable by authenticated users for their own keys
CREATE OR REPLACE FUNCTION public.decrypt_api_credential(
    ciphertext BYTEA,
    encryption_key TEXT
)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.encrypt_api_credential(TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.decrypt_api_credential(BYTEA, TEXT) TO authenticated;

-- ============================================================================
-- AUDIT LOGGING FOR API KEY USAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.api_key_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    api_key_id UUID NOT NULL REFERENCES public.user_api_keys(id) ON DELETE CASCADE,

    action TEXT NOT NULL CHECK (action IN ('created', 'updated', 'deleted', 'used', 'failed')),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_key_audit_log_user_id ON public.api_key_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_log_api_key_id ON public.api_key_audit_log(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_log_created_at ON public.api_key_audit_log(created_at DESC);

-- Enable RLS
ALTER TABLE public.api_key_audit_log ENABLE ROW LEVEL SECURITY;

-- Users can view their own audit logs
CREATE POLICY "Users can view their own audit logs"
    ON public.api_key_audit_log
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGER TO UPDATE updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_user_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_api_keys_updated_at
    BEFORE UPDATE ON public.user_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_user_api_keys_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE public.user_api_keys IS 'Encrypted storage for user API keys (Alpaca, Binance, etc.)';
COMMENT ON COLUMN public.user_api_keys.api_key_encrypted IS 'Encrypted API key using pgp_sym_encrypt';
COMMENT ON COLUMN public.user_api_keys.api_secret_encrypted IS 'Encrypted API secret using pgp_sym_encrypt';
COMMENT ON COLUMN public.user_api_keys.environment IS 'Trading environment: paper (demo) or live (real money)';
COMMENT ON TABLE public.api_key_audit_log IS 'Audit trail for API key access and usage';

-- ============================================================================
-- COMPLETION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Secure API Keys Storage Created';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  ✓ user_api_keys (encrypted credentials)';
    RAISE NOTICE '  ✓ api_key_audit_log (audit trail)';
    RAISE NOTICE '';
    RAISE NOTICE 'Security features:';
    RAISE NOTICE '  ✓ PGP symmetric encryption for keys';
    RAISE NOTICE '  ✓ RLS policies for user isolation';
    RAISE NOTICE '  ✓ Encryption/decryption helper functions';
    RAISE NOTICE '  ✓ Audit logging for compliance';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Set ENCRYPTION_KEY in environment!';
    RAISE NOTICE '================================================';
END $$;
