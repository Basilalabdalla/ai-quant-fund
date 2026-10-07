import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import ccxt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RiskAndExecutionService")


class ActionEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ExecutionStatus(str, Enum):
    EXECUTED = "EXECUTED"
    REJECTED_BY_RISK = "REJECTED_BY_RISK"
    SIMULATED = "SIMULATED"
    FAILED = "FAILED"


class OrderRequest(BaseModel):
    symbol: str
    action: ActionEnum
    confidence: float
    recommended_position_size_pct: float
    risk_score: int
    current_price: float
    market_regime: str
    reasoning: List[str]


class ExecutionResult(BaseModel):
    status: ExecutionStatus
    symbol: str
    action: ActionEnum
    executed_price: Optional[float] = None
    executed_amount: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RiskFirewall:
    def __init__(self, max_position_pct: float = 5.0, max_allowed_risk_score: int = 7):
        self.max_position_pct = max_position_pct
        self.max_allowed_risk_score = max_allowed_risk_score

    def validate_order(self, order: OrderRequest) -> tuple[bool, List[str]]:
        rejections = []

        # 1. Reject HOLD actions
        if order.action == ActionEnum.HOLD:
            rejections.append("Action is HOLD - No order execution needed.")
            return False, rejections

        # 2. Market Regime Risk Check
        if order.market_regime == "HIGH_VOLATILITY" and order.confidence < 0.90:
            rejections.append("Risk Rule Triggered: Market Regime is HIGH_VOLATILITY and AI confidence < 90%.")

        # 3. Risk Score Limit Check
        if order.risk_score > self.max_allowed_risk_score:
            rejections.append(f"Risk Rule Triggered: Risk Score ({order.risk_score}) exceeds maximum limit ({self.max_allowed_risk_score}).")

        # 4. Position Size Cap
        if order.recommended_position_size_pct > self.max_position_pct:
            rejections.append(f"Risk Rule Triggered: Position size ({order.recommended_position_size_pct}%) exceeds hard cap ({self.max_position_pct}%).")

        is_approved = len(rejections) == 0
        return is_approved, rejections


class CCXTExecutionEngine:
    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.exchange = ccxt.binance({'enableRateLimit': True})

    def execute_order(self, order: OrderRequest, approved_size_pct: float) -> ExecutionResult:
        """تنفيذ الصفقة عبر CCXT أو محاكاتها آمنة ورقياً"""
        stop_loss = round(order.current_price * 0.98, 2)   # 2% Stop Loss
        take_profit = round(order.current_price * 1.05, 2)  # 5% Take Profit
        
        if self.paper_trading:
            logger.info(f"📝 [PAPER TRADING] Executed {order.action.value} for {order.symbol} @ ${order.current_price:,.2f}")
            logger.info(f"🛡️ Protection Set -> Stop Loss: ${stop_loss:,.2f} | Take Profit: ${take_profit:,.2f}")
            
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                symbol=order.symbol,
                action=order.action,
                executed_price=order.current_price,
                executed_amount=approved_size_pct,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit
            )
        else:
            # تنفيذ حقيقي بـ CCXT
            # order_res = self.exchange.create_order(symbol=order.symbol, type='market', side=order.action.value.lower(), amount=...)
            pass


def main():
    logger.info("🚀 Testing Deterministic Risk Firewall & CCXT Execution Service...")
    
    risk_firewall = RiskFirewall(max_position_pct=5.0, max_allowed_risk_score=7)
    execution_engine = CCXTExecutionEngine(paper_trading=True)

    # حالة اختبار 1: أوردر مرفوض بسبب عالية التقلبات ودرجة مخاطرة مرتفعة
    risky_order = OrderRequest(
        symbol="BTC/USDT",
        action=ActionEnum.BUY,
        confidence=0.75,
        recommended_position_size_pct=8.0,
        risk_score=8,
        current_price=83475.80,
        market_regime="HIGH_VOLATILITY",
        reasoning=["High volatility breakout attempt"]
    )

    logger.info("🔍 Evaluating Risky Order through Risk Firewall...")
    approved, reasons = risk_firewall.validate_order(risky_order)
    
    if not approved:
        result = ExecutionResult(
            status=ExecutionStatus.REJECTED_BY_RISK,
            symbol=risky_order.symbol,
            action=risky_order.action,
            rejection_reasons=reasons
        )
        logger.warning(f"🛑 ORDER BLOCKED BY RISK FIREWALL:\n{result.model_dump_json(indent=2)}")

    # حالة اختبار 2: أوردر مقبول يفي بشروط جدار الحماية
    safe_order = OrderRequest(
        symbol="BTC/USDT",
        action=ActionEnum.BUY,
        confidence=0.95,
        recommended_position_size_pct=3.5,
        risk_score=4,
        current_price=83475.80,
        market_regime="BULL_TREND",
        reasoning=["Strong trend confirmation", "Low volatility"]
    )

    logger.info("\n🔍 Evaluating Safe Order through Risk Firewall...")
    approved, reasons = risk_firewall.validate_order(safe_order)
    
    if approved:
        exec_result = execution_engine.execute_order(safe_order, approved_size_pct=safe_order.recommended_position_size_pct)
        logger.info(f"✅ EXECUTION SUCCESSFUL:\n{exec_result.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()