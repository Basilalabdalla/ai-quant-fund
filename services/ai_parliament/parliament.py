from typing import Dict, Any  # <-- تم إضافة الاستيراد لحل تحذيرات Dict و Any
from strategies.market_maker_agent import MarketMakerAgent, OrderBookDepth


class AIParliamentConsensus:
    def __init__(self):
        self.mm_agent = MarketMakerAgent()

    def get_parliament_decision(self, symbol: str, depth_data: OrderBookDepth, macro_trend: str) -> Dict[str, Any]:
        # 1. إشارة صانع السوق (Microstructure)
        mm_signal = self.mm_agent.evaluate(symbol, depth_data)
        
        # 2. أوزان تصويت البرلمان (Macro vs Microstructure)
        vote_weights = {
            "BUY": 0.0,
            "SELL": 0.0,
            "HOLD": 0.0
        }

        # إضافة وزن وكيل OBI
        vote_weights[mm_signal.action] += mm_signal.confidence * 0.40  # 40% Weight for Microstructure
        
        # إضافة وزن الاتجاه العام (Macro Trend)
        macro_action = "BUY" if macro_trend == "BULL_TREND" else "SELL"
        vote_weights[macro_action] += 0.60                            # 60% Weight for Macro Trend

        final_action = max(vote_weights, key=vote_weights.get)
        
        return {
            "consensus_action": final_action,
            "mm_agent_signal": mm_signal.model_dump(),
            "confidence_score": round(vote_weights[final_action], 2)
        }