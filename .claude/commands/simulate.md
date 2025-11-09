---
description: Run paper trading simulation to test strategies in real-time without risking capital
---

You are helping set up and run a paper trading simulation. Follow these steps:

1. **Configure simulation parameters**:
   - Ask which strategy to simulate (or use what the user specified)
   - Determine simulation mode:
     - Live market data with simulated orders
     - Historical replay at accelerated speed
     - Hybrid (historical with realistic delays)
   - Set initial capital and position sizing rules
   - Define assets/markets to trade

2. **Set up the environment**:
   - Initialize virtual portfolio with starting capital
   - Configure data feeds (live or historical)
   - Set up order execution simulation (include slippage model)
   - Enable logging for all decisions and trades

3. **Implement simulation logic**:
   - Process market data through the strategy
   - Simulate order placement and execution
   - Track portfolio state (positions, cash, equity)
   - Apply realistic constraints:
     - Transaction costs/fees
     - Slippage estimates
     - Order execution delays
     - Market hours (if applicable)
     - Position limits

4. **Monitor and track**:
   - Log all trading signals and decisions
   - Track performance metrics in real-time:
     - Current equity
     - Open positions
     - P&L (realized and unrealized)
     - Win/loss ratio
     - Recent trades
   - Flag unusual behavior or errors

5. **Generate reports**:
   - Summary of simulation results
   - Performance metrics compared to benchmark
   - Trade log with entry/exit points
   - Identified issues or edge cases
   - Recommendations for strategy refinement

**Safety checks**:
- Verify orders are simulated, not real (double-check API configuration)
- Ensure no real money is at risk
- Validate that execution logic matches what would happen in production
- Test error handling (connection failures, invalid data, API errors)
- Confirm position sizing doesn't exceed limits

**Simulation quality**:
- Realistic order fills (don't assume instant execution at exact price)
- Include bid-ask spread in execution
- Model partial fills for large orders if relevant
- Simulate realistic latency for data and orders
