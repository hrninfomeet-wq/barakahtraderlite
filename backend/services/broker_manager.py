"""
Broker Manager - Barakah Trader Lite
Unified broker abstraction layer with smart failover and data aggregation
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from services.upstox_api import upstox_service
from services.flattrade_api import flattrade_service
from services.fyers_api import fyers_service
from services.aliceblue_api import aliceblue_service

class BrokerManager:
    def __init__(self):
        """Initialize broker manager with all supported brokers"""
        self.brokers = {
            'upstox': upstox_service,
            'flattrade': flattrade_service,
            'fyers': fyers_service,
            'aliceblue': aliceblue_service,
        }
        
        # Priority order for data fetching (most reliable first)
        # Fyers first for real data when user specifically authenticates
        self.priority_order = ['fyers', 'upstox', 'flattrade', 'aliceblue']
        
        logger.info(f"BrokerManager initialized with {len(self.brokers)} brokers")
    
    def get_auth_url(self, broker_id: str) -> str:
        """Get OAuth authentication URL for a specific broker"""
        if broker_id not in self.brokers:
            raise ValueError(f"Unknown broker: {broker_id}")
        
        service = self.brokers[broker_id]
        if not hasattr(service, 'get_auth_url'):
            raise ValueError(f"Broker {broker_id} does not support OAuth authentication")
        
        return service.get_auth_url()
    
    async def exchange_code_for_token(self, broker_id: str, auth_code: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if broker_id not in self.brokers:
            return {"error": f"Unknown broker: {broker_id}"}
        
        service = self.brokers[broker_id]
        if not hasattr(service, 'exchange_code_for_token'):
            return {"error": f"Broker {broker_id} does not support token exchange"}
        
        try:
            # AliceBlue requires user_id parameter for token exchange
            if broker_id == 'aliceblue':
                result = await service.exchange_code_for_token(auth_code, user_id)
            else:
                result = await service.exchange_code_for_token(auth_code)
                
            if result.get('error'):
                return result
            else:
                # Token exchange successful, refresh status
                logger.info(f"{broker_id} authentication completed successfully")
                return {"success": True, "broker": broker_id, "token_data": result}
        except Exception as e:
            logger.error(f"Error during {broker_id} token exchange: {str(e)}")
            return {"error": f"Token exchange failed: {str(e)}"}
    
    async def authenticate_with_api_key(self, broker_id: str, api_key: str) -> Dict[str, Any]:
        """Authenticate broker using API key (for brokers that don't use OAuth)"""
        if broker_id not in self.brokers:
            return {"error": f"Unknown broker: {broker_id}"}
        
        # Legacy method - most brokers now use OAuth
        if broker_id in ['aliceblue', 'fyers', 'upstox', 'flattrade']:
            return {"error": f"Broker {broker_id} uses OAuth authentication, not API key"}
        
        service = self.brokers[broker_id]
        if not hasattr(service, 'authenticate_with_api_key'):
            return {"error": f"Broker {broker_id} does not support API key authentication"}
        
        try:
            result = await service.authenticate_with_api_key(api_key)
            if result.get('success'):
                logger.info(f"{broker_id} API key authentication completed successfully")
                return {"success": True, "broker": broker_id, "auth_data": result}
            else:
                return result
        except Exception as e:
            logger.error(f"Error during {broker_id} API key authentication: {str(e)}")
            return {"error": f"API key authentication failed: {str(e)}"}
    
    def get_connected_brokers(self) -> List[str]:
        """Get list of brokers that are currently connected and valid"""
        connected = []
        for broker_id, service in self.brokers.items():
            if service.has_credentials():
                connected.append(broker_id)
        return connected
    
    async def get_broker_status(self, broker_id: str) -> Dict[str, Any]:
        """Get status for a specific broker"""
        if broker_id not in self.brokers:
            return {"error": "Unknown broker"}
        
        service = self.brokers[broker_id]
        # Handle both sync and async get_status methods
        if hasattr(service.get_status, '__call__'):
            if asyncio.iscoroutinefunction(service.get_status):
                return await service.get_status()
            else:
                return service.get_status()
        else:
            return {"error": "Service does not have get_status method"}
    
    async def get_all_broker_statuses(self) -> Dict[str, Any]:
        """Get status for all brokers"""
        statuses = {}
        for broker_id, service in self.brokers.items():
            # Handle both sync and async get_status methods
            if hasattr(service.get_status, '__call__'):
                if asyncio.iscoroutinefunction(service.get_status):
                    statuses[broker_id] = await service.get_status()
                else:
                    statuses[broker_id] = service.get_status()
            else:
                statuses[broker_id] = {"error": "Service does not have get_status method"}
        
        connected_count = len([s for s in statuses.values() if s.get('has_credentials')])
        
        return {
            'brokers': statuses,
            'connected_count': connected_count,
            'total_count': len(self.brokers),
            'connected_brokers': self.get_connected_brokers(),
        }
    
    async def get_market_data_with_failover(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch market data with smart failover across multiple brokers
        Returns aggregated data with source information
        """
        connected_brokers = self.get_connected_brokers()
        
        if not connected_brokers:
            logger.warning("No brokers connected for market data")
            return {
                "error": "No brokers available",
                "source": "none",
                "live_mode": False
            }
        
        # Try brokers in priority order
        for broker_id in self.priority_order:
            if broker_id not in connected_brokers:
                continue
                
            logger.info(f"Attempting market data fetch from {broker_id}")
            
            try:
                service = self.brokers[broker_id]
                result = await service.get_market_data(symbols)
                
                if result.get("success") or result.get("data"):
                    logger.info(f"Successfully fetched data from {broker_id}")
                    return {
                        **result,
                        "primary_source": broker_id,
                        "live_mode": True,
                        "fallback_used": False,
                    }
                else:
                    logger.warning(f"{broker_id} returned error: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error fetching from {broker_id}: {str(e)}")
                continue
        
        # If all brokers failed, return error
        logger.error("All connected brokers failed to provide market data")
        return {
            "error": "All brokers failed",
            "attempted_brokers": connected_brokers,
            "source": "failed",
            "live_mode": False
        }
    
    async def get_aggregated_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch market data from multiple brokers and aggregate for better accuracy
        """
        connected_brokers = self.get_connected_brokers()
        
        if not connected_brokers:
            logger.warning("No brokers connected for aggregated data")
            return await self.get_market_data_with_failover(symbols)
        
        if len(connected_brokers) == 1:
            # Only one broker available, use regular failover
            return await self.get_market_data_with_failover(symbols)
        
        logger.info(f"Fetching aggregated data from {len(connected_brokers)} brokers")
        
        # Fetch from multiple brokers concurrently
        tasks = []
        for broker_id in connected_brokers[:3]:  # Limit to 3 for performance
            service = self.brokers[broker_id]
            task = asyncio.create_task(service.get_market_data(symbols))
            tasks.append((broker_id, task))
        
        # Wait for all responses with timeout
        results = {}
        sources_used = []
        
        for broker_id, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=10.0)
                if result.get("success") or result.get("data"):
                    results[broker_id] = result
                    sources_used.append(broker_id)
            except Exception as e:
                logger.warning(f"Aggregation: {broker_id} failed: {str(e)}")
        
        if not results:
            return {
                "error": "All brokers failed in aggregation",
                "source": "failed",
                "live_mode": False
            }
        
        # Aggregate the data (use first successful for now, can be enhanced)
        primary_broker = sources_used[0]
        primary_data = results[primary_broker]
        
        return {
            **primary_data,
            "primary_source": primary_broker,
            "sources_used": sources_used,
            "aggregation_count": len(sources_used),
            "live_mode": True,
            "aggregated": True,
        }
    
    def disconnect_broker(self, broker_id: str) -> Dict[str, Any]:
        """Disconnect a specific broker"""
        if broker_id not in self.brokers:
            return {"error": f"Unknown broker: {broker_id}"}
        
        service = self.brokers[broker_id]
        return service.disconnect()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of the broker system"""
        connected_brokers = self.get_connected_brokers()
        total_brokers = len(self.brokers)
        
        health_score = (len(connected_brokers) / total_brokers) * 100
        
        return {
            "health_score": health_score,
            "connected_count": len(connected_brokers),
            "total_count": total_brokers,
            "connected_brokers": connected_brokers,
            "status": "healthy" if health_score >= 50 else "degraded" if health_score > 0 else "down",
            "redundancy": "high" if len(connected_brokers) >= 3 else "medium" if len(connected_brokers) >= 2 else "low",
        }

# Singleton instance
broker_manager = BrokerManager()