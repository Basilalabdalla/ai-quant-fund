import os
import logging
from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from crewai import Agent, Task, Crew, Process

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AIParliament")

# --- 1. Pydantic Guardrails (Structured Output Schema) ---
class ActionEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class QuantitativeDecision(BaseModel):
    symbol: str = Field(description="رمز الأصل المالي (مثل BTC/USDT)")
    action: ActionEnum = Field(description="قرار التداول: BUY أو SELL أو HOLD")
    confidence: float = Field(ge=0.0, le=1.0, description="درجة الثقة بالقرار من 0.0 إلى 1.0")
    recommended_position_size_pct: float = Field(ge=0.0, le=100.0, description="حجم الصفقة الموصى به كنسبة مئوية من المحفظة")
    risk_score: int = Field(ge=1, le=10, description="تقييم المخاطرة من 1 (منخفض) إلى 10 (مرتفع جداً)")
    reasoning: List[str] = Field(description="قائمة بالأسباب الرئيسية وراء القرار")


# --- 2. CrewAI Engine Construction ---
class AIParliamentService:
    def __init__(self, api_key: str = None):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    def create_agents(self) -> tuple[Agent, Agent, Agent]:
        quant_analyst = Agent(
            role="Senior Quantitative Technical Analyst",
            goal="Analyze technical data, market regime, and indicators to identify high-probability setups.",
            backstory="You are a veteran Wall Street quantitative trader who strictly relies on technical indicators, liquidity, and statistical market regimes.",
            verbose=False
        )

        sentiment_analyst = Agent(
            role="Macro & Sentiment Analyst",
            goal="Evaluate market sentiment, news impact, and macro environments.",
            backstory="You specialize in assessing trader psychology, market fear/greed metrics, and liquidity trends.",
            verbose=False
        )

        risk_officer = Agent(
            role="Chief Risk Officer (CRO)",
            goal="Synthesize technical and sentiment inputs, enforce capital preservation, and make final risk-adjusted decisions.",
            backstory="You prioritize capital preservation above all else. You reject aggressive trades during uncertain or highly volatile regimes.",
            verbose=False
        )

        return quant_analyst, sentiment_analyst, risk_officer

    def evaluate_trade(self, symbol: str, current_price: float, market_regime: str) -> QuantitativeDecision:
        quant, sentiment, cro = self.create_agents()

        task_quant = Task(
            description=f"Analyze symbol {symbol} at current price ${current_price} under Market Regime: {market_regime}. Evaluate technical setup.",
            expected_output="Detailed technical report on price action and risk/reward ratio.",
            agent=quant
        )

        task_sentiment = Task(
            description=f"Evaluate sentiment conditions for {symbol} under regime {market_regime}.",
            expected_output="Short sentiment and macro liquidity evaluation.",
            agent=sentiment
        )

        task_final_decision = Task(
            description=f"Review quant and sentiment reports for {symbol}. Issue a final risk-adjusted recommendation including Action (BUY/SELL/HOLD), Confidence, Position Size %, Risk Score (1-10), and key reasoning.",
            expected_output="Structured final decision for the trading execution engine.",
            agent=cro,
            output_pydantic=QuantitativeDecision
        )

        crew = Crew(
            agents=[quant, sentiment, cro],
            tasks=[task_quant, task_sentiment, task_final_decision],
            process=Process.sequential,
            verbose=False
        )

        logger.info(f"🏛️ Convening AI Parliament for {symbol} (Regime: {market_regime})...")
        result = crew.kickoff()
        
        # Access structured output directly from final task
        return task_final_decision.output.pydantic


def main():
    # Example execution (Fallback demo / API check)
    api_key = os.getenv("OPENAI_API_KEY", "mock-key")
    
    if api_key == "mock-key":
        logger.warning("⚠️ OPENAI_API_KEY not found in environment. Demonstrating Pydantic Schema output fallback...")
        demo_decision = QuantitativeDecision(
            symbol="BTC/USDT",
            action=ActionEnum.HOLD,
            confidence=0.85,
            recommended_position_size_pct=0.0,
            risk_score=8,
            reasoning=[
                "Market Regime is HIGH_VOLATILITY.",
                "High risk of whipsaws and liquidation cascades.",
                "Capital preservation rule triggered: Stand aside until regime stabilizes."
            ]
        )
        logger.info(f"🎯 Structured Output Received:\n{demo_decision.model_dump_json(indent=2)}")
    else:
        parliament = AIParliamentService(api_key=api_key)
        decision = parliament.evaluate_trade(symbol="BTC/USDT", current_price=83475.80, market_regime="HIGH_VOLATILITY")
        logger.info(f"🎯 AI Parliament Final Decision:\n{decision.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()