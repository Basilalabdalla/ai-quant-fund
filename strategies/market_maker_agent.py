import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MarketMakerAgent")


class OrderBookDepth(BaseModel):
    bids: List[List[float]] = Field(description="[[price, volume], ...]")
    asks: List[List[float]] = Field(description="[[price, volume], ...]")


class MarketMakerSignal(BaseModel):
    agent_name: str = "MarketMakerAgent"
    action: str = Field(description="BUY, SELL, or HOLD")
    confidence: float
    obi_score: float
    target_bid: float
    target_ask: float
    reasoning: str


class MarketMakerAgent:
    """وكيل كمّي لحساب Order Book Imbalance وتوليد تسعير ثنائي الاتجاه"""

    def __init__(self, depth_levels: int = 5, obi_threshold: float = 0.3):
        self.depth_levels = depth_levels
        self.obi_threshold = obi_threshold

    def calculate_obi(self, depth: OrderBookDepth) -> float:
        """حساب معادل اختلال دفتر الأوامر OBI"""
        top_bids_vol = sum(bid[1] for bid in depth.bids[:self.depth_levels])
        top_asks_vol = sum(ask[1] for ask in depth.asks[:self.depth_levels])
        
        total_vol = top_bids_vol + top_asks_vol
        if total_vol == 0:
            return 0.0
            
        return (top_bids_vol - top_asks_vol) / total_vol

    def evaluate(self, symbol: str, depth: OrderBookDepth, spread_pct: float = 0.002) -> MarketMakerSignal:
        obi = self.calculate_obi(depth)
        best_bid = depth.bids[0][0]
        best_ask = depth.asks[0][0]
        mid_price = (best_bid + best_ask) / 2.0

        # احتساب الهامش الديناميكي للصانع (Quote Skewing)
        target_bid = mid_price * (1 - spread_pct / 2)
        target_ask = mid_price * (1 + spread_pct / 2)

        if obi > self.obi_threshold:
            action = "BUY"
            confidence = min(0.5 + abs(obi) / 2, 0.95)
            reason = f"Strong Bid Imbalance (OBI={obi:.2f}). Heavy buying liquidity."
        elif obi < -self.obi_threshold:
            action = "SELL"
            confidence = min(0.5 + abs(obi) / 2, 0.95)
            reason = f"Strong Ask Imbalance (OBI={obi:.2f}). Heavy selling liquidity."
        else:
            action = "HOLD"
            confidence = 0.50
            reason = f"Balanced Order Book (OBI={obi:.2f}). Neutral market making zone."

        return MarketMakerSignal(
            action=action,
            confidence=confidence,
            obi_score=round(obi, 4),
            target_bid=round(target_bid, 2),
            target_ask=round(target_ask, 2),
            reasoning=reason
        )


if __name__ == "__main__":
    # نموذج محاكاة لعمق دفتر أوامر ذو انحياز شرائي قاطعة (Bullish Order Book)
    sample_depth = OrderBookDepth(
        bids=[[62000.0, 12.5], [61990.0, 18.0], [61980.0, 25.0]],
        asks=[[62010.0, 2.1],  [62020.0, 3.5],  [62030.0, 4.0]]
    )

    agent = MarketMakerAgent()
    signal = agent.evaluate(symbol="BTC/USDT", depth=sample_depth)
    
    logger.info(f"📊 Market Maker Agent Evaluation:\n{signal.model_dump_json(indent=2)}")