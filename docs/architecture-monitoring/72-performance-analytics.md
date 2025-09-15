# **7.2 Performance Analytics**

```python
class PerformanceAnalytics:
    """Advanced performance analytics and optimization"""
    
    def __init__(self):
        self.metrics_database = MetricsDatabase()
        self.analytics_engine = AnalyticsEngine()
        
    async def analyze_trading_performance(self) -> TradingAnalytics:
        """Comprehensive trading performance analysis"""
        trades = await self.get_recent_trades(days=30)
        
        analytics = TradingAnalytics()
        analytics.total_trades = len(trades)
        analytics.winning_trades = len([t for t in trades if t.pnl > 0])
        analytics.win_rate = analytics.winning_trades / analytics.total_trades
        analytics.total_pnl = sum(trade.pnl for trade in trades)
        analytics.average_profit = analytics.total_pnl / analytics.total_trades
        analytics.sharpe_ratio = await self.calculate_sharpe_ratio(trades)
        analytics.max_drawdown = await self.calculate_max_drawdown(trades)
        
        return analytics
    
    async def analyze_system_performance(self) -> SystemAnalytics:
        """System performance analysis"""
        metrics = await self.metrics_database.get_recent_metrics(hours=24)
        
        analytics = SystemAnalytics()
        analytics.avg_response_time = np.mean([m.response_time for m in metrics])
        analytics.p95_response_time = np.percentile([m.response_time for m in metrics], 95)
        analytics.avg_npu_utilization = np.mean([m.npu_utilization for m in metrics])
        analytics.error_rate = len([m for m in metrics if m.has_error]) / len(metrics)
        analytics.uptime_percentage = await self.calculate_uptime(metrics)
        
        return analytics
```

---
