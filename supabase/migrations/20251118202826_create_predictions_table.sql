-- Create predictions table for ML price predictions
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Indexes for common queries
    CONSTRAINT valid_status CHECK (status IN ('running', 'queued', 'completed', 'failed'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON public.predictions(status);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_timeframe ON public.predictions(symbol, timeframe);

-- Enable Row Level Security
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only see/manage their own predictions
CREATE POLICY "Users can view their own predictions"
    ON public.predictions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own predictions"
    ON public.predictions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own predictions"
    ON public.predictions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own predictions"
    ON public.predictions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Enable realtime for predictions table
ALTER PUBLICATION supabase_realtime ADD TABLE public.predictions;

-- Add helpful comment
COMMENT ON TABLE public.predictions IS 'Stores ML price prediction results for users';
