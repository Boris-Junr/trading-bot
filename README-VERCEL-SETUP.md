# Vercel Deployment Configuration

## Frontend Deployment

Since this is a monorepo, you need to configure Vercel to build only the frontend:

### Option 1: Via Vercel Dashboard (Recommended)

1. Go to your Vercel project settings
2. Set **Root Directory** to: `frontend`
3. Set **Framework Preset** to: `Vite`
4. Build settings should auto-detect:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

### Option 2: Using vercel.json

The `frontend/vercel.json` file is already configured. When deploying:

```bash
cd frontend
vercel --prod
```

### Environment Variables

Make sure to set in Vercel dashboard:
- `VITE_SUPABASE_URL` - Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `VITE_API_BASE_URL` - Your backend API URL (if different from default)

### Troubleshooting

If you get TypeScript errors during build:
1. Ensure `frontend/src/vite-env.d.ts` exists
2. Check that all dependencies are installed
3. Verify Node.js version is 22.x
