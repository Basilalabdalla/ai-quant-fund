# services/skeleton_runner.py
import asyncio
import logging
from datetime import datetime
from pydantic import ValidationError

from shared_lib.schemas import MarketData, TradeSignal, SignalAction, ExecutionResult
from shared_lib.interfaces import (
    AbstractDataIngestion,
    AbstractAIParliament,
    AbstractRiskEngine,
    AbstractExecutionEngine,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WalkingSkeleton")

# --- Dummy Implementations for Phase 0 ---

class DummyDataIngestion(AbstractDataIngestion):
    async def fetch_latest_tick(self, symbol: str) -> MarketData:
        # Simulating low-latency WebSocket feed
        return MarketData(symbol=symbol, price=65000.50, volume=1.2)

class DummyAIParliament(AbstractAIParliament):
    async def evaluate_market(self, data: MarketData) -> TradeSignal:
        # Dummy Agent outputting structured Pydantic payload
        return TradeSignal(
            symbol=data.symbol,
            action=SignalAction.BUY,
            confidence=85.0,
            suggested_amount=0.01,
            reasoning="Skeleton test: Dummy consensus reached"
        )

class DummyRiskEngine(AbstractRiskEngine):
    def validate_signal(self, signal: TradeSignal, current_price: float) -> bool:
        # Hardcoded deterministic firewall checks
        if signal.suggested_amount * current_price > 5000: # Max $5000 allocation per trade
            logger.warning("Risk Firewall: Trade size exceeds maximum safety limit.")
            return False
        return True

class DummyExecutionEngine(AbstractExecutionEngine):
    async def execute_order(self, signal: TradeSignal) -> ExecutionResult:
        return ExecutionResult(
            order_id="ORD-SKELETON-999",
            symbol=signal.symbol,
            action=signal.action,
            executed_price=65000.50,
            amount=signal.suggested_amount,
            status="FILLED"
        )

# --- Zero-Crash Pipeline Orchestrator ---

async def run_pipeline():
    logger.info("⚡ Starting Walking Skeleton Pipeline Test...")
    
    ingestion = DummyDataIngestion()
    ai_parliament = DummyAIParliament()
    risk_engine = DummyRiskEngine()
    execution = DummyExecutionEngine()

    try:
        # Step 1: Data Ingestion
        tick = await ingestion.fetch_latest_tick("BTC/USDT")
        logger.info(f"1. Data Ingested: {tick.symbol} @ ${tick.price}")

        # Step 2: AI Parliament Analysis
        signal = await ai_parliament.evaluate_market(tick)
        logger.info(f"2. Signal Generated: {signal.action} (Confidence: {signal.confidence}%)")

        # Step 3: Risk Firewall Verification
        is_safe = risk_engine.validate_signal(signal, tick.price)
        if not is_safe:
            logger.warning("3. Signal rejected by Risk Firewall. Execution halted safely.")
            return

        logger.info("3. Signal APPROVED by Risk Firewall.")

        # Step 4: Execution Engine
        result = await execution.execute_order(signal)
        logger.info(f"4. Execution Complete: Order {result.order_id} {result.status}")

    except ValidationError as ve:
        # Defensive check: Catch malformed AI or API output
        logger.error(f"❌ Validation Error Caught (Dropped safely without crash): {ve}")
    except Exception as e:
        # Global catch-all to prevent service termination
        logger.critical(f"❌ Unexpected Error Caught in Event Loop: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_pipeline())