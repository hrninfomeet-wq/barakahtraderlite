"""
Unit tests for MultiAPIManager and related components
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.trading import APIProvider, APIConfig, HealthStatus
from services.multi_api_manager import (
    EnhancedRateLimiter as RateLimiter, TradingAPIInterface, MultiAPIManager, 
    HealthMonitor, IntelligentLoadBalancer as LoadBalancer
)


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(requests_per_second=10)
        
        assert limiter.requests_per_second == 10
        assert limiter.requests_per_minute == 600
        assert limiter.requests_per_hour == 36000
    
    def test_is_rate_limited_false(self):
        """Test rate limiter when not limited"""
        limiter = RateLimiter(requests_per_second=10)
        
        # Should not be rate limited initially
        assert limiter.is_rate_limited() is False
    
    def test_is_rate_limited_true(self):
        """Test rate limiter when limited"""
        limiter = RateLimiter(requests_per_second=1)
        
        # Record one request
        limiter.record_request()
        
        # Should be rate limited after exceeding limit
        assert limiter.is_rate_limited() is True
    
    def test_get_status(self):
        """Test getting rate limit status"""
        limiter = RateLimiter(requests_per_second=10)
        
        status = limiter.get_status()
        
        assert "requests_per_second" in status
        assert "current_second" in status
        assert status["requests_per_second"] == 10
        assert status["current_second"] == 0


class MockAPI(TradingAPIInterface):
    """Mock API implementation for testing"""
    
    def __init__(self, config: APIConfig, should_fail_health: bool = False):
        super().__init__(config)
        self.should_fail_health = should_fail_health
        self.authenticated = False
    
    async def authenticate(self, credentials: dict) -> bool:
        self.authenticated = True
        return True
    
    async def place_order(self, order_data: dict) -> dict:
        return {"order_id": "test_123", "status": "placed"}
    
    async def get_positions(self) -> list:
        return []
    
    async def get_portfolio(self) -> dict:
        if self.should_fail_health:
            raise Exception("Health check failed")
        return {"total_value": 100000}
    
    async def get_market_data(self, symbols: list) -> dict:
        return {symbol: {"price": 100.0} for symbol in symbols}
    
    async def cancel_order(self, order_id: str) -> bool:
        return True


class TestTradingAPIInterface:
    """Test TradingAPIInterface functionality"""
    
    @pytest.fixture
    def api_config(self):
        """Create test API config"""
        return APIConfig(
            provider=APIProvider.FLATTRADE,
            rate_limits={"requests_per_second": 10}
        )
    
    @pytest.fixture
    def mock_api(self, api_config):
        """Create mock API instance"""
        return MockAPI(api_config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self, mock_api):
        """Test API authentication"""
        credentials = {"api_key": "test", "api_secret": "secret"}
        
        result = await mock_api.authenticate(credentials)
        
        assert result is True
        assert mock_api.authenticated is True
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_api):
        """Test successful health check"""
        result = await mock_api.health_check()
        
        assert result is True
        assert mock_api.health_status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, api_config):
        """Test failed health check"""
        mock_api = MockAPI(api_config, should_fail_health=True)
        
        result = await mock_api.health_check()
        
        assert result is False
        assert mock_api.health_status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_rate_limits(self, mock_api):
        """Test getting rate limits"""
        limits = mock_api.get_rate_limits()
        
        assert "requests_per_second" in limits
        assert limits["requests_per_second"] == 10


class TestLoadBalancer:
    """Test LoadBalancer functionality"""
    
    @pytest.fixture
    def healthy_apis(self):
        """Create healthy APIs for testing"""
        config1 = APIConfig(provider=APIProvider.FLATTRADE, rate_limits={"requests_per_second": 10})
        config2 = APIConfig(provider=APIProvider.FYERS, rate_limits={"requests_per_second": 10})
        
        api1 = MockAPI(config1)
        api1.health_status = HealthStatus.HEALTHY
        
        api2 = MockAPI(config2)
        api2.health_status = HealthStatus.HEALTHY
        
        return {"flattrade": api1, "fyers": api2}
    
    @pytest.mark.asyncio
    async def test_select_best_api(self, healthy_apis):
        """Test selecting best API"""
        load_balancer = LoadBalancer(healthy_apis)
        
        selected_api = await load_balancer.select_best_api("get_portfolio")
        
        assert selected_api in ["flattrade", "fyers"]
    
    @pytest.mark.asyncio
    async def test_select_best_api_no_healthy(self):
        """Test selecting API when none are healthy"""
        unhealthy_apis = {
            "api1": MockAPI(APIConfig(provider=APIProvider.FLATTRADE)),
            "api2": MockAPI(APIConfig(provider=APIProvider.FYERS))
        }
        
        load_balancer = LoadBalancer(unhealthy_apis)
        
        with pytest.raises(Exception, match="No healthy APIs available"):
            await load_balancer.select_best_api("get_portfolio")


class TestHealthMonitor:
    """Test HealthMonitor functionality"""
    
    @pytest.fixture
    def test_apis(self):
        """Create test APIs for monitoring"""
        config1 = APIConfig(provider=APIProvider.FLATTRADE, rate_limits={"requests_per_second": 10})
        config2 = APIConfig(provider=APIProvider.FYERS, rate_limits={"requests_per_second": 10})
        
        return {
            "flattrade": MockAPI(config1),
            "fyers": MockAPI(config2)
        }
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, test_apis):
        """Test starting and stopping health monitoring"""
        monitor = HealthMonitor(test_apis, interval=1)
        
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.monitoring_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.monitoring_task is None
    
    def test_get_health_status(self, test_apis):
        """Test getting health status"""
        monitor = HealthMonitor(test_apis)
        
        # Manually set health status
        monitor.health_statuses = {
            "flattrade": {
                "status": HealthStatus.HEALTHY,
                "last_check": datetime.now(),
                "rate_limits": {"current_second": 5}
            }
        }
        
        status = monitor.get_health_status("flattrade")
        
        assert status is not None
        assert status["status"] == HealthStatus.HEALTHY


class TestMultiAPIManager:
    """Test MultiAPIManager functionality"""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger"""
        logger = Mock()
        logger.log_api_usage = AsyncMock(return_value=True)
        return logger
    
    @pytest.fixture
    def api_manager_config(self):
        """Create API manager configuration"""
        return {
            "enabled_apis": ["flattrade", "fyers"],
            "routing_rules": {
                "get_portfolio": ["flattrade", "fyers"]
            },
            "fallback_chain": ["flattrade", "fyers"],
            "flattrade": {
                "rate_limits": {"requests_per_second": 10}
            },
            "fyers": {
                "rate_limits": {"requests_per_second": 10}
            }
        }
    
    @pytest.mark.asyncio
    async def test_initialize_apis(self, api_manager_config, mock_audit_logger):
        """Test initializing APIs"""
        with patch('backend.services.multi_api_manager.FlattradeAPI', MockAPI), \
             patch('backend.services.multi_api_manager.FyersAPI', MockAPI):
            
            manager = MultiAPIManager(api_manager_config, mock_audit_logger)
            await manager.initialize_apis()
            
            assert len(manager.apis) == 2
            assert "flattrade" in manager.apis
            assert "fyers" in manager.apis
            assert manager.health_monitor is not None
            assert manager.load_balancer is not None
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self, api_manager_config, mock_audit_logger):
        """Test successful operation execution"""
        with patch('backend.services.multi_api_manager.FlattradeAPI', MockAPI), \
             patch('backend.services.multi_api_manager.FyersAPI', MockAPI):
            
            manager = MultiAPIManager(api_manager_config, mock_audit_logger)
            await manager.initialize_apis()
            
            result = await manager.execute_with_fallback("get_portfolio")
            
            assert result == {"total_value": 100000, "cash": 50000}
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_failure(self, api_manager_config, mock_audit_logger):
        """Test operation execution when all APIs fail"""
        with patch('backend.services.multi_api_manager.FlattradeAPI', MockAPI), \
             patch('backend.services.multi_api_manager.FyersAPI', MockAPI):
            
            manager = MultiAPIManager(api_manager_config, mock_audit_logger)
            await manager.initialize_apis()
            
            # Make all APIs unhealthy by mocking health_check to return False
            for api in manager.apis.values():
                api.health_check = AsyncMock(return_value=False)
            
            with pytest.raises(Exception, match="All APIs failed for operation"):
                await manager.execute_with_fallback("get_portfolio")
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, api_manager_config, mock_audit_logger):
        """Test getting health status"""
        with patch('backend.services.multi_api_manager.FlattradeAPI', MockAPI), \
             patch('backend.services.multi_api_manager.FyersAPI', MockAPI):
            
            manager = MultiAPIManager(api_manager_config, mock_audit_logger)
            await manager.initialize_apis()
            
            health_status = await manager.get_health_status()
            
            assert isinstance(health_status, dict)
    
    @pytest.mark.asyncio
    async def test_shutdown(self, api_manager_config, mock_audit_logger):
        """Test API manager shutdown"""
        with patch('backend.services.multi_api_manager.FlattradeAPI', MockAPI), \
             patch('backend.services.multi_api_manager.FyersAPI', MockAPI):
            
            manager = MultiAPIManager(api_manager_config, mock_audit_logger)
            await manager.initialize_apis()
            
            await manager.shutdown()
            
            # Verify health monitor was stopped
            assert manager.health_monitor.monitoring_task is None


if __name__ == "__main__":
    pytest.main([__file__])
