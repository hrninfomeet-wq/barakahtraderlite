# **2. Global Header & NPU Status Strip**

### **2.1 NPU Status Strip Design**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🧠NPU:87% 📊GPU:45% 💾RAM:2.1GB │ 📚F&O Progress:●●●●○ 67% │ 🔴LIVE│⚡API:4/4 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### **Components (Left to Right)**
1. **Hardware Metrics** (First 40%)
   - NPU Utilization: Real-time percentage with color coding
   - GPU Usage: Graphics processing load indicator
   - RAM Usage: Current memory consumption in GB
   - Color Code: Green (<70%), Yellow (70-85%), Red (>85%)

2. **Educational Progress** (Middle 30%)
   - Progress dots showing F&O learning completion
   - Percentage indicator for current module
   - Subtle animation for active learning
   - Click to open learning center

3. **System Status** (Right 30%)
   - Trading Mode: LIVE (red) / PAPER (blue) indicator
   - API Health: Connected APIs count with green lightning bolt
   - Emergency stop button (always visible)
   - Profile/settings access

### **2.2 Mode Toggle Specifications**

#### **Paper Trading Integration (Algotest Style)**
```
┌─────────────────────────────────────────────────────────────────┐
│ Mode: [LIVE] [PAPER] │ Paper P&L: +₹2,345 (5.2%) │ Virtual Cash: ₹50,000 │
└─────────────────────────────────────────────────────────────────┘
```

- **Visual Distinction**: 
  - LIVE mode: Red border, solid background
  - PAPER mode: Blue border, dashed background
- **Always Visible**: Mode indicator appears in every interface element
- **One-Click Toggle**: Single click switches modes with confirmation dialog
- **Data Continuity**: Both modes maintain separate performance tracking

---
