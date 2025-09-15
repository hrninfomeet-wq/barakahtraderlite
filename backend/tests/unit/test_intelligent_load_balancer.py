"""
Unit tests for Intelligent Load Balancer
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from collections import deque

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.multi_api_manager import IntelligentLoadBalancer, TradingAPIInterface, EnhancedRateLimiter
from models.trading import HealthStatus, APIConfig, APIProvider


class MockAPI(TradingAPIInterface):
    """Mock API for testing"""
    
    def __init__(self, name: str, health_status: HealthStatus = HealthStatus.HEALTHY, 
                 rate_limit_status: bool = False, approaching_limit: bool = False):
        config = APIConfig(
            provider=APIProvider.FLATTRADE,
            rate_limits={'requests_per_second': 10, 'requests_per_minute': 600}
        )
        super().__init__(config)
        self.name = name
        self.health_status = health_status
        self._rate_limit_status = rate_limit_status
        self._approaching_limit = approaching_limit
        
        # Override rate limiter with mock behavior
        self.rate_limiter = Mock()
        self.rate_limiter.is_rate_limited.return_value = rate_limit_status
        self.rate_limiter.is_approaching_limit.return_value = approaching_limit
        self.rate_limiter.get_status.return_value = {
            'usage_percentages': {'second_usage': 0.5}
        }
    
    async def authenticate(self, credentials: dict) -> bool:
        return True
    
    async def place_order(self, order_data: dict) -> dict:
        return {"order_id": f"{self.name}_123", "status": "placed"}
    
    async def get_positions(self) -> list:
        return []
    
    async def get_portfolio(self) -> dict:
        return {"total_value": 100000}
    
    async def get_market_data(self, symbols: list) -> dict:
        return {symbol: {"price": 100.0} for symbol in symbols}
    
    async def cancel_order(self, order_id: str) -> bool:
        return True
    
    async def health_check(self) -> bool:
        return self.health_status == HealthStatus.HEALTHY


class TestIntelligentLoadBalancer:
    """Test cases for Intelligent Load Balancer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.apis = {
            'api1': MockAPI('api1', HealthStatus.HEALTHY, False, False),
            'api2': MockAPI('api2', HealthStatus.HEALTHY, False, False),
            'api3': MockAPI('api3', HealthStatus.UNHEALTHY, True, False),
        }
        self.load_balancer = IntelligentLoadBalancer(self.apis)
    
    @pytest.mark.asyncio
    async def test_select_best_api_basic(self):
        """Test basic API selection"""
        selected_api = await self.load_balancer.select_best_api('place_order')
        
        # Should select one of the healthy APIs
        assert selected_api in ['api1', 'api2']
        assert selected_api != 'api3'  # Should not select unhealthy API
    
    @pytest.mark.asyncio
    async def test_select_best_api_with_rate_limits(self):
        """Test API selection considering rate limits"""
        # Make api1 rate limited
        self.apis['api1'].rate_limiter.is_rate_limited.return_value = True
        
        selected_api = await self.load_balancer.select_best_api('place_order')
        
        # Should select api2 (not rate limited)
        assert selected_api == 'api2'
    
    @pytest.mark.asyncio
    async def test_select_best_api_approaching_limits(self):
        """Test API selection considering approaching limits"""
        # Make api1 approaching limits
        self.apis['api1'].rate_limiter.is_approaching_limit.return_value = True
        
        selected_api = await self.load_balancer.select_best_api('place_order')
        
        # Should select api2 (not approaching limits)
        assert selected_api == 'api2'
    
    @pytest.mark.asyncio
    async def test_select_best_api_fallback(self):
        """Test fallback when no ideal APIs available"""
        # Make all APIs approaching limits but not rate limited
        for api in self.apis.values():
            api.rate_limiter.is_approaching_limit.return_value = True
        
        selected_api = await self.load_balancer.select_best_api('place_order')
        
        # Should still select a healthy API
        assert selected_api in ['api1', 'api2']
    
    @pytest.mark.asyncio
    async def test_select_best_api_no_available(self):
        """Test when no APIs are available"""
        # Make all APIs unhealthy
        for api in self.apis.values():
            api.health_status = HealthStatus.UNHEALTHY
        
        with pytest.raises(Exception, match="No healthy APIs available"):
            await self.load_balancer.select_best_api('place_order')
    
    def test_calculate_api_score(self):
        """Test API score calculation"""
        api = self.apis['api1']
        
        score = asyncio.run(self.load_balancer._calculate_api_score('api1', api, 'place_order'))
        
        # Score should be positive
        assert score > 0
        assert isinstance(score, float)
    
    def test_get_performance_score_default(self):
        """Test performance score for new APIs"""
        score = self.load_balancer._get_performance_score('new_api', 'place_order')
        
        # Should return default score for new APIs
        assert score == 0.5
    
    def test_get_performance_score_with_metrics(self):
        """Test performance score with existing metrics"""
        # Add performance metrics
        self.load_balancer.performance_metrics['api1'] = {
            'place_order': {
                'avg_response_time': 500,  # 500ms
                'success_rate': 0.9
            }
        }
        
        score = self.load_balancer._get_performance_score('api1', 'place_order')
        
        # Should calculate score based on metrics
        assert score > 0.5  # Should be higher than default
        assert score <= 1.0
    
    def test_get_recent_api_usage(self):
        """Test recent API usage tracking"""
        # Add some routing history
        current_time = time.time()
        for i in range(5):
            self.load_balancer.routing_history.append({
                'timestamp': current_time - (5 - i) * 10,  # 10 seconds apart
                'selected_api': 'api1',
                'operation': 'place_order'
            })
        
        usage = self.load_balancer._get_recent_api_usage('api1')
        
        # Should calculate recent usage
        assert usage > 0
        assert usage <= 1.0
    
    def test_update_performance_metrics(self):
        """Test performance metrics updating"""
        # Update metrics for a new API
        self.load_balancer.update_performance_metrics('new_api', 'place_order', 300.0, True)
        
        # Check metrics were recorded
        assert 'new_api' in self.load_balancer.performance_metrics
        assert 'place_order' in self.load_balancer.performance_metrics['new_api']
        
        metrics = self.load_balancer.performance_metrics['new_api']['place_order']
        assert metrics['total_count'] == 1
        assert metrics['success_count'] == 1
        assert metrics['avg_response_time'] == 300.0
        assert metrics['success_rate'] == 1.0
    
    def test_update_performance_metrics_multiple(self):
        """Test performance metrics with multiple updates"""
        # Add multiple metrics
        self.load_balancer.update_performance_metrics('api1', 'place_order', 200.0, True)
        self.load_balancer.update_performance_metrics('api1', 'place_order', 400.0, True)
        self.load_balancer.update_performance_metrics('api1', 'place_order', 300.0, False)
        
        metrics = self.load_balancer.performance_metrics['api1']['place_order']
        
        assert metrics['total_count'] == 3
        assert metrics['success_count'] == 2
        assert metrics['success_rate'] == 2/3
        assert metrics['avg_response_time'] == 300.0  # (200+400+300)/3
    
    def test_get_load_balancing_analytics_empty(self):
        """Test analytics with no routing history"""
        analytics = self.load_balancer.get_load_balancing_analytics()
        
        assert 'error' in analytics
        assert analytics['error'] == 'No routing history available'
    
    def test_get_load_balancing_analytics_with_data(self):
        """Test analytics with routing history"""
        # Add routing history
        current_time = time.time()
        for i in range(20):
            self.load_balancer.routing_history.append({
                'timestamp': current_time - (20 - i),
                'operation': 'place_order',
                'selected_api': 'api1' if i < 12 else 'api2',
                'available_apis': ['api1', 'api2'],
                'scores': {'api1': 0.8, 'api2': 0.6}
            })
        
        analytics = self.load_balancer.get_load_balancing_analytics()
        
        assert 'total_routings' in analytics
        assert 'api_distribution' in analytics
        assert 'load_balance_efficiency' in analytics
        assert 'recent_selections' in analytics
        
        assert analytics['total_routings'] == 20
        assert 'api1' in analytics['api_distribution']
        assert 'api2' in analytics['api_distribution']
        assert analytics['api_distribution']['api1'] == 12
        assert analytics['api_distribution']['api2'] == 8
    
    @pytest.mark.asyncio
    async def test_routing_history_recording(self):
        """Test that routing decisions are recorded"""
        initial_history_length = len(self.load_balancer.routing_history)
        
        await self.load_balancer.select_best_api('place_order')
        
        # Should have recorded the routing decision
        assert len(self.load_balancer.routing_history) == initial_history_length + 1
        
        last_routing = self.load_balancer.routing_history[-1]
        assert 'timestamp' in last_routing
        assert 'operation' in last_routing
        assert 'selected_api' in last_routing
        assert 'available_apis' in last_routing
        assert 'scores' in last_routing
        
        assert last_routing['operation'] == 'place_order'
        assert last_routing['selected_api'] in ['api1', 'api2']
    
    def test_performance_metrics_deque_limit(self):
        """Test that performance metrics deques respect maxlen"""
        # Add many response times
        for i in range(150):
            self.load_balancer.update_performance_metrics('api1', 'place_order', i * 10.0, True)
        
        metrics = self.load_balancer.performance_metrics['api1']['place_order']
        
        # Should respect maxlen of 100
        assert len(metrics['response_times']) == 100
        assert metrics['total_count'] == 150  # Total count should still be accurate
        assert metrics['success_count'] == 150
    
    def test_api_score_components(self):
        """Test different components of API scoring"""
        api = self.apis['api1']
        
        # Test with different rate limit usage
        api.rate_limiter.get_status.return_value = {
            'usage_percentages': {'second_usage': 0.2}  # 20% usage
        }
        
        score = asyncio.run(self.load_balancer._calculate_api_score('api1', api, 'place_order'))
        
        # Should get high capacity score (80% of 40 points = 32 points)
        assert score > 30  # Should be high due to low usage
    
    def test_load_balancing_efficiency_calculation(self):
        """Test load balancing efficiency calculation"""
        # Create balanced distribution
        current_time = time.time()
        for i in range(20):
            api_name = 'api1' if i % 2 == 0 else 'api2'
            self.load_balancer.routing_history.append({
                'timestamp': current_time - (20 - i),
                'operation': 'place_order',
                'selected_api': api_name,
                'available_apis': ['api1', 'api2'],
                'scores': {'api1': 0.8, 'api2': 0.8}
            })
        
        analytics = self.load_balancer.get_load_balancing_analytics()
        
        # Should have good efficiency with balanced distribution
        assert analytics['load_balance_efficiency'] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_api_selection(self):
        """Test concurrent API selection"""
        async def select_api():
            return await self.load_balancer.select_best_api('place_order')
        
        # Run multiple concurrent selections
        tasks = [select_api() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All selections should be valid
        for result in results:
            assert result in ['api1', 'api2']
        
        # Should have recorded all routing decisions
        assert len(self.load_balancer.routing_history) == 10


class TestIntelligentLoadBalancerIntegration:
    """Integration tests for Intelligent Load Balancer"""
    
    def test_performance_metrics_accuracy(self):
        """Test accuracy of performance metrics over time"""
        load_balancer = IntelligentLoadBalancer({})
        
        # Simulate realistic performance data
        response_times = [100, 150, 120, 200, 180, 110, 160, 140, 130, 170]
        successes = [True, True, True, False, True, True, False, True, True, True]
        
        for rt, success in zip(response_times, successes):
            load_balancer.update_performance_metrics('test_api', 'place_order', rt, success)
        
        metrics = load_balancer.performance_metrics['test_api']['place_order']
        
        # Verify calculations
        assert metrics['total_count'] == 10
        assert metrics['success_count'] == 8
        assert metrics['success_rate'] == 0.8
        assert abs(metrics['avg_response_time'] - 146.0) < 1.0  # Should be close to mean
    
    def test_routing_history_cleanup(self):
        """Test routing history cleanup with maxlen"""
        apis = {'api1': MockAPI('api1')}
        load_balancer = IntelligentLoadBalancer(apis)
        
        # Add more than maxlen routing decisions
        current_time = time.time()
        for i in range(1200):  # More than maxlen of 1000
            load_balancer.routing_history.append({
                'timestamp': current_time - (1200 - i),
                'operation': 'place_order',
                'selected_api': 'api1',
                'available_apis': ['api1'],
                'scores': {'api1': 0.8}
            })
        
        # Should respect maxlen
        assert len(load_balancer.routing_history) == 1000
        
        # Should keep the most recent entries
        last_entry = load_balancer.routing_history[-1]
        assert abs(last_entry['timestamp'] - current_time) <= 1.0  # Within 1 second


if __name__ == '__main__':
    pytest.main([__file__])
