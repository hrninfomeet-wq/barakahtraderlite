# **6. Risk Management & Compliance**

## **6.1 Comprehensive Risk Framework**

```python
class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self):
        self.daily_loss_limit = 50000  # ₹50,000 daily loss limit
        self.position_limits = {
            'single_stock': 0.10,      # 10% of portfolio
            'sector_exposure': 0.25,    # 25% per sector
            'options_exposure': 0.30,   # 30% in options
            'overnight_exposure': 0.20  # 20% overnight positions
        }
        self.current_exposure = {}
        
    async def validate_order(self, order: OrderRequest) -> RiskValidation:
        """Comprehensive order validation"""
        validations = [
            await self.check_daily_loss_limit(order),
            await self.check_position_limits(order),
            await self.check_margin_availability(order),
            await self.check_concentration_risk(order),
            await self.check_correlation_risk(order)
        ]
        
        failed_checks = [v for v in validations if not v.passed]
        
        if failed_checks:
            return RiskValidation(
                approved=False,
                reason='; '.join([check.reason for check in failed_checks])
            )
        
        return RiskValidation(approved=True)
    
    async def monitor_portfolio_risk(self):
        """Continuous portfolio risk monitoring"""
        while True:
            portfolio = await self.get_current_portfolio()
            
            # Calculate portfolio-level risk metrics
            var_95 = await self.calculate_var(portfolio, confidence=0.95)
            max_drawdown = await self.calculate_max_drawdown(portfolio)
            correlation_matrix = await self.calculate_correlations(portfolio)
            
            # Check risk thresholds
            if var_95 > self.var_limit:
                await self.trigger_risk_alert('VAR_EXCEEDED', var_95)
            
            if max_drawdown > self.drawdown_limit:
                await self.trigger_risk_alert('DRAWDOWN_EXCEEDED', max_drawdown)
            
            await asyncio.sleep(60)  # Check every minute during market hours
```

## **6.2 SEBI Compliance Framework**

```python
class ComplianceManager:
    """SEBI regulatory compliance management"""
    
    def __init__(self):
        self.position_limits = {
            'equity_single': 5000000,    # ₹50L per equity stock
            'index_futures': 10000000,   # ₹1Cr in index futures
            'options_premium': 2000000,  # ₹20L options premium
        }
        self.reporting_requirements = {
            'trade_reporting': True,
            'position_reporting': True,
            'risk_disclosure': True,
            'audit_trail': True
        }
    
    async def validate_regulatory_compliance(self, order: OrderRequest) -> bool:
        """Validate order against SEBI regulations"""
        
        # Check position limits
        if not await self.check_position_limits(order):
            return False
        
        # Validate trading hours
        if not await self.check_trading_hours(order):
            return False
        
        # Check market segment permissions
        if not await self.check_segment_permissions(order):
            return False
        
        return True
    
    async def generate_compliance_reports(self):
        """Generate required compliance reports"""
        reports = {
            'daily_trading_summary': await self.generate_daily_summary(),
            'position_report': await self.generate_position_report(),
            'risk_report': await self.generate_risk_report(),
            'audit_trail': await self.generate_audit_trail()
        }
        
        return reports
```

---
