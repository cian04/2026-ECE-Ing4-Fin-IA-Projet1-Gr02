# Project Specifications  
## Genetic Algorithm for Algorithmic Trading (Full Autonomy)

---

## 1. Project Overview & Rules

**Goal**  
Build a robust, fully local Python application using **Genetic Algorithms (DEAP)** to optimize a quantitative trading strategy (**Backtrader**) on financial data (**Yahoo Finance**).

**Critical Requirement**  
The system **must implement Walk-Forward Analysis (WFA)** to validate robustness and prevent overfitting.

---

## 1.1 Development Rules for the AI

1. **Modularity**  
   Each component (Data, Strategy, GA, Backtest) must be implemented in a separate file.

2. **Windows Compatibility**  
   All multiprocessing entry points must be protected with:
   ```python
   if __name__ == "__main__":
Error Handling
Any failed backtest (insufficient data, division by zero, etc.) must return:

text
Copier le code
(-infinity, +infinity)
so the GA loop never crashes.

Clean Code

Mandatory type hints (List[float], Dict, etc.)

Full docstrings for all public functions and classes

2. Technical Stack & Versions (Strict)
OS: Windows 10 / 11

Python: 3.10 or 3.11 (avoid 3.12+)

Backtesting: backtrader

Genetic Algorithm: DEAP

Market Data: yfinance

Numerical: numpy, pandas

Plotting: matplotlib

Note: Backtrader requires legacy plotting syntax

3. Architecture & File Structure
text
Copier le code
algo_trading_project/
├── data/                       # Cached CSV market data
│   └── .keep
├── logs/                       # Execution and debug logs
├── src/
│   ├── __init__.py
│   ├── config.py               # Central configuration
│   ├── data_manager.py         # Download, sanitize, slice data
│   ├── strategy_genes.py       # Backtrader strategy definition
│   ├── backtest_runner.py      # Cerebro encapsulation
│   ├── ga_core.py              # DEAP setup and evaluation
│   └── walk_forward.py         # Walk-forward orchestration
├── main.py                     # CLI entry point
├── requirements.txt            # Frozen dependencies
└── specifications.md           # This file
4. Detailed Component Implementation
4.1 Configuration (src/config.py)
Centralized configuration class to avoid hardcoding.

Asset: "BTC-USD" (crypto) or "SPY" (stock)

Interval: "1d"

Train/Test Split: 70% / 30%

Initial Cash: 10,000 USD

Commission:

Crypto: 0.001

Stocks: 0.0001

GA Hyperparameters

Population: 50

Generations: 10

Crossover Probability (CXPB): 0.7

Mutation Probability (MUTPB): 0.2

4.2 Data Manager (src/data_manager.py)
Responsibilities

Download OHLCV data using yfinance

Cache data in data/{ticker}.csv

Reload cached data if available

Sanitization

Drop NaNs

Ensure index is DatetimeIndex

API

python
Copier le code
get_data_slice(start_date, end_date)
Returns a clean dataframe for backtesting.

4.3 Strategy Logic (src/strategy_genes.py)
The strategy must accept dynamic parameters from the GA.

Chromosome Definition (7 Genes)
Gene	Meaning	Type	Range
SMA_F	Fast SMA	int	[5, 50]
SMA_S	Slow SMA	int	[50, 200]
RSI_P	RSI Period	int	[5, 30]
RSI_UP	RSI Overbought	int	[60, 90]
RSI_LO	RSI Oversold	int	[10, 40]
SL	Stop Loss (%)	float	[0.01, 0.10]
TP	Take Profit (%)	float	[0.02, 0.20]

Constraints
If SMA_F >= SMA_S: no trade allowed

Entry (Long)
Close > SMA_F

SMA_F > SMA_S

RSI < RSI_LO

Exit
RSI > RSI_UP OR

Close < SMA_S

Order Management
Use BuyBracket

Stop Loss: price * (1 - SL)

Take Profit: price * (1 + TP)

4.4 Backtest Runner (src/backtest_runner.py)
Function

python
Copier le code
run_backtest(params, data_feed) -> (profit_pct, max_drawdown_pct)
Setup

cerebro.addstrategy(strategy, **params)

Initial cash: 10_000

Commission: configurable

Analyzers

TradeAnalyzer

DrawDown

Safety Rules

No trades → return (-100, 100)

Any runtime error → return (-inf, +inf)

4.5 GA Core (src/ga_core.py)
Optimization

Multi-objective:

Maximize Profit

Minimize Drawdown

Fitness Weights

python
Copier le code
(1.0, -1.0)
DEAP Configuration

Individual: list

Selection: selNSGA2

Crossover: cxTwoPoint

Mutation:

Int genes: ±1 to ±5

Float genes: ±0.01

Evaluation

Decode chromosome → parameter dict

Call run_backtest

Return (profit, drawdown)

Evaluation function must be top-level (Windows multiprocessing requirement).

4.6 Walk-Forward Analysis (src/walk_forward.py)
Dataset

Example: 4 years total

Window Parameters

Train window: 12 months

Test window: 3 months

Step size: 3 months

Algorithm

Run GA on [T, T + 12 months]

Select best individual from Pareto front

Test on [T + 12, T + 15 months]

Record out-of-sample PnL

Slide window by 3 months

Aggregate OOS results

Report

Total OOS performance

Comparison vs Buy & Hold

5. Implementation Phases
Phase 1 – Infrastructure
Create requirements.txt

Implement config.py

Implement data_manager.py

Implement strategy_genes.py

Manual backtest with fixed parameters

Phase 2 – Core Engine
Implement backtest_runner.py

Implement ga_core.py

Run GA with 1 generation for validation

Phase 3 – Validation
Implement walk_forward.py

Implement main.py

Full WFA execution

6. Known Issues & Fixes
Pickling Error (Windows)
DEAP evaluation functions must not be class methods

Empty Backtests
Very strict parameters may produce zero trades

Must handle:

ZeroDivisionError

Empty analyzers

No trades gracefully

markdown
Copier le code
