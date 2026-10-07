# AI Agent Integration & Architecture Guide

Welcome AI Agent! This repository implements an end-to-end multi-tenant quantitative hedge fund platform with an AI Parliament architecture.

## System Services Architecture

1. **SaaS Gateway (`services/saas/auth_billing.py`)**:
   - Port: `8080`
   - FastAPI-based API for tenant registration, subscription tier control, and Stripe webhooks.
   - Endpoints: `/tenants/register`, `/tenants/validate-order`, `/webhooks/stripe`, `/health`

2. **AI Parliament (`services/agents/`)**:
   - Multi-agent consensus mechanism (Market Maker Agent, Macro Agent, Risk Agent).
   - Generates OBI (Order Book Imbalance) metrics and confidence score.
   - Stores reasoning logs directly in ChromaDB for Explainable AI (XAI).

3. **Paper Trader (`services/execution/paper_trader.py`)**:
   - Continuous background worker simulating order matching and portfolio updates.

4. **UI Dashboard (`services/ui/app.py`)**:
   - Port: `8501`
   - Streamlit dashboard for real-time AI decision visualization and XAI memory queries.

5. **Infrastructural Databases**:
   - **Postgres** (Port 5432): Relational storage for tenant data and system state.
   - **Redis** (Port 6379): Caching and high-speed message broker.
   - **ChromaDB** (Port 8000): Vector store for Explainable AI (XAI) query retrieval.

## Standard Execution Workflow
`UI Dashboard / Client` ➔ `SaaS Gateway (/tenants/validate-order)` ➔ `AI Parliament Decision` ➔ `Paper Trader Execution` ➔ `ChromaDB Memory Logging`

## Commands for Agents
- Build and Run All Services: `docker compose up --build -d`
- Check Services Status: `docker compose ps`
- Run API Gateway Health Check: `curl http://localhost:8080/health`