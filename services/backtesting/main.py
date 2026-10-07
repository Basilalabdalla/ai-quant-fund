import logging
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NightlyBacktestEngine")


class BacktestMetrics(BaseModel):
    strategy_name: str
    symbol: str
    total_return_pct: float
    buy_and_hold_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    optimal_params: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VectorBTEngine:
    """محرك محاكاة كمّي موجه (Vectorized Quant Backtesting)"""

    def __init__(self, initial_capital: float = 10_000.0):
        self.initial_capital = initial_capital

    def generate_mock_ohlcv(self, symbol: str = "BTC/USDT", days: int = 365) -> pd.DataFrame:
        """توليد بيانات أسعار تاريخية لمحاكاة الاختبار"""
        np.random.seed(42)
        dates = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=days * 24, freq="1h")
        
        # Random Walk مع اتجاه صاعد طفيف
        returns = np.random.normal(loc=0.0001, scale=0.012, size=len(dates))
        price_path = 60000.0 * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            "timestamp": dates,
            "open": price_path * (1 + np.random.uniform(-0.002, 0.002, len(dates))),
            "high": price_path * (1 + np.random.uniform(0.001, 0.008, len(dates))),
            "low": price_path * (1 + np.random.uniform(-0.008, -0.001, len(dates))),
            "close": price_path,
            "volume": np.random.uniform(10, 500, len(dates))
        })
        df.set_index("timestamp", inplace=True)
        return df

    def run_ma_crossover_strategy(self, df: pd.DataFrame, fast_window: int = 20, slow_window: int = 50) -> Tuple[pd.Series, pd.Series]:
        """محاكاة استراتيجية تقاطع المتوسطات المتحركة"""
        fast_ma = df["close"].rolling(window=fast_window).mean()
        slow_ma = df["close"].rolling(window=slow_window).mean()

        # إشارات الشراء (1) والبيع (-1)
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma <= slow_ma] = 0

        # التغيير في الإشارة يحدد بداية/نهاية الصفقة
        positions = signals.diff().fillna(0)
        return signals, positions

    def evaluate_performance(self, df: pd.DataFrame, signals: pd.Series, strategy_name: str, symbol: str, params: Dict[str, Any]) -> BacktestMetrics:
        """حساب معايير الأداء الكمية"""
        market_returns = df["close"].pct_change().fillna(0)
        strategy_returns = market_returns * signals.shift(1).fillna(0)

        # 1. إجمالي العائد
        cumulative_returns = (1 + strategy_returns).cumprod()
        total_return_pct = round((cumulative_returns.iloc[-1] - 1) * 100, 2)
        
        buy_and_hold_return = (1 + market_returns).cumprod()
        buy_and_hold_pct = round((buy_and_hold_return.iloc[-1] - 1) * 100, 2)

        # 2. نسبة شارب (مفترصاً معدل خالي من المخاطر = 0% للتبسيط)
        mean_ret = strategy_returns.mean() * 24 * 365
        std_ret = strategy_returns.std() * np.sqrt(24 * 365)
        sharpe_ratio = round(mean_ret / std_ret, 2) if std_ret > 0 else 0.0

        # 3. أقصى تراجع (Max Drawdown)
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown_pct = round(abs(drawdown.min()) * 100, 2)

        # 4. نسبة النجاح الصفقات
        trade_signals = signals.diff()
        entries = trade_signals[trade_signals == 1].index
        exits = trade_signals[trade_signals == -1].index
        
        trade_returns = []
        for entry, exit_idx in zip(entries, exits):
            ret = (df.loc[exit_idx, "close"] - df.loc[entry, "close"]) / df.loc[entry, "close"]
            trade_returns.append(ret)

        total_trades = len(trade_returns)
        winning_trades = sum(1 for r in trade_returns if r > 0)
        win_rate_pct = round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0.0

        return BacktestMetrics(
            strategy_name=strategy_name,
            symbol=symbol,
            total_return_pct=total_return_pct,
            buy_and_hold_return_pct=buy_and_hold_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            win_rate_pct=win_rate_pct,
            total_trades=total_trades,
            optimal_params=params
        )

    def grid_search_optimization(self, df: pd.DataFrame, symbol: str) -> BacktestMetrics:
        """البحث الشبكي للوصول لأفضل قيم بارامترية للاستراتيجية"""
        best_sharpe = -999.0
        best_metric = None

        fast_range = [10, 20, 30]
        slow_range = [50, 100, 200]

        logger.info("🔍 Running Nightly Grid Search Parameter Optimization...")

        for fast in fast_range:
            for slow in slow_range:
                if fast >= slow:
                    continue
                
                signals, _ = self.run_ma_crossover_strategy(df, fast_window=fast, slow_window=slow)
                metrics = self.evaluate_performance(
                    df, signals, 
                    strategy_name="MA_Crossover_Optimized", 
                    symbol=symbol, 
                    params={"fast_window": fast, "slow_window": slow}
                )

                if metrics.sharpe_ratio > best_sharpe:
                    best_sharpe = metrics.sharpe_ratio
                    best_metric = metrics

        return best_metric


def main():
    logger.info("🌙 Starting Nightly Backtesting & Strategy Self-Optimization Engine...")

    engine = VectorBTEngine(initial_capital=10_000.0)
    symbol = "BTC/USDT"
    
    # 1. تحميل البيانات التاريخية
    df = engine.generate_mock_ohlcv(symbol=symbol, days=180)
    logger.info(f"📊 Loaded {len(df)} OHLCV candle bars for {symbol}")

    # 2. تشغيل المحاكاة واستخراج الاستراتيجية المُثلى
    optimized_result = engine.grid_search_optimization(df, symbol=symbol)

    logger.info("✅ Nightly Optimization Completed!")
    logger.info(f"🎯 OPTIMIZED RESULTS REPORT:\n{optimized_result.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()