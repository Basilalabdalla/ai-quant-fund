# shared_lib/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional
from shared_lib.schemas import MarketData, TradeSignal, ExecutionResult

class AbstractDataIngestion(ABC):
    @abstractmethod
    async def fetch_latest_tick(self, symbol: str) -> Optional[MarketData]:
        pass

class AbstractAIParliament(ABC):
    @abstractmethod
    async def evaluate_market(self, data: MarketData) -> TradeSignal:
        pass

class AbstractRiskEngine(ABC):
    @abstractmethod
    def validate_signal(self, signal: TradeSignal, current_price: float) -> bool:
        pass

class AbstractExecutionEngine(ABC):
    @abstractmethod
    async def execute_order(self, signal: TradeSignal) -> ExecutionResult:
        pass