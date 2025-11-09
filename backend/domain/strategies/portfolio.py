"""
Portfolio management for tracking positions and performance.

Handles:
- Cash and position tracking
- P&L calculation
- Position sizing
- Performance metrics
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from .base import Position


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    entry_time: datetime
    exit_price: float
    exit_time: datetime
    size: float
    pnl: float
    pnl_pct: float
    commission: float = 0.0

    @property
    def duration(self) -> float:
        """Trade duration in days."""
        return (self.exit_time - self.entry_time).total_seconds() / 86400

    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0


class Portfolio:
    """
    Manages trading portfolio with cash and positions.

    Tracks:
    - Cash balance
    - Open positions
    - Trade history
    - Performance metrics
    """

    def __init__(self, initial_cash: float = 100000.0, commission: float = 0.0):
        """
        Initialize portfolio.

        Args:
            initial_cash: Starting cash balance
            commission: Commission per trade (as fraction, e.g., 0.001 for 0.1%)
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_rate = commission

        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []

    @property
    def equity(self) -> float:
        """Calculate total equity (cash + positions value)."""
        positions_value = sum(
            pos.current_price * pos.size for pos in self.positions.values()
        )
        return self.cash + positions_value

    @property
    def total_return(self) -> float:
        """Calculate total return as percentage."""
        return ((self.equity - self.initial_cash) / self.initial_cash) * 100

    @property
    def total_pnl(self) -> float:
        """Calculate total P&L in dollars."""
        return self.equity - self.initial_cash

    def open_position(
        self,
        symbol: str,
        side: str,
        price: float,
        timestamp: datetime,
        size_pct: float = 1.0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[Position]:
        """
        Open a new position.

        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            price: Entry price
            timestamp: Entry timestamp
            size_pct: Fraction of available cash to use (0.0 to 1.0)
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Position object if successful, None if insufficient funds
        """
        if symbol in self.positions:
            raise ValueError(f"Position already open for {symbol}")

        # Calculate position size
        available_cash = self.cash * size_pct
        commission = available_cash * self.commission_rate
        net_cash = available_cash - commission

        if net_cash <= 0:
            return None

        size = net_cash / price

        # Update cash based on position type
        if side == 'long':
            # Long: pay for shares
            self.cash -= available_cash
        else:  # short
            # Short: receive cash from selling (minus commission)
            self.cash += net_cash

        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=price,
            entry_time=timestamp,
            size=size,
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions[symbol] = position
        return position

    def close_position(
        self,
        symbol: str,
        price: float,
        timestamp: datetime
    ) -> Optional[Trade]:
        """
        Close an open position.

        Args:
            symbol: Trading symbol
            price: Exit price
            timestamp: Exit timestamp

        Returns:
            Trade object representing the closed trade
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]

        # Calculate P&L
        if position.side == 'long':
            pnl = (price - position.entry_price) * position.size
        else:  # short
            pnl = (position.entry_price - price) * position.size

        pnl_pct = (pnl / (position.entry_price * position.size)) * 100

        # Calculate proceeds and commission
        proceeds = price * position.size
        commission = proceeds * self.commission_rate

        # Update cash based on position type
        if position.side == 'long':
            # Long: sell shares, receive cash
            net_proceeds = proceeds - commission
            self.cash += net_proceeds
        else:  # short
            # Short: buy back shares, pay cash
            cost = proceeds + commission
            self.cash -= cost

        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=position.side,
            entry_price=position.entry_price,
            entry_time=position.entry_time,
            exit_price=price,
            exit_time=timestamp,
            size=position.size,
            pnl=pnl - (commission * 2),  # Entry + exit commission
            pnl_pct=pnl_pct,
            commission=commission * 2
        )

        self.trades.append(trade)
        del self.positions[symbol]

        return trade

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.

        Args:
            prices: Dict of {symbol: price}
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol."""
        return symbol in self.positions

    # Performance metrics

    @property
    def total_trades(self) -> int:
        """Total number of completed trades."""
        return len(self.trades)

    @property
    def winning_trades(self) -> int:
        """Number of winning trades."""
        return sum(1 for t in self.trades if t.is_winner)

    @property
    def losing_trades(self) -> int:
        """Number of losing trades."""
        return sum(1 for t in self.trades if not t.is_winner)

    @property
    def win_rate(self) -> float:
        """Win rate as percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def avg_win(self) -> float:
        """Average winning trade P&L."""
        winners = [t.pnl for t in self.trades if t.is_winner]
        return sum(winners) / len(winners) if winners else 0.0

    @property
    def avg_loss(self) -> float:
        """Average losing trade P&L."""
        losers = [t.pnl for t in self.trades if not t.is_winner]
        return sum(losers) / len(losers) if losers else 0.0

    @property
    def profit_factor(self) -> float:
        """Profit factor (gross profit / gross loss)."""
        gross_profit = sum(t.pnl for t in self.trades if t.is_winner)
        gross_loss = abs(sum(t.pnl for t in self.trades if not t.is_winner))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    def get_summary(self) -> dict:
        """Get portfolio performance summary."""
        return {
            'initial_cash': self.initial_cash,
            'cash': self.cash,
            'equity': self.equity,
            'total_pnl': self.total_pnl,
            'total_return': self.total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'open_positions': len(self.positions)
        }
