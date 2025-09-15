# **1. Overall Layout Architecture**

### **1.1 Multi-Monitor Adaptive Layout**

#### **Primary Display (14.5" Laptop - 1920x1080)**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Global Header] NPU Strip | Mode Toggle | API Health | Profile  │
├─────────────────────────────────────────────────────────────────┤
│ [Tab Navigation] Dashboard | Charts | F&O | BTST | Portfolio |  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     ACTIVE TAB CONTENT                         │
│                   (Optimized for Touch)                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [Quick Actions Strip] Buy/Sell | Emergency Stop | Alerts       │
└─────────────────────────────────────────────────────────────────┘
```

#### **Secondary Display (27" 4K - 3840x2160) - When Connected**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTENDED CHART WORKSPACE                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                          │
│  │ Chart 1 │ │ Chart 2 │ │ Chart 3 │ │ Chart 4 │                          │
│  │ NIFTY   │ │BankNIFTY│ │ FINNIFTY│ │ Custom  │                          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                          │
│                                                                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│  │  Order Book     │ │  Greeks Matrix  │ │ System Monitor  │             │
│  │  Live Orders    │ │  Portfolio Risk │ │ API Performance │             │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **1.2 Tab System Architecture (TradingView Inspired)**

#### **6 Primary Tabs (Reduced from 8 per requirements)**
1. **Dashboard** - Main trading overview and quick actions
2. **Charts** - Multi-chart analysis with expandable layout
3. **F&O Strategy** - Options strategies and Greeks calculator
4. **BTST Intelligence** - AI-powered overnight trading (active 2:15 PM+)
5. **Portfolio** - Cross-API holdings and performance analytics
6. **System** - Debugging, settings, and educational center

#### **Tab Behavior Specifications**
- **Expandable to Full Screen**: Any tab can expand to full screen with `F11` or double-click
- **Persistent State**: Each tab maintains its state when switching
- **Configurable Layout**: Chart count and arrangement configurable in settings
- **Touch Gestures**: Swipe left/right for tab navigation on touch screen
- **Keyboard Shortcuts**: `Ctrl+1` through `Ctrl+6` for quick tab switching

---
