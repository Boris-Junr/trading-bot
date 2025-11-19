# Vercel Deployment Troubleshooting

## Current TypeScript Module Resolution Issue

If you're getting `Cannot find module '@/lib/supabase'` errors on Vercel, follow these steps:

### 1. Clear Vercel's Build Cache

Vercel caches dependencies and build outputs. After pushing code changes, you must clear the cache:

**In Vercel Dashboard:**
1. Go to your project
2. Click **Settings** → **General**
3. Scroll to **Build & Development Settings**
4. Click **Clear Build Cache** button
5. Redeploy

**OR via Vercel CLI:**
```bash
vercel --force
```

### 2. Verify Root Directory Setting

1. Settings → General
2. **Root Directory** must be set to: `frontend`
3. **Framework Preset**: `Vite`

### 3. Verify Environment Variables

Settings → Environment Variables - ensure these are set:
- `VITE_SUPABASE_URL` - Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Your Supabase anon/public key
- `VITE_API_BASE_URL` - **REQUIRED**: Your Render backend URL (e.g., `https://your-app.onrender.com/api`)

**IMPORTANT**: After adding/changing environment variables, you MUST:
1. Clear build cache (Settings → General → Clear Build Cache)
2. Redeploy (Deployments → ⋯ → Redeploy, uncheck "Use existing Build Cache")

### 4. Verify Node.js Version

1. Settings → General
2. Under **Node.js Version**, select: `22.x`

### 5. Check Build Command

The build command should be auto-detected as:
```
npm run build
```

Which runs: `vue-tsc --noEmit && vite build`

### 6. Manual Redeploy

After making the above changes:
1. Go to **Deployments** tab
2. Click ⋯ menu on latest deployment
3. Select **Redeploy**
4. Make sure "Use existing Build Cache" is **UNCHECKED**

## Recent Fixes Applied

✅ Added `frontend/src/vite-env.d.ts` for Vite type declarations
✅ Updated `frontend/tsconfig.json` with path mappings
✅ Changed build command from `vue-tsc -b` to `vue-tsc --noEmit`
✅ All TypeScript errors resolved locally

## If Still Failing

1. Check Vercel build logs for the EXACT error
2. Verify all commits are pushed: `git log --oneline -5`
3. Ensure Vercel pulled latest code: check deployment commit hash
4. Try deploying from a fresh branch

## Contact

If issue persists after following all steps, provide:
- Full Vercel build log
- Deployment commit hash
- Screenshot of Vercel settings
