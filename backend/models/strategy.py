"""
Strategy models for F&O Educational Learning System
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class InstrumentType(str, Enum):
    """Types of financial instruments"""
    CALL = "call"
    PUT = "put"
    STOCK = "stock"
    INDEX = "index"

class PositionType(str, Enum):
    """Position types"""
    LONG = "long"
    SHORT = "short"

class StrategyType(str, Enum):
    """Options strategy types"""
    BASIC = "basic"
    SPREAD = "spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    BUTTERFLY = "butterfly"
    CONDOR = "condor"
    CALENDAR = "calendar"
    RATIO = "ratio"
    PROTECTIVE = "protective"
    INCOME = "income"
    VOLATILITY = "volatility"  # Added for volatility strategies

class RiskLevel(str, Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MarketCondition(str, Enum):
    """Market conditions"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"
    HIGH_VOLATILITY = "high_volatility"

class StrategyLeg(BaseModel):
    """Individual leg of options strategy"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    leg_id: str = Field(..., description="Unique leg ID")
    instrument_type: InstrumentType = Field(..., description="Type of instrument")
    position_type: PositionType = Field(..., description="Long or short position")
    strike_price: Decimal = Field(..., description="Strike price")
    expiry_date: datetime = Field(..., description="Expiry date")
    quantity: int = Field(..., description="Number of contracts")
    premium: Optional[Decimal] = Field(None, description="Premium paid/received")
    underlying_symbol: str = Field(..., description="Underlying symbol")
    option_symbol: Optional[str] = Field(None, description="Option symbol")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @field_validator('strike_price')
    @classmethod
    def validate_strike_price(cls, v):
        if v <= 0:
            raise ValueError('Strike price must be positive')
        return v

class RiskParameters(BaseModel):
    """Risk parameters for strategy"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    max_loss: Optional[Decimal] = Field(None, description="Maximum possible loss")
    max_profit: Optional[Decimal] = Field(None, description="Maximum possible profit (None for unlimited)")
    breakeven_points: List[Decimal] = Field(default_factory=list, description="Breakeven points")
    risk_reward_ratio: Optional[float] = Field(None, description="Risk to reward ratio")
    probability_of_profit: Optional[float] = Field(None, description="Probability of profit")
    margin_required: Optional[Decimal] = Field(None, description="Margin required")
    time_decay_impact: Optional[str] = Field(None, description="Time decay impact")
    volatility_impact: Optional[str] = Field(None, description="Volatility impact")
    
    @field_validator('probability_of_profit')
    @classmethod
    def validate_probability(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Probability must be between 0 and 1')
        return v
    
    @field_validator('risk_reward_ratio')
    @classmethod
    def validate_risk_reward(cls, v):
        if v is not None and v < 0:
            raise ValueError('Risk-reward ratio cannot be negative')
        return v

class RiskRewardProfile(BaseModel):
    """Strategy risk/reward analysis"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    max_profit: Decimal = Field(..., description="Maximum profit")
    max_loss: Decimal = Field(..., description="Maximum loss")
    breakeven_points: List[Decimal] = Field(default_factory=list, description="Breakeven points")
    profit_probability: float = Field(..., description="Probability of profit")
    risk_reward_ratio: float = Field(..., description="Risk to reward ratio")
    expected_value: Optional[Decimal] = Field(None, description="Expected value")
    win_rate: Optional[float] = Field(None, description="Historical win rate")
    average_profit: Optional[Decimal] = Field(None, description="Average profit")
    average_loss: Optional[Decimal] = Field(None, description="Average loss")
    
    @field_validator('profit_probability')
    @classmethod
    def validate_probability(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Probability must be between 0 and 1')
        return v
    
    @field_validator('risk_reward_ratio')
    @classmethod
    def validate_risk_reward(cls, v):
        if v < 0:
            raise ValueError('Risk-reward ratio cannot be negative')
        return v

class OptionsStrategy(BaseModel):
    """Options strategy configuration"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Strategy ID")
    name: str = Field(..., description="Strategy name")
    strategy_type: StrategyType = Field(..., description="Type of strategy")
    legs: List[StrategyLeg] = Field(..., description="Strategy legs")
    entry_conditions: Dict[str, Any] = Field(default_factory=dict, description="Entry conditions")
    exit_conditions: Dict[str, Any] = Field(default_factory=dict, description="Exit conditions")
    risk_parameters: RiskParameters = Field(..., description="Risk parameters")
    market_conditions: List[MarketCondition] = Field(default_factory=list, description="Optimal market conditions")
    description: str = Field(..., description="Strategy description")
    example_scenario: Optional[Dict[str, Any]] = Field(None, description="Example scenario")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @field_validator('legs')
    @classmethod
    def validate_legs(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Strategy must have at least one leg')
        return v

class StrategyTemplate(BaseModel):
    """Strategy template for educational purposes"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    strategy_type: StrategyType = Field(..., description="Type of strategy")
    difficulty_level: int = Field(..., description="Difficulty level (1-5)")
    risk_level: RiskLevel = Field(..., description="Risk level")
    legs_template: List[Dict[str, Any]] = Field(..., description="Legs template configuration")
    entry_criteria: Dict[str, Any] = Field(default_factory=dict, description="Entry criteria")
    exit_criteria: Dict[str, Any] = Field(default_factory=dict, description="Exit criteria")
    risk_parameters: RiskParameters = Field(..., description="Risk parameters")
    market_conditions: List[MarketCondition] = Field(default_factory=list, description="Optimal market conditions")
    educational_content: Dict[str, Any] = Field(default_factory=dict, description="Educational content")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Strategy examples")
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Difficulty level must be between 1 and 5')
        return v

class GreeksImpact(BaseModel):
    """Greeks impact analysis for strategy"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    strategy_id: str = Field(..., description="Strategy ID")
    delta: Decimal = Field(..., description="Strategy delta")
    gamma: Decimal = Field(..., description="Strategy gamma")
    theta: Decimal = Field(..., description="Strategy theta")
    vega: Decimal = Field(..., description="Strategy vega")
    rho: Decimal = Field(..., description="Strategy rho")
    delta_exposure: Optional[str] = Field(None, description="Delta exposure description")
    gamma_exposure: Optional[str] = Field(None, description="Gamma exposure description")
    theta_exposure: Optional[str] = Field(None, description="Theta exposure description")
    vega_exposure: Optional[str] = Field(None, description="Vega exposure description")
    risk_analysis: Dict[str, Any] = Field(default_factory=dict, description="Risk analysis")

class PnLScenario(BaseModel):
    """Profit/Loss scenario analysis"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    scenario_name: str = Field(..., description="Scenario name")
    underlying_price: Decimal = Field(..., description="Underlying price at expiry")
    strategy_pnl: Decimal = Field(..., description="Strategy P&L")
    individual_legs_pnl: List[Decimal] = Field(default_factory=list, description="Individual legs P&L")
    scenario_probability: Optional[float] = Field(None, description="Scenario probability")
    description: Optional[str] = Field(None, description="Scenario description")
    
    @field_validator('scenario_probability')
    @classmethod
    def validate_probability(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Probability must be between 0 and 1')
        return v

class StrategyAnalysis(BaseModel):
    """Complete strategy analysis"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    strategy: OptionsStrategy = Field(..., description="Strategy configuration")
    risk_reward_profile: RiskRewardProfile = Field(..., description="Risk/reward profile")
    greeks_impact: GreeksImpact = Field(..., description="Greeks impact")
    pnl_scenarios: List[PnLScenario] = Field(default_factory=list, description="P&L scenarios")
    market_suitability: Dict[str, Any] = Field(default_factory=dict, description="Market suitability analysis")
    recommendations: List[str] = Field(default_factory=list, description="Strategy recommendations")
    warnings: List[str] = Field(default_factory=list, description="Strategy warnings")
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class StrategyValidationResult(BaseModel):
    """Strategy validation result"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    is_valid: bool = Field(..., description="Whether strategy is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    risk_assessment: RiskLevel = Field(..., description="Risk assessment")
    complexity_score: int = Field(..., description="Complexity score (1-10)")
    suitability_score: float = Field(..., description="Market suitability score")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    
    @field_validator('complexity_score')
    @classmethod
    def validate_complexity(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Complexity score must be between 1 and 10')
        return v
    
    @field_validator('suitability_score')
    @classmethod
    def validate_suitability(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Suitability score must be between 0 and 1')
        return v

class StrategyRecommendation(BaseModel):
    """Strategy recommendation"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    strategy_template: StrategyTemplate = Field(..., description="Recommended strategy template")
    confidence_score: float = Field(..., description="Recommendation confidence (0-1)")
    reasoning: List[str] = Field(default_factory=list, description="Reasoning for recommendation")
    market_conditions: MarketCondition = Field(..., description="Current market condition")
    expected_performance: Dict[str, Any] = Field(default_factory=dict, description="Expected performance")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    alternative_strategies: List[str] = Field(default_factory=list, description="Alternative strategy IDs")
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v

class StrategyBuilderRequest(BaseModel):
    """Request to build a strategy"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    user_id: str = Field(..., description="User ID")
    strategy_type: StrategyType = Field(..., description="Desired strategy type")
    underlying_symbol: str = Field(..., description="Underlying symbol")
    market_outlook: MarketCondition = Field(..., description="Market outlook")
    risk_tolerance: RiskLevel = Field(..., description="Risk tolerance")
    capital_allocation: Decimal = Field(..., description="Capital allocation")
    time_horizon: int = Field(..., description="Time horizon in days")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="Custom parameters")
    
    @field_validator('capital_allocation')
    @classmethod
    def validate_capital(cls, v):
        if v <= 0:
            raise ValueError('Capital allocation must be positive')
        return v
    
    @field_validator('time_horizon')
    @classmethod
    def validate_time_horizon(cls, v):
        if v <= 0:
            raise ValueError('Time horizon must be positive')
        return v

