# Mermaid Test Diagram

## Simple Flowchart Test

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

## Complex Flowchart Test

```mermaid
graph TD
    A["Start: Project Idea"] --> B{"Optional: Analyst Research"}
    B -->|Yes| C["Analyst: Brainstorming"]
    B -->|No| G{"Project Brief Available?"}
    C --> C2["Analyst: Market Research"]
    C2 --> C3["Analyst: Competitor Analysis"]
    C3 --> D["Analyst: Create Project Brief"]
    D --> G
    G -->|Yes| E["PM: Create PRD from Brief"]
    G -->|No| E2["PM: Interactive PRD Creation"]
    E --> F["PRD Created with FRs, NFRs, Epics & Stories"]
    E2 --> F
    F --> H["Architect: Create Architecture"]
    H --> I["PO: Run Master Checklist"]
    I --> J{"Documents Aligned?"}
    J -->|Yes| K["Planning Complete"]
    J -->|No| L["PO: Update Epics & Stories"]
    L --> M["Update PRD/Architecture"]
    M --> I
    K --> N["Ready for Development"]

    style A fill:#f5f5f5,color:#000
    style B fill:#e3f2fd,color:#000
    style C fill:#e8f5e8,color:#000
    style D fill:#fff3e0,color:#000
    style E fill:#f3e5f5,color:#000
    style F fill:#e0f2f1,color:#000
    style H fill:#fce4ec,color:#000
    style I fill:#fff8e1,color:#000
    style K fill:#e8f5e8,color:#000
```

## Trading Engine Workflow Test

```mermaid
graph TD
    A["Market Data Input"] --> B["AI Analysis Engine"]
    B --> C["Strategy Selection"]
    C --> D["Risk Assessment"]
    D --> E{"Risk Acceptable?"}
    E -->|Yes| F["Execute Trade"]
    E -->|No| G["Adjust Strategy"]
    G --> D
    F --> H["Monitor Position"]
    H --> I["Update P&L"]
    I --> J{"Exit Condition?"}
    J -->|Yes| K["Close Position"]
    J -->|No| H
    K --> L["Record Trade"]
    L --> M["Update Strategy Performance"]
    M --> A

    style A fill:#e3f2fd,color:#000
    style B fill:#e8f5e8,color:#000
    style F fill:#fff3e0,color:#000
    style K fill:#fce4ec,color:#000
    style L fill:#f3e5f5,color:#000
```

## Test Instructions

1. Open this file in Cursor
2. Right-click on the tab and select "Open Preview"
3. Check if the Mermaid diagrams render correctly
4. If they don't render, try the troubleshooting steps below

