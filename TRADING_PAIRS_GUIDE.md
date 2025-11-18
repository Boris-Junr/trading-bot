# Trading Pairs Configuration Guide

## Overview

The trading bot now has a centralized configuration system for allowed trading pairs, focusing on **high-volatility, liquid assets** suitable for day trading and scalping strategies.

## Location

- **Configuration**: `backend/domain/config/trading_pairs.py`
- **Validation**: `backend/domain/config/validation.py`

## Supported Asset Types

### 1. Cryptocurrency (8 pairs)
24/7 trading, highest volatility

| Symbol | Name | Daily Volatility | Rank | Recommended Timeframes |
|--------|------|------------------|------|------------------------|
| BTC/USDT | Bitcoin / Tether | 3.5% | #1 | 1m, 5m, 15m, 1h |
| ETH/USDT | Ethereum / Tether | 4.5% | #2 | 1m, 5m, 15m, 1h |
| BNB/USDT | Binance Coin / Tether | 5.0% | #3 | 1m, 5m, 15m, 1h |
| SOL/USDT | Solana / Tether | 6.0% | #4 | 1m, 5m, 15m |
| XRP/USDT | Ripple / Tether | 5.5% | #5 | 1m, 5m, 15m |
| ADA/USDT | Cardano / Tether | 5.5% | #6 | 1m, 5m, 15m |
| DOGE/USDT | Dogecoin / Tether | **8.0%** | #7 | 1m, 5m, 15m |
| MATIC/USDT | Polygon / Tether | 6.0% | #8 | 1m, 5m, 15m |

### 2. Forex (5 pairs)
As mentioned in the YouTube video strategy

| Symbol | Name | Daily Volatility | Rank | Recommended Timeframes |
|--------|------|------------------|------|------------------------|
| EUR/USD | Euro / US Dollar | 0.8% (80 pips) | #1 | 1m, 5m, 15m, 1h |
| GBP/USD | British Pound / US Dollar | 1.0% (100 pips) | #2 | 1m, 5m, 15m, 1h |
| USD/JPY | US Dollar / Japanese Yen | 0.9% (90 pips) | #3 | 1m, 5m, 15m, 1h |
| GBP/JPY | British Pound / Japanese Yen | **1.5%** (150 pips) | #5 | 1m, 5m, 15m |
| EUR/GBP | Euro / British Pound | 0.8% (80 pips) | #6 | 1m, 5m, 15m |

*Trading Hours: 24/5 (Sunday 22:00 - Friday 22:00 UTC)*

### 3. Stock Indices (6 pairs)
As mentioned in the YouTube video strategy

| Symbol | Name | Daily Volatility | Rank | Recommended Timeframes |
|--------|------|------------------|------|------------------------|
| US30 | Dow Jones | 1.5% | #1 | 1m, 5m, 15m, 1h |
| NAS100 | NASDAQ 100 | **2.0%** | #2 | 1m, 5m, 15m, 1h |
| SPX500 | S&P 500 | 1.5% | #1 | 1m, 5m, 15m, 1h |
| GER40 | German DAX 40 | 1.8% | #3 | 1m, 5m, 15m, 1h |
| UK100 | FTSE 100 | 1.4% | #4 | 1m, 5m, 15m |
| FRA40 | French CAC 40 | 1.6% | #5 | 1m, 5m, 15m |

*Trading Hours: Market hours only (varies by exchange)*

## Usage in Code

### Python (Backend)

```python
from domain.config import (
    get_pair,
    is_valid_symbol,
    get_best_pairs_for_strategy,
    validate_trading_request,
    AssetType,
)

# Validate a symbol
if is_valid_symbol('BTC/USDT'):
    print("Valid symbol!")

# Get pair configuration
pair = get_pair('BTC/USDT')
print(f"Volatility: {pair.avg_daily_range * 100:.2f}%")
print(f"Recommended timeframes: {pair.recommended_timeframes}")

# Validate trading request
is_valid, error, pair_config = validate_trading_request(
    symbol='BTC/USDT',
    timeframe='1m',
    raise_error=False
)

# Get best pairs for a strategy
best_pairs = get_best_pairs_for_strategy(
    strategy_type='scalping',
    timeframe='1m',
    min_volatility=0.04,  # 4% minimum
    top_n=5
)

for pair in best_pairs:
    print(f"{pair.symbol}: {pair.avg_daily_range*100:.2f}%")
```

### Command Line

```bash
# List recommended pairs for scalping
cd backend
python scripts/backtest_breakout_scalping.py --list-pairs --timeframe 1m

# Run backtest with validation
python scripts/backtest_breakout_scalping.py --symbol DOGE/USDT --timeframe 1m --days 7
```

## Strategy Recommendations

### For Breakout Scalping (1-5 minute timeframes)

**Minimum volatility: 3%**

**Top Crypto Pairs:**
1. DOGE/USDT (8.0%) - Highest volatility, best for aggressive scalping
2. SOL/USDT (6.0%) - Very volatile, good liquidity
3. MATIC/USDT (6.0%) - High volatility, L2 solution
4. XRP/USDT (5.5%) - Consistent volatility
5. BNB/USDT (5.0%) - Exchange token, good liquidity

**Top Forex Pairs:**
1. GBP/JPY (1.5%) - Most volatile forex cross
2. GBP/USD (1.0%) - "Cable", good for scalping
3. USD/JPY (0.9%) - High liquidity, consistent moves

**Top Indices:**
1. NAS100 (2.0%) - Tech-heavy, most volatile
2. GER40 (1.8%) - DAX mentioned in video
3. FRA40 (1.6%) - CAC 40 mentioned in video

### For Day Trading (15-60 minute timeframes)

**Minimum volatility: 2%**

Best pairs: All crypto pairs + NAS100, GER40, US30

### For Swing Trading (1-4 hour timeframes)

**Minimum volatility: 1.5%**

Best pairs: BTC/USDT, ETH/USDT, major indices

## Adding New Pairs

To add a new trading pair, edit `backend/domain/config/trading_pairs.py`:

```python
TradingPair(
    symbol="NEW/USDT",
    name="New Asset / Tether",
    asset_type=AssetType.CRYPTO,
    base_currency="NEW",
    quote_currency="USDT",
    min_volatility=0.03,  # Minimum daily volatility
    avg_daily_range=0.05,  # Average daily range (5%)
    liquidity_rank=9,  # Higher = less liquid
    recommended_timeframes=["1m", "5m", "15m"],
    trading_hours="24/7",
    tick_size=0.01,
    min_position_size=1.0,
)
```

Then add it to the appropriate list (`CRYPTO_PAIRS`, `FOREX_PAIRS`, or `INDICES_PAIRS`).

## Validation Features

### Symbol Validation
Automatically validates symbols before backtests:

```
[OK] Symbol validated: Dogecoin / Tether
  Volatility: 8.00% daily range
  Liquidity Rank: #7
```

### Timeframe Validation
Warns if using non-recommended timeframes:

```
[WARNING] Timeframe '4h' is not recommended for BTC/USDT.
Recommended: 1m, 5m, 15m, 1h
```

### Strategy Recommendations
Shows best pairs for your strategy:

```
[INFO] Recommended pairs for scalping (1m):
   1. ETH/USDT        | 4.50% volatility
   2. BNB/USDT        | 5.00% volatility
   3. SOL/USDT        | 6.00% volatility
```

## Best Practices

1. **Match volatility to strategy**
   - Scalping: 3%+ volatility
   - Day trading: 2%+ volatility
   - Swing trading: 1.5%+ volatility

2. **Consider trading hours**
   - Crypto: Trade 24/7
   - Forex: Best during session overlaps (London/NY)
   - Indices: Only during market hours

3. **Start with high liquidity**
   - Rank #1-3 pairs have the best execution
   - Lower ranks may have slippage issues

4. **Use recommended timeframes**
   - Configured based on typical trading patterns
   - Other timeframes may work but haven't been tested

5. **Test thoroughly**
   - Run backtests on multiple pairs
   - Minimum 30 days, 100+ trades for statistical significance
   - Compare performance across pairs

## Related Files

- `backend/domain/config/trading_pairs.py` - Pair definitions
- `backend/domain/config/validation.py` - Validation utilities
- `backend/domain/config/__init__.py` - Public API
- `backend/scripts/backtest_breakout_scalping.py` - Example usage
- `backend/domain/strategies/implementations/breakout_scalping_strategy.py` - Strategy using pairs

## Future Enhancements

- [ ] Add real-time volatility calculation
- [ ] Integrate with exchange APIs for tick sizes
- [ ] Add more exotic pairs (commodities, etc.)
- [ ] Market hours awareness for auto-trading
- [ ] Volatility-based position sizing
- [ ] Pair correlation analysis
