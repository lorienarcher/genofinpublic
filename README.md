# GenOfin Public (Valkyrie Infrastructure)

Welcome to the public repository for GenOfin's algorithmic trading infrastructure, code-named **Valkyrie**. 

This repository serves as a demonstrative portfolio of the architectural foundation behind a multi-exchange quantitative copy-trading operation. It showcases institutional-grade network programming, rigorous statistical backtesting, and ultra-low latency execution modules.

> **⚠️ Note on Proprietary Alpha:** To protect intellectual property, the scripts provided in this public repository are **sanitized versions**. Specific quantitative alpha—including proprietary indicator math (e.g., custom ATR/RSI combinations), exact Walk-Forward Optimization parameter grids, and dynamic equity-curve recovery matrices—has been abstracted or replaced with generic placeholders.

---

## 📈 Performance Context
The underlying proprietary systems running on this infrastructure have achieved significant market outperformance, powering a **Binance Champion Tier** Lead Trading portfolio. 
* **Recent Milestone:** 96% Copier ROI in Q4 2024.
* **Global Ranking:** Top 5 highest-performing Lead Trader on Binance Futures at peak.

---

## 🏗️ Repository Architecture

The repository is structured into distinct, modular components, handling everything from data ingestion to live, multi-threaded execution.

### `📁 trader/` (Execution Engine)
The core live-trading environment.
* `01_valkyrie_trader.py`: A multi-threaded execution engine that aggregates WebSocket OHLCV streams and routes execution logic across concurrent macro-trend, mean-reversion, and high-volatility strategies.
* Includes separated `config.py` and `config_test.py` environments for seamless transition between paper and live trading.

### `📁 genofinlib/` (Core Library)
Bespoke, low-latency execution and analysis modules explicitly built to bypass heavy, generalized libraries like CCXT.
* `order_manager.py`: Constructs and cryptographically signs payload requests (HMAC SHA-256) natively for Binance Futures.
* `ws_manager.py` & `helpers.py`: Maintains resilient, self-healing WebSocket streams for real-time order lifecycle tracking.
* `slack_bot.py`: Daemon-threaded, asynchronous monitoring alerts to ensure the main execution loop is never blocked by network latency.
* `indicators.py`: Highly optimized Python DataFrame translations of complex technical indicators.

### `📁 backtesters/`
High-fidelity historical simulation models designed to test strategy survivability.
* Integrates dynamic position sizing based on real-time equity drawdown limits.
* Demonstrates macro-awareness by structurally adapting Take-Profit and Stop-Loss boundaries based on fundamental market events (e.g., Bitcoin Halving cycles).

### `📁 optimizers/`
Scripts dedicated to continuous strategy refinement, avoiding curve-fitting through rigorous methodology.
* Implements rolling Walk-Forward Optimization (WFO) across localized, out-of-sample data slices.
* Target optimization metrics prioritize statistical **Expectancy [%]** over raw returns to ensure long-term capital preservation.

### `📁 data/`
Automated ETL (Extract, Transform, Load) pipelines.
* Manages paginated API requests to maintain a gapless, high-resolution local OHLCV database for quantitative research.

---

## 🚀 Key Technical Features

1. **CCXT-Free Execution Segment:** For live order transmission, the infrastructure utilizes direct WebSocket streams and HMAC SHA-256 REST signing for maximum reliability and minimum latency.
2. **Multi-Strategy Concurrency:** Valkyrie actively monitors and trades across varying timeframes and logic triggers simultaneously without thread-locking.
3. **Advanced Risk Laddering:** Features complex stop-loss and scaling matrices, dynamically increasing or decreasing exposure based on the active drawdown state of the account equity.

---

## ⚙️ Setup & Installation

1. Clone the repository:

        git clone https://github.com/genofinpublic/genofinpublic.git
        cd genofinpublic

2. Install dependencies:

        pip install -r requirements.txt

3. Configure your environments by populating the API keys in `trader/config.py` and `trader/config_test.py`.

---

## 👤 About the Author
**Founder & Portfolio Manager, GenOfin**
Specialist in quantitative technical analysis, macro-driven systematic design, and cryptocurrency derivatives trading. 

* **Primary Stack:** Python, Pine Script, Pandas, NumPy, Websockets
* **Execution Venues:** Binance, OKX, BitMEX

---

## ⚠️ Legal & Financial Disclaimer
The code and strategies provided in this repository are **sanitized, demonstrative versions** intended strictly for educational and portfolio purposes. 

* **Not Financial Advice:** Nothing in this repository constitutes financial, investment, or trading advice. 
* **No Proprietary Alpha:** The active GenOfin proprietary trading algorithms, exact parameters, and mathematical models have been completely removed. 
* **Use at Your Own Risk:** Trading cryptocurrencies and derivatives carries a significant risk of loss. The author and GenOfin assume no responsibility or liability for any financial losses incurred by attempting to deploy, test, or modify this code in a live trading environment.
