import logging
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, Tuple  # <-- تم إضافة Tuple هنا

# استيراد الخدمات المنشأة سابقاً مع تفعيل آليات التدهور الرشيق
from tests.test_chaos import ResilientRegimeDetector, ResilientAIParliament, ResilientVectorMemory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PaperTradingEngine")

class PaperTraderService:
    def __init__(self):
        self.is_running = True

    def run_trading_cycle(self):
        logger.info("🔄 [Paper Trader Loop] Processing order book & listening for execution events...")
        # هنا يتم وضع منطق مطابقة الأوامر الحقيقي مع قواعد البيانات

    def start(self):
        logger.info("🚀 Starting Paper Trader Background Worker...")
        while self.is_running:
            try:
                self.run_trading_cycle()
                time.sleep(10)  # دورة تداول كل 10 ثوانٍ
            except Exception as e:
                logger.error(f"Error in Paper Trader Loop: {e}")
                time.sleep(5)


if __name__ == "__main__":
    trader = PaperTraderService()
    trader.start()


class PaperBrokerage:
    """محاكي الوسيط المالي (Simulated Paper Account)"""
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []

    def execute_paper_order(self, symbol: str, action: str, amount_usd: float, price: float, sl: float, tp: float) -> Dict[str, Any]:
        if action == "BUY":
            if self.balance < amount_usd:
                return {"status": "REJECTED", "reason": "Insufficient paper balance"}
            
            qty = amount_usd / price
            self.balance -= amount_usd
            self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
            
            order_info = {
                "order_id": f"PAPER_{int(time.time())}",
                "symbol": symbol,
                "action": action,
                "price": price,
                "amount_usd": amount_usd,
                "stop_loss": sl,
                "take_profit": tp,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.trade_history.append(order_info)
            return {"status": "FILLED", "order": order_info}
        
        return {"status": "NO_ACTION"}


class RiskFirewallGuard:
    """جدار حماية المخاطر الحتمي"""
    def validate_proposal(self, proposal: Dict[str, Any], balance: float, current_price: float) -> Tuple[bool, str, Dict[str, float]]:
        action = proposal.get("action", "HOLD")
        confidence = proposal.get("confidence", 0.0)
        
        if action != "BUY":
            return False, "Action is not BUY", {}
            
        if confidence < 0.85:
            return False, f"Confidence too low ({confidence*100}% < 85%)", {}
            
        # تخصيص 5% من المحفظة كحد أقصى للمخاطرة
        max_position_size = balance * 0.05
        stop_loss = current_price * 0.98  # -2%
        take_profit = current_price * 1.04 # +4%
        
        return True, "Passed Risk Check", {
            "amount_usd": max_position_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }


def run_paper_trading_loop(iterations: int = 3):
    logger.info("🚀 STARTING LIVE PAPER TRADING EXECUTION LOOP...")
    
    broker = PaperBrokerage(initial_balance=10000.0)
    regime_detector = ResilientRegimeDetector()
    ai_parliament = ResilientAIParliament()
    memory_store = ResilientVectorMemory()
    risk_firewall = RiskFirewallGuard()

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    for i in range(1, iterations + 1):
        logger.info(f"\n--- 🔄 Loop Cycle #{i} | Wallet Balance: ${broker.balance:.2f} ---")
        symbol = random.choice(symbols)
        current_price = round(random.uniform(60000, 65000) if symbol == "BTC/USDT" else random.uniform(2500, 3000), 2)
        
        logger.info(f"📈 Market Tick: {symbol} @ ${current_price:.2f}")

        # 1. كشف حالة السوق
        regime = regime_detector.get_regime_with_fallback()
        logger.info(f"🧠 Detected Regime: {regime}")

        # 2. قرار برلمان الذكاء الاصطناعي
        ai_proposal = ai_parliament.evaluate_with_fallback(symbol=symbol)
        logger.info(f"🏛️ AI Parliament Proposal: {ai_proposal['action']} (Confidence: {ai_proposal['confidence']*100}%)")

        # 3. فحص جدار حماية المخاطر
        is_safe, reason, params = risk_firewall.validate_proposal(ai_proposal, broker.balance, current_price)
        
        if is_safe:
            logger.info(f"🛡️ Risk Firewall PASSED: Executing Trade...")
            execution = broker.execute_paper_order(
                symbol=symbol,
                action=ai_proposal['action'],
                amount_usd=params['amount_usd'],
                price=current_price,
                sl=params['stop_loss'],
                tp=params['take_profit']
            )
            logger.info(f"✅ Executed: {execution}")
        else:
            logger.warning(f"🛑 Risk Firewall REJECTED / PASSED OVER: {reason}")

        # 4. توثيق القرار في الذاكرة المتجهة (XAI)
        memory_store.store_decision_with_fallback({
            "cycle": i,
            "symbol": symbol,
            "price": current_price,
            "regime": regime,
            "proposal": ai_proposal,
            "passed_firewall": is_safe
        })
        
        time.sleep(1)

    logger.info(f"\n🏁 Paper Trading Completed. Final Paper Balance: ${broker.balance:.2f}")


if __name__ == "__main__":
    run_paper_trading_loop(iterations=3)