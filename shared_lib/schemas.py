# shared_lib/schemas.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MarketData(BaseModel):
    symbol: str
    price: float = Field(gt=0, description="Price must be positive")
    volume: float = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TradeSignal(BaseModel):
    symbol: str
    action: SignalAction
    confidence: float = Field(ge=0.0, le=100.0)
    suggested_amount: float = Field(gt=0.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionResult(BaseModel):
    order_id: str
    symbol: str
    action: SignalAction
    executed_price: float
    amount: float
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)