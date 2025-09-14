"""
System API endpoints for health monitoring and status
"""
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from models.trading import APIProvider, HealthStatus
from services.multi_api_manager import MultiAPIManager
from core.database import DatabaseManager, AuditLogger


router = APIRouter(prefix="/system", tags=["system"])


class HealthStatusResponse(BaseModel):
    """API health status response"""
    provider: str
    status: str
    last_check: datetime
    response_time_ms: float = None
    error_message: str = None
    consecutive_failures: int = 0
    rate_limit_remaining: int = None


class SystemStatusResponse(BaseModel):
    """Overall system status response"""
    timestamp: datetime
    total_apis: int
    healthy_apis: int
    unhealthy_apis: int
    api_statuses: List[HealthStatusResponse]


# Dependency injection for MultiAPIManager
async def get_api_manager() -> MultiAPIManager:
    """Get MultiAPIManager instance"""
    # In a real application, this would come from dependency injection
    # For now, we'll create a placeholder
    db_manager = DatabaseManager()
    db_manager.initialize()
    audit_logger = AuditLogger(db_manager)
    
    config = {
        "enabled_apis": ["flattrade", "fyers", "upstox", "alice_blue"],
        "routing_rules": {},
        "fallback_chain": ["fyers", "upstox", "flattrade", "alice_blue"]
    }
    
    api_manager = MultiAPIManager(config, audit_logger)
    await api_manager.initialize_apis()
    
    return api_manager


@router.get("/health", response_model=SystemStatusResponse)
async def get_system_health(api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get overall system health status
    """
    try:
        health_statuses = await api_manager.get_health_status()
        
        api_status_responses = []
        healthy_count = 0
        unhealthy_count = 0
        
        for api_name, status_data in health_statuses.items():
            api_status = HealthStatusResponse(
                provider=api_name,
                status=status_data["status"].value,
                last_check=status_data["last_check"],
                consecutive_failures=0,  # Would be tracked in real implementation
                rate_limit_remaining=status_data["rate_limits"].get("current_second", 0)
            )
            
            api_status_responses.append(api_status)
            
            if status_data["status"] == HealthStatus.HEALTHY:
                healthy_count += 1
            else:
                unhealthy_count += 1
        
        return SystemStatusResponse(
            timestamp=datetime.now(),
            total_apis=len(health_statuses),
            healthy_apis=healthy_count,
            unhealthy_apis=unhealthy_count,
            api_statuses=api_status_responses
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/health/{provider}", response_model=HealthStatusResponse)
async def get_api_health(provider: str, api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get health status for specific API provider
    """
    try:
        # Validate provider
        try:
            api_provider = APIProvider(provider.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid API provider: {provider}")
        
        health_statuses = await api_manager.get_health_status()
        
        if provider.lower() not in health_statuses:
            raise HTTPException(status_code=404, detail=f"API provider {provider} not found")
        
        status_data = health_statuses[provider.lower()]
        
        return HealthStatusResponse(
            provider=provider.lower(),
            status=status_data["status"].value,
            last_check=status_data["last_check"],
            consecutive_failures=0,  # Would be tracked in real implementation
            rate_limit_remaining=status_data["rate_limits"].get("current_second", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API health: {str(e)}")


@router.post("/health/{provider}/check")
async def trigger_health_check(provider: str, api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Manually trigger health check for specific API provider
    """
    try:
        # Validate provider
        try:
            api_provider = APIProvider(provider.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid API provider: {provider}")
        
        # Get API instance
        api = api_manager.apis.get(provider.lower())
        if not api:
            raise HTTPException(status_code=404, detail=f"API provider {provider} not found")
        
        # Trigger health check
        is_healthy = await api.health_check()
        
        return {
            "provider": provider.lower(),
            "healthy": is_healthy,
            "timestamp": datetime.now(),
            "message": f"Health check {'passed' if is_healthy else 'failed'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")


@router.get("/rate-limits")
async def get_rate_limits(api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get rate limit information for all APIs
    """
    try:
        rate_limits = {}
        
        for api_name, api in api_manager.apis.items():
            rate_limits[api_name] = api.get_rate_limits()
        
        return {
            "timestamp": datetime.now(),
            "rate_limits": rate_limits
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limits: {str(e)}")


@router.get("/rate-limits/{provider}")
async def get_api_rate_limits(provider: str, api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get rate limit information for specific API provider
    """
    try:
        # Validate provider
        try:
            api_provider = APIProvider(provider.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid API provider: {provider}")
        
        api = api_manager.apis.get(provider.lower())
        if not api:
            raise HTTPException(status_code=404, detail=f"API provider {provider} not found")
        
        return {
            "provider": provider.lower(),
            "timestamp": datetime.now(),
            "rate_limits": api.get_rate_limits()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API rate limits: {str(e)}")


@router.get("/dashboard/overview")
async def get_dashboard_overview(api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get comprehensive dashboard overview with real-time usage percentages, 
    historical patterns, and optimization suggestions (AC1.2.4)
    """
    try:
        # Get all dashboard data
        rate_analytics = await api_manager.get_rate_limit_analytics()
        load_analytics = await api_manager.get_load_balancing_insights()
        optimization_suggestions = await api_manager.get_optimization_suggestions()
        health_status = await api_manager.get_health_status()
        
        # Calculate overall system metrics
        total_apis = len(health_status)
        healthy_apis = sum(1 for status in health_status.values() 
                          if status["status"] == HealthStatus.HEALTHY)
        
        # Calculate average usage across all APIs
        total_usage = 0
        active_apis = 0
        for api_name, analytics in rate_analytics.items():
            usage = analytics['rate_limit_status']['usage_percentages']['second_usage']
            if usage > 0:
                total_usage += usage
                active_apis += 1
        
        avg_usage = (total_usage / active_apis * 100) if active_apis > 0 else 0
        
        return {
            "timestamp": datetime.now(),
            "system_overview": {
                "total_apis": total_apis,
                "healthy_apis": healthy_apis,
                "average_usage_percentage": round(avg_usage, 2),
                "load_balance_efficiency": load_analytics.get('load_balance_efficiency', 0)
            },
            "api_details": rate_analytics,
            "load_balancing": load_analytics,
            "optimization_suggestions": optimization_suggestions,
            "alerts": [
                suggestion for suggestion in optimization_suggestions 
                if suggestion['type'] in ['high_usage_warning', 'approaching_limit']
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/dashboard/usage-patterns")
async def get_usage_patterns(api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get historical usage patterns for analytics and trend analysis
    """
    try:
        rate_analytics = await api_manager.get_rate_limit_analytics()
        
        # Extract usage patterns from each API
        patterns = {}
        for api_name, analytics in rate_analytics.items():
            predictive = analytics.get('predictive_analytics', {})
            patterns[api_name] = {
                "current_usage": analytics['rate_limit_status']['usage_percentages'],
                "trend": predictive.get('trend', 0),
                "volatility": predictive.get('volatility', 0),
                "prediction_accuracy": predictive.get('prediction_accuracy', 0),
                "last_spike_detected": predictive.get('last_spike_detected'),
                "total_requests": analytics['rate_limit_status']['total_requests'],
                "blocked_requests": analytics['rate_limit_status']['blocked_requests']
            }
        
        return {
            "timestamp": datetime.now(),
            "usage_patterns": patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage patterns: {str(e)}")


@router.get("/dashboard/performance-metrics")
async def get_performance_metrics(api_manager: MultiAPIManager = Depends(get_api_manager)):
    """
    Get detailed performance metrics for all APIs
    """
    try:
        load_analytics = await api_manager.get_load_balancing_insights()
        
        return {
            "timestamp": datetime.now(),
            "performance_metrics": load_analytics,
            "routing_efficiency": {
                "total_routings": load_analytics.get('total_routings', 0),
                "api_distribution": load_analytics.get('api_distribution', {}),
                "load_balance_efficiency": load_analytics.get('load_balance_efficiency', 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")
