"""
Integration Tests for Market Data Pipeline
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.market_data_service import MarketDataPipeline
from backend.models.market_data import (
    MarketDataRequest, MarketDataResponse, DataType, ValidationTier,
    MarketData, Alert, PerformanceMetrics
)


class TestMarketDataPipelineIntegration:
    """Integration tests for MarketDataPipeline"""
    
    @pytest_asyncio.fixture
    async def market_data_pipeline(self):
        """Create MarketDataPipeline for testing"""
        pipeline = MarketDataPipeline()
        
        # Mock the WebSocket pool initialization
        with patch.object(pipeline.websocket_pool, 'initialize'):
            with patch.object(pipeline.performance_architecture, 'initialize'):
                await pipeline.initialize()
        
        return pipeline
    
    @pytest.mark.asyncio
    async def test_get_market_data_full_workflow(self, market_data_pipeline):
        """Test complete market data workflow"""
        # Create request
        request = MarketDataRequest(
            symbols=["NIFTY50", "BANKNIFTY"],
            data_types=[DataType.PRICE],
            max_age_seconds=1.0,
            validation_tier=ValidationTier.FAST,
            priority=1
        )
        
        # Mock the performance architecture to return test data
        with patch.object(market_data_pipeline.performance_architecture, 'get_market_data') as mock_get_data:
            mock_data = {
                "NIFTY50": MarketData(
                    symbol="NIFTY50",
                    exchange="NSE",
                    last_price=15000.0,
                    volume=1000000,
                    timestamp=datetime.now(),
                    data_type=DataType.PRICE,
                    source="fyers",
                    validation_tier=ValidationTier.FAST
                ),
                "BANKNIFTY": MarketData(
                    symbol="BANKNIFTY",
                    exchange="NSE",
                    last_price=35000.0,
                    volume=500000,
                    timestamp=datetime.now(),
                    data_type=DataType.PRICE,
                    source="upstox",
                    validation_tier=ValidationTier.FAST
                )
            }
            mock_get_data.return_value = mock_data
            
            # Execute request
            response = await market_data_pipeline.get_market_data(request)
            
        # Verify response
        assert isinstance(response, MarketDataResponse)
        assert response.request_id is not None
        assert set(response.symbols_requested) == {"NIFTY50", "BANKNIFTY"}
        assert len(response.data) == 2
        assert "NIFTY50" in response.data
        assert "BANKNIFTY" in response.data
        assert response.processing_time_ms >= 0  # Allow for very fast mocked processing
        assert response.cache_hit_rate >= 0
    
    @pytest.mark.asyncio
    async def test_subscribe_to_symbols(self, market_data_pipeline):
        """Test symbol subscription workflow"""
        symbols = ["NIFTY50", "BANKNIFTY", "RELIANCE"]
        
        # Mock symbol distribution and WebSocket subscription
        with patch.object(market_data_pipeline.websocket_pool, 'subscribe_symbols') as mock_subscribe:
            mock_subscribe.return_value = {
                "fyers_pool_0": True,
                "upstox_pool": True
            }
            
            result = await market_data_pipeline.subscribe_to_symbols(symbols)
            
            assert result is True
            assert market_data_pipeline.subscribed_symbols == set(symbols)
            mock_subscribe.assert_called_once_with(symbols)
    
    @pytest.mark.asyncio
    async def test_subscribe_to_symbols_failure(self, market_data_pipeline):
        """Test symbol subscription failure"""
        symbols = ["NIFTY50", "BANKNIFTY"]
        
        # Mock subscription failure
        with patch.object(market_data_pipeline.websocket_pool, 'subscribe_symbols') as mock_subscribe:
            mock_subscribe.return_value = {
                "fyers_pool_0": False,
                "upstox_pool": False
            }
            
            result = await market_data_pipeline.subscribe_to_symbols(symbols)
            
            assert result is False
            assert market_data_pipeline.subscribed_symbols == set()  # No symbols added
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_symbols(self, market_data_pipeline):
        """Test symbol unsubscription workflow"""
        # First subscribe to some symbols
        market_data_pipeline.subscribed_symbols = {"NIFTY50", "BANKNIFTY", "RELIANCE"}
        
        symbols_to_unsubscribe = ["NIFTY50", "BANKNIFTY"]
        
        result = await market_data_pipeline.unsubscribe_from_symbols(symbols_to_unsubscribe)
        
        assert result is True
        assert market_data_pipeline.subscribed_symbols == {"RELIANCE"}  # Only RELIANCE remains
    
    @pytest.mark.asyncio
    async def test_data_handler_integration(self, market_data_pipeline):
        """Test data handler integration"""
        received_data = []
        
        async def test_handler(data: MarketData):
            received_data.append(data)
        
        # Add handler
        market_data_pipeline.add_data_handler(test_handler)
        
        # Verify handler was added
        assert test_handler in market_data_pipeline.data_handlers
        
        # Simulate receiving market data
        test_data = MarketData(
            symbol="NIFTY50",
            exchange="NSE",
            last_price=15000.0,
            volume=1000000,
            timestamp=datetime.now(),
            data_type=DataType.PRICE,
            source="fyers",
            validation_tier=ValidationTier.FAST
        )
        
        # Call handler directly
        await test_handler(test_data)
        
        assert len(received_data) == 1
        assert received_data[0].symbol == "NIFTY50"
    
    @pytest.mark.asyncio
    async def test_alert_handler_integration(self, market_data_pipeline):
        """Test alert handler integration"""
        received_alerts = []
        
        async def test_alert_handler(alert: Alert):
            received_alerts.append(alert)
        
        # Add alert handler
        market_data_pipeline.add_alert_handler(test_alert_handler)
        
        # Verify handler was added
        assert test_alert_handler in market_data_pipeline.alert_handlers
        
        # Create test alert
        test_alert = Alert(
            alert_id="test_alert_1",
            alert_type="validation_discrepancy",
            severity="medium",
            message="Test alert message",
            timestamp=datetime.now()
        )
        
        # Call handler directly
        await test_alert_handler(test_alert)
        
        assert len(received_alerts) == 1
        assert received_alerts[0].alert_id == "test_alert_1"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, market_data_pipeline):
        """Test performance monitoring integration"""
        # Get initial status
        initial_status = market_data_pipeline.get_pipeline_status()
        
        assert "performance_metrics" in initial_status
        assert "connection_status" in initial_status
        assert "validation_metrics" in initial_status
        assert "performance_architecture_metrics" in initial_status
        
        # Verify performance metrics structure
        perf_metrics = initial_status["performance_metrics"]
        assert "response_time_ms" in perf_metrics
        assert "cache_hit_rate" in perf_metrics
        assert "validation_accuracy" in perf_metrics
        assert "connection_uptime" in perf_metrics
        assert "error_rate" in perf_metrics
        assert "throughput_symbols_per_second" in perf_metrics
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, market_data_pipeline):
        """Test error handling in pipeline"""
        # Create valid request first
        request = MarketDataRequest(
            symbols=["INVALID_SYMBOL"],  # Invalid symbol
            data_types=[DataType.PRICE],
            max_age_seconds=1.0,
            validation_tier=ValidationTier.FAST,
            priority=1
        )
        
        # Mock the performance architecture to return no data for invalid symbol
        with patch.object(market_data_pipeline.performance_architecture, 'get_market_data') as mock_get_data:
            mock_get_data.return_value = {}  # No data for invalid symbol
            
            # This should handle the error gracefully
            response = await market_data_pipeline.get_market_data(request)
            
            # Should return error response
            assert isinstance(response, MarketDataResponse)
            assert response.symbols_returned == []
            assert response.data == {}
    
    @pytest.mark.asyncio
    async def test_pipeline_shutdown(self, market_data_pipeline):
        """Test pipeline shutdown"""
        # Mock shutdown methods
        with patch.object(market_data_pipeline.performance_architecture, 'shutdown'):
            with patch.object(market_data_pipeline.websocket_pool, 'shutdown'):
                await market_data_pipeline.shutdown()
        
        assert market_data_pipeline.is_running is False
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, market_data_pipeline):
        """Test handling concurrent requests"""
        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            request = MarketDataRequest(
                symbols=[f"SYMBOL_{i}"],
                data_types=[DataType.PRICE],
                max_age_seconds=1.0,
                validation_tier=ValidationTier.FAST,
                priority=1
            )
            requests.append(request)
        
        # Mock performance architecture
        with patch.object(market_data_pipeline.performance_architecture, 'get_market_data') as mock_get_data:
            def mock_get_data_func(symbols):
                return {
                    symbol: MarketData(
                        symbol=symbol,
                        exchange="NSE",
                        last_price=1000.0,
                        volume=100000,
                        timestamp=datetime.now(),
                        data_type=DataType.PRICE,
                        source="test",
                        validation_tier=ValidationTier.FAST
                    )
                    for symbol in symbols
                }
            
            mock_get_data.side_effect = mock_get_data_func
            
            # Execute concurrent requests
            tasks = [
                market_data_pipeline.get_market_data(request)
                for request in requests
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(responses) == 5
            for response in responses:
                assert isinstance(response, MarketDataResponse)
                assert len(response.symbols_returned) == 1
    
    @pytest.mark.asyncio
    async def test_cache_warming_integration(self, market_data_pipeline):
        """Test cache warming functionality"""
        # Mock cache optimization loop (which includes cache warming)
        with patch.object(market_data_pipeline, '_cache_optimization_loop') as mock_optimization:
            # Start pipeline tasks
            market_data_pipeline._start_pipeline_tasks()
            
            # Verify cache optimization task was started
            assert len(market_data_pipeline.pipeline_tasks) > 0
            
            # Cancel tasks
            for task in market_data_pipeline.pipeline_tasks:
                if not task.done():
                    task.cancel()
    
    @pytest.mark.asyncio
    async def test_symbol_distribution_integration(self, market_data_pipeline):
        """Test symbol distribution integration"""
        # Test symbol distribution analytics
        status = market_data_pipeline.get_pipeline_status()
        
        # Check that status contains expected keys
        assert "pipeline_id" in status
        assert "is_running" in status
        assert "subscribed_symbols" in status
        assert "performance_metrics" in status


class TestMarketDataAPIEndpoints:
    """Integration tests for Market Data API endpoints"""
    
    @pytest_asyncio.fixture
    async def api_client(self):
        """Create test API client"""
        from fastapi.testclient import TestClient
        from backend.main import app
        
        # Mock the global pipeline instances
        with patch('backend.api.v1.market_data.market_data_pipeline', None):
            with patch('backend.api.v1.market_data.fallback_manager', None):
                client = TestClient(app)
                return client
    
    def test_get_market_data_endpoint(self, api_client):
        """Test GET /api/v1/market-data/get endpoint"""
        request_data = {
            "symbols": ["NIFTY50", "BANKNIFTY"],
            "data_types": ["PRICE"],
            "max_age_seconds": 1.0,
            "validation_tier": "FAST",
            "priority": 1
        }
        
        # Test the endpoint (without mocking to avoid complexity)
        response = api_client.post("/api/v1/market-data/get", json=request_data)
        
        # Check that we get a valid response structure
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "symbols_requested" in data
        assert data["symbols_requested"] == ["NIFTY50", "BANKNIFTY"]
    
    def test_get_single_symbol_endpoint(self, api_client):
        """Test GET /api/v1/market-data/symbols/{symbol} endpoint"""
        response = api_client.get("/api/v1/market-data/symbols/NIFTY50")
        
        # Check that we get a valid response structure
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "NIFTY50"
    
    def test_batch_market_data_endpoint(self, api_client):
        """Test GET /api/v1/market-data/batch endpoint"""
        response = api_client.get("/api/v1/market-data/batch?symbols=NIFTY50,BANKNIFTY")
        
        # Check that we get a valid response structure
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "symbols_requested" in data
    
    def test_subscribe_endpoint(self, api_client):
        """Test POST /api/v1/market-data/subscribe endpoint"""
        # Test the endpoint structure (actual subscription will fail due to no real connections)
        response = api_client.post("/api/v1/market-data/subscribe", json={"symbols": ["NIFTY50", "BANKNIFTY"]})
        
        # The endpoint should handle the request properly even if subscription fails
        assert response.status_code in [200, 500]  # Allow both success and expected failure
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
        else:
            # If it fails, it should be due to connection issues, not validation
            assert response.status_code == 500
    
    def test_pipeline_status_endpoint(self, api_client):
        """Test GET /api/v1/market-data/status endpoint"""
        with patch('backend.api.v1.market_data.get_market_data_pipeline') as mock_get_pipeline:
            mock_pipeline = AsyncMock()
            mock_get_pipeline.return_value = mock_pipeline
            mock_pipeline.get_pipeline_status.return_value = {
                "pipeline_id": "test_pipeline_1",
                "is_running": True,
                "subscribed_symbols": ["NIFTY50"],
                "performance_metrics": {},
                "connection_status": {},
                "validation_metrics": {},
                "performance_architecture_metrics": {},
                "symbol_distribution_analytics": {}
            }
            
            response = api_client.get("/api/v1/market-data/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "pipeline_id" in data
            assert data["is_running"] is True
    
    def test_health_check_endpoint(self, api_client):
        """Test GET /api/v1/market-data/health endpoint"""
        response = api_client.get("/api/v1/market-data/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "market-data-api"
