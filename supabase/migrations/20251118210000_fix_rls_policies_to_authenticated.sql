-- Fix RLS policies to use 'authenticated' role instead of 'public'
-- This ensures only authenticated users can access tables

-- ============================================================================
-- BACKTESTS TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "backtests_isolation_policy" ON public.backtests;

-- Create new policy with authenticated role
CREATE POLICY "backtests_isolation_policy"
    ON public.backtests
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- PREDICTIONS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own predictions" ON public.predictions;
DROP POLICY IF EXISTS "Users can insert their own predictions" ON public.predictions;
DROP POLICY IF EXISTS "Users can update their own predictions" ON public.predictions;
DROP POLICY IF EXISTS "Users can delete their own predictions" ON public.predictions;

-- Create new policies with authenticated role
CREATE POLICY "Users can view their own predictions"
    ON public.predictions
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own predictions"
    ON public.predictions
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own predictions"
    ON public.predictions
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own predictions"
    ON public.predictions
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- ML_MODELS TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "ml_models_isolation_policy" ON public.ml_models;

-- Create new policy with authenticated role
CREATE POLICY "ml_models_isolation_policy"
    ON public.ml_models
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- PORTFOLIOS TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "portfolios_isolation_policy" ON public.portfolios;

-- Create new policy with authenticated role
CREATE POLICY "portfolios_isolation_policy"
    ON public.portfolios
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- TRADES TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "trades_isolation_policy" ON public.trades;

-- Create new policy with authenticated role
CREATE POLICY "trades_isolation_policy"
    ON public.trades
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "users_isolation_policy" ON public.users;

-- Create new policy with authenticated role
CREATE POLICY "users_isolation_policy"
    ON public.users
    FOR ALL
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- ============================================================================
-- USER_ROLE_ASSIGNMENTS TABLE
-- ============================================================================

-- Drop existing policy
DROP POLICY IF EXISTS "Users can view their own role assignments" ON public.user_role_assignments;

-- Create new policy with authenticated role
CREATE POLICY "Users can view their own role assignments"
    ON public.user_role_assignments
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- USER_ROLES TABLE (already correct, but included for completeness)
-- ============================================================================

-- This one is already correct, but let's ensure it's properly set
DROP POLICY IF EXISTS "Anyone can view roles" ON public.user_roles;

CREATE POLICY "Authenticated users can view roles"
    ON public.user_roles
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'RLS Policies Updated to Authenticated Role';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'All policies now require authenticated users';
    RAISE NOTICE 'Anonymous access is blocked at the policy level';
    RAISE NOTICE '================================================';
END $$;
