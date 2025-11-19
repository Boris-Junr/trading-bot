"""
Portfolio API endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from api.models import Portfolio, Position

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=Portfolio)
async def get_portfolio():
    """Get current portfolio state"""
    # Mock data for now - will be replaced with real data
    return Portfolio(
        total_value=12345.67,
        cash=5000.00,
        positions=[
            Position(
                symbol="ETH_USDT",
                side="long",
                quantity=3.0,
                entry_price=2300.00,
                current_price=2345.67,
                pnl=137.01,
                pnl_pct=1.98,
                opened_at=(datetime.now() - timedelta(hours=2)).isoformat()
            ),
            Position(
                symbol="BTC_USDT",
                side="long",
                quantity=0.15,
                entry_price=42000.00,
                current_price=42500.00,
                pnl=75.00,
                pnl_pct=1.19,
                opened_at=(datetime.now() - timedelta(hours=5)).isoformat()
            )
        ],
        daily_pnl=145.50,
        daily_pnl_pct=1.18,
        total_pnl=534.23,
        total_pnl_pct=4.52
    )


@router.get("/history")
async def get_portfolio_history(days: int = 30):
    """Get portfolio value history"""
    # Mock data - will be replaced with real data
    history = []
    base_value = 10000
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        value = base_value + (i * 50) + ((-1)**i * 100)
        history.append({
            "date": date.isoformat(),
            "value": value
        })
    return history
