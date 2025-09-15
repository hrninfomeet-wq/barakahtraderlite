# Paper Trading Data Isolation Architecture

## Executive Summary

This document defines the data isolation architecture to ensure complete separation between paper and live trading data, addressing DATA-001 (High Risk) for Story 2.1.

## 1. Database Schema Separation

### 1.1 Schema Design Pattern

```sql
-- Separate schemas for paper and live data
CREATE SCHEMA IF NOT EXISTS paper_trading;
CREATE SCHEMA IF NOT EXISTS live_trading;
CREATE SCHEMA IF NOT EXISTS shared_data;  -- For market data, symbols, etc.

-- Paper Trading Schema
CREATE TABLE paper_trading.portfolios (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    cash_balance DECIMAL(15, 2) DEFAULT 500000.00,  -- ₹5 lakh starting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE paper_trading.positions (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER REFERENCES paper_trading.portfolios(id),
    symbol VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(15, 2) NOT NULL,
    current_price DECIMAL(15, 2),
    pnl DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE paper_trading.orders (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER REFERENCES paper_trading.portfolios(id),
    symbol VARCHAR(50) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(15, 2),
    status VARCHAR(20) NOT NULL,
    execution_price DECIMAL(15, 2),
    execution_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_paper_order BOOLEAN DEFAULT TRUE  -- Always true for paper schema
);

-- Live Trading Schema (mirrors paper structure)
CREATE TABLE live_trading.portfolios (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    api_provider VARCHAR(20) NOT NULL,
    account_id VARCHAR(100) NOT NULL,
    cash_balance DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shared Data Schema (read-only for both modes)
CREATE TABLE shared_data.market_data (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    last_price DECIMAL(15, 2),
    volume BIGINT,
    timestamp TIMESTAMP,
    INDEX idx_symbol_timestamp (symbol, timestamp)
);
```

### 1.2 Data Access Layer

```python
# backend/core/data_isolation.py
from enum import Enum
from typing import Optional, Dict, Any
import asyncpg

class DataSchema(Enum):
    PAPER = "paper_trading"
    LIVE = "live_trading"
    SHARED = "shared_data"

class IsolatedDataAccess:
    """Enforces data isolation between paper and live trading"""
    
    def __init__(self):
        self.connections: Dict[DataSchema, asyncpg.Connection] = {}
        self.mode_validator = ModeValidator()
    
    async def get_connection(
        self, 
        mode: TradingMode,
        operation_type: str = "read"
    ) -> asyncpg.Connection:
        """Get connection for appropriate schema based on mode"""
        
        # Validate operation is allowed in mode
        if not self.mode_validator.is_operation_allowed(operation_type, mode):
            raise PermissionError(f"Operation {operation_type} not allowed in {mode}")
        
        # Map mode to schema
        if mode == TradingMode.PAPER:
            schema = DataSchema.PAPER
        elif mode == TradingMode.LIVE:
            schema = DataSchema.LIVE
        else:
            schema = DataSchema.SHARED
        
        # Return isolated connection
        return self.connections[schema]
    
    async def execute_query(
        self,
        query: str,
        mode: TradingMode,
        params: Optional[tuple] = None,
        operation_type: str = "read"
    ):
        """Execute query in appropriate schema"""
        
        # Validate query doesn't cross schemas
        if not self._validate_query_isolation(query, mode):
            raise SecurityException("Query violates schema isolation")
        
        # Get appropriate connection
        conn = await self.get_connection(mode, operation_type)
        
        # Add schema prefix if needed
        query = self._add_schema_prefix(query, mode)
        
        # Execute with audit logging
        result = await conn.fetch(query, *params) if params else await conn.fetch(query)
        
        # Log data access
        await self._audit_data_access(mode, query, operation_type)
        
        return result
    
    def _validate_query_isolation(self, query: str, mode: TradingMode) -> bool:
        """Ensure query doesn't access wrong schema"""
        
        query_lower = query.lower()
        
        # Paper mode cannot access live schema
        if mode == TradingMode.PAPER:
            if "live_trading." in query_lower:
                return False
        
        # Live mode cannot access paper schema (except for migration)
        if mode == TradingMode.LIVE:
            if "paper_trading." in query_lower and not self._is_migration_query(query):
                return False
        
        return True
```

## 2. Data Validation Framework

### 2.1 Entry Point Validation

```python
# backend/services/data_validator.py
class DataValidator:
    """Validates data at all entry points"""
    
    def __init__(self):
        self.validators = {
            TradingMode.PAPER: PaperDataValidator(),
            TradingMode.LIVE: LiveDataValidator()
        }
    
    async def validate_order(
        self, 
        order: Order,
        mode: TradingMode
    ) -> ValidationResult:
        """Validate order data based on mode"""
        
        validator = self.validators[mode]
        
        # Common validations
        if not validator.validate_symbol(order.symbol):
            return ValidationResult(False, "Invalid symbol")
        
        if not validator.validate_quantity(order.quantity):
            return ValidationResult(False, "Invalid quantity")
        
        # Mode-specific validations
        if mode == TradingMode.PAPER:
            return await self._validate_paper_order(order)
        else:
            return await self._validate_live_order(order)
    
    async def _validate_paper_order(self, order: Order) -> ValidationResult:
        """Paper-specific validations"""
        
        # Check virtual portfolio constraints
        portfolio = await self.get_paper_portfolio(order.user_id)
        
        if order.value > portfolio.cash_balance:
            return ValidationResult(False, "Insufficient virtual funds")
        
        # No real API validation needed
        return ValidationResult(True, "Valid paper order")
    
    async def _validate_live_order(self, order: Order) -> ValidationResult:
        """Live-specific validations"""
        
        # Check real portfolio constraints
        portfolio = await self.get_live_portfolio(order.user_id)
        
        if order.value > portfolio.available_margin:
            return ValidationResult(False, "Insufficient margin")
        
        # Validate with broker API
        broker_validation = await self.validate_with_broker(order)
        if not broker_validation.is_valid:
            return broker_validation
        
        return ValidationResult(True, "Valid live order")
```

### 2.2 Data Integrity Checks

```python
# backend/services/data_integrity.py
class DataIntegrityMonitor:
    """Monitors data integrity between modes"""
    
    async def verify_isolation(self):
        """Verify no data leakage between modes"""
        
        issues = []
        
        # Check for paper order IDs in live tables
        paper_ids_in_live = await self.db.fetch("""
            SELECT COUNT(*) as count
            FROM live_trading.orders
            WHERE order_id LIKE 'PAPER_%'
        """)
        
        if paper_ids_in_live[0]['count'] > 0:
            issues.append("Paper order IDs found in live tables")
        
        # Check for live order IDs in paper tables
        live_ids_in_paper = await self.db.fetch("""
            SELECT COUNT(*) as count
            FROM paper_trading.orders
            WHERE order_id NOT LIKE 'PAPER_%'
        """)
        
        if live_ids_in_paper[0]['count'] > 0:
            issues.append("Live order IDs found in paper tables")
        
        # Check for data consistency
        await self.verify_data_consistency()
        
        if issues:
            await self.alert_data_integrity_issues(issues)
            return False
        
        return True
    
    async def verify_data_consistency(self):
        """Verify data consistency within each mode"""
        
        # Paper trading consistency
        paper_issues = await self.db.fetch("""
            SELECT p.id, p.cash_balance, 
                   SUM(pos.quantity * pos.current_price) as position_value
            FROM paper_trading.portfolios p
            LEFT JOIN paper_trading.positions pos ON p.id = pos.portfolio_id
            GROUP BY p.id, p.cash_balance
            HAVING p.cash_balance + COALESCE(SUM(pos.quantity * pos.current_price), 0) 
                   != 500000  -- Initial capital
        """)
        
        if paper_issues:
            await self.log_consistency_issues("paper", paper_issues)
```

## 3. Audit Trail System

### 3.1 Mode Operation Auditing

```python
# backend/services/audit_trail.py
class ModeOperationAuditor:
    """Comprehensive audit trail for mode operations"""
    
    async def audit_mode_operation(
        self,
        operation: str,
        mode: TradingMode,
        user_id: str,
        details: Dict[str, Any]
    ):
        """Record all mode-related operations"""
        
        audit_entry = {
            "id": generate_uuid(),
            "timestamp": datetime.now(),
            "user_id": user_id,
            "mode": mode.value,
            "operation": operation,
            "details": json.dumps(details),
            "ip_address": self.get_client_ip(),
            "session_id": self.get_session_id(),
            "checksum": self.calculate_checksum(details)
        }
        
        # Store in appropriate audit table
        table = f"{mode.value}_trading.audit_log"
        
        await self.db.execute(f"""
            INSERT INTO {table} 
            (id, timestamp, user_id, operation, details, ip_address, session_id, checksum)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, *audit_entry.values())
        
        # Also store in central audit log
        await self.central_audit_log(audit_entry)
    
    async def audit_data_access(
        self,
        schema: DataSchema,
        query: str,
        mode: TradingMode,
        user_id: str
    ):
        """Audit all data access operations"""
        
        await self.db.execute("""
            INSERT INTO shared_data.data_access_log
            (timestamp, user_id, mode, schema_accessed, query_hash, operation_type)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, datetime.now(), user_id, mode.value, schema.value, 
            hashlib.sha256(query.encode()).hexdigest(),
            self.determine_operation_type(query))
```

### 3.2 Cross-Mode Detection

```python
# backend/services/cross_mode_detector.py
class CrossModeDetector:
    """Detects and prevents cross-mode operations"""
    
    async def detect_cross_mode_attempt(
        self,
        requested_mode: TradingMode,
        actual_mode: TradingMode,
        operation: str
    ) -> bool:
        """Detect attempts to perform cross-mode operations"""
        
        if requested_mode != actual_mode:
            # Log security event
            await self.log_security_event({
                "event_type": "cross_mode_attempt",
                "requested_mode": requested_mode.value,
                "actual_mode": actual_mode.value,
                "operation": operation,
                "timestamp": datetime.now(),
                "blocked": True
            })
            
            # Alert security team
            await self.alert_security_team(
                f"Cross-mode operation attempted: {operation}"
            )
            
            return True
        
        return False
```

## 4. Data Migration Tools

### 4.1 Paper to Live Migration

```python
# backend/services/data_migration.py
class PaperToLiveMigration:
    """Tools for migrating strategies from paper to live"""
    
    async def export_paper_strategy(
        self,
        user_id: str,
        strategy_id: str
    ) -> Dict[str, Any]:
        """Export paper trading strategy (read-only)"""
        
        # Get paper trading data
        strategy_data = await self.db.fetch("""
            SELECT * FROM paper_trading.strategies
            WHERE user_id = $1 AND id = $2
        """, user_id, strategy_id)
        
        # Get performance metrics
        performance = await self.db.fetch("""
            SELECT * FROM paper_trading.performance_metrics
            WHERE strategy_id = $1
        """, strategy_id)
        
        # Package for review (no automatic execution)
        return {
            "strategy": strategy_data,
            "performance": performance,
            "warning": "Manual review required before live deployment",
            "exported_at": datetime.now()
        }
    
    async def prepare_live_deployment(
        self,
        paper_strategy: Dict[str, Any]
    ) -> DeploymentPlan:
        """Prepare strategy for live deployment (requires approval)"""
        
        plan = DeploymentPlan()
        
        # Validate strategy performance
        if paper_strategy["performance"]["win_rate"] < 0.6:
            plan.add_warning("Win rate below 60%")
        
        # Scale position sizes for live trading
        plan.position_scaling = 0.1  # Start with 10% of paper size
        
        # Add safety limits
        plan.daily_loss_limit = 10000  # ₹10,000 max daily loss
        plan.position_limit = 5  # Max 5 positions
        
        # Require manual approval
        plan.requires_approval = True
        plan.approval_checklist = [
            "Review all paper trades",
            "Verify risk parameters",
            "Confirm position sizing",
            "Set stop losses"
        ]
        
        return plan
```

## 5. Implementation Architecture

### 5.1 Service Layer Integration

```python
# backend/services/trading_service.py
class TradingService:
    """Main trading service with data isolation"""
    
    def __init__(self):
        self.data_access = IsolatedDataAccess()
        self.validator = DataValidator()
        self.auditor = ModeOperationAuditor()
    
    async def place_order(
        self,
        order: Order,
        mode: TradingMode
    ):
        """Place order with full data isolation"""
        
        # Validate data
        validation = await self.validator.validate_order(order, mode)
        if not validation.is_valid:
            raise ValidationError(validation.message)
        
        # Audit operation start
        await self.auditor.audit_mode_operation(
            "place_order", mode, order.user_id, order.dict()
        )
        
        # Execute in isolated schema
        if mode == TradingMode.PAPER:
            result = await self._place_paper_order(order)
        else:
            result = await self._place_live_order(order)
        
        # Audit operation complete
        await self.auditor.audit_mode_operation(
            "order_placed", mode, order.user_id, result
        )
        
        return result
```

## 6. Monitoring and Alerts

### 6.1 Data Isolation Monitoring

```python
# backend/services/isolation_monitor.py
class IsolationMonitor:
    """Monitors data isolation integrity"""
    
    async def continuous_monitoring(self):
        """Run continuous isolation checks"""
        
        while True:
            # Check schema isolation
            isolation_valid = await self.verify_schema_isolation()
            
            # Check for cross-mode queries
            cross_mode_attempts = await self.check_cross_mode_queries()
            
            # Check data consistency
            consistency_valid = await self.verify_data_consistency()
            
            # Generate metrics
            metrics = {
                "isolation_valid": isolation_valid,
                "cross_mode_attempts": cross_mode_attempts,
                "consistency_valid": consistency_valid,
                "timestamp": datetime.now()
            }
            
            # Alert if issues
            if not isolation_valid or cross_mode_attempts > 0:
                await self.alert_data_isolation_breach(metrics)
            
            # Sleep for next check
            await asyncio.sleep(60)  # Check every minute
```

## 7. Risk Mitigation Summary

This data isolation architecture addresses DATA-001 (High Risk) by:

1. **Complete schema separation** prevents data mixing
2. **Validation at all entry points** ensures data integrity
3. **Comprehensive audit trails** track all operations
4. **Cross-mode detection** prevents unauthorized access
5. **Continuous monitoring** detects isolation breaches

## 8. Implementation Checklist

- [ ] Create separate database schemas
- [ ] Implement IsolatedDataAccess class
- [ ] Add DataValidator for all entry points
- [ ] Create ModeOperationAuditor
- [ ] Implement CrossModeDetector
- [ ] Set up continuous monitoring
- [ ] Create data migration tools
- [ ] Add integration tests
- [ ] Document data flow diagrams
- [ ] Create operational runbooks
