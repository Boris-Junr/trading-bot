-- Split RLS policies into separate policies per operation (SELECT, INSERT, UPDATE, DELETE)
-- This follows security best practices for granular access control and future flexibility

-- ============================================================================
-- BACKTESTS TABLE
-- ============================================================================

-- Drop existing combined policy
DROP POLICY IF EXISTS "backtests_isolation_policy" ON public.backtests;

-- Create separate policies for each operation
CREATE POLICY "Users can view their own backtests"
    ON public.backtests
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own backtests"
    ON public.backtests
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own backtests"
    ON public.backtests
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own backtests"
    ON public.backtests
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- ML_MODELS TABLE
-- ============================================================================

-- Drop existing combined policy
DROP POLICY IF EXISTS "ml_models_isolation_policy" ON public.ml_models;

-- Create separate policies for each operation
CREATE POLICY "Users can view their own ml_models"
    ON public.ml_models
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own ml_models"
    ON public.ml_models
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own ml_models"
    ON public.ml_models
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own ml_models"
    ON public.ml_models
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- PORTFOLIOS TABLE
-- ============================================================================

-- Drop existing combined policy
DROP POLICY IF EXISTS "portfolios_isolation_policy" ON public.portfolios;

-- Create separate policies for each operation
CREATE POLICY "Users can view their own portfolios"
    ON public.portfolios
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own portfolios"
    ON public.portfolios
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own portfolios"
    ON public.portfolios
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own portfolios"
    ON public.portfolios
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- TRADES TABLE
-- ============================================================================

-- Drop existing combined policy
DROP POLICY IF EXISTS "trades_isolation_policy" ON public.trades;

-- Create separate policies for each operation
CREATE POLICY "Users can view their own trades"
    ON public.trades
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own trades"
    ON public.trades
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own trades"
    ON public.trades
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own trades"
    ON public.trades
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Drop existing combined policy
DROP POLICY IF EXISTS "users_isolation_policy" ON public.users;

-- Create separate policies for each operation
-- Note: users.id references auth.uid() directly (not user_id column)
CREATE POLICY "Users can view their own profile"
    ON public.users
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.users
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can delete their own profile"
    ON public.users
    FOR DELETE
    TO authenticated
    USING (auth.uid() = id);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'RLS Policies Split by Operation';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'All tables now have separate policies for:';
    RAISE NOTICE '  - SELECT (view)';
    RAISE NOTICE '  - INSERT (create)';
    RAISE NOTICE '  - UPDATE (modify)';
    RAISE NOTICE '  - DELETE (remove)';
    RAISE NOTICE '';
    RAISE NOTICE 'This provides:';
    RAISE NOTICE '  ✓ Granular access control';
    RAISE NOTICE '  ✓ Better auditability';
    RAISE NOTICE '  ✓ Future flexibility';
    RAISE NOTICE '  ✓ Security best practices';
    RAISE NOTICE '================================================';
END $$;
