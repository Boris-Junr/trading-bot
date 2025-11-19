-- Create user_roles reference table
CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_role_name CHECK (role_name IN ('admin', 'user'))
);

-- Insert default roles
INSERT INTO public.user_roles (role_name, description) VALUES
    ('admin', 'Administrator with full system access including resource monitoring'),
    ('user', 'Regular user with access to their own tasks and predictions')
ON CONFLICT (role_name) DO NOTHING;

-- Create user_role_assignments table
CREATE TABLE IF NOT EXISTS public.user_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES public.user_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Ensure a user can only have one role assignment per role
    CONSTRAINT unique_user_role UNIQUE (user_id, role_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_user_id ON public.user_role_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_role_id ON public.user_role_assignments(role_id);

-- Enable Row Level Security
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_role_assignments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_roles (read-only for all authenticated users)
CREATE POLICY "Anyone can view roles"
    ON public.user_roles
    FOR SELECT
    TO authenticated
    USING (true);

-- RLS Policies for user_role_assignments
-- Users can view their own role assignments
CREATE POLICY "Users can view their own role assignments"
    ON public.user_role_assignments
    FOR SELECT
    USING (auth.uid() = user_id);

-- Only admins can insert/update/delete role assignments
-- Note: This will be enforced by the application layer initially
-- You can add more complex policies later with a is_admin() function

-- Add helpful comments
COMMENT ON TABLE public.user_roles IS 'Reference table for available user roles';
COMMENT ON TABLE public.user_role_assignments IS 'Assigns roles to users for access control';

-- Create a helper function to check if a user is an admin
CREATE OR REPLACE FUNCTION public.is_user_admin(check_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM public.user_role_assignments ura
        JOIN public.user_roles ur ON ura.role_id = ur.id
        WHERE ura.user_id = check_user_id
        AND ur.role_name = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION public.is_user_admin(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_user_admin(UUID) TO anon;

COMMENT ON FUNCTION public.is_user_admin IS 'Check if a user has admin role';
