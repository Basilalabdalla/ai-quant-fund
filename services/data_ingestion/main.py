import asyncio
import logging
from typing import Optional
import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared_lib.schemas import MarketData
from shared_lib.interfaces import AbstractDataIngestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataIngestionService")


class ResilientDataIngestion(AbstractDataIngestion):
    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        # Safe initialization of dynamic exchange adapter
        exchange_class = getattr(ccxt, exchange_id, None)
        if not exchange_class:
            raise ValueError(f"Exchange {exchange_id} is not supported by CCXT.")
        self.exchange = exchange_class({'enableRateLimit': True})

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"⚠️ Exchange network drop detected. Retrying attempt {retry_state.attempt_number}..."
        )
    )
    async def fetch_latest_tick(self, symbol: str) -> MarketData:
        """
        Fetches live orderbook tick data with automatic Circuit Breaker retries.
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            
            # Defensive Pydantic parsing
            market_data = MarketData(
                symbol=symbol,
                price=float(ticker['last']),
                volume=float(ticker['baseVolume']),
            )
            return market_data

        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:
            logger.error(f"Network error during ticker fetch: {e}")
            raise e  # Triggers tenacity retry
        except Exception as e:
            logger.error(f"Non-retryable exception caught in ingestion: {e}")
            raise e

    async def close(self):
        await self.exchange.close()


async def main():
    logger.info("🚀 Starting Resilient Data Ingestion Service...")
    ingestion = ResilientDataIngestion(exchange_id="binance")

    try:
        # Stream live tickers for test symbols
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        for _ in range(3):  # Run 3 test stream loops
            for symbol in symbols:
                data = await ingestion.fetch_latest_tick(symbol)
                logger.info(f"🟢 LIVE TICK -> Symbol: {data.symbol} | Price: ${data.price:,.2f} | Vol: {data.volume:.2f}")
            await asyncio.sleep(2)

    except Exception as e:
        logger.critical(f"❌ Unhandled error in Ingestion loop: {e}")
    finally:
        await ingestion.close()
        logger.info("🛑 Ingestion Service Closed Gracefully.")

if __name__ == "__main__":
    asyncio.run(main())