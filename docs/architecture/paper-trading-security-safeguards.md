# Paper Trading Security Safeguards Architecture

## Executive Summary

This document defines comprehensive security safeguards to prevent mode confusion and accidental live trades, addressing SEC-001 (High Risk) for Story 2.1.

## 1. Visual Mode Indicators

### 1.1 Global Mode Display

```python
# frontend/components/mode_indicator.py
class ModeIndicator:
    """Prominent mode indicator component"""
    
    MODES = {
        TradingMode.LIVE: {
            "icon": "🔴",
            "text": "LIVE",
            "color": "#FF0000",
            "border": "solid 3px red",
            "background": "rgba(255, 0, 0, 0.1)",
            "pulse": True,
            "warning_level": "critical"
        },
        TradingMode.PAPER: {
            "icon": "🔵",
            "text": "PAPER",
            "color": "#0066CC",
            "border": "dashed 3px blue",
            "background": "rgba(0, 102, 204, 0.05)",
            "pulse": False,
            "warning_level": "safe"
        },
        TradingMode.MAINTENANCE: {
            "icon": "🟡",
            "text": "MAINTENANCE",
            "color": "#FFA500",
            "border": "solid 3px orange",
            "background": "rgba(255, 165, 0, 0.1)",
            "pulse": True,
            "warning_level": "warning"
        }
    }
    
    def render(self, current_mode: TradingMode):
        """Render mode indicator with appropriate styling"""
        mode_config = self.MODES[current_mode]
        
        return st.container():
            # Sticky header that follows scroll
            st.markdown(f"""
                <div class="mode-indicator {mode_config['warning_level']}" 
                     style="position: sticky; 
                            top: 0; 
                            z-index: 9999;
                            border: {mode_config['border']};
                            background: {mode_config['background']};
                            animation: {'pulse 2s infinite' if mode_config['pulse'] else 'none'};">
                    <span style="color: {mode_config['color']}; 
                                 font-size: 24px; 
                                 font-weight: bold;">
                        {mode_config['icon']} {mode_config['text']} MODE
                    </span>
                </div>
            """, unsafe_allow_html=True)
```

### 1.2 Component-Level Indicators

```python
# frontend/components/trading_components.py
class TradingComponent:
    """Base class for all trading components"""
    
    def render_with_mode_context(self, mode: TradingMode):
        """Render component with mode-specific styling"""
        
        if mode == TradingMode.LIVE:
            # Red border for all interactive elements
            self.add_class("live-mode-component")
            self.show_warning("⚠️ LIVE TRADING - Real Money at Risk")
        elif mode == TradingMode.PAPER:
            # Blue dashed border for paper mode
            self.add_class("paper-mode-component")
            self.show_info("📝 Paper Trading - No Real Money")
        
        # Render actual component
        self.render_content()
```

### 1.3 Order Confirmation Dialogs

```python
# frontend/components/order_confirmation.py
class OrderConfirmationDialog:
    """Enhanced confirmation dialog with mode awareness"""
    
    def show_confirmation(self, order: Order, mode: TradingMode):
        """Show confirmation dialog based on mode"""
        
        if mode == TradingMode.LIVE:
            return self._show_live_confirmation(order)
        else:
            return self._show_paper_confirmation(order)
    
    def _show_live_confirmation(self, order: Order):
        """Live trading confirmation with multiple checks"""
        
        # Step 1: Mode warning
        st.error("🔴 LIVE TRADING MODE - REAL MONEY WILL BE USED")
        
        # Step 2: Order details
        st.write(f"""
            **Order Details:**
            - Symbol: {order.symbol}
            - Type: {order.order_type}
            - Quantity: {order.quantity}
            - Price: ₹{order.price}
            - Total Value: ₹{order.quantity * order.price}
        """)
        
        # Step 3: Checkbox confirmation
        confirm_understanding = st.checkbox(
            "I understand this is a LIVE trade with real money"
        )
        
        # Step 4: Text confirmation
        typed_confirmation = st.text_input(
            "Type 'CONFIRM LIVE' to proceed:"
        )
        
        # Step 5: Final button (disabled until confirmations)
        if confirm_understanding and typed_confirmation == "CONFIRM LIVE":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Execute Live Trade", type="primary"):
                    return True
            with col2:
                if st.button("❌ Cancel", type="secondary"):
                    return False
        
        return False
    
    def _show_paper_confirmation(self, order: Order):
        """Paper trading confirmation (simpler)"""
        
        st.info("🔵 Paper Trading Mode - Simulated Trade")
        
        st.write(f"""
            **Order Details (Paper):**
            - Symbol: {order.symbol}
            - Quantity: {order.quantity}
            - Virtual Value: ₹{order.quantity * order.price}
        """)
        
        if st.button("Execute Paper Trade"):
            return True
        
        return False
```

## 2. Mode Switching Security

### 2.1 Mode Switch Dialog

```python
# frontend/components/mode_switch_dialog.py
class ModeSwitchDialog:
    """Secure mode switching with multiple confirmations"""
    
    async def request_mode_switch(
        self, 
        from_mode: TradingMode, 
        to_mode: TradingMode
    ):
        """Request mode switch with security checks"""
        
        # Check for pending operations
        pending = await self.check_pending_operations()
        if pending:
            st.error(f"Cannot switch modes: {len(pending)} pending operations")
            return False
        
        # Different flows for different transitions
        if to_mode == TradingMode.LIVE:
            return await self._switch_to_live(from_mode)
        elif to_mode == TradingMode.PAPER:
            return await self._switch_to_paper(from_mode)
        else:
            return await self._switch_to_maintenance(from_mode)
    
    async def _switch_to_live(self, from_mode: TradingMode):
        """Switch to live mode with enhanced security"""
        
        st.warning("⚠️ SWITCHING TO LIVE TRADING MODE")
        
        # Step 1: Education
        st.info("""
            **Live Trading Mode means:**
            - Real money will be used
            - Real orders will be placed
            - Real profits and losses
            - Cannot be undone
        """)
        
        # Step 2: Account verification
        st.subheader("Verify Your Account")
        password = st.text_input("Enter password:", type="password")
        
        # Step 3: 2FA if enabled
        if self.user_has_2fa():
            totp_code = st.text_input("Enter 2FA code:")
            if not self.verify_2fa(totp_code):
                st.error("Invalid 2FA code")
                return False
        
        # Step 4: Cooling period with async countdown
        placeholder = st.empty()
        for seconds in range(5, 0, -1):
            placeholder.info(f"Please wait {seconds} seconds before confirming...")
            await asyncio.sleep(1)
        placeholder.success("You may now confirm")
        
        # Step 5: Final confirmation
        confirm_text = st.text_input(
            "Type 'ENABLE LIVE TRADING' to confirm:"
        )
        
        if confirm_text == "ENABLE LIVE TRADING":
            # Generate confirmation token
            token = self.generate_confirmation_token()
            
            # Execute switch
            success = await self.mode_controller.switch_mode(
                from_mode, 
                TradingMode.LIVE,
                token
            )
            
            if success:
                st.success("Switched to LIVE mode")
                st.balloons()
                return True
        
        return False
```

### 2.2 Session-Based Mode Persistence

```python
# backend/services/session_manager.py
class SessionModeManager:
    """Manages mode persistence across sessions"""
    
    def __init__(self):
        self.redis_client = redis.Redis()
        self.session_timeout = 3600  # 1 hour
    
    async def set_session_mode(
        self, 
        session_id: str, 
        mode: TradingMode,
        user_id: str
    ):
        """Set mode for session with expiry"""
        
        session_data = {
            "mode": mode.value,
            "user_id": user_id,
            "set_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        }
        
        # Store in Redis with expiry
        self.redis_client.setex(
            f"session:mode:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        # Also store in database for audit
        await self.db.execute("""
            INSERT INTO session_modes 
            (session_id, user_id, mode, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, session_id, user_id, mode.value, 
            datetime.now(), 
            datetime.now() + timedelta(seconds=self.session_timeout)
        )
    
    async def get_session_mode(self, session_id: str) -> Optional[TradingMode]:
        """Get mode for session"""
        
        # Try Redis first (fast)
        session_data = self.redis_client.get(f"session:mode:{session_id}")
        
        if session_data:
            data = json.loads(session_data)
            return TradingMode(data["mode"])
        
        # Fallback to database
        result = await self.db.fetchone("""
            SELECT mode FROM session_modes 
            WHERE session_id = ? 
            AND expires_at > ?
        """, session_id, datetime.now())
        
        if result:
            return TradingMode(result["mode"])
        
        # Default to paper mode for safety
        return TradingMode.PAPER
```

## 3. Frontend Security Implementation

### 3.1 Streamlit App Integration

```python
# frontend/app.py
import streamlit as st
from components.mode_indicator import ModeIndicator
from components.mode_switch_dialog import ModeSwitchDialog
from services.session_manager import SessionModeManager

class TradingApp:
    """Main trading application with mode security"""
    
    def __init__(self):
        self.mode_indicator = ModeIndicator()
        self.mode_switch_dialog = ModeSwitchDialog()
        self.session_manager = SessionModeManager()
    
    def run(self):
        """Run the trading application"""
        
        # Initialize session state
        if 'mode' not in st.session_state:
            st.session_state.mode = self.get_persisted_mode()
        
        # Always show mode indicator at top
        self.mode_indicator.render(st.session_state.mode)
        
        # Mode switch button in sidebar
        with st.sidebar:
            self.render_mode_controls()
        
        # Main content area
        self.render_main_content()
    
    def render_mode_controls(self):
        """Render mode switching controls"""
        
        st.subheader("Trading Mode")
        
        current_mode = st.session_state.mode
        st.write(f"Current: {current_mode.value.upper()}")
        
        # Mode switch buttons
        if current_mode == TradingMode.PAPER:
            if st.button("🔴 Switch to LIVE"):
                if self.mode_switch_dialog.request_mode_switch(
                    current_mode, 
                    TradingMode.LIVE
                ):
                    st.session_state.mode = TradingMode.LIVE
                    st.rerun()
        
        elif current_mode == TradingMode.LIVE:
            if st.button("🔵 Switch to PAPER"):
                if self.mode_switch_dialog.request_mode_switch(
                    current_mode, 
                    TradingMode.PAPER
                ):
                    st.session_state.mode = TradingMode.PAPER
                    st.rerun()
        
        # Emergency stop button (always visible)
        st.divider()
        if st.button("🛑 EMERGENCY STOP", type="primary"):
            self.activate_emergency_stop()
```

### 3.2 CSS Styling for Mode Indicators

```css
/* frontend/assets/css/mode-indicators.css */

/* Global mode indicator */
.mode-indicator {
    position: sticky;
    top: 0;
    z-index: 9999;
    padding: 10px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 20px;
}

.mode-indicator.critical {
    animation: pulse-red 2s infinite;
}

.mode-indicator.warning {
    animation: pulse-orange 2s infinite;
}

/* Component-level indicators */
.live-mode-component {
    border: 3px solid red !important;
    box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
}

.paper-mode-component {
    border: 3px dashed blue !important;
    background: rgba(0, 102, 204, 0.02);
}

/* Animations */
@keyframes pulse-red {
    0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
    50% { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
}

@keyframes pulse-orange {
    0% { box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.7); }
    50% { box-shadow: 0 0 0 10px rgba(255, 165, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 165, 0, 0); }
}

/* Confirmation dialogs */
.live-confirmation-dialog {
    border: 5px solid red;
    background: rgba(255, 0, 0, 0.05);
    padding: 20px;
    border-radius: 10px;
}

.paper-confirmation-dialog {
    border: 3px dashed blue;
    background: rgba(0, 102, 204, 0.02);
    padding: 15px;
    border-radius: 10px;
}
```

## 4. Backend Security Implementation

### 4.1 API Security Headers

```python
# backend/api/middleware/mode_security.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

class ModeSecurityMiddleware:
    """Middleware for mode security validation"""
    
    async def __call__(self, request: Request, call_next):
        """Validate mode in request headers"""
        
        # Extract mode from header
        mode_header = request.headers.get("X-Trading-Mode")
        
        # Validate mode header
        if not mode_header:
            # Default to paper mode for safety
            request.state.mode = TradingMode.PAPER
        else:
            try:
                request.state.mode = TradingMode(mode_header.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid trading mode: {mode_header}"
                )
        
        # Add mode to request context
        response = await call_next(request)
        
        # Add mode to response headers
        response.headers["X-Current-Mode"] = request.state.mode.value
        
        return response
```

### 4.2 Mode Validation Decorators

```python
# backend/api/decorators/mode_validation.py
from functools import wraps

def require_mode(allowed_modes: List[TradingMode]):
    """Decorator to enforce mode requirements"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            current_mode = request.state.mode
            
            if current_mode not in allowed_modes:
                raise HTTPException(
                    status_code=403,
                    detail=f"Operation not allowed in {current_mode.value} mode"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# Usage example
@router.post("/orders/place")
@require_mode([TradingMode.LIVE, TradingMode.PAPER])
async def place_order(order: OrderRequest, request: Request):
    """Place an order (works in both live and paper modes)"""
    pass

@router.post("/funds/transfer")
@require_mode([TradingMode.LIVE])
async def transfer_funds(transfer: TransferRequest, request: Request):
    """Transfer funds (only in live mode)"""
    pass
```

## 5. Monitoring and Alerts

### 5.1 Mode Confusion Detection

```python
# backend/services/mode_monitor.py
class ModeMonitor:
    """Monitors for mode confusion patterns"""
    
    async def detect_confusion_patterns(self, user_id: str):
        """Detect potential mode confusion"""
        
        patterns = []
        
        # Pattern 1: Rapid mode switching
        recent_switches = await self.get_recent_mode_switches(user_id, hours=1)
        if len(recent_switches) > 3:
            patterns.append("rapid_mode_switching")
        
        # Pattern 2: Failed live operations in paper mode
        failed_ops = await self.get_failed_operations(user_id, hours=24)
        if failed_ops > 5:
            patterns.append("repeated_mode_errors")
        
        # Pattern 3: Unusual trading patterns after mode switch
        if await self.detect_unusual_patterns(user_id):
            patterns.append("unusual_post_switch_behavior")
        
        if patterns:
            await self.alert_user(user_id, patterns)
            await self.log_confusion_event(user_id, patterns)
```

## 6. Risk Mitigation Summary

This security architecture addresses SEC-001 (High Risk) by:

1. **Prominent visual indicators** prevent mode confusion
2. **Multiple confirmation steps** for mode switching
3. **Session-based persistence** maintains mode consistency
4. **Security validations** at multiple layers
5. **Monitoring and alerts** detect confusion patterns

## 7. Implementation Checklist

- [ ] Implement global mode indicator component
- [ ] Add mode-specific styling to all components
- [ ] Create confirmation dialogs with appropriate checks
- [ ] Implement session-based mode persistence
- [ ] Add API security middleware
- [ ] Create mode validation decorators
- [ ] Set up monitoring and alerts
- [ ] Add CSS animations and styling
- [ ] Implement emergency stop mechanism
- [ ] Create comprehensive test suite
