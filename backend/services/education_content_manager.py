"""
Education Content Manager Service
Manages educational content for F&O learning system
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from models.education import (
    EducationalContent, ContentType, DifficultyLevel,
    ContentUpdateRequest, ContentSearchRequest,
    GreeksTutorial, StrategyGuide, MarketEducation
)

class EducationContentManager:
    """Manages educational content storage and retrieval"""

    def __init__(self):
        """Initialize content manager with sample content"""
        self.content_store: Dict[str, EducationalContent] = {}
        self._load_sample_content()
        logger.info("Education Content Manager initialized")

    def _load_sample_content(self):
        """Load comprehensive sample educational content"""
        # Greeks Tutorials
        self.content_store["greeks_delta"] = EducationalContent(
            id="greeks_delta",
            title="Understanding Delta",
            content_type=ContentType.GREEKS,
            difficulty_level=DifficultyLevel.BEGINNER,
            content_data={
                "tutorial": GreeksTutorial(
                    greek_type="delta",
                    explanation="Delta measures how much an option's price changes with a ₹1 change in the underlying asset. For calls, it's between 0 and 1; for puts, -1 to 0.",
                    visual_examples=[{"type": "chart", "data": "delta_curve"}],
                    interactive_calculator={"sliders": ["price", "volatility"]},
                    practical_examples=[{"scenario": "NIFTY at 18000", "calculation": "Delta 0.5 → ₹50 move = ₹25 option change"}],
                    key_concepts=["Directional sensitivity", "Hedge ratio"],
                    common_mistakes=["Confusing with probability"]
                )
            },
            metadata={"tags": ["greeks", "basic"]},
            author="System",
            review_status="approved"
        )

        # Add more Greeks...

        # Strategy Guides
        self.content_store["strategy_long_call"] = EducationalContent(
            id="strategy_long_call",
            title="Long Call Strategy",
            content_type=ContentType.STRATEGY,
            difficulty_level=DifficultyLevel.BEGINNER,
            content_data={
                "guide": StrategyGuide(
                    strategy_name="Long Call",
                    strategy_type="basic",
                    risk_level="medium",
                    market_conditions=["bullish"],
                    entry_criteria={"outlook": "strong upward move"},
                    exit_criteria={"target": "profit target or expiry"},
                    risk_reward_profile={"risk": "limited to premium", "reward": "unlimited"},
                    examples=[{"nifty": "Buy 18000CE at ₹200"}],
                    greeks_impact={"delta": "positive", "theta": "negative"},
                    profit_loss_diagram={"type": "hockey_stick"}
                )
            },
            metadata={"tags": ["strategy", "basic"]},
            author="System",
            review_status="approved"
        )

        # Add more strategies...

        # Market Education
        self.content_store["market_nse_fo"] = EducationalContent(
            id="market_nse_fo",
            title="NSE F&O Basics",
            content_type=ContentType.MARKET,
            difficulty_level=DifficultyLevel.BEGINNER,
            content_data={
                "education": MarketEducation(
                    topic="NSE F&O Market",
                    content_type="market_basics",
                    regulations=["SEBI guidelines", "Position limits"],
                    trading_hours={"equity": "9:15-15:30 IST"},
                    market_mechanics={"lot_size": "variable", "expiry": "last Thursday"},
                    tax_implications={"stt": "0.01%", "transaction_tax": "variable"},
                    risk_management={"margin": "SPAN", "circuit": "10-20%"},
                    examples=[{"nifty_futures": "Contract value calculation"}]
                )
            },
            metadata={"tags": ["market", "india"]},
            author="System",
            review_status="approved"
        )

        # Add more market topics...

    def get_content(self, content_id: str) -> Optional[EducationalContent]:
        """Retrieve specific content"""
        content = self.content_store.get(content_id)
        if content:
            logger.info(f"Retrieved content {content_id}")
            return content
        logger.warning(f"Content not found: {content_id}")
        return None

    def update_content(self, request: ContentUpdateRequest) -> EducationalContent:
        """Update existing content"""
        if request.content_id not in self.content_store:
            logger.error(f"Content not found for update: {request.content_id}")
            raise ValueError("Content not found")

        content = self.content_store[request.content_id]

        if request.title:
            content.title = request.title
        if request.content_data:
            content.content_data = request.content_data
        if request.metadata:
            content.metadata = request.metadata
        if request.version:
            content.version = request.version
        if request.review_status:
            content.review_status = request.review_status

        content.updated_at = datetime.now()

        logger.info(f"Updated content {request.content_id}")
        return content

    def search_content(self, request: ContentSearchRequest) -> List[EducationalContent]:
        """Search educational content"""
        results = list(self.content_store.values())

        if request.content_type:
            results = [c for c in results if c.content_type == request.content_type]

        if request.difficulty_level:
            results = [c for c in results if c.difficulty_level == request.difficulty_level]

        if request.search_query:
            query = request.search_query.lower()
            results = [c for c in results if query in c.title.lower() or query in str(c.content_data).lower()]

        if request.tags:
            results = [c for c in results if any(tag in c.metadata.get('tags', []) for tag in request.tags)]

        # Apply pagination
        return results[request.offset:request.offset + request.limit]

    def get_recommended_content(self, user_progress: Dict[str, Any]) -> List[EducationalContent]:
        """Get personalized content recommendations"""
        recommendations = []

        # Simple recommendation logic based on progress
        completed = user_progress.get('completed_modules', [])

        if "basic_greeks" not in completed:
            rec = self.get_content("greeks_delta")
            if rec:
                recommendations.append(rec)

        if "basic_strategies" not in completed:
            rec = self.get_content("strategy_long_call")
            if rec:
                recommendations.append(rec)

        if "market_basics" not in completed:
            rec = self.get_content("market_nse_fo")
            if rec:
                recommendations.append(rec)

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

# Global instance
education_content_manager = EducationContentManager()



