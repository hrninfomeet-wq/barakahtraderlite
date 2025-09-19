"""
Market Data API Endpoints
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
# import json  # Unused

from models.market_data import (
    MarketData, MarketDataRequest, MarketDataResponse,
    DataType, ValidationTier, SubscriptionRequest
)
from services.market_data_service import MarketDataPipeline
from services.fallback_data_source_manager import FallbackDataSourceManager, DataSource, DataSourcePriority

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/market-data", tags=["Market Data"])

# Global market data pipeline instance
market_data_pipeline: Optional[MarketDataPipeline] = None
fallback_manager: Optional[FallbackDataSourceManager] = None


async def get_market_data_pipeline() -> MarketDataPipeline:
    """Get or create market data pipeline instance"""
    global market_data_pipeline
    if market_data_pipeline is None:
        market_data_pipeline = MarketDataPipeline()
        await market_data_pipeline.initialize()
    return market_data_pipeline


async def get_fallback_manager() -> FallbackDataSourceManager:
    """Get or create fallback manager instance"""
    global fallback_manager
    if fallback_manager is None:
        fallback_manager = FallbackDataSourceManager()

        # Add sample data sources
        fyers_source = DataSource(
            source_id="fyers",
            name="FYERS API",
            priority=DataSourcePriority.PRIMARY,
            api_endpoint="wss://api-t1.fyers.in/data/websocket",
            max_symbols=200
        )

        upstox_source = DataSource(
            source_id="upstox",
            name="UPSTOX API",
            priority=DataSourcePriority.SECONDARY,
            api_endpoint="wss://api.upstox.com/index/websocket",
            max_symbols=10000
        )

        fallback_source = DataSource(
            source_id="fallback",
            name="Fallback API",
            priority=DataSourcePriority.FALLBACK,
            api_endpoint="https://api.example.com/market-data",
            max_symbols=1000
        )

        fallback_manager.add_data_source(fyers_source)
        fallback_manager.add_data_source(upstox_source)
        fallback_manager.add_data_source(fallback_source)

        await fallback_manager.initialize()
    return fallback_manager


@router.post("/get", response_model=MarketDataResponse)
async def get_market_data(
    request: MarketDataRequest,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get market data for specified symbols with real-time processing
    """
    try:
        logger.info(f"Market data request received for {len(request.symbols)} symbols")

        # Process request through pipeline
        response = await pipeline.get_market_data(request)

        return response

    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market data: {str(e)}") from e


@router.get("/symbols/{symbol}", response_model=MarketData)
async def get_single_symbol_data(
    symbol: str,
    data_types: List[DataType] = None,
    max_age_seconds: float = 1.0,
    validation_tier: ValidationTier = ValidationTier.FAST,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get market data for a single symbol
    """
    if data_types is None:
        data_types = [DataType.PRICE]

    try:
        request = MarketDataRequest(
            symbols=[symbol],
            data_types=data_types,
            max_age_seconds=max_age_seconds,
            validation_tier=validation_tier
        )

        response = await pipeline.get_market_data(request)

        if symbol not in response.data:
            raise HTTPException(status_code=404, detail=f"No data available for symbol: {symbol}")

        return response.data[symbol]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting single symbol data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data for {symbol}: {str(e)}") from e


@router.get("/batch", response_model=MarketDataResponse)
async def get_batch_market_data(
    symbols: str,  # Comma-separated symbols
    data_types: List[DataType] = None,
    max_age_seconds: float = 1.0,
    validation_tier: ValidationTier = ValidationTier.FAST,
    priority: int = 1,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get market data for multiple symbols (comma-separated)
    """
    if data_types is None:
        data_types = [DataType.PRICE]

    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")

        if len(symbol_list) > 100:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Too many symbols requested (max 100)")

        request = MarketDataRequest(
            symbols=symbol_list,
            data_types=data_types,
            max_age_seconds=max_age_seconds,
            validation_tier=validation_tier,
            priority=priority
        )

        response = await pipeline.get_market_data(request)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch market data: {str(e)}") from e


@router.post("/subscribe")
async def subscribe_to_symbols(
    request: SubscriptionRequest,
    background_tasks: BackgroundTasks,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Subscribe to real-time market data for symbols
    """
    try:
        symbols = request.symbols

        # Subscribe to symbols
        success = await pipeline.subscribe_to_symbols(symbols)

        if success:
            return {"message": f"Successfully subscribed to {len(symbols)} symbols", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to subscribe to symbols")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to symbols: {str(e)}")


@router.delete("/unsubscribe")
async def unsubscribe_from_symbols(
    symbols: List[str],
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Unsubscribe from real-time market data for symbols
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")

        # Unsubscribe from symbols
        success = await pipeline.unsubscribe_from_symbols(symbols)

        if success:
            return {"message": f"Successfully unsubscribed from {len(symbols)} symbols", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unsubscribe from symbols")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe from symbols: {str(e)}")


@router.get("/stream/{symbols}")
async def stream_market_data(
    symbols: str,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Stream real-time market data for symbols (Server-Sent Events)
    """
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")

        async def generate_stream():
            """Generate SSE stream of market data"""
            # Subscribe to symbols first
            await pipeline.subscribe_to_symbols(symbol_list)

            # Create data handler for streaming
            async def data_handler(data: MarketData):
                if data:
                    yield f"data: {data.json()}\n\n"

            # Add handler to pipeline
            pipeline.add_data_handler(data_handler)

            # Keep connection alive
            while True:
                yield "data: {\"type\": \"heartbeat\", \"timestamp\": \"" + datetime.now().isoformat() + "\"}\n\n"
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream market data: {str(e)}")


@router.get("/status")
async def get_pipeline_status(
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get comprehensive pipeline status
    """
    try:
        status = pipeline.get_pipeline_status()
        return status

    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get performance metrics for the market data pipeline
    """
    try:
        status = pipeline.get_pipeline_status()
        return {
            "performance_metrics": status["performance_metrics"],
            "connection_status": status["connection_status"],
            "validation_metrics": status["validation_metrics"],
            "performance_architecture_metrics": status["performance_architecture_metrics"]
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/sources/status")
async def get_data_sources_status(
    fallback_manager: FallbackDataSourceManager = Depends(get_fallback_manager)
):
    """
    Get status of all data sources
    """
    try:
        status = fallback_manager.get_manager_status()
        return status

    except Exception as e:
        logger.error(f"Error getting data sources status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources status: {str(e)}")


@router.post("/sources/{source_id}/health-check")
async def trigger_health_check(
    source_id: str,
    fallback_manager: FallbackDataSourceManager = Depends(get_fallback_manager)
):
    """
    Trigger health check for a specific data source
    """
    try:
        if source_id not in fallback_manager.data_sources:
            raise HTTPException(status_code=404, detail=f"Data source not found: {source_id}")

        source = fallback_manager.data_sources[source_id]
        is_healthy = await source.health_check()

        return {
            "source_id": source_id,
            "is_healthy": is_healthy,
            "status": source.status.value,
            "availability_score": source.availability_score
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering health check for {source_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")


@router.get("/validation/metrics")
async def get_validation_metrics(
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get data validation metrics
    """
    try:
        status = pipeline.get_pipeline_status()
        return status["validation_metrics"]

    except Exception as e:
        logger.error(f"Error getting validation metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get validation metrics: {str(e)}")


@router.get("/cache/status")
async def get_cache_status(
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get cache performance status
    """
    try:
        status = pipeline.get_pipeline_status()
        performance_metrics = status["performance_architecture_metrics"]

        return {
            "l1_cache": performance_metrics["l1_cache"],
            "l2_cache": performance_metrics["l2_cache"],
            "cache_hit_rate": status["performance_metrics"]["cache_hit_rate"]
        }

    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")


@router.post("/cache/warm")
async def warm_cache(
    symbols: List[str],
    background_tasks: BackgroundTasks,
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Warm cache with data for specified symbols
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")

        if len(symbols) > 100:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Too many symbols requested (max 100)")

        # Warm cache in background
        async def warm_cache_task():
            try:
                request = MarketDataRequest(
                    symbols=symbols,
                    data_types=[DataType.PRICE],
                    max_age_seconds=5.0,
                    validation_tier=ValidationTier.FAST
                )
                await pipeline.get_market_data(request)
                logger.info(f"Cache warmed for {len(symbols)} symbols")
            except Exception as e:
                logger.error(f"Error warming cache: {e}")

        background_tasks.add_task(warm_cache_task)

        return {"message": f"Cache warming initiated for {len(symbols)} symbols", "status": "initiated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    pipeline: MarketDataPipeline = Depends(get_market_data_pipeline)
):
    """
    Get recent alerts from the system
    """
    try:
        # This would return recent alerts from the pipeline
        # For now, return empty list as alerts are handled internally
        return {"alerts": [], "message": "Alert system is operational"}

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the market data service
    """
    try:
        # Basic health check
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "market-data-api",
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
