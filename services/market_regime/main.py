import numpy as np
import pandas as pd
import logging
from enum import Enum
from hmmlearn.hmm import GaussianHMM
import ccxt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MarketRegimeService")


class MarketRegime(str, Enum):
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


class HMMMarketRegimeDetector:
    def __init__(self, n_components: int = 3):
        self.n_components = n_components
        # Dialect covariance + min_covar prevents Cholesky decomposition failure
        self.model = GaussianHMM(
            n_components=n_components,
            covariance_type="diag",
            min_covar=1e-3,
            n_iter=200,
            random_state=42
        )

    def fetch_historical_ohlcv(self, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        """جلب البيانات التاريخية لحساب العوائد والتقلبات"""
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """استخراج العوائد والمدى الحركي مع تحسين النطاق المالي"""
        df['returns'] = np.log(df['close'] / df['close'].shift(1)) * 100.0
        df['range'] = ((df['high'] - df['low']) / df['close']) * 100.0
        df = df.dropna().reset_index(drop=True)
        return df

    def fit_and_predict(self, df: pd.DataFrame) -> MarketRegime:
        features = df[['returns', 'range']].values
        self.model.fit(features)
        
        hidden_states = self.model.predict(features)
        current_state = hidden_states[-1]
        
        means = self.model.means_
        
        # ترتيب الحالات بناءً على العوائد (Returns)
        sorted_by_returns = np.argsort(means[:, 0])
        
        bear_state = sorted_by_returns[0]
        bull_state = sorted_by_returns[-1]
        
        if current_state == bull_state:
            return MarketRegime.BULL_TREND
        elif current_state == bear_state:
            return MarketRegime.BEAR_TREND
        else:
            return MarketRegime.HIGH_VOLATILITY


def main():
    logger.info("🧠 Running HMM Market Regime Detection Service...")
    detector = HMMMarketRegimeDetector(n_components=3)
    
    symbol = "BTC/USDT"
    logger.info(f"📊 Fetching OHLCV data for {symbol}...")
    df = detector.fetch_historical_ohlcv(symbol=symbol, timeframe="1h", limit=500)
    
    df_features = detector.prepare_features(df)
    regime = detector.fit_and_predict(df_features)
    
    current_price = df_features['close'].iloc[-1]
    logger.info(f"🎯 Current Market Regime for {symbol} (Price: ${current_price:,.2f}): >>> {regime.value} <<<")


if __name__ == "__main__":
    main()