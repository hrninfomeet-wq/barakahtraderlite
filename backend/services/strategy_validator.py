"""
Strategy Validator Service
Validates options strategies and provides risk analysis
"""
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime
from decimal import Decimal

from models.strategy import (
    OptionsStrategy, StrategyValidationResult, RiskLevel,
    StrategyRecommendation, StrategyType, StrategyBuilderRequest,
    StrategyLeg, InstrumentType, PositionType, MarketCondition
)
from services.greeks_calculator import greeks_calculator

class StrategyValidator:
    """Validates and analyzes options strategies"""
    
    def __init__(self):
        """Initialize strategy validator"""
        logger.info("Strategy Validator initialized")
    
    def validate_strategy(self, strategy: OptionsStrategy) -> StrategyValidationResult:
        """Validate strategy configuration"""
        validation_errors = []
        warnings = []
        
        # Basic validation
        if not strategy.legs:
            validation_errors.append("Strategy must have at least one leg")
        
        if len(strategy.legs) > 10:
            warnings.append("Complex strategy with many legs - high risk of errors")
        
        # Validate legs
        for i, leg in enumerate(strategy.legs):
            if leg.quantity <= 0:
                validation_errors.append(f"Leg {i+1}: Quantity must be positive")
            
            if leg.strike_price <= 0:
                validation_errors.append(f"Leg {i+1}: Strike price must be positive")
            
            if leg.expiry_date < datetime.now():
                validation_errors.append(f"Leg {i+1}: Expiry date cannot be in the past")
        
        # Risk assessment
        risk_level = RiskLevel.MEDIUM
        if len(strategy.legs) > 4:
            risk_level = RiskLevel.HIGH
        elif len(strategy.legs) <= 2:
            risk_level = RiskLevel.LOW
        
        # Complexity score (1-10)
        complexity_score = min(10, len(strategy.legs) + 2)
        
        # Suitability score (0-1)
        suitability_score = 0.8 if not validation_errors else 0.3
        
        recommendations = []
        if validation_errors:
            recommendations.append("Fix validation errors before proceeding")
        if warnings:
            recommendations.append("Review warnings and consider simplifying strategy")
        
        result = StrategyValidationResult(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            warnings=warnings,
            risk_assessment=risk_level,
            complexity_score=complexity_score,
            suitability_score=suitability_score,
            recommendations=recommendations
        )
        
        logger.info(f"Strategy {strategy.name} validated: {'Valid' if result.is_valid else 'Invalid'}")
        return result
    
    def analyze_strategy_risk(self, strategy: OptionsStrategy, current_price: float, volatility: float) -> Dict[str, Any]:
        """Analyze strategy risk profile"""
        try:
            greeks = greeks_calculator.calculate_strategy_greeks(strategy, current_price, volatility)
            
            # Calculate breakeven points (simplified)
            breakeven_points = []
            for leg in strategy.legs:
                if leg.instrument_type == InstrumentType.CALL and leg.position_type == PositionType.LONG:
                    breakeven_points.append(float(leg.strike_price) + float(leg.premium or 0))
            
            # Risk-reward calculation
            risk_reward = {
                "max_profit": "unlimited" if strategy.strategy_type == StrategyType.BASIC else "limited",
                "max_loss": "limited" if any(l.position_type == PositionType.LONG for l in strategy.legs) else "unlimited"
            }
            
            analysis = {
                "greeks": greeks,
                "breakeven_points": breakeven_points,
                "risk_reward": risk_reward,
                "sensitivity_analysis": self._perform_sensitivity_analysis(strategy, current_price, volatility)
            }
            
            logger.info(f"Risk analysis completed for strategy {strategy.name}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing strategy risk: {e}")
            raise
    
    def _perform_sensitivity_analysis(self, strategy: OptionsStrategy, current_price: float, volatility: float) -> Dict[str, Any]:
        """Perform sensitivity analysis"""
        # Price sensitivity
        price_changes = [-10, -5, 0, 5, 10]
        price_scenarios = []
        for change in price_changes:
            new_price = current_price * (1 + change/100)
            new_greeks = greeks_calculator.calculate_strategy_greeks(strategy, new_price, volatility)
            price_scenarios.append({
                "price_change": change,
                "delta": float(new_greeks.delta)
            })
        
        # Volatility sensitivity
        vol_changes = [-20, -10, 0, 10, 20]
        vol_scenarios = []
        for change in vol_changes:
            new_vol = volatility * (1 + change/100)
            new_greeks = greeks_calculator.calculate_strategy_greeks(strategy, current_price, new_vol)
            vol_scenarios.append({
                "vol_change": change,
                "vega": float(new_greeks.vega)
            })
        
        return {
            "price_sensitivity": price_scenarios,
            "volatility_sensitivity": vol_scenarios
        }
    
    def recommend_strategy(self, request: StrategyBuilderRequest) -> StrategyRecommendation:
        """Recommend strategy based on parameters"""
        try:
            # Simple recommendation logic
            template_id = "long_call" if request.market_outlook == MarketCondition.BULLISH else "long_put"
            
            recommendation = StrategyRecommendation(
                strategy_template=StrategyTemplate(
                    id=template_id,
                    name="Recommended Strategy",
                    strategy_type=request.strategy_type,
                    difficulty_level=2,
                    risk_level=request.risk_tolerance,
                    legs_template=[],
                    risk_parameters={},
                    market_conditions=[request.market_outlook]
                ),
                confidence_score=0.85,
                reasoning=["Based on bullish outlook", "Matches risk tolerance"],
                market_conditions=request.market_outlook,
                expected_performance={"profit_probability": 0.6},
                risk_factors=["Market volatility", "Time decay"],
                alternative_strategies=["covered_call"]
            )
            
            logger.info(f"Strategy recommendation generated for user {request.user_id}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error recommending strategy: {e}")
            raise

# Global instance
strategy_validator = StrategyValidator()
