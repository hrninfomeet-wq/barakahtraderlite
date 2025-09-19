"""
Trading API Models and Data Structures
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from decimal import Decimal


class APIProvider(str, Enum):
    """Supported API providers"""
    FLATTRADE = "flattrade"
    FYERS = "fyers"
    UPSTOX = "upstox"
    ALICE_BLUE = "alice_blue"


class HealthStatus(str, Enum):
    """API health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class APIConfig(BaseModel):
    """API Configuration Model"""
    provider: APIProvider
    credentials: Dict[str, Any] = Field(default_factory=dict)
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    endpoints: Dict[str, str] = Field(default_factory=dict)
    health_check_interval: int = 30  # seconds
    timeout: int = 30  # seconds
    retry_attempts: int = 3

    model_config = {"use_enum_values": True}


class EncryptedCredentials(BaseModel):
    """Encrypted Credential Storage Model"""
    provider: APIProvider
    encrypted_data: bytes
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    is_active: bool = True

    model_config = {"use_enum_values": True}


class APIHealthStatus(BaseModel):
    """API Health Status Model"""
    provider: APIProvider
    status: HealthStatus
    last_check: datetime = Field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    rate_limit_remaining: Optional[int] = None

    model_config = {"use_enum_values": True}


class APIRateLimit(BaseModel):
    """API Rate Limit Information"""
    provider: APIProvider
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    current_usage_second: int = 0
    current_usage_minute: int = 0
    current_usage_hour: int = 0
    last_reset: datetime = Field(default_factory=datetime.now)

    model_config = {"use_enum_values": True}


class TOTPConfig(BaseModel):
    """TOTP Configuration for 2FA"""
    secret_key: str
    issuer: str = "AI Trading Engine"
    account_name: str
    digits: int = 6
    period: int = 30
    algorithm: str = "sha1"


class TradingMode(str, Enum):
    """Trading mode enum"""
    PAPER = "PAPER"
    LIVE = "LIVE"
    MAINTENANCE = "MAINTENANCE"


class OrderType(str, Enum):
    """Order type enum"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status enum"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class Order(BaseModel):
    """Order model for trading"""
    symbol: str
    quantity: int
    side: str  # BUY or SELL
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    stop_price: Optional[float] = None
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"use_enum_values": True}


class TradingPosition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_id: str = Field(..., description="Unique position ID")
    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., description="Position quantity")
    avg_price: Decimal = Field(..., description="Average entry price")
    current_price: Decimal = Field(..., description="Current market price")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L")
    realized_pnl: Decimal = Field(..., description="Realized P&L")
    open_date: datetime = Field(..., description="Position open date")
    position_type: str = Field(..., description="Long/Short")
    instrument_type: str = Field(..., description="Call/Put/Future")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    strike_price: Optional[Decimal] = Field(None, description="Strike price")
    delta: Decimal = Field(0, description="Position delta")
    theta: Decimal = Field(0, description="Position theta")

class Portfolio(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str = Field(..., description="Unique portfolio ID")
    user_id: str = Field(..., description="User ID")
    positions: List[TradingPosition] = Field(default_factory=list, description="Current positions")
    total_value: Decimal = Field(..., description="Total portfolio value")
    cash_balance: Decimal = Field(..., description="Available cash")
    margin_used: Decimal = Field(..., description="Margin used")

