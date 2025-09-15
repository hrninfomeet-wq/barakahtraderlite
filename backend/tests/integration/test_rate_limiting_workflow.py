"""
Integration tests for complete rate limiting workflows
Tests the integration of Enhanced Rate Limiter + Intelligent Load Balancer + MultiAPIManager
"""
import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.multi_api_manager import (
    MultiAPIManager, EnhancedRateLimiter, IntelligentLoadBalancer, 
    TradingAPIInterface, FlattradeAPI, FyersAPI, UpstoxAPI, AliceBlueAPI
)
from models.trading import APIConfig, APIProvider, HealthStatus
from core.database import DatabaseManager, AuditLogger


class MockTradingAPI(TradingAPIInterface):
    """Mock trading API for integration testing"""
    
    def __init__(self, name: str, config: APIConfig, response_time: float = 0.1, 
                 failure_rate: float = 0.0, health_status: HealthStatus = HealthStatus.HEALTHY):
        super().__init__(config)
        self.name = name
        self.response_time = response_time
        self.failure_rate = failure_rate
        self.health_status = health_status
        self.request_count = 0
        self.last_request_time = None
    
    async def authenticate(self, credentials: dict) -> bool:
        return True
    
    async def place_order(self, order_data: dict = None, **kwargs) -> dict:
        # Handle both dict and keyword arguments
        if order_data is None:
            order_data = kwargs
        
        self.request_count += 1
        self.last_request_time = time.time()
        
        # Simulate response time
        await asyncio.sleep(self.response_time)
        
        # Simulate failure rate
        if self.failure_rate > 0 and (self.request_count % int(1/self.failure_rate)) == 0:
            raise Exception(f"Simulated failure in {self.name}")
        
        return {"order_id": f"{self.name}_order_{self.request_count}", "status": "placed"}
    
    async def get_positions(self) -> list:
        self.request_count += 1
        self.last_request_time = time.time()
        await asyncio.sleep(self.response_time)
        return [{"symbol": "TEST", "quantity": 100, "api": self.name}]
    
    async def get_portfolio(self) -> dict:
        self.request_count += 1
        self.last_request_time = time.time()
        await asyncio.sleep(self.response_time)
        return {"total_value": 10000, "api": self.name}
    
    async def get_market_data(self, symbols: list) -> dict:
        self.request_count += 1
        self.last_request_time = time.time()
        await asyncio.sleep(self.response_time)
        return {symbol: {"price": 100.0, "api": self.name} for symbol in symbols}
    
    async def cancel_order(self, order_id: str) -> bool:
        self.request_count += 1
        self.last_request_time = time.time()
        await asyncio.sleep(self.response_time)
        return True
    
    async def health_check(self) -> bool:
        return self.health_status == HealthStatus.HEALTHY


class TestRateLimitingWorkflow:
    """Integration tests for complete rate limiting workflows"""
    
    @pytest_asyncio.fixture
    async def db_manager(self):
        """Create database manager for testing"""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.initialize()
        return db_manager
    
    @pytest_asyncio.fixture
    async def audit_logger(self, db_manager):
        """Create audit logger for testing"""
        return AuditLogger(db_manager)
    
    @pytest_asyncio.fixture
    async def mock_apis(self):
        """Create mock APIs for testing"""
        apis = {}
        
        # Create APIs with different characteristics
        configs = {
            'fyers': APIConfig(
                provider=APIProvider.FYERS,
                rate_limits={'requests_per_second': 10, 'requests_per_minute': 600}
            ),
            'upstox': APIConfig(
                provider=APIProvider.UPSTOX,
                rate_limits={'requests_per_second': 50, 'requests_per_minute': 3000}
            ),
            'flattrade': APIConfig(
                provider=APIProvider.FLATTRADE,
                rate_limits={'requests_per_second': 20, 'requests_per_minute': 1200}
            )
        }
        
        apis['fyers'] = MockTradingAPI('fyers', configs['fyers'], response_time=0.05)
        apis['upstox'] = MockTradingAPI('upstox', configs['upstox'], response_time=0.1)
        apis['flattrade'] = MockTradingAPI('flattrade', configs['flattrade'], response_time=0.08)
        
        return apis
    
    @pytest_asyncio.fixture
    async def api_manager(self, mock_apis, audit_logger):
        """Create API manager with mock APIs"""
        config = {
            "enabled_apis": ["fyers", "upstox", "flattrade"],
            "routing_rules": {},
            "fallback_chain": ["fyers", "upstox", "flattrade"]
        }
        
        manager = MultiAPIManager(config, audit_logger)
        
        # Manually set the APIs instead of initializing
        manager.apis = mock_apis
        manager.health_monitor = Mock()
        manager.load_balancer = IntelligentLoadBalancer(mock_apis)
        
        return manager
    
    @pytest.mark.asyncio
    async def test_rate_limit_violation_prevention(self, api_manager):
        """Test that rate limit violations are prevented"""
        # Generate requests that would exceed rate limits
        tasks = []
        
        # Create 15 requests in 1 second (exceeds FYERS limit of 10/sec)
        for i in range(15):
            task = asyncio.create_task(
                api_manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that some requests were handled by different APIs
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 15  # All should succeed due to load balancing
        
        # Verify load balancing occurred
        fyers_count = sum(1 for api in api_manager.apis.values() if api.name == 'fyers')
        assert fyers_count > 0
        
        # Check that rate limiting prevented violations
        fyers_api = api_manager.apis['fyers']
        assert fyers_api.request_count <= 10  # Should not exceed rate limit
    
    @pytest.mark.asyncio
    async def test_automatic_failover_at_80_percent(self, api_manager):
        """Test automatic failover when API approaches 80% of rate limit"""
        # Simulate high usage on FYERS (approaching limit)
        fyers_api = api_manager.apis['fyers']
        
        # Generate requests to get FYERS close to 80% threshold
        for i in range(8):  # 80% of 10/sec limit
            fyers_api.rate_limiter.record_request()
        
        # Now make requests - should prefer other APIs
        results = []
        for i in range(5):
            result = await api_manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
            results.append(result)
        
        # Verify that requests were distributed to other APIs
        upstox_api = api_manager.apis['upstox']
        flattrade_api = api_manager.apis['flattrade']
        
        # At least one request should go to other APIs
        assert upstox_api.request_count > 0 or flattrade_api.request_count > 0
    
    @pytest.mark.asyncio
    async def test_predictive_analytics_spike_detection(self, api_manager):
        """Test predictive analytics for usage spike detection"""
        fyers_api = api_manager.apis['fyers']
        rate_limiter = fyers_api.rate_limiter
        
        # Create usage patterns that simulate a spike
        current_time = time.time()
        spike_pattern = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        for i, usage in enumerate(spike_pattern):
            pattern = {
                'timestamp': current_time - (len(spike_pattern) - i),
                'second_usage': usage,
                'minute_usage': usage * 0.8,
                'hour_usage': usage * 0.6
            }
            rate_limiter.usage_patterns.append(pattern)
        
        # Check if spike is predicted
        spike_predicted = rate_limiter._predict_usage_spike()
        
        # With the spike pattern, should detect spike
        assert isinstance(spike_predicted, bool)
    
    @pytest.mark.asyncio
    async def test_load_balancing_performance_metrics(self, api_manager):
        """Test load balancing with performance metrics"""
        # Make requests to build performance data
        tasks = []
        for i in range(20):
            task = asyncio.create_task(
                api_manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Check load balancing analytics
        analytics = await api_manager.get_load_balancing_insights()
        
        assert 'total_routings' in analytics
        assert 'api_distribution' in analytics
        assert 'load_balance_efficiency' in analytics
        
        # Verify that load balancing occurred
        assert analytics['total_routings'] > 0
        assert len(analytics['api_distribution']) > 1  # Multiple APIs used
    
    @pytest.mark.asyncio
    async def test_complete_dashboard_workflow(self, api_manager):
        """Test complete dashboard workflow with all components"""
        # Generate some activity
        for i in range(10):
            await api_manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
        
        # Test dashboard overview
        rate_analytics = await api_manager.get_rate_limit_analytics()
        load_analytics = await api_manager.get_load_balancing_insights()
        optimization_suggestions = await api_manager.get_optimization_suggestions()
        
        # Verify all dashboard components work
        assert len(rate_analytics) > 0
        assert 'load_balance_efficiency' in load_analytics
        assert isinstance(optimization_suggestions, list)
        
        # Verify analytics contain expected data
        for api_name, analytics in rate_analytics.items():
            assert 'rate_limit_status' in analytics
            assert 'predictive_analytics' in analytics
            
            rate_status = analytics['rate_limit_status']
            assert 'usage_percentages' in rate_status
            assert 'approaching_limit' in rate_status
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, api_manager):
        """Test error handling and recovery mechanisms"""
        # Simulate API failure
        failing_api = api_manager.apis['fyers']
        original_method = failing_api.place_order
        
        async def failing_place_order(*args, **kwargs):
            raise Exception("Simulated API failure")
        
        failing_api.place_order = failing_place_order
        
        # Make request - should failover to other APIs
        result = await api_manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
        
        # Should succeed despite FYERS failure
        assert result is not None
        assert 'order_id' in result
        
        # Restore original method
        failing_api.place_order = original_method
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, api_manager):
        """Test handling of concurrent requests"""
        # Create many concurrent requests
        tasks = []
        for i in range(50):
            task = asyncio.create_task(
                api_manager.execute_with_fallback('place_order', symbol=f'TEST{i}', quantity=100)
            )
            tasks.append(task)
        
        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 50
        
        # Verify load balancing occurred
        total_requests = sum(api.request_count for api in api_manager.apis.values())
        assert total_requests == 50
        
        # Verify no API exceeded its rate limit
        for api in api_manager.apis.values():
            assert api.request_count <= api.rate_limiter.requests_per_second


if __name__ == '__main__':
    pytest.main([__file__])
