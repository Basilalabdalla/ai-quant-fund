import logging
from datetime import datetime
import chromadb
from chromadb.config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MemoryXAIService")


class MemoryXAIService:
    def __init__(self, db_path: str = "./chroma_db"):
        """تهيئة قاعدة البيانات المتجهة ChromaDB"""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="trading_decisions",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("🧠 ChromaDB Memory & XAI Engine Initialized.")

    def store_decision(self, decision_data: dict, market_regime: str):
        """تخزين قرار التداول وتضمين الأسباب كمواجهات متجهة"""
        symbol = decision_data.get("symbol", "UNKNOWN")
        action = decision_data.get("action", "HOLD")
        confidence = decision_data.get("confidence", 0.0)
        reasoning_text = " ".join(decision_data.get("reasoning", []))
        
        doc_id = f"dec_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        document = f"Symbol: {symbol} | Action: {action} | Regime: {market_regime} | Reasoning: {reasoning_text}"
        
        metadata = {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "market_regime": market_regime,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logger.info(f"💾 Decision logged to Vector Memory -> ID: {doc_id}")

    def explain_decision(self, symbol: str, query: str, n_results: int = 2) -> list:
        """استرجاع وتفسير أسباب القرارات بناءً على استعلام باللغة الطبيعية"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"symbol": symbol}
        )
        
        explanations = []
        if results and results.get("documents"):
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                explanations.append({
                    "explanation": doc,
                    "metadata": meta
                })
        return explanations


def main():
    logger.info("🚀 Starting Memory & XAI Service Test...")
    xai = MemoryXAIService()

    # 1. محاكاة تخزين القرار الأخير القادم من CrewAI
    sample_decision = {
        "symbol": "BTC/USDT",
        "action": "HOLD",
        "confidence": 0.85,
        "recommended_position_size_pct": 0.0,
        "risk_score": 8,
        "reasoning": [
            "Market Regime is HIGH_VOLATILITY.",
            "High risk of whipsaws and liquidation cascades.",
            "Capital preservation rule triggered: Stand aside until regime stabilizes."
        ]
    }
    
    xai.store_decision(decision_data=sample_decision, market_regime="HIGH_VOLATILITY")

    # 2. استجواب النظام عن سبب الامتناع عن التداول (XAI Explanation Query)
    query = "لماذا لم يقم البوت بشراء البيتكوين؟"
    logger.info(f"🔍 Querying XAI Engine: '{query}'")
    
    explanations = xai.explain_decision(symbol="BTC/USDT", query=query)
    
    for idx, exp in enumerate(explanations, 1):
        logger.info(f"\n--- Explanation #{idx} ---")
        logger.info(f"Text: {exp['explanation']}")
        logger.info(f"Metadata: {exp['metadata']}")


if __name__ == "__main__":
    main()