---
description: Run backtests on trading strategies with validation and performance analysis
---

You are helping run a backtest for a trading strategy. Follow these steps:

1. **Identify the strategy**: Ask the user which strategy to backtest (or use the one they specified)

2. **Gather parameters**:
   - Time period (start/end dates)
   - Asset(s) to test on
   - Initial capital
   - Position sizing rules
   - Any strategy-specific parameters

3. **Execute the backtest**:
   - Load historical data for the specified period and assets
   - Run the strategy logic through the historical data
   - Track all trades, positions, and portfolio value

4. **Calculate metrics**:
   - Total return (%)
   - Sharpe ratio
   - Maximum drawdown
   - Win rate
   - Average profit/loss per trade
   - Number of trades executed
   - Best and worst trades

5. **Analyze results**:
   - Identify periods of high performance and drawdowns
   - Check for overfitting indicators
   - Validate that the strategy logic executed correctly
   - Flag any numerical issues, edge cases, or bugs discovered

6. **Generate report**: Present findings clearly with actionable insights

**Important checks**:
- Verify no look-ahead bias in the strategy
- Ensure proper handling of missing data
- Check for survivorship bias if testing multiple assets
- Validate transaction costs are included
- Confirm slippage assumptions are realistic
