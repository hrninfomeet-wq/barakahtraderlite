"""
Trading API Models and Data Structures
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


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

