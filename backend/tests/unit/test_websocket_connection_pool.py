"""
Unit Tests for WebSocket Connection Pool
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

from services.websocket_connection_pool import (
    WebSocketPool, WebSocketConnectionPool, ConnectionStatus
)
from models.market_data import MarketData, DataType, ValidationTier


class TestWebSocketPool:
    """Test WebSocketPool class"""
    
    @pytest_asyncio.fixture
    async def websocket_pool(self):
        """Create WebSocket pool for testing"""
        pool = WebSocketPool(
            connection_id="test_pool",
            provider="fyers",
            max_symbols=200
        )
        return pool
    
    @pytest.mark.asyncio
    async def test_initialization(self, websocket_pool):
        """Test WebSocket pool initialization"""
        assert websocket_pool.connection_id == "test_pool"
        assert websocket_pool.provider == "fyers"
        assert websocket_pool.max_symbols == 200
        assert websocket_pool.status == ConnectionStatus.DISCONNECTED
        assert websocket_pool.subscribed_symbols == set()
        assert websocket_pool.error_count == 0
    
    @pytest.mark.asyncio
    async def test_connect_success(self, websocket_pool):
        """Test successful connection"""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            result = await websocket_pool.connect()
            
            assert result is True
            assert websocket_pool.status == ConnectionStatus.CONNECTED
            assert websocket_pool.websocket == mock_websocket
            assert websocket_pool.connection_info.connected_at is not None
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, websocket_pool):
        """Test connection failure"""
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            result = await websocket_pool.connect()
            
            assert result is False
            assert websocket_pool.status == ConnectionStatus.FAILED
            assert websocket_pool.error_count == 1
    
    @pytest.mark.asyncio
    async def test_subscribe_symbols_success(self, websocket_pool):
        """Test successful symbol subscription"""
        # Mock connection
        mock_websocket = AsyncMock()
        websocket_pool.websocket = mock_websocket
        websocket_pool.status = ConnectionStatus.CONNECTED
        
        symbols = ["NIFTY50", "BANKNIFTY"]
        result = await websocket_pool.subscribe_symbols(symbols)
        
        assert result is True
        assert websocket_pool.subscribed_symbols == set(symbols)
        mock_websocket.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_symbols_limit_exceeded(self, websocket_pool):
        """Test symbol limit exceeded"""
        # Mock connection
        mock_websocket = AsyncMock()
        websocket_pool.websocket = mock_websocket
        websocket_pool.status = ConnectionStatus.CONNECTED
        
        # Set max symbols to 2 and already have 1 subscribed
        websocket_pool.max_symbols = 2
        websocket_pool.subscribed_symbols = {"EXISTING_SYMBOL"}
        
        symbols = ["NIFTY50", "BANKNIFTY"]  # This would exceed limit
        result = await websocket_pool.subscribe_symbols(symbols)
        
        assert result is False
        assert websocket_pool.subscribed_symbols == {"EXISTING_SYMBOL"}  # Unchanged
    
    @pytest.mark.asyncio
    async def test_handle_market_data_message(self, websocket_pool):
        """Test handling market data message"""
        # Mock data handler
        data_handler = AsyncMock()
        websocket_pool.add_data_handler(data_handler)
        
        # Mock message
        message_data = {
            "type": "market_data",
            "symbol": "NIFTY50",
            "ltp": 15000.0,
            "volume": 1000000,
            "timestamp": 1640995200000,
            "exchange": "NSE"
        }
        
        message = json.dumps(message_data)
        await websocket_pool._handle_message(message)
        
        # Verify handler was called
        data_handler.assert_called_once()
        call_args = data_handler.call_args[0][0]
        assert isinstance(call_args, MarketData)
        assert call_args.symbol == "NIFTY50"
        assert call_args.last_price == 15000.0
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, websocket_pool):
        """Test handling heartbeat message"""
        initial_heartbeat = websocket_pool.last_heartbeat
        
        message_data = {"type": "heartbeat"}
        message = json.dumps(message_data)
        await websocket_pool._handle_message(message)
        
        assert websocket_pool.last_heartbeat is not None
        assert websocket_pool.last_heartbeat != initial_heartbeat
    
    def test_is_healthy_connected(self, websocket_pool):
        """Test health check when connected"""
        websocket_pool.status = ConnectionStatus.CONNECTED
        websocket_pool.last_heartbeat = datetime.now()
        websocket_pool.error_count = 0
        
        assert websocket_pool.is_healthy() is True
    
    def test_is_healthy_disconnected(self, websocket_pool):
        """Test health check when disconnected"""
        websocket_pool.status = ConnectionStatus.DISCONNECTED
        
        assert websocket_pool.is_healthy() is False
    
    def test_is_healthy_stale_heartbeat(self, websocket_pool):
        """Test health check with stale heartbeat"""
        websocket_pool.status = ConnectionStatus.CONNECTED
        websocket_pool.last_heartbeat = datetime.now() - timedelta(seconds=35)  # Stale
        websocket_pool.error_count = 0
        
        assert websocket_pool.is_healthy() is False
    
    def test_is_healthy_high_error_count(self, websocket_pool):
        """Test health check with high error count"""
        websocket_pool.status = ConnectionStatus.CONNECTED
        websocket_pool.last_heartbeat = datetime.now()
        websocket_pool.error_count = 15  # High error count
        
        assert websocket_pool.is_healthy() is False


class TestWebSocketConnectionPool:
    """Test WebSocketConnectionPool class"""
    
    @pytest_asyncio.fixture
    async def connection_pool(self):
        """Create connection pool for testing"""
        pool = WebSocketConnectionPool()
        return pool
    
    @pytest.mark.asyncio
    async def test_initialization(self, connection_pool):
        """Test connection pool initialization"""
        assert connection_pool.fyers_pools == []
        assert connection_pool.upstox_pool is None
        assert connection_pool.is_running is False
        assert connection_pool.data_handlers == []
    
    @pytest.mark.asyncio
    async def test_subscribe_symbols_distribution(self, connection_pool):
        """Test symbol distribution across pools"""
        # Mock the symbol distribution manager
        with patch.object(connection_pool.symbol_distribution, 'distribute_symbols') as mock_distribute:
            mock_distribution = Mock()
            mock_distribution.fyers_pools = [
                {"pool_id": "fyers_pool_0", "symbols": ["NIFTY50", "BANKNIFTY"]}
            ]
            mock_distribution.upstox_pool = ["RELIANCE", "TCS"]
            mock_distribute.return_value = mock_distribution
            
            # Mock _get_or_create_fyers_pool
            with patch.object(connection_pool, '_get_or_create_fyers_pool') as mock_get_pool:
                mock_pool = AsyncMock()
                mock_pool.subscribe_symbols = AsyncMock(return_value=True)
                mock_get_pool.return_value = mock_pool
                
                # Mock _connect_upstox_pool
                with patch.object(connection_pool, '_connect_upstox_pool') as mock_connect_upstox:
                    connection_pool.upstox_pool = AsyncMock()
                    connection_pool.upstox_pool.subscribe_symbols = AsyncMock(return_value=True)
                    
                    symbols = ["NIFTY50", "BANKNIFTY", "RELIANCE", "TCS"]
                    results = await connection_pool.subscribe_symbols(symbols)
                    
                    assert "fyers_pool_0" in results
                    assert "upstox_pool" in results
                    assert results["fyers_pool_0"] is True
                    assert results["upstox_pool"] is True
    
    @pytest.mark.asyncio
    async def test_get_connection_status(self, connection_pool):
        """Test getting connection status"""
        # Add mock FYERS pool
        mock_fyers_pool = Mock()
        mock_fyers_pool.connection_id = "fyers_pool_0"
        mock_fyers_pool.status = ConnectionStatus.CONNECTED
        mock_fyers_pool.subscribed_symbols = {"NIFTY50"}
        mock_fyers_pool.max_symbols = 200
        mock_fyers_pool.error_count = 0
        mock_fyers_pool.is_healthy = Mock(return_value=True)
        mock_fyers_pool.connection_info.connected_at = datetime.now()
        mock_fyers_pool.connection_info.last_heartbeat = datetime.now()
        
        connection_pool.fyers_pools = [mock_fyers_pool]
        
        # Add mock UPSTOX pool
        mock_upstox_pool = Mock()
        mock_upstox_pool.connection_id = "upstox_pool"
        mock_upstox_pool.status = ConnectionStatus.CONNECTED
        mock_upstox_pool.subscribed_symbols = {"RELIANCE"}
        mock_upstox_pool.max_symbols = float('inf')
        mock_upstox_pool.error_count = 0
        mock_upstox_pool.is_healthy = Mock(return_value=True)
        mock_upstox_pool.connection_info.connected_at = datetime.now()
        mock_upstox_pool.connection_info.last_heartbeat = datetime.now()
        
        connection_pool.upstox_pool = mock_upstox_pool
        
        status = connection_pool.get_connection_status()
        
        assert status['total_connections'] == 2
        assert status['healthy_connections'] == 2
        assert len(status['fyers_pools']) == 1
        assert status['upstox_pool'] is not None
        assert status['fyers_pools'][0]['connection_id'] == "fyers_pool_0"
        assert status['upstox_pool']['connection_id'] == "upstox_pool"
    
    def test_add_data_handler(self, connection_pool):
        """Test adding data handler"""
        handler1 = Mock()
        handler2 = Mock()
        
        connection_pool.add_data_handler(handler1)
        connection_pool.add_data_handler(handler2)
        
        assert len(connection_pool.data_handlers) == 2
        assert handler1 in connection_pool.data_handlers
        assert handler2 in connection_pool.data_handlers
    
    @pytest.mark.asyncio
    async def test_shutdown(self, connection_pool):
        """Test connection pool shutdown"""
        # Mock pools
        mock_fyers_pool = AsyncMock()
        mock_upstox_pool = AsyncMock()
        connection_pool.fyers_pools = [mock_fyers_pool]
        connection_pool.upstox_pool = mock_upstox_pool
        connection_pool.is_running = True
        
        await connection_pool.shutdown()
        
        assert connection_pool.is_running is False
        mock_fyers_pool.disconnect.assert_called_once()
        mock_upstox_pool.disconnect.assert_called_once()


class TestSymbolDistributionManager:
    """Test SymbolDistributionManager class"""
    
    @pytest.fixture
    def distribution_manager(self):
        """Create symbol distribution manager for testing"""
        from services.symbol_distribution_manager import SymbolDistributionManager
        return SymbolDistributionManager()
    
    def test_get_symbol_priority(self, distribution_manager):
        """Test getting symbol priority"""
        # Test high priority symbols
        assert distribution_manager.get_symbol_priority("NIFTY50") == 1
        assert distribution_manager.get_symbol_priority("RELIANCE") == 1
        
        # Test medium priority symbols
        assert distribution_manager.get_symbol_priority("NIFTY100") == 2
        
        # Test unknown symbol (default priority)
        assert distribution_manager.get_symbol_priority("UNKNOWN_SYMBOL") == 3
    
    def test_update_symbol_usage(self, distribution_manager):
        """Test updating symbol usage"""
        symbol = "NIFTY50"
        
        # Initial usage should be 0
        assert distribution_manager.symbol_frequency[symbol] == 0
        
        # Update usage
        distribution_manager.update_symbol_usage(symbol)
        distribution_manager.update_symbol_usage(symbol)
        
        assert distribution_manager.symbol_frequency[symbol] == 2
        assert distribution_manager.symbol_last_access[symbol] is not None
    
    def test_get_symbol_frequency_category(self, distribution_manager):
        """Test getting symbol frequency category"""
        symbol = "NIFTY50"
        
        # Initially low frequency
        assert distribution_manager.get_symbol_frequency_category(symbol) == "low"
        
        # Update to high frequency
        for _ in range(101):  # Above high frequency threshold
            distribution_manager.update_symbol_usage(symbol)
        
        assert distribution_manager.get_symbol_frequency_category(symbol) == "high"
    
    def test_distribute_symbols(self, distribution_manager):
        """Test symbol distribution"""
        symbols = ["NIFTY50", "BANKNIFTY", "RELIANCE", "TCS", "UNKNOWN_SYMBOL"]
        
        # Update usage for some symbols to make them high frequency
        for _ in range(101):
            distribution_manager.update_symbol_usage("NIFTY50")
            distribution_manager.update_symbol_usage("BANKNIFTY")
        
        distribution = distribution_manager.distribute_symbols(symbols)
        
        assert distribution.total_symbols == len(symbols)
        assert len(distribution.fyers_pools) > 0  # High frequency symbols should go to FYERS
        assert len(distribution.upstox_pool) > 0  # Other symbols should go to UPSTOX
    
    def test_get_distribution_analytics(self, distribution_manager):
        """Test getting distribution analytics"""
        # Add some distribution history
        distribution_manager.distribution_history = [
            {
                'timestamp': datetime.now(),
                'total_symbols': 100,
                'fyers_pools': 1,
                'upstox_symbols': 50,
                'distribution': {}
            }
        ]
        
        analytics = distribution_manager.get_distribution_analytics()
        
        assert 'total_distributions' in analytics
        assert 'avg_fyers_pools' in analytics
        assert 'avg_upstox_symbols' in analytics
        assert 'fyers_utilization' in analytics
    
    def test_optimize_distribution(self, distribution_manager):
        """Test distribution optimization"""
        # Add some distribution history
        distribution_manager.distribution_history = [
            {
                'timestamp': datetime.now(),
                'total_symbols': 100,
                'fyers_pools': 1,
                'upstox_symbols': 50,
                'distribution': {}
            }
        ]
        
        optimization = distribution_manager.optimize_distribution()
        
        assert 'status' in optimization
        assert 'analytics' in optimization
        assert 'suggestions' in optimization
        assert 'optimization_score' in optimization
