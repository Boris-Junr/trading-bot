# Trading Bot Frontend

Modern Vue 3 + TypeScript frontend for managing and visualizing trading bot operations.

## Tech Stack

- Vue 3, TypeScript, Vite
- Vue Router, Pinia (state management)
- Tailwind CSS, Chart.js
- Axios for API calls

## Setup

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start dev server
npm run dev
```

## Available Scripts

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Project Structure

- `src/views/` - Page components
- `src/components/` - Reusable components
- `src/stores/` - Pinia state management
- `src/services/` - API service layer
- `src/types/` - TypeScript types
- `src/router/` - Vue Router configuration

## Features

- Dashboard with portfolio overview
- Backtest results visualization
- ML predictions display
- Strategy management
- Real-time portfolio tracking

See full documentation at [frontend/docs](./docs) (coming soon)
