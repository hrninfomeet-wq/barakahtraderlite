"""
Educational API endpoints for F&O Educational Learning System
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from models.education import (
    TutorialContent, GreeksTutorial, StrategyGuide, MarketEducation,
    EducationalContent, ContentUpdateRequest, ContentSearchRequest,
    ContentType, GreekType, DifficultyLevel
)
from models.progress import (
    UserProgress, ModuleProgress, Assessment, AssessmentResult,
    ProgressUpdateRequest, CompletionStatus
)
from models.strategy import (
    OptionsStrategy, StrategyTemplate, GreeksImpact, StrategyAnalysis,
    StrategyValidationResult, StrategyRecommendation, StrategyBuilderRequest
)
from services.greeks_calculator import greeks_calculator
from services.education_content_manager import education_content_manager
from services.progress_tracker import progress_tracker
from services.strategy_validator import strategy_validator
from services.contextual_help import contextual_help
from core.security import get_current_user

router = APIRouter(prefix="/api/v1/education", tags=["Education"])

# Mock data for demonstration - in production, this would come from database
MOCK_EDUCATIONAL_CONTENT = {
    "delta_tutorial": GreeksTutorial(
        greek_type=GreekType.DELTA,
        explanation="Delta measures the rate of change of option price with respect to underlying asset price. It indicates how much the option price will change for a ₹1 change in the underlying price.",
        visual_examples=[
            {
                "title": "Delta vs Strike Price",
                "description": "Shows how delta changes with strike price for calls and puts",
                "chart_type": "line",
                "data": {"x": [17000, 17500, 18000, 18500, 19000], "y": [0.1, 0.3, 0.5, 0.7, 0.9]}
            }
        ],
        interactive_calculator={
            "type": "delta_calculator",
            "inputs": ["stock_price", "strike_price", "time_to_expiry", "volatility", "interest_rate"],
            "outputs": ["delta", "option_price"]
        },
        practical_examples=[
            {
                "title": "NIFTY 18000 Call Example",
                "scenario": "NIFTY at 18000, Call strike 18000, 30 days to expiry",
                "market_data": {"price": 18000, "strike": 18000, "days": 30, "volatility": 0.20},
                "calculations": {"delta": 0.52, "option_price": 245.50},
                "interpretation": "For every ₹1 increase in NIFTY, this call option increases by ₹0.52"
            }
        ],
        key_concepts=[
            "Delta ranges from 0 to 1 for calls and -1 to 0 for puts",
            "ATM options have delta around 0.5 for calls",
            "Delta increases as option moves ITM",
            "Delta changes with time and volatility"
        ],
        common_mistakes=[
            "Confusing delta with probability of expiring ITM",
            "Not accounting for delta changes over time",
            "Ignoring delta when hedging positions"
        ]
    )
}

MOCK_STRATEGIES = {
    "long_call": StrategyTemplate(
        id="long_call",
        name="Long Call",
        strategy_type="basic",
        difficulty_level=1,
        risk_level="medium",
        legs_template=[
            {"instrument_type": "call", "position_type": "long", "quantity": 1}
        ],
        entry_criteria={
            "market_outlook": "bullish",
            "volatility": "moderate_to_high",
            "time_horizon": "medium_term"
        },
        risk_parameters={
            "max_loss": 100,
            "max_profit": None,  # Changed to None for unlimited
            "breakeven": "strike_price + premium_paid"
        },
        educational_content={
            "description": "Buy a call option to profit from upward price movement",
            "when_to_use": "When expecting significant upward price movement",
            "risk_reward": "Limited risk (premium paid), unlimited profit potential"
        }
    )
}

@router.get("/tutorials/greeks/{greek_type}")
async def get_greeks_tutorial(
    greek_type: GreekType,
    current_user: str = Depends(get_current_user)
) -> GreeksTutorial:
    """Get interactive Greeks tutorial"""
    try:
        logger.info(f"Getting Greeks tutorial for {greek_type} for user {current_user}")

        # In production, fetch from database
        tutorial_key = f"{greek_type.value}_tutorial"
        if tutorial_key in MOCK_EDUCATIONAL_CONTENT:
            return MOCK_EDUCATIONAL_CONTENT[tutorial_key]

        # Generate educational content dynamically
        education_content = greeks_calculator.get_greeks_education_content(greek_type)

        tutorial = GreeksTutorial(
            greek_type=greek_type,
            explanation=education_content.get('description', ''),
            key_concepts=education_content.get('key_concepts', []),
            practical_examples=[{
                "title": f"{education_content.get('name', 'Greek')} Example",
                "scenario": "Real market example",
                "interpretation": education_content.get('interpretation', ''),
                "key_learnings": [education_content.get('risk_management', '')]
            }],
            common_mistakes=[education_content.get('risk_management', '')]
        )

        return tutorial

    except Exception as e:
        logger.error(f"Error getting Greeks tutorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Greeks tutorial: {str(e)}"
        )

@router.get("/strategies/{strategy_name}")
async def get_strategy_guide(
    strategy_name: str,
    current_user: str = Depends(get_current_user)
) -> StrategyGuide:
    """Get options strategy guide"""
    try:
        logger.info(f"Getting strategy guide for {strategy_name} for user {current_user}")

        # In production, fetch from database
        if strategy_name in MOCK_STRATEGIES:
            template = MOCK_STRATEGIES[strategy_name]

            strategy_guide = StrategyGuide(
                strategy_name=template.name,
                strategy_type=template.strategy_type,
                risk_level=template.risk_level,
                market_conditions=template.market_conditions,
                entry_criteria=template.entry_criteria,
                exit_criteria=template.exit_criteria,
                risk_reward_profile=template.risk_parameters,
                examples=[template.educational_content]
            )

            return strategy_guide

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy guide not found: {strategy_name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy guide: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy guide: {str(e)}"
        )

@router.get("/market-education/{topic}")
async def get_market_education(
    topic: str,
    current_user: str = Depends(get_current_user)
) -> MarketEducation:
    """Get Indian market education"""
    try:
        logger.info(f"Getting market education for {topic} for user {current_user}")

        # Mock market education data
        market_education_data = {
            "nse_regulations": MarketEducation(
                topic="NSE Regulations",
                content_type="regulation",
                regulations=[
                    "Position limits for F&O contracts",
                    "Margin requirements and SPAN margin",
                    "Settlement cycles and procedures",
                    "Circuit breaker rules"
                ],
                trading_hours={
                    "equity": "09:15 - 15:30 IST",
                    "fno": "09:15 - 15:30 IST",
                    "currency": "09:00 - 17:00 IST"
                },
                market_mechanics={
                    "lot_sizes": "Standardized contract sizes",
                    "tick_size": "Minimum price movement",
                    "expiry_cycle": "Last Thursday of every month"
                },
                tax_implications={
                    "stcg": "15% on profits < 1 year",
                    "ltcg": "10% on profits > 1 year (>1 lakh)",
                    "fno_tax": "Business income, no STT on delivery"
                }
            )
        }

        if topic in market_education_data:
            return market_education_data[topic]

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market education topic not found: {topic}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market education: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market education: {str(e)}"
        )

@router.post("/greeks/calculate")
async def calculate_greeks(
    calculation_request: Dict[str, Any],
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Calculate options Greeks"""
    try:
        logger.info(f"Calculating Greeks for user {current_user}")

        # Extract parameters
        S = calculation_request.get('stock_price', 0)
        K = calculation_request.get('strike_price', 0)
        T = calculation_request.get('time_to_expiry', 0) / 365.0  # Convert days to years
        r = calculation_request.get('interest_rate', 0.06)
        sigma = calculation_request.get('volatility', 0.2)
        option_type = calculation_request.get('option_type', 'call')

        # Validate inputs
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid calculation parameters"
            )

        # Calculate Greeks
        greeks = greeks_calculator.calculate_all_greeks(S, K, T, r, sigma, option_type)

        # Add educational interpretation
        interpretation = {
            'delta_interpretation': greeks_calculator._analyze_delta_exposure(greeks['delta']),
            'gamma_interpretation': greeks_calculator._analyze_gamma_exposure(greeks['gamma']),
            'theta_interpretation': greeks_calculator._analyze_theta_exposure(greeks['theta']),
            'vega_interpretation': greeks_calculator._analyze_vega_exposure(greeks['vega'])
        }

        return {
            'greeks': greeks,
            'interpretation': interpretation,
            'parameters': calculation_request
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate Greeks: {str(e)}"
        )

@router.post("/strategy/validate")
async def validate_strategy(
    strategy: OptionsStrategy,
    current_user: str = Depends(get_current_user)
) -> StrategyValidationResult:
    """Validate options strategy"""
    try:
        logger.info(f"Validating strategy {strategy.name} for user {current_user}")

        validation_errors = []
        warnings = []

        # Basic validation
        if not strategy.legs:
            validation_errors.append("Strategy must have at least one leg")

        if len(strategy.legs) > 10:
            warnings.append("Strategy has many legs - consider complexity")

        # Validate legs
        for i, leg in enumerate(strategy.legs):
            if leg.quantity <= 0:
                validation_errors.append(f"Leg {i+1}: Quantity must be positive")

            if leg.strike_price <= 0:
                validation_errors.append(f"Leg {i+1}: Strike price must be positive")

            if leg.expiry_date < datetime.now():
                validation_errors.append(f"Leg {i+1}: Expiry date cannot be in the past")

        # Risk assessment
        risk_level = "medium"  # Default
        if len(strategy.legs) > 4:
            risk_level = "high"
        elif len(strategy.legs) <= 2:
            risk_level = "low"

        # Complexity score (1-10)
        complexity_score = min(10, len(strategy.legs) + 2)

        # Suitability score (mock calculation)
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

        return result

    except Exception as e:
        logger.error(f"Error validating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate strategy: {str(e)}"
        )

@router.get("/progress/{user_id}")
async def get_user_progress(
    user_id: str,
    current_user: str = Depends(get_current_user)
) -> UserProgress:
    """Get user learning progress"""
    try:
        logger.info(f"Getting progress for user {user_id}")

        # Mock progress data - in production, fetch from database
        progress = UserProgress(
            user_id=user_id,
            completed_modules=["delta_tutorial", "basic_strategies"],
            assessment_scores={"delta_quiz": 85.5, "strategy_quiz": 92.0},
            competency_levels={"greeks": "intermediate", "strategies": "beginner"},
            learning_path=["delta_tutorial", "gamma_tutorial", "basic_strategies"],
            total_time_spent=180,  # 3 hours
            current_module="gamma_tutorial",
            learning_goals=["Master all Greeks", "Learn 10+ strategies"]
        )

        return progress

    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user progress: {str(e)}"
        )

@router.post("/progress/update")
async def update_progress(
    update_request: ProgressUpdateRequest,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user progress"""
    try:
        logger.info(f"Updating progress for user {update_request.user_id}")

        # In production, update database
        # For now, return success response

        return {
            "status": "success",
            "message": "Progress updated successfully",
            "user_id": update_request.user_id,
            "module_id": update_request.module_id,
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )

@router.get("/content/search")
async def search_educational_content(
    content_type: Optional[ContentType] = Query(None),
    difficulty_level: Optional[DifficultyLevel] = Query(None),
    search_query: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Search educational content"""
    try:
        logger.info(f"Searching educational content for user {current_user}")

        # Mock search results
        results = []

        if content_type == ContentType.GREEKS or content_type is None:
            results.extend([
                {
                    "id": "delta_tutorial",
                    "title": "Delta Tutorial",
                    "content_type": "greeks",
                    "difficulty_level": 1,
                    "description": "Learn about option delta and price sensitivity"
                },
                {
                    "id": "gamma_tutorial",
                    "title": "Gamma Tutorial",
                    "content_type": "greeks",
                    "difficulty_level": 2,
                    "description": "Understand gamma and delta acceleration"
                }
            ])

        if content_type == ContentType.STRATEGY or content_type is None:
            results.extend([
                {
                    "id": "long_call_guide",
                    "title": "Long Call Strategy Guide",
                    "content_type": "strategy",
                    "difficulty_level": 1,
                    "description": "Learn the basics of buying call options"
                }
            ])

        # Apply filters
        if difficulty_level:
            results = [r for r in results if r['difficulty_level'] == difficulty_level.value]

        if search_query:
            results = [r for r in results if search_query.lower() in r['title'].lower()]

        # Apply pagination
        total_results = len(results)
        paginated_results = results[offset:offset + limit]

        return {
            "results": paginated_results,
            "total": total_results,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_results
        }

    except Exception as e:
        logger.error(f"Error searching educational content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search content: {str(e)}"
        )

@router.get("/content/{content_id}")
async def get_content(content_id: str, current_user: str = Depends(get_current_user)) -> EducationalContent:
    content = education_content_manager.get_content(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "education-api",
        "version": "1.0.0"
    }
