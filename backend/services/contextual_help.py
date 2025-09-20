"""
Contextual Help Service
Provides real-time contextual help and tips
"""
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime

from models.strategy import PositionType
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

    def get_trading_context_help(self, trading_action: str, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual help for trading UI actions"""
        try:
            context_help = {
                "action": trading_action,
                "help_text": "",
                "warnings": [],
                "educational_links": []
            }

            if trading_action == "place_order":
                context_help["help_text"] = "Review Greeks impact before placing order"
                context_help["warnings"] = ["Check time decay for short-term options"]
                context_help["educational_links"] = ["greeks_delta", "strategy_basics"]

            elif trading_action == "close_position":
                context_help["help_text"] = "Consider profit/loss and remaining time value"
                context_help["warnings"] = ["Early assignment risk for ITM options"]

            elif trading_action == "modify_strategy":
                context_help["help_text"] = "Analyze Greeks changes before modification"
                context_help["educational_links"] = ["strategy_management"]

            logger.info(f"Trading context help generated for {trading_action}")
            return context_help

        except Exception as e:
            logger.error(f"Error getting trading context help: {e}")
            return {"action": trading_action, "help_text": "Help temporarily unavailable"}

    def get_real_time_alerts(self, portfolio: Portfolio, market_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate real-time alerts based on portfolio and market conditions"""
        try:
            alerts = []

            # Check for expiry alerts
            for position in portfolio.positions:
                if position.expiry_date:
                    days_to_expiry = (position.expiry_date - datetime.now()).days
                    if days_to_expiry <= 7:
                        alerts.append({
                            "type": "expiry_warning",
                            "message": f"{position.symbol} expires in {days_to_expiry} days",
                            "severity": "medium",
                            "action": "Consider closing or rolling position"
                        })

            # Check for high volatility
            if market_conditions.get("volatility_spike", False):
                alerts.append({
                    "type": "volatility_alert",
                    "message": "High volatility detected - review vega exposure",
                    "severity": "low",
                    "action": "Check vega impact on positions"
                })

            logger.info(f"Generated {len(alerts)} real-time alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error generating real-time alerts: {e}")
            return []

# Global instance
contextual_help = ContextualHelpSystem()



