"""
Multi-API Manager with Intelligent Routing and Load Balancing
Handles FLATTRADE, FYERS, UPSTOX, and Alice Blue API connections
"""
import asyncio
import aiohttp
import time
import statistics
import os
from urllib.parse import quote
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Deque
from collections import deque
from loguru import logger

from models.trading import (
    APIProvider, APIConfig, HealthStatus,
    TradingMode
)
# from core.database import AuditLogger  # Unused

# Import paper trading engine for module-level access
from services.paper_trading import paper_trading_engine


class MockAuditLogger:
    """Mock audit logger for when audit logging is not configured"""
    
    async def log_api_usage(self, **kwargs):
        """Mock log API usage"""
        pass


class APIOperationError(Exception):
    """Raised when all APIs fail for an operation."""
    pass


class EnhancedRateLimiter:
    """Enhanced rate limiting with predictive analytics and real-time tracking"""

    def __init__(self, requests_per_second: int, requests_per_minute: Optional[int] = None, requests_per_hour: Optional[int] = None):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute or requests_per_second * 60
        self.requests_per_hour = requests_per_hour or self.requests_per_minute * 60

        # Real-time usage tracking with deques for efficient sliding window
        self.second_requests: Deque[float] = deque(maxlen=self.requests_per_second * 2)
        self.minute_requests: Deque[float] = deque(maxlen=self.requests_per_minute * 2)
        self.hour_requests: Deque[float] = deque(maxlen=self.requests_per_hour * 2)

        # Predictive analytics data
        self.usage_patterns: Deque[Dict[str, Any]] = deque(maxlen=100)  # Last 100 usage snapshots
        self.prediction_threshold = 0.8  # 80% threshold for failover
        self.volatility_window = 300  # 5 minutes for volatility analysis

        # Performance metrics
        self.total_requests = 0
        self.blocked_requests = 0
        self.last_spike_detected = None

    def is_rate_limited(self) -> bool:
        """Check if rate limit is exceeded with predictive analytics"""
        now = time.time()

        # Clean old requests (deque automatically handles this with maxlen)
        current_second_count = len([req_time for req_time in self.second_requests if now - req_time < 1])
        current_minute_count = len([req_time for req_time in self.minute_requests if now - req_time < 60])
        current_hour_count = len([req_time for req_time in self.hour_requests if now - req_time < 3600])

        # Check current limits
        if current_second_count >= self.requests_per_second:
            return True
        if current_minute_count >= self.requests_per_minute:
            return True
        if current_hour_count >= self.requests_per_hour:
            return True

        return False

    def is_approaching_limit(self) -> bool:
        """Check if approaching rate limit using predictive analytics"""
        now = time.time()

        # Calculate current usage percentages
        second_usage = len([req_time for req_time in self.second_requests if now - req_time < 1]) / self.requests_per_second
        minute_usage = len([req_time for req_time in self.minute_requests if now - req_time < 60]) / self.requests_per_minute

        # Check if approaching threshold
        if second_usage >= self.prediction_threshold or minute_usage >= self.prediction_threshold:
            return True

        # Use predictive analytics for spike detection
        if self._predict_usage_spike():
            return True

        return False

    def _predict_usage_spike(self) -> bool:
        """Predict if usage spike is likely using sliding window analysis"""
        try:
            if len(self.usage_patterns) < 10:  # Need minimum data points
                return False

            recent_patterns = list(self.usage_patterns)[-10:]  # Last 10 snapshots

            # Calculate trend with error handling
            usage_values = [pattern['second_usage'] for pattern in recent_patterns]
            if len(usage_values) < 3:
                return False

            # Simple linear regression for trend detection with zero-division protection
            try:
                trend = statistics.mean(usage_values[-3:]) - statistics.mean(usage_values[:3])
            except statistics.StatisticsError:
                return False

            # Check for volatility spike with error handling
            if len(usage_values) >= 5:
                try:
                    volatility = statistics.stdev(usage_values[-5:])
                    avg_volatility = statistics.mean([
                        statistics.stdev(usage_values[i:i+5])
                        for i in range(len(usage_values)-4)
                        if len(usage_values[i:i+5]) > 1
                    ])

                    # If volatility is significantly higher than average and trend is increasing
                    if avg_volatility > 0 and volatility > avg_volatility * 1.5 and trend > 0.1:
                        self.last_spike_detected = datetime.now()
                        logger.warning(f"Usage spike predicted: volatility={volatility:.3f}, trend={trend:.3f}")
                        return True
                except statistics.StatisticsError:
                    # If we can't calculate volatility, don't predict spike
                    return False

            return False
        except Exception as e:
            logger.error(f"Error in usage spike prediction: {e}")
            return False

    def record_request(self):
        """Record a request for rate limiting with analytics"""
        now = time.time()
        self.second_requests.append(now)
        self.minute_requests.append(now)
        self.hour_requests.append(now)
        self.total_requests += 1

        # Record usage pattern for analytics
        current_usage = self._calculate_current_usage()
        self.usage_patterns.append({
            'timestamp': now,
            'second_usage': current_usage['second_usage'],
            'minute_usage': current_usage['minute_usage'],
            'hour_usage': current_usage['hour_usage']
        })

    def _calculate_current_usage(self) -> Dict[str, float]:
        """Calculate current usage percentages"""
        now = time.time()

        return {
            'second_usage': len([req_time for req_time in self.second_requests if now - req_time < 1]) / self.requests_per_second,
            'minute_usage': len([req_time for req_time in self.minute_requests if now - req_time < 60]) / self.requests_per_minute,
            'hour_usage': len([req_time for req_time in self.hour_requests if now - req_time < 3600]) / self.requests_per_hour
        }

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive rate limit status with analytics"""
        now = time.time()
        current_usage = self._calculate_current_usage()

        return {
            "requests_per_second": self.requests_per_second,
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "current_second": len([req_time for req_time in self.second_requests if now - req_time < 1]),
            "current_minute": len([req_time for req_time in self.minute_requests if now - req_time < 60]),
            "current_hour": len([req_time for req_time in self.hour_requests if now - req_time < 3600]),
            "usage_percentages": current_usage,
            "approaching_limit": self.is_approaching_limit(),
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "success_rate": (self.total_requests - self.blocked_requests) / max(self.total_requests, 1),
            "last_spike_detected": self.last_spike_detected.isoformat() if self.last_spike_detected else None,
            "prediction_threshold": self.prediction_threshold
        }

    def get_analytics(self) -> Dict[str, Any]:
        """Get predictive analytics data"""
        if not self.usage_patterns:
            return {"error": "Insufficient data for analytics"}

        recent_patterns = list(self.usage_patterns)[-20:]  # Last 20 snapshots
        usage_values = [pattern['second_usage'] for pattern in recent_patterns]

        if len(usage_values) < 3:
            return {"error": "Insufficient data for analytics"}

        return {
            "average_usage": statistics.mean(usage_values),
            "usage_volatility": statistics.stdev(usage_values) if len(usage_values) > 1 else 0,
            "trend": statistics.mean(usage_values[-3:]) - statistics.mean(usage_values[:3]),
            "peak_usage": max(usage_values),
            "pattern_count": len(self.usage_patterns),
            "prediction_accuracy": self._calculate_prediction_accuracy()
        }

    def _calculate_prediction_accuracy(self) -> float:
        """Calculate prediction accuracy based on historical data"""
        # This would be implemented based on actual historical performance
        # For now, return a placeholder value
        return 0.85  # 85% accuracy placeholder


# Alias for backward compatibility
RateLimiter = EnhancedRateLimiter


class TradingAPIInterface(ABC):
    """Abstract base class for all trading API implementations"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = EnhancedRateLimiter(
            config.rate_limits.get('requests_per_second', 10),
            config.rate_limits.get('requests_per_minute', 600),
            config.rate_limits.get('requests_per_hour', 36000)
        )
        self.health_status = HealthStatus.UNKNOWN
        self.last_health_check = None
        self.auth_token = None
        self.token_expiry = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with the API provider"""
        pass

    @abstractmethod
    async def place_order(self, order_data: Dict) -> Dict:
        """Place a trading order"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        pass

    @abstractmethod
    async def get_portfolio(self) -> Dict:
        """Get portfolio information"""
        pass

    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time market data"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        pass

    async def health_check(self) -> bool:
        """Perform health check on API"""
        try:
            start_time = time.time()
            # Call portfolio to verify connectivity
            await self.get_portfolio()
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            self.health_status = HealthStatus.HEALTHY
            self.last_health_check = datetime.now()

            provider_name = self.config.provider.value if hasattr(self.config.provider, 'value') else self.config.provider
            logger.info(f"{provider_name} health check passed in {response_time:.2f}ms")
            return True

        except Exception as e:
            self.health_status = HealthStatus.UNHEALTHY
            self.last_health_check = datetime.now()
            provider_name = self.config.provider.value if hasattr(self.config.provider, 'value') else self.config.provider
            logger.warning(f"{provider_name} health check failed: {e}")
            return False

    def get_rate_limits(self) -> Dict[str, int]:
        """Get current rate limit information"""
        return self.rate_limiter.get_status()

    async def refresh_token(self) -> bool:
        """Refresh authentication token if needed"""
        if not self.token_expiry or datetime.now() >= self.token_expiry:
            logger.info(f"Refreshing token for {self.config.provider.value}")
            # Implementation will be in specific API adapters
            return True
        return True


class FlattradeAPI(TradingAPIInterface):
    """FLATTRADE API Implementation using FlattradeAPIService"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        # Import the service here to avoid circular imports
        from services.flattrade_api import flattrade_service
        self.service = flattrade_service

    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with FLATTRADE API"""
        try:
            if self.service.has_credentials():
                self.auth_token = self.service.access_token
                self.token_expiry = datetime.now() + timedelta(hours=24)
                logger.info("FLATTRADE authentication successful with existing token")
                return True
            else:
                logger.warning("FLATTRADE authentication failed: missing credentials")
                return False
        except Exception as e:
            logger.error(f"FLATTRADE authentication failed: {e}")
            return False

    async def place_order(self, order_data: Dict) -> Dict:
        """Place order via FLATTRADE"""
        # This would be implemented when order placement is needed
        # For now, return placeholder since we're in paper trading mode
        return {"order_id": "FL_12345", "status": "placed", "provider": "flattrade"}

    async def get_positions(self) -> List[Dict]:
        """Get positions from FLATTRADE"""
        # This would fetch real positions from Flattrade API
        # For now, return empty list since we're focusing on market data
        return []

    async def get_portfolio(self) -> Dict:
        """Get portfolio from FLATTRADE"""
        # This would fetch real portfolio from Flattrade API
        # For now, return basic portfolio data
        if self.service.has_credentials():
            return {"total_value": 100000, "cash": 50000, "provider": "flattrade", "status": "connected"}
        else:
            return {"error": "Not authenticated", "provider": "flattrade"}

    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data from FLATTRADE using real API"""
        try:
            if not self.service.has_credentials():
                logger.warning("FLATTRADE market data: missing credentials, returning demo data")
                return {symbol: {"price": 100.0, "source": "demo"} for symbol in symbols}
            
            # Use real Flattrade API service
            result = await self.service.get_market_data(symbols)
            
            if result.get('success'):
                # Transform to expected format
                transformed_data = {}
                for symbol, data in result['data'].items():
                    transformed_data[symbol] = {
                        "price": data.get('last_price', 0),
                        "change": data.get('change', 0),
                        "change_percent": data.get('change_percent', 0),
                        "volume": data.get('volume', 0),
                        "high": data.get('high', 0),
                        "low": data.get('low', 0),
                        "open": data.get('open', 0),
                        "timestamp": data.get('timestamp'),
                        "source": "flattrade"
                    }
                return transformed_data
            else:
                logger.error(f"FLATTRADE market data error: {result.get('error')}")
                return {symbol: {"price": None, "error": result.get('error'), "source": "flattrade"} for symbol in symbols}
                
        except Exception as e:
            logger.error(f"FLATTRADE market data exception: {e}")
            return {symbol: {"price": None, "error": str(e), "source": "flattrade"} for symbol in symbols}

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order via FLATTRADE"""
        # This would be implemented when order cancellation is needed
        return True


class FyersAPI(TradingAPIInterface):
    """FYERS API Implementation using FyersAPIService"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        # Import the service here to avoid circular imports
        from services.fyers_api import fyers_service
        self.service = fyers_service

    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with FYERS API"""
        try:
            if self.service.has_credentials():
                self.auth_token = self.service.access_token
                self.token_expiry = datetime.now() + timedelta(hours=24)
                logger.info("FYERS authentication successful with existing token")
                return True
            else:
                logger.warning("FYERS authentication failed: missing access token")
                return False
        except Exception as e:
            logger.error(f"FYERS authentication failed: {e}")
            return False

    async def place_order(self, order_data: Dict) -> Dict:
        """Place order via FYERS"""
        # This would be implemented when order placement is needed
        # For now, return placeholder since we're in paper trading mode
        return {"order_id": "FY_12345", "status": "placed", "provider": "fyers"}

    async def get_positions(self) -> List[Dict]:
        """Get positions from FYERS"""
        # This would fetch real positions from Fyers API
        # For now, return empty list since we're focusing on market data
        return []

    async def get_portfolio(self) -> Dict:
        """Get portfolio from FYERS"""
        # This would fetch real portfolio from Fyers API
        # For now, return basic portfolio data
        if self.service.has_credentials():
            return {"total_value": 100000, "cash": 50000, "provider": "fyers", "status": "connected"}
        else:
            return {"error": "Not authenticated - missing access token", "provider": "fyers"}

    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data from FYERS using real API"""
        try:
            if not self.service.has_credentials():
                logger.warning("FYERS market data: missing credentials, returning demo data")
                return {symbol: {"price": 100.0, "source": "demo", "provider": "fyers"} for symbol in symbols}
            
            # Use real Fyers API service
            result = await self.service.get_market_data(symbols)
            
            if result.get('success'):
                # Transform to expected format
                transformed_data = {}
                for symbol, data in result['data'].items():
                    transformed_data[symbol] = {
                        "price": data.get('last_price', 0),
                        "change": data.get('change', 0),
                        "change_percent": data.get('change_percent', 0),
                        "volume": data.get('volume', 0),
                        "high": data.get('high', 0),
                        "low": data.get('low', 0),
                        "open": data.get('open', 0),
                        "timestamp": data.get('timestamp'),
                        "source": "fyers"
                    }
                return transformed_data
            else:
                logger.error(f"FYERS market data error: {result.get('error')}")
                return {symbol: {"price": None, "error": result.get('error'), "source": "fyers"} for symbol in symbols}
                
        except Exception as e:
            logger.error(f"FYERS market data exception: {e}")
            return {symbol: {"price": None, "error": str(e), "source": "fyers"} for symbol in symbols}

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order via FYERS"""
        # This would be implemented when order cancellation is needed
        return True


class UpstoxAPI(TradingAPIInterface):
    """UPSTOX API Implementation"""

    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with UPSTOX API"""
        try:
            # If an access token is already provided via env or credentials, use it
            access_token = credentials.get('access_token') or os.environ.get('UPSTOX_ACCESS_TOKEN')
            if access_token:
                self.auth_token = access_token
                # Note: Without expiry info, set a conservative expiry window
                self.token_expiry = datetime.now() + timedelta(hours=4)
                logger.info("UPSTOX authentication: using provided access token")
                return True

            # PKCE/OAuth flow would go here; for now, require pre-provisioned token
            logger.warning("UPSTOX authentication skipped: no access token provided. Set UPSTOX_ACCESS_TOKEN or pass credentials.")
            return False
        except Exception as e:
            logger.error(f"UPSTOX authentication failed: {e}")
            return False

    async def place_order(self, order_data: Dict) -> Dict:
        """Place order via UPSTOX"""
        # Implementation placeholder
        return {"order_id": "UP_12345", "status": "placed"}

    async def get_positions(self) -> List[Dict]:
        """Get positions from UPSTOX"""
        # Implementation placeholder
        return []

    async def get_portfolio(self) -> Dict:
        """Get portfolio from UPSTOX"""
        # Implementation placeholder
        return {"total_value": 100000, "cash": 50000}

    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data from UPSTOX"""
        # Feature flag: enable real live data when explicitly turned on
        live_enabled = os.environ.get('UPSTOX_LIVE_DATA_ENABLED', 'false').lower() == 'true'
        if not live_enabled:
            return {symbol: {"price": 100.0} for symbol in symbols}

        base_url = os.environ.get('UPSTOX_BASE_URL', 'https://api.upstox.com/v2')
        # Default instrument mapping (can be refined per symbol type)
        def to_instrument_key(sym: str) -> str:
            # Upstox instrument format example: NSE_EQ|RELIANCE
            return f"NSE_EQ|{sym}"

        instrument_keys = [to_instrument_key(s) for s in symbols]
        # API expects instrument_key param, allow comma-separated encoding of pipe
        instrument_param = ",".join(quote(k, safe='|') for k in instrument_keys)
        url = f"{base_url}/market-quote/ltp?instrument_key={instrument_param}"

        headers = {}
        token = self.auth_token or os.environ.get('UPSTOX_ACCESS_TOKEN')
        if token:
            headers['Authorization'] = f"Bearer {token}"

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        session = self.session or aiohttp.ClientSession(timeout=timeout)
        created_session = self.session is None

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 429:
                    # Rate limited - surface minimal info
                    logger.warning("UPSTOX rate limit hit (429) while fetching market data")
                    return {symbol: {"price": None, "error": "rate_limited"} for symbol in symbols}
                resp.raise_for_status()
                data = await resp.json()

                # Expected shape varies; normalize to {symbol: {"price": ltp}}
                result: Dict[str, Dict] = {}
                # Try common shapes: { 'data': { instrument_key: { 'ltp': value, ... } } }
                payload = data.get('data') if isinstance(data, dict) else None
                if isinstance(payload, dict):
                    inv_map = {to_instrument_key(s): s for s in symbols}
                    for key, md in payload.items():
                        symbol = inv_map.get(key)
                        if symbol:
                            ltp = md.get('ltp') if isinstance(md, dict) else None
                            result[symbol] = {"price": ltp}
                # Fallback: return placeholder if normalization failed
                if not result:
                    result = {symbol: {"price": None, "error": "unexpected_response"} for symbol in symbols}
                return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error fetching UPSTOX market data: {e}")
            return {symbol: {"price": None, "error": str(e)} for symbol in symbols}
        finally:
            if created_session:
                await session.close()

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order via UPSTOX (not used in PAPER mode)."""
        return True


class AliceBlueAPI(TradingAPIInterface):
    """Alice Blue API Implementation using AliceBlueAPIService"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        # Import the service here to avoid circular imports
        from services.aliceblue_api import aliceblue_service
        self.service = aliceblue_service

    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with Alice Blue API"""
        try:
            if self.service.has_credentials():
                self.auth_token = self.service.access_token
                self.token_expiry = datetime.now() + timedelta(hours=24)
                logger.info("Alice Blue authentication successful with existing token")
                return True
            else:
                logger.warning("Alice Blue authentication failed: missing access token")
                return False
        except Exception as e:
            logger.error(f"Alice Blue authentication failed: {e}")
            return False

    async def place_order(self, order_data: Dict) -> Dict:
        """Place order via Alice Blue"""
        # This would be implemented when order placement is needed
        # For now, return placeholder since we're in paper trading mode
        return {"order_id": "AB_12345", "status": "placed", "provider": "aliceblue"}

    async def get_positions(self) -> List[Dict]:
        """Get positions from Alice Blue"""
        # This would fetch real positions from Alice Blue API
        # For now, return empty list since we're focusing on market data
        return []

    async def get_portfolio(self) -> Dict:
        """Get portfolio from Alice Blue"""
        # This would fetch real portfolio from Alice Blue API
        # For now, return basic portfolio data
        if self.service.has_credentials():
            return {"total_value": 100000, "cash": 50000, "provider": "aliceblue", "status": "connected"}
        else:
            return {"error": "Not authenticated - missing access token", "provider": "aliceblue"}

    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data from Alice Blue using real API"""
        try:
            if not self.service.has_credentials():
                logger.warning("Alice Blue market data: missing credentials, returning demo data")
                return {symbol: {"price": 100.0, "source": "demo", "provider": "aliceblue"} for symbol in symbols}
            
            # Use real Alice Blue API service
            result = await self.service.get_market_data(symbols)
            
            if result.get('success'):
                # Transform to expected format
                transformed_data = {}
                for symbol, data in result['data'].items():
                    transformed_data[symbol] = {
                        "price": data.get('last_price', 0),
                        "change": data.get('change', 0),
                        "change_percent": data.get('change_percent', 0),
                        "volume": data.get('volume', 0),
                        "high": data.get('high', 0),
                        "low": data.get('low', 0),
                        "open": data.get('open', 0),
                        "timestamp": data.get('timestamp'),
                        "source": "aliceblue"
                    }
                return transformed_data
            else:
                logger.error(f"Alice Blue market data error: {result.get('error')}")
                return {symbol: {"price": None, "error": result.get('error'), "source": "aliceblue"} for symbol in symbols}
                
        except Exception as e:
            logger.error(f"Alice Blue market data exception: {e}")
            return {symbol: {"price": None, "error": str(e), "source": "aliceblue"} for symbol in symbols}

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order via Alice Blue"""
        # This would be implemented when order cancellation is needed
        return True


class IntelligentLoadBalancer:
    """Intelligent load balancing with performance-based routing and predictive analytics"""

    def __init__(self, apis: Dict[str, TradingAPIInterface]):
        self.apis = apis
        self.performance_metrics = {}
        self.routing_history: Deque[Dict[str, Any]] = deque(maxlen=1000)

    async def select_best_api(self, operation: str) -> str:
        """Select the best API using intelligent routing with performance metrics"""
        # Input validation
        if not operation or not isinstance(operation, str):
            raise ValueError("Operation must be a non-empty string")

        if not operation.strip():
            raise ValueError("Operation cannot be empty or whitespace only")

        # Filter available APIs
        available_apis = []
        for name, api in self.apis.items():
            if (api.health_status == HealthStatus.HEALTHY and
                not api.rate_limiter.is_rate_limited() and
                not api.rate_limiter.is_approaching_limit()):
                available_apis.append(name)

        if not available_apis:
            # Fallback to APIs that are healthy but approaching limits
            fallback_apis = [
                name for name, api in self.apis.items()
                if api.health_status == HealthStatus.HEALTHY and not api.rate_limiter.is_rate_limited()
            ]
            if fallback_apis:
                available_apis = fallback_apis
            else:
                raise Exception("No healthy APIs available")

        # Score APIs based on performance and current capacity
        api_scores = {}
        for api_name in available_apis:
            api = self.apis[api_name]
            score = await self._calculate_api_score(api_name, api, operation)
            api_scores[api_name] = score

        # Select API with highest score
        if not api_scores:
            raise Exception("No API scores calculated")
        best_api = max(api_scores, key=lambda k: api_scores[k])

        # Record routing decision
        self.routing_history.append({
            'timestamp': time.time(),
            'operation': operation,
            'selected_api': best_api,
            'available_apis': available_apis,
            'scores': api_scores
        })

        return best_api

    async def _calculate_api_score(self, api_name: str, api: TradingAPIInterface, operation: str) -> float:
        """Calculate comprehensive API score for routing decisions"""
        score = 0.0

        # Rate limit capacity score (0-40 points)
        rate_limit_status = api.rate_limiter.get_status()
        capacity_score = (1 - rate_limit_status['usage_percentages']['second_usage']) * 40
        score += capacity_score

        # Performance score (0-30 points)
        performance_score = self._get_performance_score(api_name, operation)
        score += performance_score * 30

        # Health score (0-20 points)
        health_score = 20 if api.health_status == HealthStatus.HEALTHY else 0
        score += health_score

        # Load balancing score (0-10 points) - prefer less used APIs
        recent_usage = self._get_recent_api_usage(api_name)
        load_score = max(0, 10 - recent_usage)
        score += load_score

        return score

    def _get_performance_score(self, api_name: str, operation: str) -> float:
        """Get performance score based on historical metrics"""
        if api_name not in self.performance_metrics:
            return 0.5  # Default score for new APIs

        metrics = self.performance_metrics[api_name].get(operation, {})

        # Calculate score based on response time and success rate
        avg_response_time = metrics.get('avg_response_time', 1000)  # ms
        success_rate = metrics.get('success_rate', 0.5)

        # Normalize response time (lower is better)
        response_score = max(0, (1000 - avg_response_time) / 1000)

        # Combined score
        return (response_score + success_rate) / 2

    def _get_recent_api_usage(self, api_name: str, window_seconds: int = 60) -> float:
        """Get recent API usage count for load balancing"""
        now = time.time()
        recent_usage = 0

        for routing in self.routing_history:
            if (now - routing['timestamp'] < window_seconds and
                routing['selected_api'] == api_name):
                recent_usage += 1

        return min(recent_usage / 10, 1.0)  # Normalize to 0-1

    def update_performance_metrics(self, api_name: str, operation: str,
                                 response_time: float, success: bool):
        """Update performance metrics for routing decisions"""
        if api_name not in self.performance_metrics:
            self.performance_metrics[api_name] = {}

        if operation not in self.performance_metrics[api_name]:
            self.performance_metrics[api_name][operation] = {
                'response_times': deque(maxlen=100),
                'success_count': 0,
                'total_count': 0
            }

        metrics = self.performance_metrics[api_name][operation]
        metrics['response_times'].append(response_time)
        metrics['total_count'] += 1

        if success:
            metrics['success_count'] += 1

        # Update calculated metrics
        metrics['avg_response_time'] = statistics.mean(metrics['response_times'])
        metrics['success_rate'] = metrics['success_count'] / metrics['total_count']

    def get_load_balancing_analytics(self) -> Dict[str, Any]:
        """Get load balancing analytics and insights"""
        if not self.routing_history:
            return {"error": "No routing history available"}

        recent_routings = list(self.routing_history)[-50:]  # Last 50 routing decisions

        # Calculate API distribution
        api_distribution = {}
        for routing in recent_routings:
            api_name = routing['selected_api']
            api_distribution[api_name] = api_distribution.get(api_name, 0) + 1

        # Calculate load balancing efficiency
        total_routings = len(recent_routings)
        if total_routings > 0:
            import math
            distribution_entropy = -sum(
                (count / total_routings) * math.log2(count / total_routings)
                for count in api_distribution.values()
            )
        else:
            distribution_entropy = 0

        return {
            "total_routings": total_routings,
            "api_distribution": api_distribution,
            "load_balance_efficiency": distribution_entropy,
            "performance_metrics": self.performance_metrics,
            "recent_selections": [r['selected_api'] for r in recent_routings[-10:]]
        }


# Alias for backward compatibility
LoadBalancer = IntelligentLoadBalancer


class HealthMonitor:
    """Health monitoring for all API connections"""

    def __init__(self, apis: Dict[str, TradingAPIInterface], interval: int = 30):
        self.apis = apis
        self.interval = interval
        self.monitoring_task = None
        self.health_statuses = {}

    async def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring_task:
            return

        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        logger.info("Health monitoring stopped")

    async def _monitor_loop(self):
        """Health monitoring loop"""
        while True:
            try:
                for api_name, api in self.apis.items():
                    await api.health_check()
                    self.health_statuses[api_name] = {
                        "status": api.health_status,
                        "last_check": api.last_health_check,
                        "rate_limits": api.get_rate_limits()
                    }

                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.interval)

    def get_health_status(self, api_name: str) -> Optional[Dict]:
        """Get health status for specific API"""
        return self.health_statuses.get(api_name)


class MultiAPIManager:
    """Manages multiple trading API connections with intelligent routing"""

    def __init__(self, config: Dict[str, Any], audit_logger=None):
        self.config = config
        self.audit_logger = audit_logger or MockAuditLogger()
        self.apis: Dict[str, TradingAPIInterface] = {}
        self.routing_rules = config.get('routing_rules', {})
        self.fallback_chain = config.get('fallback_chain', [])
        self.health_monitor = None
        self.load_balancer = None

    async def initialize_apis(self):
        """Initialize all configured API connections"""
        api_configs = {
            APIProvider.FLATTRADE.value: FlattradeAPI,
            APIProvider.FYERS.value: FyersAPI,
            APIProvider.UPSTOX.value: UpstoxAPI,
            APIProvider.ALICE_BLUE.value: AliceBlueAPI
        }

        for api_name, api_class in api_configs.items():
            if api_name in self.config.get('enabled_apis', []):
                api_config = APIConfig(
                    provider=APIProvider(api_name),
                    **self.config.get(api_name, {})
                )

                self.apis[api_name] = api_class(api_config)

                # Authenticate API
                credentials = self.config[api_name].get('credentials', {})
                if credentials:
                    await self.apis[api_name].authenticate(credentials)

        # Initialize health monitor and intelligent load balancer
        self.health_monitor = HealthMonitor(self.apis)
        self.load_balancer = IntelligentLoadBalancer(self.apis)

        # Start health monitoring
        await self.health_monitor.start_monitoring()

        logger.info(f"Initialized {len(self.apis)} APIs: {list(self.apis.keys())}")

    async def execute_with_fallback(self, operation: str, mode: Optional[TradingMode] = None, **kwargs) -> Any:
        """Execute operation with intelligent routing and automatic API fallback

        Enhanced with mode validation for paper trading safety
        """
        # LAYER 1: Mode routing/validation placed before try so ValueError is not swallowed
        if mode == TradingMode.PAPER:
            # Route to paper trading engine (imported at module level)
            if operation == "place_order":
                order = kwargs.get('order')
                user_id = kwargs.get('user_id', 'default')
                if order is None:
                    raise ValueError("Order data is required for place_order operation")
                result = await paper_trading_engine.execute_order(order, user_id)
                return result
            elif operation in ["get_positions", "get_portfolio"]:
                user_id = kwargs.get('user_id', 'default')
                return await paper_trading_engine.get_portfolio(user_id)
            else:
                # For market data operations, continue to real APIs
                pass

        # LAYER 2: Validate operation is allowed in current mode
        if mode and not self._is_operation_allowed(operation, mode):
            raise ValueError(f"Operation '{operation}' not allowed in {mode.value} mode")

        try:

            # Use intelligent load balancer to select best API
            if not self.load_balancer:
                raise APIOperationError("Load balancer not initialized")
            api_name = await self.load_balancer.select_best_api(operation)
            api = self.apis[api_name]

            start_time = time.time()

            # Record request for rate limiting
            api.rate_limiter.record_request()

            # Execute operation
            result = await getattr(api, operation)(**kwargs)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Update performance metrics
            if self.load_balancer:
                self.load_balancer.update_performance_metrics(
                    api_name, operation, response_time, True
                )

            # Log successful operation
            if self.audit_logger:
                await self.audit_logger.log_api_usage(
                    api_provider=api_name,
                    endpoint=operation,
                    request_type="POST",
                    status_code=200,
                    response_time_ms=response_time
                )

            logger.info(f"Operation {operation} successful via {api_name} in {response_time:.2f}ms")
            return result

        except Exception as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            api_name = api_name if 'api_name' in locals() else "unknown"

            # Update performance metrics for failure
            if api_name and self.load_balancer:
                self.load_balancer.update_performance_metrics(
                    api_name, operation, response_time, False
                )

                if self.audit_logger:
                    await self.audit_logger.log_api_usage(
                        api_provider=api_name,
                        endpoint=operation,
                        request_type="POST",
                        status_code=500,
                        response_time_ms=response_time
                    )

            logger.error(f"Operation {operation} failed: {e}")

            # Try fallback APIs if intelligent selection failed
            preferred_apis = self.routing_rules.get(operation, self.fallback_chain)

            for fallback_api_name in preferred_apis:
                if api_name and fallback_api_name == api_name:  # Skip already tried API
                    continue

                fallback_api = self.apis.get(fallback_api_name)
                if not fallback_api or not await fallback_api.health_check():
                    continue

                if fallback_api.rate_limiter.is_rate_limited():
                    continue

                try:
                    fallback_start_time = time.time()

                    # Record request for rate limiting
                    fallback_api.rate_limiter.record_request()

                    # Execute operation
                    result = await getattr(fallback_api, operation)(**kwargs)

                    # Calculate response time
                    fallback_response_time = (time.time() - fallback_start_time) * 1000

                    # Update performance metrics
                    self.load_balancer.update_performance_metrics(
                        fallback_api_name, operation, fallback_response_time, True
                    )

                    # Log successful fallback operation
                    await self.audit_logger.log_api_usage(
                        api_provider=fallback_api_name,
                        endpoint=operation,
                        request_type="POST",
                        status_code=200,
                        response_time_ms=fallback_response_time
                    )

                    logger.info(f"Operation {operation} successful via fallback {fallback_api_name} in {fallback_response_time:.2f}ms")
                    return result

                except Exception as fallback_e:
                    fallback_response_time = (time.time() - fallback_start_time) * 1000 if 'fallback_start_time' in locals() else 0

                    # Update performance metrics for failure
                    if self.load_balancer:
                        self.load_balancer.update_performance_metrics(
                            fallback_api_name, operation, fallback_response_time, False
                        )

                    await self.audit_logger.log_api_usage(
                        api_provider=fallback_api_name,
                        endpoint=operation,
                        request_type="POST",
                        status_code=500,
                        response_time_ms=fallback_response_time
                    )

                    logger.error(f"Fallback API {fallback_api_name} failed for operation {operation}: {fallback_e}")
                    continue

            raise APIOperationError(f"All APIs failed for operation: {operation}") from e

    def _is_operation_allowed(self, operation: str, mode: TradingMode) -> bool:
        """Check if operation is allowed in the given mode"""
        # Define operations that are restricted in paper mode
        paper_restricted_operations = [
            'transfer_funds',
            'withdraw_funds',
            'modify_bank_details'
        ]

        # Define operations that are restricted in live mode (if any)
        live_restricted_operations = []

        if mode == TradingMode.PAPER:
            return operation not in paper_restricted_operations
        elif mode == TradingMode.LIVE:
            return operation not in live_restricted_operations

        return True

    async def get_health_status(self) -> Dict[str, Dict]:
        """Get health status for all APIs"""
        if not self.health_monitor:
            return {}
        return self.health_monitor.health_statuses

    async def get_rate_limit_analytics(self) -> Dict[str, Any]:
        """Get comprehensive rate limit analytics for all APIs"""
        analytics = {}

        for api_name, api in self.apis.items():
            analytics[api_name] = {
                'rate_limit_status': api.rate_limiter.get_status(),
                'predictive_analytics': api.rate_limiter.get_analytics()
            }

        return analytics

    async def get_load_balancing_insights(self) -> Dict[str, Any]:
        """Get load balancing insights and performance metrics"""
        if not self.load_balancer:
            return {}
        return self.load_balancer.get_load_balancing_analytics()

    async def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on current performance"""
        suggestions = []

        # Get current analytics
        rate_analytics = await self.get_rate_limit_analytics()
        load_analytics = await self.get_load_balancing_insights()

        # Analyze each API for optimization opportunities
        for api_name, api_analytics in rate_analytics.items():
            rate_status = api_analytics['rate_limit_status']
            predictive = api_analytics['predictive_analytics']

            # Check for high usage APIs
            if rate_status['usage_percentages']['second_usage'] > 0.7:
                suggestions.append({
                    'type': 'high_usage_warning',
                    'api': api_name,
                    'message': f"{api_name} is using {rate_status['usage_percentages']['second_usage']*100:.1f}% of rate limit",
                    'recommendation': 'Consider load balancing to other APIs or implement request queuing'
                })

            # Check for approaching limits
            if rate_status['approaching_limit']:
                suggestions.append({
                    'type': 'approaching_limit',
                    'api': api_name,
                    'message': f"{api_name} is approaching rate limit threshold",
                    'recommendation': 'Switch to alternative API or reduce request frequency'
                })

            # Check for spike predictions
            if predictive.get('trend', 0) > 0.2:
                suggestions.append({
                    'type': 'usage_spike_prediction',
                    'api': api_name,
                    'message': f"Usage spike predicted for {api_name} (trend: {predictive['trend']:.2f})",
                    'recommendation': 'Prepare alternative routing or implement preemptive load balancing'
                })

        # Load balancing suggestions
        if load_analytics.get('load_balance_efficiency', 0) < 0.5:
            suggestions.append({
                'type': 'load_balancing_inefficiency',
                'message': 'Load balancing efficiency is low',
                'recommendation': 'Review routing algorithms and API performance metrics'
            })

        return suggestions


    async def shutdown(self):
        """Shutdown API manager"""
        if self.health_monitor:
            await self.health_monitor.stop_monitoring()

        for api in self.apis.values():
            if api.session:
                await api.session.close()

        logger.info("MultiAPIManager shutdown complete")


class MockAuditLogger:
    def log_api_usage(self, api_provider: str, endpoint: str, request_type: str, status_code: int, response_time_ms: float):
        logger.debug(
            f"MockAuditLogger: provider={api_provider} endpoint={endpoint} "
            f"type={request_type} status={status_code} rt={response_time_ms:.2f}ms"
        )
