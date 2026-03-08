# Algorithmic Market Sentiment Analyser - Interview Questions

## Technical Indicators

**Q1: What is a Simple Moving Average (SMA) and how does it help identify trends?**
A: SMA calculates the average price over a specified time period, smoothing out short-term price fluctuations to reveal longer-term trends. When price stays above the SMA, it suggests bullish momentum; when below, bearish momentum. The longer the window, the smoother the trend but with more lag in signals.

**Q2: How does Exponential Moving Average (EMA) differ from SMA and why is it more responsive?**
A: EMA gives more weight to recent prices using a smoothing factor, making it more responsive to new information while still providing smoothing. Unlike SMA which gives equal weight to all periods, EMA's weighting decreases exponentially for older data, allowing faster reaction to price changes.

**Q3: Explain RSI and what overbought/oversold levels of 70/30 signify.**
A: RSI is a momentum oscillator measuring the speed and change of price movements, ranging from 0-100. Readings above 70 indicate overbought conditions where the asset may be due for a price correction, while below 30 suggests oversold conditions where the asset may be undervalued and due for a bounce.

**Q4: How does MACD generate trading signals through its components?**
A: MACD uses two exponential moving averages (12 and 26 periods) with the difference forming the MACD line, which is then smoothed with a 9-period EMA to create the signal line. Bullish signals occur when MACD crosses above the signal line, bearish when crossing below, with the histogram showing momentum strength.

**Q5: What do Bollinger Bands tell us about market volatility and price levels?**
A: Bollinger Bands create a price channel around a 20-period SMA using two standard deviations. The bands widen during high volatility and narrow during low volatility, helping identify potential breakouts when price moves outside the bands, and mean reversion opportunities when price touches the bands.

**Q6: How is VWAP different from regular moving averages and why is it important?**
A: VWAP calculates the true average price weighted by trading volume, giving more significance to high-volume price levels. Unlike regular moving averages that only consider price, VWAP reflects where the majority of trading occurred, making it crucial for institutional traders and as a support/resistance level.

## Backtesting & Performance

**Q7: What is look-ahead bias and how did you prevent it in your backtesting?**
A: Look-ahead bias occurs when using information not available at trading time, like using closing prices for same-day trades. I prevented this by generating signals at market close (T) and executing trades at next day's open (T+1), ensuring decisions use only historical information available at that moment.

**Q8: Explain Sharpe ratio and what values indicate good risk-adjusted returns.**
A: Sharpe ratio measures risk-adjusted returns by dividing excess returns over risk-free rate by volatility. Values above 1 indicate good risk-adjusted performance, above 2 is very good, and above 3 is excellent. It shows how much return you're getting per unit of risk taken.

**Q9: Why are your backtest returns likely overfitted and what does overfitting mean?**
A: Overfitting occurs when strategies perform well historically due to data mining bias, parameter optimization, and survivorship bias. My high backtest returns are likely overfitted because I optimized parameters on historical data, tested multiple strategies, and used clean historical data without accounting for real-world frictions like slippage, market impact, or liquidity constraints.

**Q10: How does maximum drawdown relate to risk management in trading strategies?**
A: Maximum drawdown measures the largest peak-to-trough decline, showing the worst possible loss an investor could have experienced. It's crucial for risk management as it indicates strategy resilience during adverse periods and helps determine appropriate position sizing and risk tolerance.

**Q11: What role do transaction costs and stop-losses play in realistic backtesting?**
A: Transaction costs (10 bps each way) and stop-losses (5%) make backtesting more realistic by accounting for trading expenses and risk management. Without these, backtested returns would be artificially inflated since real trading involves costs and the need to limit losses on individual positions.

## Options Market Making Connection

**Q12: How does technical analysis relate to options market making strategies?**
A: Technical analysis helps market makers identify directional bias and volatility expectations, which are crucial for pricing options. Moving averages and momentum indicators can inform delta hedging decisions, while volatility indicators like Bollinger Bands help assess implied volatility levels for option pricing.

**Q13: Why is understanding Greeks important when using technical signals for options trading?**
A: Greeks measure option sensitivity to various factors; technical signals should be combined with Greeks analysis. For example, a bullish technical signal might be implemented differently depending on delta exposure, while volatility indicators help assess whether to buy or sell options based on vega exposure.

**Q14: How does your backtesting approach apply to options market making risk management?**
A: The risk management principles (position sizing, stop-losses, portfolio safeguards) directly apply to options market making where managing delta exposure, gamma risk, and volatility risk is crucial. The same systematic approach to limiting losses and preserving capital applies to options portfolios.

**Q15: What limitations of your technical analysis system are most important for options traders to understand?**
A: Options traders must understand that technical analysis only provides directional signals, not volatility or time decay insights which are critical for options. The overfitting concerns are especially relevant for options as complex instruments require more sophisticated modeling beyond simple price patterns.

## System Architecture & Implementation

**Q16: Why did you implement technical indicators from scratch instead of using existing libraries?**
A: Implementing from scratch demonstrates deep understanding of the mathematical formulas and trading logic, allows full control over parameter optimization, and ensures no black-box dependencies which is crucial for financial systems where transparency and debugging are essential.

**Q17: How does your caching system improve performance for repeated analyses?**
A: The caching system stores downloaded data by ticker and date range, avoiding repeated API calls which are rate-limited and slow. This significantly improves performance for backtesting multiple strategies on the same data and reduces external dependency risks.

**Q18: What would you add to make this system production-ready for live trading?**
A: For production, I'd add real-time data feeds, order execution integration, comprehensive risk monitoring, position tracking across multiple accounts, compliance reporting, stress testing, and robust error handling with circuit breakers to prevent catastrophic losses.

## Risk & Portfolio Management

**Q19: How would you incorporate correlation analysis when trading multiple assets?**
A: I'd calculate correlation matrices to understand how positions move together, adjusting position sizes to reduce portfolio concentration risk. High correlation would require smaller individual positions to maintain target portfolio volatility, while low correlation allows larger positions with better diversification benefits.

**Q20: What role does volatility forecasting play in improving your trading strategies?**
A: Volatility forecasting helps optimize position sizing (smaller positions in high volatility), adjust stop-loss levels, and identify regime changes. It's especially important for options pricing and risk management, where volatility directly impacts option values and hedging costs.
