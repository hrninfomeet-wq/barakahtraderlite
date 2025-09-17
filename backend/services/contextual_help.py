"""
Contextual Help Service
Provides real-time contextual help and tips
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from models.strategy import OptionsStrategy, PositionType
from models.trading import TradingPosition, Portfolio
from services.greeks_calculator import greeks_calculator

class ContextualHelpSystem:
    """Provides contextual help based on user actions and positions"""
    
    def __init__(self):
        """Initialize contextual help system"""
        self.help_database: Dict[str, Dict[str, Any]] = self._load_help_content()
        logger.info("Contextual Help System initialized")
    
    def _load_help_content(self) -> Dict[str, Dict[str, Any]]:
        """Load help content database"""
        return {
            "position_help": {
                "long_call": {
                    "description": "Long call gives you the right to buy at strike price",
                    "risks": ["Limited to premium paid", "Time decay"],
                    "tips": ["Use when expecting price increase", "Monitor delta"]
                },
                # Add more position types...
            },
            "portfolio_warnings": {
                "high_delta": "Your portfolio has high delta exposure - consider hedging",
                "high_theta": "Significant time decay risk - monitor positions close to expiry"
            },
            "educational_tips": {
                "beginner": ["Start with basic strategies", "Learn Greeks first"],
                "advanced": ["Consider volatility trades", "Use multi-leg strategies"]
            }
        }
    
    def get_position_help(self, position: TradingPosition) -> Dict[str, Any]:
        """Get help for specific position"""
        try:
            position_type = f"{position.position_type}_{position.instrument_type}"
            help_content = self.help_database.get("position_help", {}).get(position_type, {})
            
            # Add dynamic analysis
            help_content["current_greeks"] = greeks_calculator.calculate_all_greeks(
                float(position.current_price),
                float(position.strike_price),
                (position.expiry_date - datetime.now()).days / 365.0,
                0.06,
                0.20,  # Assuming default volatility
                position.instrument_type
            )
            
            logger.info(f"Position help generated for {position_type}")
            return help_content
            
        except Exception as e:
            logger.error(f"Error getting position help: {e}")
            return {}
    
    def get_portfolio_risk_warnings(self, portfolio: Portfolio) -> List[str]:
        """Get risk warnings for portfolio"""
        warnings = []
        
        try:
            # Calculate portfolio Greeks
            total_delta = sum(pos.delta for pos in portfolio.positions)
            total_theta = sum(pos.theta for pos in portfolio.positions)
            
            if abs(total_delta) > 1.0:
                warnings.append(self.help_database["portfolio_warnings"]["high_delta"])
            
            if total_theta < -10.0:
                warnings.append(self.help_database["portfolio_warnings"]["high_theta"])
            
            # Add more risk checks...
            
            logger.info(f"Generated {len(warnings)} portfolio warnings")
            return warnings
            
        except Exception as e:
            logger.error(f"Error getting portfolio warnings: {e}")
            return []
    
    def get_educational_tips(self, user_level: str, context: str) -> List[str]:
        """Get contextual educational tips"""
        try:
            tips = self.help_database.get("educational_tips", {}).get(user_level, [])
            
            # Add context-specific tips
            if context == "strategy_building":
                tips.append("Always consider Greeks impact on your strategy")
            
            logger.info(f"Generated educational tips for {user_level} in {context} context")
            return tips
            
        except Exception as e:
            logger.error(f"Error getting educational tips: {e}")
            return []
    
    def analyze_user_behavior(self, user_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user behavior and provide help"""
        try:
            analysis = {
                "patterns_detected": [],
                "recommendations": []
            }
            
            # Simple behavior analysis
            error_count = sum(1 for action in user_actions if action.get("type") == "error")
            if error_count > 3:
                analysis["patterns_detected"].append("Frequent errors - review basics")
                analysis["recommendations"].append("Take beginner tutorial")
            
            logger.info("User behavior analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")
            return {}

# Global instance
contextual_help = ContextualHelpSystem()
