# Setup & Deployment Guide

Complete guide for setting up and deploying the trading bot application in development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Database Setup (Supabase)](#database-setup-supabase)
4. [Environment Configuration](#environment-configuration)
5. [Running the Application](#running-the-application)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Prerequisites

### Required Software

#### Backend Requirements
- **Python**: Version 3.13 or higher
  - Download: https://www.python.org/downloads/
  - Verify: `python --version` or `python3 --version`
- **pip**: Python package manager (included with Python)
  - Verify: `pip --version`
- **virtualenv** (recommended): For isolated Python environments
  - Install: `pip install virtualenv`

#### Frontend Requirements
- **Node.js**: Version 22.x or higher (LTS recommended)
  - Download: https://nodejs.org/
  - Verify: `node --version`
- **npm**: Node package manager (included with Node.js)
  - Verify: `npm --version`

#### General Requirements
- **Git**: For version control
  - Download: https://git-scm.com/
  - Verify: `git --version`
- **Text Editor/IDE**: VS Code, PyCharm, or similar

### System Requirements

#### Development Environment
- **CPU**: 4+ cores recommended
- **RAM**: 8+ GB (16 GB recommended for ML training)
- **Disk Space**: 5+ GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

#### Production Environment
- **CPU**: 8+ cores recommended
- **RAM**: 16+ GB (32 GB for high-frequency trading)
- **Disk Space**: 20+ GB for historical data and model storage
- **OS**: Linux (Ubuntu 22.04 LTS recommended)

---

## Development Setup

### 1. Clone the Repository

```bash
# Clone from your repository
git clone <repository-url>
cd trading-bot

# Verify project structure
ls -la
# You should see: backend/, frontend/, README.md, CLAUDE.md, etc.
```

### 2. Backend Setup

#### 2.1 Create Python Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python  # macOS/Linux
where python  # Windows
```

#### 2.2 Install Backend Dependencies

```bash
# Ensure you're in backend/ directory with venv activated
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
# Should show: fastapi, uvicorn, ccxt, pandas, etc.
```

#### 2.3 Install ML Dependencies (Optional but Recommended)

If you plan to train models locally:

```bash
pip install lightgbm>=4.0.0
pip install scikit-learn>=1.3.0
pip install ta>=0.11.0  # Technical analysis library
```

### 3. Frontend Setup

#### 3.1 Install Node Dependencies

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
# Should show: vue, vite, pinia, tailwindcss, etc.
```

#### 3.2 Verify Build Tools

```bash
# Test TypeScript compilation
npm run build

# If successful, you'll see dist/ directory created
ls dist/
```

---

## Database Setup (Supabase)

The application uses Supabase for authentication, data storage, and real-time features.

### 1. Create Supabase Project

1. Go to https://supabase.com/
2. Sign up or log in
3. Click "New Project"
4. Fill in project details:
   - **Name**: trading-bot (or your preferred name)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
5. Wait for project to be provisioned (~2 minutes)

### 2. Get API Credentials

1. In Supabase Dashboard, go to **Settings** → **API**
2. Note the following values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Project API keys**:
     - `anon` public key (for frontend)
     - `service_role` secret key (for backend, admin operations)

### 3. Set Up Database Schema

#### 3.1 Create Tables

Run this SQL in Supabase SQL Editor (**SQL Editor** → **New Query**):

```sql
-- API Key Providers
CREATE TABLE api_key_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User API Keys (encrypted)
CREATE TABLE user_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider_id UUID NOT NULL REFERENCES api_key_providers(id),
  environment TEXT NOT NULL CHECK (environment IN ('live', 'testnet')),
  api_key_encrypted TEXT NOT NULL,
  api_secret_encrypted TEXT NOT NULL,
  api_key_hint TEXT,
  api_secret_hint TEXT,
  label TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, provider_id, environment, label)
);

-- Predictions
CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Backtests (optional - currently stored as files)
CREATE TABLE backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  strategy TEXT NOT NULL,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ NOT NULL,
  initial_capital NUMERIC NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Insert default providers
INSERT INTO api_key_providers (provider_name) VALUES
  ('binance'),
  ('alpaca'),
  ('interactive_brokers');
```

#### 3.2 Set Up Row Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtests ENABLE ROW LEVEL SECURITY;

-- User API Keys policies
CREATE POLICY "Users can view their own API keys"
  ON user_api_keys FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own API keys"
  ON user_api_keys FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own API keys"
  ON user_api_keys FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own API keys"
  ON user_api_keys FOR DELETE
  USING (auth.uid() = user_id);

-- Predictions policies
CREATE POLICY "Users can view their own predictions"
  ON predictions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own predictions"
  ON predictions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Backtests policies
CREATE POLICY "Users can view their own backtests"
  ON backtests FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own backtests"
  ON backtests FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

#### 3.3 Create Admin User Metadata

To designate admin users (who can see all tasks and resource metrics):

```sql
-- Add is_admin column to user metadata
-- This is done in Supabase Dashboard: Authentication → Users
-- For each admin user, add to their user_metadata:
{
  "is_admin": true
}
```

### 4. Set Up Authentication

1. In Supabase Dashboard, go to **Authentication** → **Providers**
2. Enable **Email** provider (enabled by default)
3. Configure email templates if desired (**Authentication** → **Email Templates**)
4. Create your first user:
   - Go to **Authentication** → **Users**
   - Click "Add user"
   - Enter email and password
   - Check "Auto Confirm User" to skip email verification
   - Click "Create user"
5. Set as admin (optional):
   - Click on the user
   - Go to "User Metadata" tab
   - Add: `{"is_admin": true}`
   - Click "Save"

---

## Environment Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Encryption Key for API Keys
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-generated-encryption-key-here

# Exchange API Keys (for data fetching)
# Binance (optional - for crypto data)
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-secret

# Alpaca (optional - for stock data)
ALPACA_API_KEY=your-alpaca-key
ALPACA_API_SECRET=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use paper trading endpoint

# Data Storage Backend
# Options: "parquet" (default, file-based) or "timescaledb" (postgres-based)
DATA_BACKEND=parquet

# TimescaleDB Configuration (if using timescaledb backend)
# TIMESCALEDB_URL=postgresql://user:password@localhost:5432/trading_data

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

#### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# Supabase Configuration (same as backend)
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### Security Notes

- **Never commit `.env` files** to version control
- Keep `.env.example` files with dummy values for reference
- Use different credentials for development/staging/production
- Rotate API keys and secrets regularly
- Use service role key only in backend, never in frontend

---

## Running the Application

### Development Mode

#### 1. Start Backend Server

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Run FastAPI server with auto-reload
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the shorthand:
uvicorn api.main:app --reload
```

**Backend will be available at:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 2. Start Frontend Dev Server

In a **new terminal window**:

```bash
# Navigate to frontend directory
cd frontend

# Start Vite dev server
npm run dev
```

**Frontend will be available at:**
- App: http://localhost:5173

#### 3. Access the Application

1. Open browser to http://localhost:5173
2. You should see the login page
3. Log in with your Supabase user credentials
4. Explore the dashboard!

### Production Mode

#### Backend Production

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run with multiple workers for production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn (recommended for Linux production)
pip install gunicorn
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Production

```bash
cd frontend

# Build for production
npm run build

# Preview production build locally
npm run preview

# Or serve with a static file server
npx serve -s dist -p 5173
```

---

## Production Deployment

### Option 1: VPS Deployment (DigitalOcean, Linode, AWS EC2)

#### 1. Prepare Server

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install required software
apt install -y python3.13 python3.13-venv python3-pip nginx certbot python3-certbot-nginx nodejs npm git

# Create app user
useradd -m -s /bin/bash trading-bot
usermod -aG sudo trading-bot
su - trading-bot
```

#### 2. Clone and Setup Application

```bash
# Clone repository
git clone <your-repo-url>
cd trading-bot

# Setup backend
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build
```

#### 3. Configure Systemd Service (Backend)

Create `/etc/systemd/system/trading-bot-backend.service`:

```ini
[Unit]
Description=Trading Bot Backend API
After=network.target

[Service]
Type=notify
User=trading-bot
Group=trading-bot
WorkingDirectory=/home/trading-bot/trading-bot/backend
Environment="PATH=/home/trading-bot/trading-bot/backend/venv/bin"
ExecStart=/home/trading-bot/trading-bot/backend/venv/bin/gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot-backend
sudo systemctl start trading-bot-backend
sudo systemctl status trading-bot-backend
```

#### 4. Configure Nginx (Reverse Proxy + Frontend)

Create `/etc/nginx/sites-available/trading-bot`:

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /home/trading-bot/trading-bot/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Set Up SSL with Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

#### 6. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### Option 2: Docker Deployment (Coming Soon)

Docker support is planned for future versions. The setup would include:
- Multi-stage Docker builds for backend and frontend
- Docker Compose orchestration
- Volume mounts for data persistence
- Health checks and auto-restart

### Option 3: Cloud Platforms

#### Vercel (Frontend Only)

```bash
cd frontend
npm install -g vercel
vercel
```

#### Railway (Backend + Frontend)

1. Connect GitHub repository
2. Add environment variables
3. Deploy with auto-scaling

#### Render (Full Stack)

1. Create Web Service for backend
2. Create Static Site for frontend
3. Configure environment variables
4. Deploy

---

## Troubleshooting

### Common Issues

#### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'api'`

**Solution**:
```bash
# Ensure you're running from the backend/ directory
cd backend
python -m uvicorn api.main:app --reload
```

**Problem**: `Address already in use: Port 8000`

**Solution**:
```bash
# Find and kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Or use different port:
uvicorn api.main:app --port 8001
```

**Problem**: Supabase authentication errors

**Solution**:
- Verify `.env` file has correct `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- Check Supabase project is active and accessible
- Ensure user exists in Supabase Auth dashboard

#### Frontend Issues

**Problem**: `Failed to fetch` or CORS errors

**Solution**:
- Verify backend is running on port 8000
- Check `VITE_API_BASE_URL` in frontend `.env`
- Ensure CORS is enabled in FastAPI (should be enabled by default)

**Problem**: Authentication redirect loop

**Solution**:
- Clear browser cache and cookies
- Verify Supabase URL and keys match between frontend and backend
- Check Supabase Auth settings allow redirects to localhost

**Problem**: Build fails with TypeScript errors

**Solution**:
```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```

#### Database Issues

**Problem**: RLS policies preventing access

**Solution**:
- Verify user is authenticated (check JWT token)
- Ensure RLS policies are correctly set up in Supabase
- Check user_id matches between auth and data tables

**Problem**: Predictions/backtests not saving

**Solution**:
- Check backend logs for SQL errors
- Verify Supabase service role key is correct
- Ensure tables exist and have correct schema

### Debug Mode

#### Backend Debug Mode

Add to `backend/.env`:
```env
LOG_LEVEL=DEBUG
```

Then check logs:
```bash
# View backend logs
tail -f backend/logs/api.log

# Or run with verbose output
uvicorn api.main:app --reload --log-level debug
```

#### Frontend Debug Mode

Open browser DevTools (F12) and check:
- **Console tab**: JavaScript errors
- **Network tab**: API request/response details
- **Application tab**: LocalStorage, cookies

Enable Vue DevTools:
- Install browser extension: Vue.js devtools
- Restart browser
- Open DevTools → Vue tab

### Performance Issues

**Problem**: ML training takes too long

**Solution**:
- Reduce `days_history` parameter (e.g., 7 instead of 30)
- Reduce `n_steps_ahead` (e.g., 100 instead of 300)
- Use faster timeframes (5m instead of 1m for testing)
- Increase system RAM if available

**Problem**: Frontend is slow/laggy

**Solution**:
- Check browser extensions (ad blockers can interfere)
- Clear browser cache
- Disable browser animations if needed
- Use production build (`npm run build`) instead of dev mode

---

## Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd ../frontend
npm install

# Rebuild frontend
npm run build

# Restart services
sudo systemctl restart trading-bot-backend
```

### Database Backups

#### Automated Supabase Backups

Supabase provides automatic daily backups for paid plans. For free tier:

1. Go to **Database** → **Backups** in Supabase Dashboard
2. Click "Backup Now" to create manual backup
3. Download backup file for safekeeping

#### Manual Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump "$SUPABASE_DB_URL" > "backup_$DATE.sql"
echo "Backup created: backup_$DATE.sql"
```

### Log Rotation

For production, set up log rotation:

Create `/etc/logrotate.d/trading-bot`:

```
/home/trading-bot/trading-bot/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 trading-bot trading-bot
}
```

### Monitoring

#### Health Checks

- Backend health: `curl http://localhost:8000/api/health`
- Expected response: `{"status":"ok","version":"1.0.0"}`

#### System Resources

Monitor via the Status Center in the web UI, or use command line:

```bash
# CPU usage
top -bn1 | grep "Cpu(s)"

# Memory usage
free -h

# Disk usage
df -h
```

#### Application Logs

```bash
# Backend logs
journalctl -u trading-bot-backend -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Security Updates

**Monthly routine**:
1. Update system packages: `sudo apt update && sudo apt upgrade`
2. Update Python packages: `pip list --outdated` then `pip install --upgrade <package>`
3. Update Node packages: `npm outdated` then `npm update`
4. Review Supabase security advisories
5. Rotate API keys if compromised
6. Review access logs for suspicious activity

---

## Related Documentation

- [Architecture Overview](../features/01-ARCHITECTURE.md)
- [Authentication & Security](../features/03-AUTHENTICATION-SECURITY.md)
- [API Reference](../features/08-API-REFERENCE.md)
- [System Monitoring](../features/04-SYSTEM-MONITORING.md)

---

**Questions or Issues?**

- Check the [Troubleshooting](#troubleshooting) section
- Review backend logs for error details
- Open an issue in the repository

**Happy Trading!** 🚀📈
