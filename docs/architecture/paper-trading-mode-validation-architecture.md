# Paper Trading Mode Validation Architecture

## Executive Summary

This document defines the comprehensive mode validation architecture for Story 2.1, addressing the critical risk (TECH-001) of paper trades potentially reaching live APIs.

## 1. Mode Validation Framework

### 1.1 Core Principles

- **Fail-Safe Design**: Default to paper mode if mode is undefined
- **Multiple Validation Layers**: Check mode at multiple points in execution flow
- **Immutable Mode Context**: Mode cannot be changed during operation execution
- **Audit Trail**: All mode switches are logged with timestamps and user confirmation

### 1.2 Mode States

```python
from enum import Enum

class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    MAINTENANCE = "maintenance"  # No trading allowed

class ModeContext:
    """Immutable mode context for operation execution"""
    
    def __init__(self, mode: TradingMode, user_id: str, session_id: str):
        self._mode = mode
        self._user_id = user_id
        self._session_id = session_id
        self._created_at = datetime.now()
        self._validation_token = self._generate_validation_token()
    
    @property
    def mode(self) -> TradingMode:
        return self._mode
    
    def validate(self) -> bool:
        """Validate mode context integrity"""
        return self._validate_token() and self._validate_session()
```

## 2. Modified MultiAPIManager Architecture

### 2.1 Enhanced execute_with_fallback Method

```python
class MultiAPIManager:
    """Enhanced with mode validation"""
    
    def __init__(self, config: Dict):
        # Existing initialization
        self.apis: Dict[str, TradingAPIInterface] = {}
        self.paper_trading_engine = PaperTradingEngine()
        self.mode_validator = ModeValidator()
        self.current_mode: TradingMode = TradingMode.PAPER  # Default to PAPER
    
    async def execute_with_fallback(
        self, 
        operation: str, 
        mode_context: ModeContext = None,
        **kwargs
    ) -> Any:
        """Execute operation with mode validation"""
        
        # LAYER 1: Mode Context Validation
        if not mode_context:
            mode_context = await self._get_current_mode_context()
        
        if not mode_context.validate():
            raise SecurityException("Invalid mode context")
        
        # LAYER 2: Operation Permission Check
        if not self.mode_validator.is_operation_allowed(operation, mode_context.mode):
            raise PermissionError(f"Operation {operation} not allowed in {mode_context.mode} mode")
        
        # LAYER 3: Route to Appropriate Engine
        if mode_context.mode == TradingMode.PAPER:
            return await self._execute_paper_trading(operation, **kwargs)
        elif mode_context.mode == TradingMode.LIVE:
            return await self._execute_live_trading(operation, mode_context, **kwargs)
        else:
            raise InvalidModeException(f"Invalid mode: {mode_context.mode}")
    
    async def _execute_paper_trading(self, operation: str, **kwargs) -> Any:
        """Execute in paper trading mode - NEVER touches live APIs"""
        # All operations routed to paper trading engine
        return await self.paper_trading_engine.execute(operation, **kwargs)
    
    async def _execute_live_trading(
        self, 
        operation: str, 
        mode_context: ModeContext,
        **kwargs
    ) -> Any:
        """Execute in live trading mode with additional validation"""
        
        # LAYER 4: Final Safety Check
        if not await self._confirm_live_execution(operation, mode_context):
            raise SafetyCheckException("Live execution safety check failed")
        
        # Existing live trading logic
        preferred_apis = self.routing_rules.get(operation, self.fallback_chain)
        # ... rest of existing implementation
```

### 2.2 Mode Validator Component

```python
class ModeValidator:
    """Validates operations against mode permissions"""
    
    OPERATION_PERMISSIONS = {
        TradingMode.PAPER: {
            "place_order": True,
            "cancel_order": True,
            "get_portfolio": True,
            "get_market_data": True,
            "modify_order": True,
            "get_positions": True,
            "authenticate": False,  # No real auth in paper mode
            "transfer_funds": False,  # Never allowed in paper mode
        },
        TradingMode.LIVE: {
            # All operations allowed in live mode
            "place_order": True,
            "cancel_order": True,
            "get_portfolio": True,
            "get_market_data": True,
            "modify_order": True,
            "get_positions": True,
            "authenticate": True,
            "transfer_funds": True,
        },
        TradingMode.MAINTENANCE: {
            # Read-only operations in maintenance
            "get_portfolio": True,
            "get_market_data": True,
            "get_positions": True,
            # No trading operations
            "place_order": False,
            "cancel_order": False,
            "modify_order": False,
            "authenticate": False,
            "transfer_funds": False,
        }
    }
    
    def is_operation_allowed(self, operation: str, mode: TradingMode) -> bool:
        """Check if operation is allowed in given mode"""
        permissions = self.OPERATION_PERMISSIONS.get(mode, {})
        return permissions.get(operation, False)
```

## 3. Failsafe Mechanisms

### 3.1 Multiple Validation Layers

1. **Frontend Validation**: Mode indicator and confirmation dialogs
2. **API Gateway Validation**: Mode header validation
3. **Service Layer Validation**: Mode context validation
4. **Execution Layer Validation**: Final safety checks

### 3.2 Mode Switch Protection

```python
class ModeSwitchController:
    """Controls mode switching with multiple safeguards"""
    
    async def switch_mode(
        self,
        from_mode: TradingMode,
        to_mode: TradingMode,
        user_id: str,
        confirmation_token: str
    ) -> bool:
        """Switch trading mode with safeguards"""
        
        # 1. Validate user permissions
        if not await self._validate_user_permissions(user_id, to_mode):
            return False
        
        # 2. Verify confirmation token (from UI dialog)
        if not await self._verify_confirmation_token(confirmation_token):
            return False
        
        # 3. Check for pending operations
        if await self._has_pending_operations():
            raise PendingOperationsException("Cannot switch mode with pending operations")
        
        # 4. Create audit log
        await self._audit_mode_switch(from_mode, to_mode, user_id)
        
        # 5. Update mode with transaction
        async with self.db.transaction():
            await self._update_mode(to_mode)
            await self._invalidate_old_sessions()
            await self._create_new_mode_context(to_mode, user_id)
        
        # 6. Broadcast mode change
        await self._broadcast_mode_change(to_mode)
        
        return True
```

### 3.3 Emergency Stop Mechanism

```python
class EmergencyStop:
    """Emergency stop for all trading operations"""
    
    async def activate(self, reason: str):
        """Immediately stop all trading operations"""
        
        # 1. Set mode to MAINTENANCE
        await self.mode_controller.force_mode(TradingMode.MAINTENANCE)
        
        # 2. Cancel all pending orders
        await self.cancel_all_pending_orders()
        
        # 3. Close all WebSocket connections
        await self.close_all_connections()
        
        # 4. Alert administrators
        await self.alert_administrators(reason)
        
        # 5. Create incident report
        await self.create_incident_report(reason)
```

## 4. Integration Points

### 4.1 Backend Services Integration

```python
# backend/services/multi_api_manager.py
class MultiAPIManager:
    # Add mode validation to existing class
    
# backend/services/paper_trading.py
class PaperTradingEngine:
    # New service for paper trading execution
    
# backend/services/mode_controller.py
class ModeController:
    # New service for mode management
```

### 4.2 Database Schema Extensions

```sql
-- Mode tracking table
CREATE TABLE trading_modes (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    switched_at TIMESTAMP NOT NULL,
    switched_from VARCHAR(20),
    confirmation_token VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Mode audit log
CREATE TABLE mode_audit_log (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    from_mode VARCHAR(20),
    to_mode VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    reason TEXT,
    confirmed BOOLEAN DEFAULT FALSE
);
```

### 4.3 API Endpoints

```python
# backend/api/v1/mode_management.py
@router.post("/mode/switch")
async def switch_mode(
    request: ModeSwitchRequest,
    current_user: User = Depends(get_current_user)
):
    """Switch between paper and live modes"""
    
@router.get("/mode/current")
async def get_current_mode(
    current_user: User = Depends(get_current_user)
):
    """Get current trading mode"""
    
@router.post("/mode/emergency-stop")
async def emergency_stop(
    request: EmergencyStopRequest,
    current_user: User = Depends(get_current_user)
):
    """Activate emergency stop"""
```

## 5. Testing Strategy

### 5.1 Unit Tests

```python
# backend/tests/unit/test_mode_validation.py
class TestModeValidation:
    def test_paper_mode_blocks_live_apis(self):
        """Verify paper mode never reaches live APIs"""
    
    def test_mode_context_immutability(self):
        """Verify mode context cannot be modified"""
    
    def test_failsafe_mechanisms(self):
        """Test all failsafe mechanisms"""
```

### 5.2 Integration Tests

```python
# backend/tests/integration/test_mode_switching.py
class TestModeSwitching:
    def test_mode_switch_with_pending_operations(self):
        """Verify mode switch blocked with pending operations"""
    
    def test_emergency_stop_activation(self):
        """Test emergency stop mechanism"""
```

## 6. Monitoring and Alerts

### 6.1 Mode Switch Monitoring

- Track all mode switches with timestamps
- Alert on unusual mode switching patterns
- Monitor failed mode switch attempts

### 6.2 Safety Violation Alerts

- Alert on any attempt to execute live operations in paper mode
- Alert on validation failures
- Alert on emergency stop activation

## 7. Risk Mitigation Summary

This architecture addresses TECH-001 (Critical Risk) by:

1. **Multiple validation layers** prevent accidental live trades
2. **Immutable mode context** ensures mode consistency
3. **Failsafe mechanisms** provide multiple safety nets
4. **Audit trails** enable tracking and debugging
5. **Emergency stop** provides immediate halt capability

## 8. Implementation Priority

1. **Phase 1**: Core mode validation in MultiAPIManager
2. **Phase 2**: Mode controller and switching logic
3. **Phase 3**: Database schema and audit logging
4. **Phase 4**: Emergency stop mechanism
5. **Phase 5**: Monitoring and alerts
