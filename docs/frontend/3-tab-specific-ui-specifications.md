# **3. Tab-Specific UI Specifications**

### **3.1 Dashboard Tab - Main Trading Overview**

#### **3.1.1 Layout Structure (Single Screen)**
```
┌─────────────────────────────────────────────────────────────────┐
│ Market Overview: NIFTY 25,840 (+127) │ Time: 14:35:22 │ Vol: High│
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │   Positions     │ │  Active Orders  │ │ Today's P&L     │   │
│ │  NIFTY25840CE   │ │  Buy 100 @25845│ │  Total: +₹4,567 │   │
│ │  +₹2,340 (4.2%) │ │  Status: Open   │ │  Realized: ₹890 │   │
│ │                 │ │                 │ │  MTM: +₹3,677   │   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │  API Health     │ │ Quick Actions   │ │ Market Alerts   │   │
│ │ ✅FLATTRADE     │ │ [BUY] [SELL]    │ │ NIFTY >25850    │   │
│ │ ✅FYERS         │ │ [SL] [TARGET]   │ │ VIX Spike: +15% │   │
│ │ ✅UPSTOX        │ │ [EMERGENCY STOP]│ │ 3 Pattern Alerts│   │
│ │ ⚠️ALICE BLUE    │ │                 │ │                 │   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.1.2 Touch Interaction Specifications**
- **Large Touch Targets**: Minimum 44px x 44px for all interactive elements
- **Swipe Gestures**: 
  - Swipe right on position: Quick sell
  - Swipe left on position: Quick buy more
  - Long press: Context menu with detailed options
- **Haptic Feedback**: Subtle vibration for successful order placement
- **Multi-touch Support**: Pinch to zoom on any data table

#### **3.1.3 Real-Time Data Updates**
- **Update Frequency**: 250ms for prices, 500ms for P&L, 1s for portfolio metrics
- **WebSocket Indicators**: Small pulse animation when receiving live data
- **Offline Handling**: Gray overlay with "Reconnecting..." when APIs disconnect
- **Performance Monitoring**: Response time displayed for each data source

### **3.2 Charts Tab - Multi-Chart Analysis**

#### **3.2.1 TradingView-Inspired Layout System**

##### **Default 4-Chart Layout (Configurable)**
```
┌─────────────────────────────────────────────────────────────────┐
│ Layout: [1] [2x2] [1x3] [2x1] │ Symbol: NIFTY │ Interval: 5min │
├─────────────────┬───────────────┬───────────────┬───────────────┤
│                 │               │               │               │
│   NIFTY 50      │   BANKNIFTY   │   FINNIFTY    │   SENSEX      │
│   Chart 1       │   Chart 2     │   Chart 3     │   Chart 4     │
│   ●NPU Pattern  │   ●Volume     │   ●RSI        │   ●MACD       │
│                 │               │               │               │
│   [Expand] [⚙]  │   [Expand] [⚙]│   [Expand] [⚙]│   [Expand] [⚙]│
└─────────────────┴───────────────┴───────────────┴───────────────┘
│ TimeFrame Sync: ☑ │ Pattern Alerts: 3 Active │ FII Flow: +₹340Cr│
└─────────────────────────────────────────────────────────────────┘
```

#### **3.2.2 Chart Configuration Options**
- **Layout Options**: 1, 2x2, 1x3, 2x1, 4x1, 1x4 (user selectable)
- **Symbol Management**: Quick symbol search with Indian market focus
- **Timeframe Synchronization**: Option to sync all charts to same timeframe
- **Template System**: Save/load chart configurations
- **Full-Screen Mode**: Double-click any chart to expand to full tab

#### **3.2.3 NPU-Accelerated Features**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 AI Pattern Recognition: [ON] │ Confidence: 8.4/10 │ 3 Alerts  │
├─────────────────────────────────────────────────────────────────┤
│ ▼ Detected Patterns (Last 5min):                               │
│ ✅ Double Bottom (8.7/10) - Entry: 25,835 Target: 25,890      │
│ ⚠️ Rising Wedge (7.2/10) - Caution: Potential reversal        │
│ 🔍 Triangle Formation (6.8/10) - Watch for breakout           │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.2.4 Touch and Gesture Controls**
- **Pinch to Zoom**: Horizontal and vertical zooming with momentum
- **Pan Gestures**: Two-finger pan for chart navigation
- **Tap Interactions**: Single tap for crosshair, double tap for zoom fit
- **Drawing Tools**: Touch-optimized trendline and shape drawing
- **Context Menus**: Long press for chart-specific options

### **3.3 F&O Strategy Tab - Options Trading Center**

#### **3.3.1 Strategy Dashboard Layout**
```
┌─────────────────────────────────────────────────────────────────┐
│ Active Strategies (3) │ Paper: ☑ │ Greeks Auto-Calc: ☑ │ Help: ? │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │ Iron Condor #1  │ │ Straddle #2     │ │ Calendar #3     │   │
│ │ NIFTY 25800-900 │ │ BANKNIFTY ATM   │ │ NIFTY Dec/Jan   │   │
│ │ P&L: +₹1,245    │ │ P&L: -₹234      │ │ P&L: +₹567      │   │
│ │ Δ:-0.02 Θ:-45   │ │ Δ:0.0 Θ:-78     │ │ Δ:0.15 Θ:-12    │   │
│ │ Days: 12 left   │ │ Days: 5 left    │ │ Days: 28 left   │   │
│ │ [Adjust] [Close]│ │ [Adjust] [Close]│ │ [Adjust] [Close]│   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ Portfolio Greeks: Δ:+0.13 Γ:+0.008 Θ:-135 ν:+2.4 ρ:+45      │
│ Risk Level: ●●●○○ (Medium) │ Max Loss: ₹12,450 │ Alerts: 1   │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.3.2 Strategy Builder Interface**
```
┌─────────────────────────────────────────────────────────────────┐
│ Create New Strategy: [Iron Condor ▼] │ Mode: Paper ☑ │ Help: ?  │
├─────────────────────────────────────────────────────────────────┤
│ Symbol: [NIFTY ▼] │ Expiry: [28-SEP ▼] │ Spot: 25,840        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                Strategy Visualization                       │ │
│ │        Risk/Reward Graph (Live Updated)                    │ │
│ │   ┌────┬────┬────┬────┬────┬────┬────┬────┬────┐          │ │
│ │   │    │    │    │▲   │▲▲▲ │▲▲▲ │▲   │    │    │          │ │
│ │   └────┴────┴────┴────┴────┴────┴────┴────┴────┘          │ │
│ │   25700  25750  25800  25850  25900  25950  26000        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ Legs Configuration:                                             │
│ 1. Buy 25800 PE │ Qty: 50 │ Premium: ₹45 │ [Auto-Fill]        │
│ 2. Sell 25850 PE│ Qty: 50 │ Premium: ₹78 │ [Auto-Fill]        │
│ 3. Sell 25850 CE│ Qty: 50 │ Premium: ₹82 │ [Auto-Fill]        │
│ 4. Buy 25900 CE │ Qty: 50 │ Premium: ₹51 │ [Auto-Fill]        │
│                                                                 │
│ Net Premium: ₹3,200 │ Max Profit: ₹5,700 │ Max Loss: ₹2,300   │
│ [Preview] [Execute] [Save Template] [Educational Guide]        │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.3.3 Educational Integration**
- **Contextual Help**: `?` buttons throughout interface for strategy explanations
- **Interactive Tooltips**: Hover/touch for Greeks definitions and calculations
- **Guided Tours**: First-time user walkthrough of strategy building
- **Video Integration**: Embedded tutorial videos for complex strategies
- **Progress Tracking**: Visual progress indicators for learning modules

### **3.4 BTST Intelligence Tab - AI-Powered Overnight Trading**

#### **3.4.1 Time-Sensitive Activation (2:15 PM+ Only)**

##### **Before 2:15 PM Display**
```
┌─────────────────────────────────────────────────────────────────┐
│ ⏰ BTST Analysis Available After 2:15 PM IST                   │
│                                                                 │
│ Current Time: 13:45:22 IST                                     │
│ Next Analysis: 14:15:00 IST (29 minutes 38 seconds)           │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              Yesterday's Performance                        │ │
│ │  Recommendations: 3 │ Executed: 2 │ Success Rate: 100%     │ │
│ │  Total P&L: +₹4,567 │ Avg Confidence: 8.9/10              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 📚 While You Wait: Review BTST Educational Content            │
│ [Learn BTST Strategies] [Historical Analysis] [Risk Management] │
└─────────────────────────────────────────────────────────────────┘
```

##### **After 2:15 PM - Active Analysis**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 AI BTST Analysis Active │ Time: 14:25:22 │ Analysis: Complete │
├─────────────────────────────────────────────────────────────────┤
│ Today's Recommendations:                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ RELIANCE │ Conf: 9.2/10 │ Entry: ₹2,845 │ Target: +2.5% │ │
│ │ Analysis: Strong FII inflow, bullish pattern, +ve sentiment │ │
│ │ Risk: ₹1,500 │ Position: 5 shares │ [Execute] [Details]    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⚠️ TCS │ Conf: 7.8/10 │ Below Threshold - Not Recommended  │ │
│ │ Analysis: Mixed signals, earnings uncertainty               │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 🚫 Zero-Force Policy: 1 stock qualified today (Minimum 8.5/10) │
│ Yesterday: 0 qualified │ This Week: 3/5 days with trades      │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.4.2 AI Confidence Visualization**
```
┌─────────────────────────────────────────────────────────────────┐
│ Confidence Score Breakdown: RELIANCE (9.2/10)                 │
├─────────────────────────────────────────────────────────────────┤
│ Technical Analysis: ●●●●● 5/5 │ Strong bullish breakout        │
│ FII/DII Flow:      ●●●●○ 4/5 │ Positive institutional buying  │
│ News Sentiment:    ●●●●○ 4/5 │ Favorable earnings preview     │
│ Volume Analysis:   ●●●●● 5/5 │ Above average participation    │
│ Market Regime:     ●●●○○ 3/5 │ Neutral to slightly bullish   │
│ Options Flow:      ●●●●○ 4/5 │ Call buying dominance          │
├─────────────────────────────────────────────────────────────────┤
│ Overall Score: 25/30 → 8.3/10 → Qualified ✅                   │
└─────────────────────────────────────────────────────────────────┘
```

### **3.5 Portfolio Tab - Cross-API Holdings Management**

#### **3.5.1 Unified Portfolio View**
```
┌─────────────────────────────────────────────────────────────────┐
│ Portfolio Value: ₹2,45,678 │ Day P&L: +₹4,567 (1.9%) │ Mode: LIVE │
├─────────────────────────────────────────────────────────────────┤
│ API Breakdown:                                                  │
│ FLATTRADE: ₹1,23,450 │ FYERS: ₹67,890 │ UPSTOX: ₹54,338      │
├─────────────────────────────────────────────────────────────────┤
│ Holdings:                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │Symbol   │Qty │Avg Cost│ LTP  │P&L    │%    │API       │Action││ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │RELIANCE │10  │₹2,840  │₹2,865│+₹250  │+0.9%│FLATTRADE │[Sell]││ │
│ │TCS      │5   │₹3,450  │₹3,465│+₹75   │+0.4%│FYERS     │[Sell]││ │
│ │NIFTY CE │50  │₹45     │₹52   │+₹350  │+15.5%│UPSTOX    │[Sell]││ │
│ │BANK PUT │25  │₹78     │₹65   │-₹325  │-16.7%│FLATTRADE │[Buy] ││ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ Risk Metrics:                                                   │
│ VaR (95%): ₹8,450 │ Max Drawdown: -2.3% │ Sharpe: 2.4        │
│ Greeks: Δ:+0.25 Γ:+0.02 Θ:-45 ν:+1.8 │ Beta: 1.1            │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.5.2 Performance Analytics Dashboard**
```
┌─────────────────────────────────────────────────────────────────┐
│ Performance Period: [Today ▼] [This Week] [This Month] [YTD]    │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │   Returns       │ │ Risk Metrics    │ │ Benchmark       │   │
│ │ Total: +18.5%   │ │ Volatility: 22% │ │ NIFTY: +15.2%   │   │
│ │ This Month:+3.2%│ │ Sharpe: 2.4     │ │ Outperf: +3.3%  │   │
│ │ Best Day: +4.1% │ │ Max DD: -5.1%   │ │ Beta: 1.1       │   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ Strategy Attribution:                                           │
│ F&O Strategies: +₹12,450 (54%) │ Index Scalping: +₹8,900 (39%) │
│ BTST Trades: +₹3,200 (14%) │ Long Holdings: -₹1,550 (-7%)     │
└─────────────────────────────────────────────────────────────────┘
```

### **3.6 System Tab - Debugging, Settings & Education**

#### **3.6.1 System Performance Monitor**
```
┌─────────────────────────────────────────────────────────────────┐
│ System Health: ✅ Optimal │ Uptime: 2d 14h 23m │ Last Restart: - │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │   Hardware      │ │   API Status    │ │  Performance    │   │
│ │ NPU: 87% (13T)  │ │ ✅ FLATTRADE    │ │ Latency: 23ms   │   │
│ │ GPU: 45% (77T)  │ │ ✅ FYERS        │ │ Orders: <30ms   │   │
│ │ RAM: 18.2/32GB  │ │ ✅ UPSTOX       │ │ Data: <100ms    │   │
│ │ CPU: 34%        │ │ ⚠️ ALICE BLUE   │ │ Charts: <100ms  │   │
│ │ SSD: 2.1TB free │ │                 │ │ NPU: <10ms      │   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ Recent Events:                                                  │
│ 14:25:22 - BTST analysis completed (3 candidates)              │
│ 14:20:15 - Pattern detected: NIFTY Double Bottom (8.7/10)      │
│ 14:18:30 - Order executed: Buy 50 NIFTY 25840 CE @ ₹52        │
│ 14:15:00 - Alice Blue API reconnected after 2min downtime     │
└─────────────────────────────────────────────────────────────────┘
```

#### **3.6.2 Educational Learning Center**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📚 F&O Learning Center │ Progress: 67% │ Next: Volatility Trading │
├─────────────────────────────────────────────────────────────────┤
│ Learning Paths:                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ Options Basics      │ 100% │ 8 lessons completed        │ │
│ │ ✅ Greeks Mastery      │ 100% │ 12 lessons completed       │ │
│ │ 🔄 Strategy Building   │ 45%  │ 6/13 lessons (In Progress) │ │
│ │ ⏳ Risk Management     │ 0%   │ 10 lessons (Not Started)  │ │
│ │ ⏳ Volatility Trading  │ 0%   │ 15 lessons (Not Started)  │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ Quick Practice:                                                 │
│ [Greeks Calculator] [Strategy Simulator] [Paper Trading] [Quiz] │
│                                                                 │
│ Recent Achievement: 🏆 "Iron Condor Master" - Completed 5      │
│ successful Iron Condor trades in paper trading mode            │
└─────────────────────────────────────────────────────────────────┘
```

---
