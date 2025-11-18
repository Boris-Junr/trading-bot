"""
Portfolio Service - Manages portfolio state and positions
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .data_service import get_data_service


class PortfolioService:
    """Service for managing portfolio state"""

    def __init__(self):
        """Initialize portfolio service"""
        self.data_dir = Path(__file__).parent.parent.parent / 'data' / 'portfolio'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / 'portfolio_state.json'
        self.history_file = self.data_dir / 'portfolio_history.json'
        self.data_service = get_data_service()
        self._load_state()

    def _load_state(self):
        """Load portfolio state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except:
                self._init_state()
        else:
            self._init_state()

    def _init_state(self):
        """Initialize default portfolio state"""
        self.state = {
            'cash': 100000.0,
            'positions': [],
            'last_updated': datetime.now().isoformat()
        }
        self._save_state()

    def _save_state(self):
        """Save portfolio state to file"""
        self.state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_portfolio(self) -> Dict:
        """
        Get current portfolio state

        Returns:
            Portfolio dictionary with positions and metrics
        """
        # Update positions with current prices
        positions = []
        total_position_value = 0.0

        for pos in self.state.get('positions', []):
            current_price = self.data_service.get_current_price(
                pos['symbol'],
                pos.get('timeframe', '1m')
            )

            if current_price is None:
                current_price = pos['entry_price']  # Fallback to entry price

            pnl = (current_price - pos['entry_price']) * pos['quantity']
            pnl_pct = pnl / (pos['entry_price'] * pos['quantity'])

            position_value = current_price * pos['quantity']
            total_position_value += position_value

            positions.append({
                'symbol': pos['symbol'],
                'side': pos['side'],
                'quantity': pos['quantity'],
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'opened_at': pos['opened_at']
            })

        cash = self.state.get('cash', 0.0)
        total_value = cash + total_position_value

        # Calculate P&L
        initial_value = 100000.0  # Would track this properly in production
        total_pnl = total_value - initial_value
        total_pnl_pct = total_pnl / initial_value

        # Daily P&L (would calculate from history in production)
        daily_pnl = sum(p['pnl'] for p in positions)
        daily_pnl_pct = (daily_pnl / total_value) if total_value > 0 else 0.0

        return {
            'total_value': total_value,
            'cash': cash,
            'positions': positions,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct
        }

    def get_history(self, days: int = 30) -> List[Dict]:
        """
        Get portfolio value history

        Args:
            days: Number of days of history to return

        Returns:
            List of historical value points
        """
        # Load history from file
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    # Filter to requested days
                    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                    return [h for h in history if h['date'] >= cutoff][-days:]
            except:
                pass

        # Generate mock history if no real data
        history = []
        base_value = 100000
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Simple random walk
            value = base_value + (i * 50) + ((-1)**i * 100)
            history.append({
                'date': date.isoformat(),
                'value': value
            })

        return history

    def add_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        timeframe: str = '1m'
    ) -> bool:
        """
        Add a new position to the portfolio

        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            quantity: Position size
            entry_price: Entry price
            timeframe: Timeframe

        Returns:
            True if successful
        """
        try:
            position_cost = entry_price * quantity

            # Check if we have enough cash
            if position_cost > self.state['cash']:
                print(f"Insufficient cash: need ${position_cost}, have ${self.state['cash']}")
                return False

            # Deduct cash
            self.state['cash'] -= position_cost

            # Add position
            self.state['positions'].append({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'timeframe': timeframe,
                'opened_at': datetime.now().isoformat()
            })

            self._save_state()
            return True

        except Exception as e:
            print(f"Error adding position: {e}")
            return False

    def close_position(self, symbol: str) -> bool:
        """
        Close a position

        Args:
            symbol: Symbol to close

        Returns:
            True if successful
        """
        try:
            # Find position
            position = None
            for i, pos in enumerate(self.state['positions']):
                if pos['symbol'] == symbol:
                    position = self.state['positions'].pop(i)
                    break

            if position is None:
                print(f"Position not found: {symbol}")
                return False

            # Get current price
            current_price = self.data_service.get_current_price(
                symbol,
                position.get('timeframe', '1m')
            )

            if current_price is None:
                current_price = position['entry_price']

            # Calculate proceeds
            proceeds = current_price * position['quantity']

            # Add cash back
            self.state['cash'] += proceeds

            self._save_state()
            return True

        except Exception as e:
            print(f"Error closing position: {e}")
            return False


# Singleton instance
_portfolio_service = None


def get_portfolio_service() -> PortfolioService:
    """Get or create portfolio service singleton"""
    global _portfolio_service
    if _portfolio_service is None:
        _portfolio_service = PortfolioService()
    return _portfolio_service
