-- ============================================================================
-- Multi-Tenant Trading Bot Schema for Supabase
-- ============================================================================
-- This schema implements a multi-tenant architecture with row-level security
-- for complete data isolation between tenants.
--
-- Key Features:
-- - Multi-tenant data isolation via RLS
-- - Time-series partitioning for market_data and predictions
-- - Optimized indexes for time-series queries
-- - Automated partition management
-- - Materialized views for performance
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_cron for automated partition management
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- ============================================================================
-- TENANTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for slug lookups
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

-- Enable RLS
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own tenant
CREATE POLICY tenant_isolation_policy ON tenants
    FOR ALL
    USING (id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- USERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see users in their tenant
CREATE POLICY users_tenant_isolation_policy ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- MARKET DATA (Time-Series Partitioned by Month)
-- ============================================================================

-- Parent table for market data
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, symbol, timeframe, timestamp)
) PARTITION BY RANGE (timestamp);

-- BRIN index for time-series queries
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data USING BRIN (timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_tenant_symbol ON market_data(tenant_id, symbol, timeframe);

-- Enable RLS
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's market data
CREATE POLICY market_data_tenant_isolation_policy ON market_data
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- Function to create market_data partitions
CREATE OR REPLACE FUNCTION create_market_data_partition(year INT, month INT)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := 'market_data_' || year || '_' || LPAD(month::TEXT, 2, '0');
    start_date := make_date(year, month, 1);
    end_date := start_date + INTERVAL '1 month';

    -- Create partition if it doesn't exist
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF market_data
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Create partitions for current month, next month, and previous 2 months
DO $$
DECLARE
    current_date DATE := CURRENT_DATE;
    i INT;
BEGIN
    FOR i IN -2..1 LOOP
        PERFORM create_market_data_partition(
            EXTRACT(YEAR FROM current_date + (i || ' month')::INTERVAL)::INT,
            EXTRACT(MONTH FROM current_date + (i || ' month')::INTERVAL)::INT
        );
    END LOOP;
END $$;

-- ============================================================================
-- PREDICTIONS (Time-Series Partitioned by Month)
-- ============================================================================

-- Parent table for predictions
CREATE TABLE IF NOT EXISTS predictions (
    id UUID DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    result JSONB,
    error TEXT,
    current_price NUMERIC(20, 8),
    predicted_prices JSONB,
    confidence_scores JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (tenant_id, id, created_at)
) PARTITION BY RANGE (created_at);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions USING BRIN (created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_tenant_symbol ON predictions(tenant_id, symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status) WHERE status IN ('queued', 'running');

-- Enable RLS
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's predictions
CREATE POLICY predictions_tenant_isolation_policy ON predictions
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- Function to create predictions partitions
CREATE OR REPLACE FUNCTION create_predictions_partition(year INT, month INT)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := 'predictions_' || year || '_' || LPAD(month::TEXT, 2, '0');
    start_date := make_date(year, month, 1);
    end_date := start_date + INTERVAL '1 month';

    -- Create partition if it doesn't exist
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF predictions
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Create partitions for current month, next month, and previous 2 months
DO $$
DECLARE
    current_date DATE := CURRENT_DATE;
    i INT;
BEGIN
    FOR i IN -2..1 LOOP
        PERFORM create_predictions_partition(
            EXTRACT(YEAR FROM current_date + (i || ' month')::INTERVAL)::INT,
            EXTRACT(MONTH FROM current_date + (i || ' month')::INTERVAL)::INT
        );
    END LOOP;
END $$;

-- ============================================================================
-- BACKTESTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    strategy TEXT NOT NULL,
    symbol TEXT NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital NUMERIC(20, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    performance JSONB,
    trading JSONB,
    trades_data JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_backtests_tenant_id ON backtests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status) WHERE status IN ('queued', 'running');
CREATE INDEX IF NOT EXISTS idx_backtests_strategy_symbol ON backtests(tenant_id, strategy, symbol);

-- Enable RLS
ALTER TABLE backtests ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's backtests
CREATE POLICY backtests_tenant_isolation_policy ON backtests
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- TRADES
-- ============================================================================

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    order_type TEXT NOT NULL CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'cancelled', 'rejected')),
    backtest_id UUID REFERENCES backtests(id) ON DELETE SET NULL,
    strategy TEXT,
    pnl NUMERIC(20, 8),
    fees NUMERIC(20, 8),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trades_tenant_id ON trades(tenant_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(tenant_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trades_backtest_id ON trades(backtest_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);

-- Enable RLS
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's trades
CREATE POLICY trades_tenant_isolation_policy ON trades
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- PORTFOLIOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_value NUMERIC(20, 2) NOT NULL,
    cash NUMERIC(20, 2) NOT NULL,
    positions JSONB NOT NULL DEFAULT '[]'::jsonb,
    daily_pnl NUMERIC(20, 2),
    total_pnl NUMERIC(20, 2),
    metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_portfolios_tenant_id ON portfolios(tenant_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_timestamp ON portfolios(timestamp DESC);

-- Enable RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's portfolios
CREATE POLICY portfolios_tenant_isolation_policy ON portfolios
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- ML MODELS METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    model_type TEXT NOT NULL,
    version TEXT NOT NULL,
    training_data_start TIMESTAMPTZ NOT NULL,
    training_data_end TIMESTAMPTZ NOT NULL,
    metrics JSONB DEFAULT '{}'::jsonb,
    config JSONB DEFAULT '{}'::jsonb,
    file_path TEXT, -- Path in Supabase Storage
    status TEXT NOT NULL DEFAULT 'training' CHECK (status IN ('training', 'ready', 'failed', 'deprecated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, symbol, timeframe, model_type, version)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ml_models_tenant_id ON ml_models(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ml_models_symbol_timeframe ON ml_models(tenant_id, symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_ml_models_status ON ml_models(status) WHERE status = 'ready';

-- Enable RLS
ALTER TABLE ml_models ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's models
CREATE POLICY ml_models_tenant_isolation_policy ON ml_models
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);

-- ============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Latest portfolio snapshot per tenant
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_portfolios AS
SELECT DISTINCT ON (tenant_id)
    *
FROM portfolios
ORDER BY tenant_id, timestamp DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_latest_portfolios_tenant_id ON latest_portfolios(tenant_id);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_latest_portfolios()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY latest_portfolios;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- AUTOMATED PARTITION MANAGEMENT
-- ============================================================================

-- Function to create next month's partitions
CREATE OR REPLACE FUNCTION create_next_month_partitions()
RETURNS void AS $$
DECLARE
    next_month DATE := CURRENT_DATE + INTERVAL '1 month';
    year INT := EXTRACT(YEAR FROM next_month);
    month INT := EXTRACT(MONTH FROM next_month);
BEGIN
    PERFORM create_market_data_partition(year, month);
    PERFORM create_predictions_partition(year, month);
    RAISE NOTICE 'Created partitions for % %', year, month;
END;
$$ LANGUAGE plpgsql;

-- Schedule automatic partition creation on the 1st of each month at 00:00
-- Note: pg_cron may not be available on all Supabase plans
-- If pg_cron is not available, run create_next_month_partitions() manually
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        PERFORM cron.schedule(
            'create-monthly-partitions',
            '0 0 1 * *', -- First day of each month at midnight
            $$SELECT create_next_month_partitions()$$
        );
    END IF;
END $$;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to set current tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_uuid::text, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get current tenant context
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', TRUE)::uuid;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Create a default tenant (comment out for production)
-- INSERT INTO tenants (name, slug, settings)
-- VALUES (
--     'Default Tenant',
--     'default',
--     '{"timezone": "UTC", "currency": "USD"}'::jsonb
-- )
-- ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- GRANTS (if using service role)
-- ============================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- Grant access to tables
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Grant access to sequences
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role, authenticated;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_models_updated_at
    BEFORE UPDATE ON ml_models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Multi-Tenant Trading Bot Schema Created Successfully!';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Create your first tenant';
    RAISE NOTICE '2. Set tenant context: SELECT set_tenant_context(''<tenant_uuid>'');';
    RAISE NOTICE '3. Start inserting data';
    RAISE NOTICE '================================================';
END $$;
