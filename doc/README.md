# Trading Bot Documentation

Comprehensive documentation for the multi-user trading bot platform with ML predictions, backtesting, and automated trading strategies.

## Quick Start

New to the project? Start here:

1. 📖 [Architecture Overview](features/01-ARCHITECTURE.md) - Understand the system design
2. 🚀 [Setup & Deployment Guide](setup/SETUP-DEPLOYMENT.md) - Get up and running
3. 🔐 [Authentication & Security](features/03-AUTHENTICATION-SECURITY.md) - Configure auth
4. 📚 [API Reference](features/08-API-REFERENCE.md) - Explore available endpoints

## Feature Documentation

### Core Features

Detailed guides for each major feature of the trading bot:

#### 1. [Architecture Overview](features/01-ARCHITECTURE.md)
System design, technology stack, and architectural patterns.
- Layered architecture (API, Domain, Infrastructure)
- Backend and frontend technologies
- Key design patterns
- System components overview

#### 2. [Backtesting System](features/02-BACKTESTING.md)
Strategy backtesting with historical data validation.
- Running backtests via UI and API
- Strategy configuration and parameters
- Performance metrics (Sharpe, Sortino, Calmar ratios)
- Trade-by-trade analysis
- Interactive charts and visualizations

#### 3. [Authentication & Security](features/03-AUTHENTICATION-SECURITY.md)
User authentication, authorization, and API key management.
- Supabase authentication flow
- JWT token management
- Row Level Security (RLS)
- Encrypted API key storage
- Admin vs non-admin access control

#### 4. [System Monitoring](features/04-SYSTEM-MONITORING.md)
Resource management, task queuing, and status monitoring.
- CPU and RAM monitoring
- Task queue system with priority scheduling
- Real-time SSE event streaming
- Status Center UI
- Admin vs non-admin views

#### 5. [Market Data](features/05-MARKET-DATA.md)
Historical data fetching, caching, and symbol management.
- Multi-source data aggregation
- Symbol auto-detection (crypto, stocks, forex, indices)
- Parquet and TimescaleDB storage backends
- Data normalization and cleaning
- Caching strategies

#### 6. [Trading Strategies](features/06-TRADING-STRATEGIES.md)
Pluggable strategy framework for backtesting and live trading.
- Strategy base classes
- ML Predictive Strategy
- Breakout Scalping Strategy
- Auto-discovery registry
- Custom strategy development

#### 7. [Model Management](features/07-MODEL-MANAGEMENT.md)
Machine learning model training and price prediction.
- AutoregressivePredictor (single smooth curve)
- MultiOHLCPredictor (4 specialized models)
- Feature engineering (100+ technical indicators)
- LightGBM gradient boosting
- Model persistence and versioning

#### 8. [API Reference](features/08-API-REFERENCE.md)
Complete REST API endpoint reference.
- Health check
- API keys management
- Market data endpoints
- ML models training and listing
- Predictions generation
- Backtests execution
- Trading strategies CRUD
- System resources and monitoring
- Portfolio management (mock)

## Setup & Deployment

#### [Setup & Deployment Guide](setup/SETUP-DEPLOYMENT.md)
Complete setup instructions for development and production.
- Prerequisites and system requirements
- Backend setup (Python, virtualenv, dependencies)
- Frontend setup (Node.js, npm, Vite)
- Supabase database configuration
- Environment variables configuration
- Development mode
- Production deployment (VPS, cloud platforms)
- Troubleshooting guide
- Maintenance procedures

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.13)
- **ML**: LightGBM, pandas, numpy
- **Data**: CCXT (crypto), Alpaca (stocks), yFinance
- **Database**: Supabase (PostgreSQL) with RLS
- **Authentication**: JWT via Supabase Auth
- **Encryption**: pgcrypto (PGP symmetric)

### Frontend
- **Framework**: Vue 3 + TypeScript
- **State**: Pinia stores
- **UI**: Tailwind CSS, Headless UI
- **Charts**: Chart.js
- **Build**: Vite
- **Auth**: Supabase Client

### Infrastructure
- **Real-time**: Server-Sent Events (SSE)
- **Caching**: Parquet files, in-memory
- **Queue**: Custom resource-aware task queue
- **Monitoring**: psutil for system resources

## Project Structure

```
trading-bot/
├── backend/
│   ├── api/              # FastAPI routers and services
│   ├── domain/           # Business logic (strategies, indicators, ML)
│   ├── data/             # Data fetching and storage
│   ├── infrastructure/   # Cross-cutting concerns (auth, resources)
│   └── backtesting/      # Backtesting engine
├── frontend/
│   ├── src/
│   │   ├── views/        # Page components
│   │   ├── components/   # Reusable UI components
│   │   ├── stores/       # Pinia state management
│   │   ├── composables/  # Vue composition functions
│   │   └── features/     # Feature-specific modules
│   └── public/
├── supabase/
│   └── migrations/       # Database migrations
└── doc/                  # This documentation
```

## Common Tasks & Workflows

### Getting Started
1. Follow [Setup & Deployment Guide](setup/SETUP-DEPLOYMENT.md)
2. Configure Supabase database (see Setup guide)
3. Set up environment variables
4. Start backend and frontend servers
5. Create your first user in Supabase Auth

### Training an ML Model
1. Navigate to Models page in UI
2. Click "Train New Model"
3. Configure: symbol, timeframe, prediction steps, history days
4. Monitor progress in Status Center
5. View model performance metrics

See: [Model Management](features/07-MODEL-MANAGEMENT.md)

### Running a Backtest
1. Navigate to Backtests page
2. Click "New Backtest"
3. Select strategy (e.g., MLPredictive)
4. Configure symbol, date range, initial capital
5. Monitor progress in Status Center
6. Analyze results with performance charts

See: [Backtesting System](features/02-BACKTESTING.md)

### Generating Predictions
1. Navigate to Predictions page
2. Click "Generate Predictions"
3. Select symbol and timeframe
4. Wait for prediction generation (auto-trains if needed)
5. View prediction chart and metrics

See: [Model Management](features/07-MODEL-MANAGEMENT.md)

### Managing API Keys
1. Navigate to Settings → API Keys
2. Click "Add API Key"
3. Select provider (Binance, Alpaca, etc.)
4. Enter credentials (encrypted automatically)
5. Test connection

See: [Authentication & Security](features/03-AUTHENTICATION-SECURITY.md)

### Monitoring System Resources
1. Click CPU chip icon in header
2. View Status Center panel
3. Monitor CPU/RAM usage (admin only)
4. Track running and queued tasks
5. View task completion history

See: [System Monitoring](features/04-SYSTEM-MONITORING.md)

## Troubleshooting

### Quick Fixes

**Backend won't start**
- Check virtual environment is activated
- Verify dependencies: `pip install -r requirements.txt`
- Check `.env` file exists with correct values

**Frontend won't start**
- Verify Node.js version: `node --version` (22.x+)
- Clear and reinstall: `rm -rf node_modules && npm install`
- Check for port conflicts (5173)

**Authentication errors**
- Verify Supabase URL and keys match in backend/frontend
- Check user exists in Supabase Auth dashboard
- Clear browser cookies and localStorage

**Tasks stuck in queue**
- Check Status Center for resource availability
- Verify resource requirements are realistic
- Ensure no other heavy tasks running

For detailed troubleshooting, see [Setup & Deployment Guide - Troubleshooting](setup/SETUP-DEPLOYMENT.md#troubleshooting)

## Contributing

When adding new features:
1. Read relevant documentation sections
2. Follow existing code patterns
3. Write clean, modular code
4. Update documentation for new features
5. Test thoroughly before submitting

See `CLAUDE.md` in repository root for project guidelines.

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Supabase Dashboard**: https://supabase.com/dashboard
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Vue 3 Docs**: https://vuejs.org/

---

**Last Updated**: January 2025

Happy Trading! 🚀📈
