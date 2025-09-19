"""
WebSocket Connection Pool for Multi-Tier Connection Management
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from models.market_data import (
    WebSocketConnectionInfo, ConnectionStatus, MarketData,
    DataType, ValidationTier
)
from services.symbol_distribution_manager import SymbolDistributionManager

logger = logging.getLogger(__name__)


class WebSocketPool:
    """Base WebSocket connection pool"""

    def __init__(self, connection_id: str, provider: str, max_symbols: int):
        self.connection_id = connection_id
        self.provider = provider
        self.max_symbols = max_symbols
        self.status = ConnectionStatus.DISCONNECTED
        self.websocket = None
        self.subscribed_symbols = set()
        self.connection_info = WebSocketConnectionInfo(
            connection_id=connection_id,
            provider=provider,
            status=self.status,
            max_symbols=max_symbols
        )
        self.data_handlers = []
        self.error_count = 0
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0

    async def connect(self) -> bool:
        """Connect to WebSocket"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.connection_info.status = self.status

            # Get WebSocket URL based on provider
            url = self._get_websocket_url()
            if not url:
                raise ValueError(f"No WebSocket URL configured for provider {self.provider}")

            self.websocket = await websockets.connect(url)
            self.status = ConnectionStatus.CONNECTED
            self.connection_info.status = self.status
            self.connection_info.connected_at = datetime.now()
            self.error_count = 0
            self.reconnect_attempts = 0

            logger.info(f"Connected to {self.provider} WebSocket: {self.connection_id}")
            return True

        except Exception as e:
            self.status = ConnectionStatus.FAILED
            self.connection_info.status = self.status
            self.error_count += 1
            logger.error(f"Failed to connect to {self.provider} WebSocket {self.connection_id}: {e}")
            return False

    async def disconnect(self):
        """Disconnect from WebSocket"""
        try:
            if self.websocket:
                await self.websocket.close()
            self.status = ConnectionStatus.DISCONNECTED
            self.connection_info.status = self.status
            self.websocket = None
            logger.info(f"Disconnected from {self.provider} WebSocket: {self.connection_id}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.provider} WebSocket {self.connection_id}: {e}")

    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to market data for symbols"""
        if not self.websocket or self.status != ConnectionStatus.CONNECTED:
            logger.error(f"Cannot subscribe to symbols: WebSocket not connected")
            return False

        # Check symbol limit
        if len(self.subscribed_symbols) + len(symbols) > self.max_symbols:
            logger.error(f"Symbol limit exceeded for {self.connection_id}: "
                        f"{len(self.subscribed_symbols)} + {len(symbols)} > {self.max_symbols}")
            return False

        try:
            # Create subscription message based on provider
            subscription_message = self._create_subscription_message(symbols)
            await self.websocket.send(json.dumps(subscription_message))

            # Update subscribed symbols
            self.subscribed_symbols.update(symbols)
            self.connection_info.current_symbols = list(self.subscribed_symbols)

            logger.info(f"Subscribed to {len(symbols)} symbols on {self.connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to symbols on {self.connection_id}: {e}")
            return False

    async def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from market data for symbols"""
        if not self.websocket or self.status != ConnectionStatus.CONNECTED:
            logger.error(f"Cannot unsubscribe from symbols: WebSocket not connected")
            return False

        try:
            # Create unsubscription message based on provider
            unsubscription_message = self._create_unsubscription_message(symbols)
            await self.websocket.send(json.dumps(unsubscription_message))

            # Update subscribed symbols
            self.subscribed_symbols -= set(symbols)
            self.connection_info.current_symbols = list(self.subscribed_symbols)

            logger.info(f"Unsubscribed from {len(symbols)} symbols on {self.connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from symbols on {self.connection_id}: {e}")
            return False

    async def listen(self):
        """Listen for incoming messages"""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except ConnectionClosed:
            logger.warning(f"WebSocket connection closed: {self.connection_id}")
            self.status = ConnectionStatus.DISCONNECTED
            self.connection_info.status = self.status
        except WebSocketException as e:
            logger.error(f"WebSocket error on {self.connection_id}: {e}")
            self.status = ConnectionStatus.FAILED
            self.connection_info.status = self.status
            self.error_count += 1

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)

            # Update heartbeat
            self.last_heartbeat = datetime.now()
            self.connection_info.last_heartbeat = self.last_heartbeat

            # Process message based on type
            message_type = data.get('type', 'unknown')

            if message_type == 'market_data':
                await self._handle_market_data(data)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(data)
            elif message_type == 'error':
                await self._handle_error(data)
            else:
                logger.debug(f"Unknown message type from {self.connection_id}: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message from {self.connection_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {self.connection_id}: {e}")

    async def _handle_market_data(self, data: Dict[str, Any]):
        """Handle market data message"""
        try:
            # Parse market data based on provider format
            market_data = self._parse_market_data(data)

            # Notify data handlers
            for handler in self.data_handlers:
                try:
                    await handler(market_data)
                except Exception as e:
                    logger.error(f"Error in data handler for {self.connection_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling market data from {self.connection_id}: {e}")

    async def _handle_heartbeat(self, data: Dict[str, Any]):
        """Handle heartbeat message"""
        self.last_heartbeat = datetime.now()
        self.connection_info.last_heartbeat = self.last_heartbeat

    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error message"""
        error_message = data.get('message', 'Unknown error')
        logger.error(f"Error from {self.connection_id}: {error_message}")
        self.error_count += 1

    def add_data_handler(self, handler: Callable[[MarketData], Any]):
        """Add data handler for incoming market data"""
        self.data_handlers.append(handler)

    def remove_data_handler(self, handler: Callable[[MarketData], Any]):
        """Remove data handler"""
        if handler in self.data_handlers:
            self.data_handlers.remove(handler)

    def _get_websocket_url(self) -> Optional[str]:
        """Get WebSocket URL for provider"""
        urls = {
            'fyers': 'wss://api-t1.fyers.in/data/websocket',
            'upstox': 'wss://api.upstox.com/index/websocket'
        }
        return urls.get(self.provider.lower())

    def _create_subscription_message(self, symbols: List[str]) -> Dict[str, Any]:
        """Create subscription message based on provider"""
        if self.provider.lower() == 'fyers':
            return {
                'type': 'subscribe',
                'symbols': symbols,
                'data_type': 'market_data'
            }
        elif self.provider.lower() == 'upstox':
            return {
                'type': 'subscribe',
                'instruments': symbols,
                'mode': 'ltp'
            }
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _create_unsubscription_message(self, symbols: List[str]) -> Dict[str, Any]:
        """Create unsubscription message based on provider"""
        if self.provider.lower() == 'fyers':
            return {
                'type': 'unsubscribe',
                'symbols': symbols
            }
        elif self.provider.lower() == 'upstox':
            return {
                'type': 'unsubscribe',
                'instruments': symbols
            }
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _parse_market_data(self, data: Dict[str, Any]) -> MarketData:
        """Parse market data based on provider format"""
        if self.provider.lower() == 'fyers':
            return MarketData(
                symbol=data['symbol'],
                exchange=data.get('exchange', 'NSE'),
                last_price=float(data['ltp']),
                volume=int(data.get('volume', 0)),
                timestamp=datetime.fromtimestamp(data['timestamp'] / 1000),
                data_type=DataType.PRICE,
                source=self.provider,
                validation_tier=ValidationTier.FAST
            )
        elif self.provider.lower() == 'upstox':
            return MarketData(
                symbol=data['instrument_token'],
                exchange=data.get('exchange', 'NSE'),
                last_price=float(data['last_price']),
                volume=int(data.get('volume', 0)),
                timestamp=datetime.fromtimestamp(data['timestamp'] / 1000),
                data_type=DataType.PRICE,
                source=self.provider,
                validation_tier=ValidationTier.FAST
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        if self.status != ConnectionStatus.CONNECTED:
            return False

        # Check heartbeat timeout (30 seconds)
        if self.last_heartbeat:
            time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
            if time_since_heartbeat > 30:
                return False

        # Check error count
        if self.error_count > 10:
            return False

        return True

    def get_connection_info(self) -> WebSocketConnectionInfo:
        """Get connection information"""
        return self.connection_info


class WebSocketConnectionPool:
    """Multi-tier connection pool manager"""

    def __init__(self):
        self.fyers_pools: List[WebSocketPool] = []
        self.upstox_pool: Optional[WebSocketPool] = None
        self.symbol_distribution = SymbolDistributionManager()
        self.data_handlers = []
        self.connection_monitor_task = None
        self.is_running = False

    async def initialize(self):
        """Initialize all connections"""
        logger.info("Initializing WebSocket connection pool")

        # Create UPSTOX pool (single connection for unlimited symbols)
        self.upstox_pool = WebSocketPool(
            connection_id="upstox_pool",
            provider="upstox",
            max_symbols=float('inf')
        )

        # Start connection monitoring
        self.connection_monitor_task = asyncio.create_task(self._monitor_connections())
        self.is_running = True

        logger.info("WebSocket connection pool initialized")

    async def shutdown(self):
        """Shutdown all connections"""
        logger.info("Shutting down WebSocket connection pool")
        self.is_running = False

        # Cancel monitoring task
        if self.connection_monitor_task:
            self.connection_monitor_task.cancel()

        # Disconnect all FYERS pools
        for pool in self.fyers_pools:
            await pool.disconnect()

        # Disconnect UPSTOX pool
        if self.upstox_pool:
            await self.upstox_pool.disconnect()

        logger.info("WebSocket connection pool shutdown complete")

    async def subscribe_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """Subscribe to symbols across all pools"""
        logger.info(f"Subscribing to {len(symbols)} symbols")

        # Get symbol distribution
        distribution = self.symbol_distribution.distribute_symbols(symbols)

        results = {}

        # Subscribe to FYERS pools
        for pool_info in distribution.fyers_pools:
            pool_id = pool_info['pool_id']
            pool_symbols = pool_info['symbols']

            # Find or create FYERS pool
            pool = await self._get_or_create_fyers_pool(pool_id)
            if pool:
                success = await pool.subscribe_symbols(pool_symbols)
                results[pool_id] = success
            else:
                results[pool_id] = False

        # Subscribe to UPSTOX pool
        if distribution.upstox_pool:
            if not self.upstox_pool or self.upstox_pool.status != ConnectionStatus.CONNECTED:
                await self._connect_upstox_pool()

            if self.upstox_pool:
                success = await self.upstox_pool.subscribe_symbols(distribution.upstox_pool)
                results['upstox_pool'] = success
            else:
                results['upstox_pool'] = False

        return results

    async def _get_or_create_fyers_pool(self, pool_id: str) -> Optional[WebSocketPool]:
        """Get existing FYERS pool or create new one"""
        # Find existing pool
        for pool in self.fyers_pools:
            if pool.connection_id == pool_id:
                return pool

        # Create new pool
        pool = WebSocketPool(
            connection_id=pool_id,
            provider="fyers",
            max_symbols=200
        )

        # Connect pool
        if await pool.connect():
            # Start listening for messages
            asyncio.create_task(pool.listen())
            self.fyers_pools.append(pool)
            logger.info(f"Created new FYERS pool: {pool_id}")
            return pool
        else:
            logger.error(f"Failed to create FYERS pool: {pool_id}")
            return None

    async def _connect_upstox_pool(self):
        """Connect UPSTOX pool"""
        if not self.upstox_pool:
            return

        if await self.upstox_pool.connect():
            # Start listening for messages
            asyncio.create_task(self.upstox_pool.listen())
            logger.info("Connected UPSTOX pool")
        else:
            logger.error("Failed to connect UPSTOX pool")

    async def _monitor_connections(self):
        """Monitor connection health and handle reconnections"""
        while self.is_running:
            try:
                # Check FYERS pools
                for pool in self.fyers_pools[:]:  # Copy list to avoid modification during iteration
                    if not pool.is_healthy():
                        logger.warning(f"Unhealthy FYERS pool detected: {pool.connection_id}")
                        await self._reconnect_pool(pool)

                # Check UPSTOX pool
                if self.upstox_pool and not self.upstox_pool.is_healthy():
                    logger.warning("Unhealthy UPSTOX pool detected")
                    await self._reconnect_pool(self.upstox_pool)

                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
                await asyncio.sleep(5)

    async def _reconnect_pool(self, pool: WebSocketPool):
        """Reconnect a pool with exponential backoff"""
        if pool.reconnect_attempts >= pool.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {pool.connection_id}")
            return

        pool.reconnect_attempts += 1
        delay = pool.reconnect_delay * (2 ** (pool.reconnect_attempts - 1))

        logger.info(f"Reconnecting {pool.connection_id} in {delay} seconds (attempt {pool.reconnect_attempts})")
        await asyncio.sleep(delay)

        pool.status = ConnectionStatus.RECONNECTING
        pool.connection_info.status = pool.status

        # Reconnect
        if await pool.connect():
            # Restart listening
            asyncio.create_task(pool.listen())
            logger.info(f"Successfully reconnected {pool.connection_id}")
        else:
            logger.error(f"Failed to reconnect {pool.connection_id}")

    def add_data_handler(self, handler: Callable[[MarketData], Any]):
        """Add data handler for all pools"""
        self.data_handlers.append(handler)

        # Add to existing pools
        for pool in self.fyers_pools:
            pool.add_data_handler(handler)

        if self.upstox_pool:
            self.upstox_pool.add_data_handler(handler)

    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all connections"""
        status = {
            'fyers_pools': [],
            'upstox_pool': None,
            'total_connections': 0,
            'healthy_connections': 0
        }

        # FYERS pools status
        for pool in self.fyers_pools:
            pool_status = {
                'connection_id': pool.connection_id,
                'status': pool.status.value,
                'subscribed_symbols': len(pool.subscribed_symbols),
                'max_symbols': pool.max_symbols,
                'error_count': pool.error_count,
                'is_healthy': pool.is_healthy(),
                'connected_at': pool.connection_info.connected_at.isoformat() if pool.connection_info.connected_at else None,
                'last_heartbeat': pool.connection_info.last_heartbeat.isoformat() if pool.connection_info.last_heartbeat else None
            }
            status['fyers_pools'].append(pool_status)
            status['total_connections'] += 1
            if pool.is_healthy():
                status['healthy_connections'] += 1

        # UPSTOX pool status
        if self.upstox_pool:
            status['upstox_pool'] = {
                'connection_id': self.upstox_pool.connection_id,
                'status': self.upstox_pool.status.value,
                'subscribed_symbols': len(self.upstox_pool.subscribed_symbols),
                'max_symbols': 'unlimited',
                'error_count': self.upstox_pool.error_count,
                'is_healthy': self.upstox_pool.is_healthy(),
                'connected_at': self.upstox_pool.connection_info.connected_at.isoformat() if self.upstox_pool.connection_info.connected_at else None,
                'last_heartbeat': self.upstox_pool.connection_info.last_heartbeat.isoformat() if self.upstox_pool.connection_info.last_heartbeat else None
            }
            status['total_connections'] += 1
            if self.upstox_pool.is_healthy():
                status['healthy_connections'] += 1

        return status

    def get_symbol_distribution_analytics(self) -> Dict[str, Any]:
        """Get symbol distribution analytics"""
        return self.symbol_distribution.get_symbol_statistics()
