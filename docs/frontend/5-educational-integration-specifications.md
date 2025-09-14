# **5. Educational Integration Specifications**

### **5.1 Contextual Learning System**

#### **5.1.1 Help Overlay Design**
```html
<!-- Educational overlay specification -->
<div class="educational-overlay" data-trigger="hover" data-delay="1000ms">
    <div class="help-tooltip">
        <h4>Delta (Δ)</h4>
        <p>Measures option price change for ₹1 move in underlying</p>
        <div class="example">
            <strong>Example:</strong> Delta 0.5 means option price 
            increases ₹0.50 for every ₹1 increase in NIFTY
        </div>
        <div class="actions">
            <button>Learn More</button>
            <button>Practice</button>
            <button class="close">×</button>
        </div>
    </div>
</div>
```

#### **5.1.2 Progressive Disclosure Pattern**
1. **Level 1**: Basic tooltips on hover (non-intrusive)
2. **Level 2**: Detailed explanations on click
3. **Level 3**: Interactive tutorials with guided practice
4. **Level 4**: Full educational module with assessments

### **5.2 Learning Progress Integration**

#### **5.2.1 NPU Strip Progress Display**
```css
.educational-progress {
    display: flex;
    align-items: center;
    font-size: 12px;
    color: #666;
}

.progress-indicator {
    display: flex;
    margin-right: 8px;
}

.progress-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 4px;
    background: #ddd;
    transition: background 0.3s;
}

.progress-dot.completed { background: #4CAF50; }
.progress-dot.current { 
    background: #2196F3; 
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

### **5.3 Paper Trading Guided Workflows**

#### **5.3.1 Learning to Live Trading Progression**
```javascript
const learningProgression = {
    stages: [
        {
            name: "Education",
            requirements: ["complete basic modules"],
            duration: "1-2 weeks",
            activities: ["tutorials", "quizzes", "theory"]
        },
        {
            name: "Paper Trading",
            requirements: ["70% education completion"],
            duration: "2-4 weeks", 
            activities: ["simulated trading", "strategy testing"]
        },
        {
            name: "Live Trading",
            requirements: ["profitable paper trading", "risk assessment"],
            duration: "ongoing",
            activities: ["real money trading", "advanced strategies"]
        }
    ]
};
```

---
