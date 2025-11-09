---
description: Scaffold a new technical indicator with proper structure, tests, and documentation
---

You are helping add a new technical indicator to the trading bot. Follow these steps:

1. **Understand the indicator**:
   - Ask what indicator to implement (or use what the user specified)
   - Clarify the calculation formula
   - Identify required parameters (periods, thresholds, etc.)
   - Determine input data requirements (OHLCV)

2. **Check existing patterns**:
   - Review existing indicator implementations in the codebase
   - Follow the established structure and naming conventions
   - Ensure consistency with existing indicators

3. **Implement the indicator**:
   - Create the indicator class/function following project structure
   - Implement the calculation logic
   - Add input validation (handle NaN, missing data, edge cases)
   - Include configurable parameters with sensible defaults
   - Add proper type hints/annotations
   - Ensure the indicator can handle both single values and arrays/dataframes

4. **Add documentation**:
   - Docstring explaining what the indicator measures
   - Parameter descriptions
   - Return value explanation
   - Usage example
   - Reference to the indicator's formula or source

5. **Create tests**:
   - Unit tests with known values (verify calculation correctness)
   - Edge case tests (empty data, single value, NaN handling)
   - Performance test for large datasets if relevant

6. **Integration**:
   - Add the indicator to any registry/factory if applicable
   - Update configuration files if needed
   - Verify it integrates with the data pipeline

**Quality checks**:
- Numerical stability (avoid division by zero, handle floating point precision)
- Performance (vectorized operations where possible)
- Memory efficiency for large datasets
- Proper handling of insufficient data (e.g., need 14 periods for RSI but only 5 available)
