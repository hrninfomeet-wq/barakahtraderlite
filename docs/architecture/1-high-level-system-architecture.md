# **1. High-Level System Architecture**

## **1.1 Overall Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          YOGA PRO 7 HARDWARE PLATFORM                       │
├─────────────┬──────────────┬──────────────┬─────────────┬─────────────────┤
│ Intel NPU   │ Intel GPU    │ CPU Cores    │ Memory      │ Storage         │
│ 13 TOPS     │ 77 TOPS      │ 16 Cores     │ 32GB RAM    │ 1TB NVMe SSD   │
│ AI Models   │ Greeks Calc  │ Multi-API    │ Data Cache  │ Historical Data │
│ Pattern Rec │ Backtesting  │ Processing   │ Live Feed   │ Trade Logs      │
└─────────────┴──────────────┴──────────────┴─────────────┴─────────────────┘
                                    ↑
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐│
│ │   Frontend UI   │ │  Core Backend   │ │   AI/ML Engine  │ │ Data Layer  ││
│ │   (Streamlit)   │ │   (FastAPI)     │ │  (Multi-Model)  │ │ (SQLite +   ││
│ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤ │  Redis)     ││
│ │• Touch Support  │ │• Multi-API Mgmt │ │• NPU Acceleration│ │• Real-time  ││
│ │• Multi-Monitor  │ │• Order Engine   │ │• Pattern Recog  │ │• Historical ││
│ │• Paper Trading  │ │• Risk Mgmt      │ │• BTST Scoring   │ │• Audit Trail││
│ │• Educational    │ │• Portfolio Mgmt │ │• Greeks Calc    │ │• Compliance ││
│ │• Debug Console  │ │• Strategy Engine│ │• Gemini Pro     │ │• Trade Data ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↑
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATIONS LAYER                             │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│   Trading APIs  │   Market Data   │   AI Services   │   Compliance        │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────┤
│• FLATTRADE      │• Google Finance │• Gemini Pro     │• SEBI Audit Trail  │
│• FYERS          │• NSE/BSE APIs   │• Local LLMs     │• Position Limits    │
│• UPSTOX         │• MCX APIs       │• Lenovo AI Now  │• Risk Controls      │
│• Alice Blue     │• FYERS Feed     │• OpenAI (Opt)   │• Tax Reporting      │
│• Smart Routing  │• UPSTOX Feed    │• Claude (Opt)   │• Compliance Logs   │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────┘
```

## **1.2 Component Interaction Flow**

```
User Interface → Backend API → Multi-API Router → Trading/Data APIs
     ↓              ↓              ↓                    ↓
NPU Status ← AI/ML Engine ← Pattern Recognition ← Market Data
     ↓              ↓              ↓                    ↓
Educational ← Strategy Engine ← Greeks Calculator ← F&O Analysis
     ↓              ↓              ↓                    ↓
Paper Trading ← Risk Manager ← Portfolio Engine ← Position Data
     ↓              ↓              ↓                    ↓
Debug Console ← System Monitor ← Performance Tracker ← Audit Logger
```

---
