# 🚀 AI Quant Fund & SaaS Gateway

An open-source, multi-tenant quantitative hedge fund ecosystem powered by an AI Parliament (XAI) decision system, real-time paper trading, and automated capital cap governance.

## 🛠 Tech Stack
- **Backend & APIs:** FastAPI, Python 3.10, Pydantic
- **AI & Memory:** ChromaDB (Vector DB), CrewAI Logic
- **Data & Caching:** PostgreSQL, Redis
- **Dashboard:** Streamlit
- **Containerization:** Docker & Docker Compose

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone [https://github.com/YOUR_USERNAME/ai-quant-fund.git](https://github.com/YOUR_USERNAME/ai-quant-fund.git)
cd ai-quant-fund

# 2. Build and launch all 6 services with Docker
docker compose up --build -d

# 3. Access Services
- UI Dashboard: http://localhost:8501
- SaaS API Gateway: http://localhost:8080
- API Docs (Swagger): http://localhost:8080/docs
- ChromaDB API: http://localhost:8000