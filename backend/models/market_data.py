"""
Market Data Models for Real-Time Multi-Source Market Data Pipeline
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import json


class DataType(str, Enum):
    """Market data types"""
    PRICE = "PRICE"
    VOLUME = "VOLUME"
    OPEN_INTEREST = "OPEN_INTEREST"
    GREEKS = "GREEKS"
    ORDERBOOK = "ORDERBOOK"


class ConnectionStatus(str, Enum):
    """WebSocket connection status"""
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


class ValidationTier(str, Enum):
    """Data validation tiers"""
    FAST = "FAST"           # Tier 1: <5ms
    CROSS_SOURCE = "CROSS_SOURCE"  # Tier 2: <20ms
    DEEP = "DEEP"           # Tier 3: <50ms


class MarketData(BaseModel):
    """Market data model with comprehensive fields"""
    symbol: str = Field(..., description="Trading symbol (e.g., NIFTY50)")
    exchange: str = Field(..., description="Exchange name (e.g., NSE, BSE)")
    last_price: float = Field(..., description="Last traded price")
    volume: int = Field(..., description="Trading volume")
    timestamp: datetime = Field(..., description="Data timestamp")
    data_type: DataType = Field(..., description="Type of market data")
    
    # Additional fields for comprehensive market data
    open_price: Optional[float] = Field(None, description="Opening price")
    high_price: Optional[float] = Field(None, description="Day's high price")
    low_price: Optional[float] = Field(None, description="Day's low price")
    close_price: Optional[float] = Field(None, description="Previous close price")
    change: Optional[float] = Field(None, description="Price change from previous close")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    
    # Metadata
    source: str = Field(..., description="Data source (FYERS, UPSTOX, etc.)")
    validation_tier: ValidationTier = Field(ValidationTier.FAST, description="Validation tier used")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Data confidence score")
    
    model_config = {"use_enum_values": True}
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        if v > datetime.now():
            raise ValueError('Timestamp cannot be in the future')
        return v
    
    @field_validator('last_price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v):
        if v is not None and v < 0:
            raise ValueError('Volume cannot be negative')
        return v


class WebSocketConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str = Field(..., description="Unique connection identifier")
    provider: str = Field(..., description="API provider (FYERS, UPSTOX)")
    status: ConnectionStatus = Field(..., description="Connection status")
    max_symbols: float = Field(..., description="Maximum symbols supported")
    current_symbols: List[str] = Field(default_factory=list, description="Currently subscribed symbols")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat received")
    error_count: int = Field(0, description="Number of connection errors")
    
    model_config = {"use_enum_values": True}


class SymbolDistribution(BaseModel):
    """Symbol distribution across connections"""
    fyers_pools: List[Dict[str, Any]] = Field(default_factory=list, description="FYERS pool distributions")
    upstox_pool: List[str] = Field(default_factory=list, description="UPSTOX pool symbols")
    total_symbols: int = Field(0, description="Total symbols distributed")
    
    def get_total_symbols(self) -> int:
        """Calculate total symbols across all pools"""
        total = len(self.upstox_pool)
        for pool in self.fyers_pools:
            total += len(pool.get('symbols', []))
        return total


class ValidationResult(BaseModel):
    """Data validation result"""
    status: str = Field(..., description="Validation status (validated, discrepancy_detected, failed)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Validation confidence")
    tier_used: ValidationTier = Field(..., description="Validation tier used")
    processing_time_ms: float = Field(..., description="Validation processing time in milliseconds")
    recommended_action: str = Field(..., description="Recommended action based on validation")
    discrepancy_details: Optional[Dict[str, Any]] = Field(None, description="Details of any discrepancies found")
    
    model_config = {"use_enum_values": True}


class PerformanceMetrics(BaseModel):
    """Performance metrics for monitoring"""
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    validation_accuracy: float = Field(..., ge=0.0, le=1.0, description="Data validation accuracy")
    connection_uptime: float = Field(..., ge=0.0, le=1.0, description="Connection uptime percentage")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    throughput_symbols_per_second: float = Field(..., description="Throughput in symbols per second")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")


class CacheEntry(BaseModel):
    """Cache entry for market data"""
    key: str = Field(..., description="Cache key")
    data: MarketData = Field(..., description="Cached market data")
    created_at: datetime = Field(default_factory=datetime.now, description="Cache creation time")
    expires_at: datetime = Field(..., description="Cache expiration time")
    access_count: int = Field(0, description="Number of times accessed")
    last_accessed: datetime = Field(default_factory=datetime.now, description="Last access time")
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.expires_at
    
    def is_fresh(self, max_age_seconds: float = 1.0) -> bool:
        """Check if cache entry is fresh (within max_age_seconds)"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age <= max_age_seconds


class Alert(BaseModel):
    """Alert for system monitoring"""
    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Alert type (discrepancy, performance, connection)")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")
    resolved: bool = Field(False, description="Whether alert is resolved")
    resolution_details: Optional[str] = Field(None, description="Resolution details")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for storage"""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_details': self.resolution_details
        }


class MarketDataRequest(BaseModel):
    """Market data request model"""
    symbols: List[str] = Field(..., description="List of symbols to fetch")
    data_types: List[DataType] = Field(default=[DataType.PRICE], description="Types of data to fetch")
    max_age_seconds: float = Field(1.0, description="Maximum age of cached data to accept")
    validation_tier: ValidationTier = Field(ValidationTier.FAST, description="Required validation tier")
    priority: int = Field(1, description="Request priority (1=highest, 5=lowest)")
    
    model_config = {"use_enum_values": True}
    
    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('At least one symbol must be specified')
        if len(v) > 1000:  # Reasonable limit
            raise ValueError('Too many symbols requested (max 1000)')
        return v


class SubscriptionRequest(BaseModel):
    """Subscription request model"""
    symbols: List[str] = Field(..., description="List of symbols to subscribe to")
    
    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('At least one symbol must be specified')
        if len(v) > 1000:  # Reasonable limit
            raise ValueError('Too many symbols requested (max 1000)')
        return v


class MarketDataResponse(BaseModel):
    """Market data response model"""
    request_id: str = Field(..., description="Request identifier")
    symbols_requested: List[str] = Field(..., description="Symbols that were requested")
    symbols_returned: List[str] = Field(..., description="Symbols that were returned")
    data: Dict[str, MarketData] = Field(..., description="Market data by symbol")
    performance_metrics: PerformanceMetrics = Field(..., description="Response performance metrics")
    validation_results: Dict[str, ValidationResult] = Field(..., description="Validation results by symbol")
    cache_hit_rate: float = Field(..., description="Cache hit rate for this request")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    def get_missing_symbols(self) -> List[str]:
        """Get symbols that were requested but not returned"""
        return list(set(self.symbols_requested) - set(self.symbols_returned))
    
    def get_success_rate(self) -> float:
        """Calculate success rate (symbols returned / symbols requested)"""
        if not self.symbols_requested:
            return 0.0
        return len(self.symbols_returned) / len(self.symbols_requested)
