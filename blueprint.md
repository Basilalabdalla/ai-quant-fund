# SYSTEM BLUEPRINT: QUANTITATIVE AI-DRIVEN HEDGE FUND ENGINE (SAAS-READY)

## 1. System Overview & Architecture
- **Architecture Style:** Event-driven, Microservices Architecture.
- **Isolation:** Fully containerized via Docker and Docker Compose.
- **Database:** PostgreSQL with TimescaleDB extension (time-series data), Redis (pub/sub messaging & caching), ChromaDB (vector storage for XAI).
- **Multi-Tenancy:** Schema-per-tenant model to support future SaaS scale and strict data isolation.

## 2. Technical Stack
- **Data Ingestion:** `CryptoFeed` (WebSockets for low-latency streaming) + Custom On-Chain/Orderbook Fetchers.
- **Market Regime Engine:** `hmmlearn` (Hidden Markov Models for market state identification).
- **AI Parliament (Agentic Reasoning):** `CrewAI` (Multi-agent orchestrator: Technical, Fundamental, and Sentiment analysis).
- **Explainable AI (XAI) & Memory:** `ChromaDB` + `LlamaIndex` (RAG engine for auditing AI decisions).
- **Execution & Integration:** `CCXT` (Unified Exchange API interface for Binance, Bybit, Coinbase).
- **Backtesting & Simulation:** `VectorBT` (High-performance NumPy/Numba backtester for nocturnal auto-tuning).

## 3. Data Pipeline & Storage
- WebSockets capture raw tick and orderbook data into Redis Pub/Sub channels.
- Aggregated OHLCV candle data is persisted into TimescaleDB hyper-tables.
- Historical trade signals, execution logs, and risk metrics are fully indexed for auditing and UI reporting.

## 4. AI Parliament & Risk Firewall
- **Parliament Workflow:** Sub-agents evaluate independent vectors -> Consensus vote generated -> Decision passed to Deterministic Risk Engine.
- **Deterministic Risk Firewall:** Hardcoded Python safety net enforcing absolute rules (Take Profit, Stop Loss, Maximum Portfolio Drawdown, Max Trade Allocation). The AI CANNOT override hard risk parameters.

## 5. Backtesting & Auto-Optimization
- VectorBT executes nightly backtesting across multi-year parameter grids.
- Performance metrics (Sharpe Ratio, Max Drawdown, Calmar Ratio) dynamically update confidence weights within the AI Parliament.

## 6. Future-Proofing & Modularity (The Adapter/Plugin Pattern)
CRITICAL ARCHITECTURE RULE: The core system MUST NEVER tightly couple to any external library. The system must support a "Plug-and-Play" architecture to easily swap or upgrade libraries in the future.

- **Use the Adapter Pattern:** All third-party libraries (`CrewAI`, `hmmlearn`, `CCXT`, `VectorBT`) MUST be wrapped in custom Adapter classes.
- **Dependency Inversion:** Define Python `Protocols` or `Abstract Base Classes (ABCs)` in `shared_lib/interfaces.py`. The core business logic relies ONLY on these interfaces.
- **Factory Pattern & Configuration:** Use a Factory class to instantiate adapters dynamically based on environment variables (e.g., `MARKET_REGIME_PROVIDER=hmmlearn`).

## 7. Zero-Crash Tolerance & Defensive Engineering
CRITICAL INSTRUCTION: This is a financial system. A crash or unhandled exception is catastrophic. You must employ extreme defensive programming.

- **The Walking Skeleton Approach:** Before implementing complex AI logic, build a fully connected, dummy end-to-end pipeline (Data Ingestion -> Dummy Agent -> Risk Engine -> Simulated Execution) to prove zero-crash reliability.
- **Circuit Breakers & Retries:** Use `tenacity` for all external I/O (Exchange APIs, LLMs, WebSockets). Never let a timeout or HTTP 500 crash a service. Implement exponential backoff.
- **Strict Bouncers (Pydantic):** EVERY payload moving between services (especially LLM outputs) MUST be validated by strict Pydantic models. Catch `ValidationError`, drop malformed signals, log tracebacks, and continue operation without crashing.
- **Graceful Degradation:** If a non-critical sub-agent (e.g., Sentiment Analyzer) fails, the main AI Parliament MUST NOT crash. Increase uncertainty parameters, reduce risk exposure automatically, and maintain operation.
- **Global Exception Handlers:** Every microservice must feature top-level try/except blocks to catch unhandled exceptions, log detailed tracebacks, trigger monitoring alerts, and keep the main event loop running.

## 8. Meta-Engineering & AI Context Management (The AI Dev Team)
CRITICAL INSTRUCTION FOR ALL AI AGENTS WORKING ON THIS REPO:
This project is maintained by a multi-agent AI development team. You must maintain perfect context across sessions and agent handoffs.

- **Self-Documenting Codebase:** Every major architectural change or new service MUST include an Architecture Decision Record (ADR) in `docs/ADRs/` explaining the decision and impact before writing code.
- **Role Separation:**
  - **Architect Agent:** Focuses on structural integrity, interface design, and updating `blueprint.md`.
  - **Developer Agent:** Writes production-grade modular code following defined ABCs/Interfaces and ADRs.
  - **QA/Testing Agent:** Writes aggressive `pytest` suites focusing on edge cases, data boundary limits, and Risk Engine constraints.
- **Context Reloading:** Before executing any changes, the active AI agent MUST read `blueprint.md` and active ADRs in `docs/ADRs/` to reload total system state.
- **Strict Testing Rule:** No feature or module is marked complete until the QA Agent creates passing test suites for it.