"""
Educational content models for F&O Educational Learning System
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
# from decimal import Decimal  # Unused
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ContentType(str, Enum):
    """Educational content types"""
    GREEKS = "greeks"
    STRATEGY = "strategy"
    MARKET = "market"

class DifficultyLevel(int, Enum):
    """Content difficulty levels"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    PROFESSIONAL = 5

class StrategyType(str, Enum):
    """Options strategy types"""
    BASIC = "basic"
    SPREAD = "spread"
    STRADDLE = "straddle"
    ADVANCED = "advanced"
    INCOME = "income"

class RiskLevel(str, Enum):
    """Risk levels for strategies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class GreekType(str, Enum):
    """Types of Greeks"""
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"
    RHO = "rho"

class CompletionStatus(str, Enum):
    """Module completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TutorialContent(BaseModel):
    """Educational tutorial content"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Unique tutorial ID")
    title: str = Field(..., description="Tutorial title")
    content_type: ContentType = Field(..., description="Type of educational content")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    content_data: Dict[str, Any] = Field(..., description="Tutorial content data")
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list, description="Interactive elements")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisite modules")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")

    @field_validator('estimated_duration')
    @classmethod
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Duration must be positive')
        return v

class GreeksTutorial(BaseModel):
    """Interactive Greeks tutorial"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    greek_type: GreekType = Field(..., description="Type of Greek")
    explanation: str = Field(..., description="Detailed explanation of the Greek")
    visual_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Visual examples")
    interactive_calculator: Dict[str, Any] = Field(default_factory=dict, description="Interactive calculator configuration")
    practical_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Practical examples")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts to learn")
    common_mistakes: List[str] = Field(default_factory=list, description="Common mistakes to avoid")

class StrategyGuide(BaseModel):
    """Options strategy guide"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    strategy_name: str = Field(..., description="Name of the strategy")
    strategy_type: StrategyType = Field(..., description="Type of strategy")
    risk_level: RiskLevel = Field(..., description="Risk level of the strategy")
    market_conditions: List[str] = Field(default_factory=list, description="Optimal market conditions")
    entry_criteria: Dict[str, Any] = Field(default_factory=dict, description="Entry criteria")
    exit_criteria: Dict[str, Any] = Field(default_factory=dict, description="Exit criteria")
    risk_reward_profile: Dict[str, Any] = Field(default_factory=dict, description="Risk/reward profile")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Strategy examples")
    greeks_impact: Dict[str, Any] = Field(default_factory=dict, description="Greeks impact analysis")
    profit_loss_diagram: Dict[str, Any] = Field(default_factory=dict, description="P&L diagram data")

class MarketEducation(BaseModel):
    """Indian market-specific education"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    topic: str = Field(..., description="Education topic")
    content_type: str = Field(..., description="Type of market education")
    regulations: List[str] = Field(default_factory=list, description="Relevant regulations")
    trading_hours: Dict[str, Any] = Field(default_factory=dict, description="Trading hours information")
    market_mechanics: Dict[str, Any] = Field(default_factory=dict, description="Market mechanics")
    tax_implications: Dict[str, Any] = Field(default_factory=dict, description="Tax implications")
    risk_management: Dict[str, Any] = Field(default_factory=dict, description="Risk management rules")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Practical examples")

class InteractiveElement(BaseModel):
    """Interactive element in tutorials"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    element_type: str = Field(..., description="Type of interactive element")
    element_id: str = Field(..., description="Unique element ID")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Element configuration")
    data_binding: Dict[str, Any] = Field(default_factory=dict, description="Data binding configuration")
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Validation rules")

class VisualExample(BaseModel):
    """Visual example for tutorials"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    visual_type: str = Field(..., description="Type of visual (chart, graph, diagram)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Visual data")
    interactive_features: List[Dict[str, Any]] = Field(default_factory=list, description="Interactive features")

class PracticalExample(BaseModel):
    """Practical example for learning"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    title: str = Field(..., description="Example title")
    scenario: str = Field(..., description="Example scenario")
    market_data: Dict[str, Any] = Field(default_factory=dict, description="Market data for example")
    calculations: Dict[str, Any] = Field(default_factory=dict, description="Calculation results")
    interpretation: str = Field(..., description="Result interpretation")
    key_learnings: List[str] = Field(default_factory=list, description="Key learnings from example")

class EducationalContent(BaseModel):
    """Complete educational content item"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Unique content ID")
    title: str = Field(..., description="Content title")
    content_type: ContentType = Field(..., description="Type of content")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    content_data: Dict[str, Any] = Field(..., description="Content data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    version: str = Field(default="1.0", description="Content version")
    author: str = Field(..., description="Content author")
    review_status: str = Field(default="pending", description="Review status")

    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Version cannot be empty')
        return v

class ContentUpdateRequest(BaseModel):
    """Request to update educational content"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    content_id: str = Field(..., description="ID of content to update")
    title: Optional[str] = Field(None, description="New title")
    content_data: Optional[Dict[str, Any]] = Field(None, description="Updated content data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    version: Optional[str] = Field(None, description="New version")
    review_status: Optional[str] = Field(None, description="Review status")

    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Version cannot be empty')
        return v

class ContentSearchRequest(BaseModel):
    """Request to search educational content"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    content_type: Optional[ContentType] = Field(None, description="Filter by content type")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty level")
    search_query: Optional[str] = Field(None, description="Search query")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(default=10, description="Maximum number of results")
    offset: int = Field(default=0, description="Number of results to skip")

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v <= 0:
            raise ValueError('Limit must be positive')
        if v > 100:
            raise ValueError('Limit cannot exceed 100')
        return v

    @field_validator('offset')
    @classmethod
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('Offset cannot be negative')
        return v




