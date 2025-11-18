# Trading Bot

An intelligent, automated trading system for cryptocurrencies and stocks with predictive analytics, backtesting capabilities, and real-time portfolio management.

## Overview

This trading bot combines machine learning predictions, technical analysis, and pattern recognition to make informed trading decisions. The system features a robust backend for data processing and decision-making, paired with a modern Vue.js frontend for monitoring and control.

## Features

### Backend Capabilities
- **Data Collection & Cleaning**: Multi-source data aggregation from crypto and stock markets
- **Predictive Analytics**:
  - Pattern recognition (pennants, flags, wedges, triangles)
  - Asset correlation analysis
  - Technical indicators (MACD, RSI, Bollinger Bands, etc.)
  - Sentiment analysis (Twitter, Reddit)
  - Machine Learning predictions using gradient boosting
- **Backtesting**: Test strategies against historical data with detailed performance metrics
- **Decision Engine**: Automated position management (open, hold, close)
- **Resource Management**: Intelligent task queuing with CPU/RAM monitoring
- **RESTful API**: Full-featured API for all trading operations

### Frontend Features
- **Portfolio Dashboard**: Real-time portfolio performance and positions
- **Strategy Management**: Configure and monitor trading strategies
- **Backtesting Interface**: Run and analyze backtests with visual charts
- **Model Monitoring**: Track ML model performance and predictions
- **System Status**: Resource monitoring and task queue management
- **Responsive Design**: Modern, glassmorphic UI with dark theme

## Tech Stack

### Backend
- **Python 3.13+**
- **FastAPI**: High-performance REST API framework
- **ccxt**: Cryptocurrency exchange integration
- **pandas/numpy**: Data processing and analysis
- **psutil**: System resource monitoring
- **uvicorn**: ASGI server

### Frontend
- **Vue 3**: Progressive JavaScript framework with Composition API
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling
- **Chart.js**: Interactive charts and visualizations
- **Heroicons**: Icon library

## Prerequisites

- **Python**: 3.13 or higher
- **Node.js**: 22.x or higher (with npm)
- **Git**: For version control

## Project Structure

```
trading-bot/
├── backend/              # Python backend
│   ├── api/             # FastAPI application
│   ├── domain/          # Business logic and strategies
│   ├── infrastructure/  # Resource management, external services
│   ├── analysis/        # ML models and technical analysis
│   ├── data/            # Data collection and storage
│   ├── output/          # Generated reports and backtests
│   └── requirements.txt # Python dependencies
├── frontend/            # Vue.js frontend
│   ├── src/
│   │   ├── features/   # Feature-based components
│   │   ├── shared/     # Shared components and utilities
│   │   ├── stores/     # Pinia state management
│   │   ├── views/      # Page components
│   │   └── router/     # Route definitions
│   └── package.json    # Node dependencies
└── CLAUDE.md           # Project guidelines
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd trading-bot
```

### 2. Backend Setup

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

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Configuration

### Backend Configuration

Create a `.env` file in the `backend/` directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Exchange API Keys (example for Binance)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Database (if applicable)
DATABASE_URL=sqlite:///./trading.db

# Environment
ENVIRONMENT=development
```

### Frontend Configuration

The frontend automatically connects to the backend at `http://localhost:8000`. To customize, create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Running the Application

### Development Mode

#### 1. Start the Backend Server

```bash
cd backend
# Activate virtual environment if not already active
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Run the FastAPI server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc` (ReDoc)

#### 2. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Production Build

#### Backend
```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend
```bash
cd frontend
npm run build
npm run preview  # Preview production build
```

## Usage

### Running a Backtest

1. Navigate to the **Backtests** page
2. Click "New Backtest"
3. Configure parameters:
   - Strategy (e.g., MLPredictive, TrendFollowing)
   - Symbol (e.g., BTC/USDT)
   - Timeframe (e.g., 1h, 1d)
   - Date range
   - Initial capital
4. Submit and monitor progress in **System Status** page
5. View results with performance metrics and charts

### Monitoring System Resources

- Click the **CPU chip icon** in the header to access the Status Center
- View real-time CPU and RAM usage
- Monitor running and queued tasks
- Track task completion history

### Managing Strategies

1. Navigate to the **Strategies** page
2. View available strategies with descriptions
3. Configure strategy parameters
4. Enable/disable strategies for live trading

## Development

### Backend Development

- **Domain-Driven Design**: Business logic organized by domain
- **Clean Architecture**: Separation of concerns across layers
- **Type Safety**: Pydantic models for data validation
- **Async/Await**: Non-blocking I/O operations

### Frontend Development

- **Component-Based**: Reusable Vue components
- **TypeScript**: Type-safe development
- **Composables**: Shared logic extraction
- **State Management**: Pinia stores for global state
- **Routing**: Vue Router for navigation

### Code Quality

- Follow existing patterns and conventions
- Keep modules small and focused (single responsibility)
- Write clean, readable code with proper comments
- Never commit API keys or secrets (use `.env` files)

## Key Architecture Features

### Resource Management System
- Monitors CPU and RAM availability
- Queues tasks when resources are insufficient
- Prioritizes tasks based on type and creation time
- Prevents system overload with 20% buffer threshold

### Task Queue System
- Background worker for automatic task execution
- Real-time progress updates via Server-Sent Events (SSE)
- Task status tracking (pending, running, completed, failed)
- Configurable resource requirements per task type

### Machine Learning Pipeline
- Gradient boosting models for price prediction
- Feature engineering with technical indicators
- Model persistence and versioning
- Backtesting validation before live deployment

## API Endpoints

Key endpoints (see `/docs` for complete API documentation):

- `GET /api/backtests` - List all backtests
- `POST /api/backtests` - Create new backtest
- `GET /api/strategies` - List available strategies
- `GET /api/models` - List trained models
- `GET /api/portfolio` - Get portfolio status
- `GET /api/system/resources` - Get system resource status
- `GET /api/tasks/running` - Get running tasks
- `GET /api/tasks/queued` - Get queued tasks

## Troubleshooting

### Backend won't start
- Ensure virtual environment is activated
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.13+)

### Frontend won't start
- Ensure Node.js is installed: `node --version` (should be 22.x+)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check for port conflicts (default: 5173)

### Tasks stuck in queue
- Check System Status page for resource availability
- Verify resource requirements are realistic
- Ensure background worker is running

### API connection errors
- Verify backend is running on correct port (default: 8000)
- Check CORS settings if accessing from different origin
- Review browser console for detailed error messages

## License

[Your chosen license]

## Contributing

1. Follow the project guidelines in `CLAUDE.md`
2. Write clean, modular code
3. Test thoroughly before submitting
4. Document new features and API changes

## Support

For issues and questions, please create an issue in the repository.

---

**Note**: This is an active development project. Features and documentation are continuously evolving.
