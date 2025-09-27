# **7. Monitoring & Observability**

## **7.1 System Monitoring Architecture**

```python
class SystemMonitor:
    """Comprehensive system monitoring and alerting"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.performance_tracker = PerformanceTracker()
        
    async def monitor_system_health(self):
        """Continuous system health monitoring"""
        while True:
            health_metrics = await self.collect_health_metrics()
            
            # Check critical metrics
            for metric_name, value in health_metrics.items():
                threshold = self.get_threshold(metric_name)
                if self.exceeds_threshold(value, threshold):
                    await self.alert_manager.send_alert(
                        metric_name, value, threshold
                    )
            
            # Store metrics for historical analysis
            await self.metrics_collector.store_metrics(health_metrics)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def collect_health_metrics(self) -> Dict[str, float]:
        """Collect comprehensive system health metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'npu_utilization': await self.get_npu_utilization(),
            'gpu_utilization': await self.get_gpu_utilization(),
            'api_response_times': await self.measure_api_response_times(),
            'database_performance': await self.measure_db_performance(),
            'cache_hit_ratio': await self.get_cache_hit_ratio(),
            'active_connections': await self.count_active_connections(),
            'error_rate': await self.calculate_error_rate()
        }

class AlertManager:
    """Intelligent alerting system"""
    
    def __init__(self):
        self.alert_channels = {
            'console': ConsoleAlerts(),
            'desktop': DesktopNotifications(),
            'email': EmailAlerts(),  # Optional
            'sms': SMSAlerts()       # Optional
        }
        
    async def send_alert(self, metric: str, value: float, threshold: float):
        """Send alerts through configured channels"""
        alert_message = self.format_alert_message(metric, value, threshold)
        
        # Determine alert severity
        severity = self.calculate_severity(metric, value, threshold)
        
        # Send through appropriate channels
        for channel_name, channel in self.alert_channels.items():
            if await self.should_use_channel(channel_name, severity):
                await channel.send_alert(alert_message, severity)
```

## **7.2 Performance Analytics**

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
