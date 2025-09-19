"""
Progress Tracker Service
Tracks user learning progress and assessments
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime, timedelta
from decimal import Decimal

from models.progress import (
    UserProgress, ModuleProgress, Assessment, AssessmentResult,
    ProgressUpdateRequest, Certificate, LearningPath, Recommendation,
    AssessmentType, CertificateType, CompletionStatus
)

class ProgressTracker:
    """Tracks user learning progress and generates certificates"""

    def __init__(self):
        """Initialize progress tracker"""
        self.user_progress: Dict[str, UserProgress] = {}
        self.assessments: Dict[str, Assessment] = {}
        self.assessment_results: Dict[str, List[AssessmentResult]] = {}
        logger.info("Progress Tracker initialized")

    def record_module_completion(self, user_id: str, module_id: str, time_spent_minutes: int) -> ModuleProgress:
        """Record module completion"""
        try:
            if user_id not in self.user_progress:
                self.user_progress[user_id] = UserProgress(user_id=user_id)

            progress = self.user_progress[user_id]

            module_progress = ModuleProgress(
                id=f"{user_id}_{module_id}",
                user_id=user_id,
                module_id=module_id,
                status=CompletionStatus.COMPLETED,
                progress_percentage=100.0,
                time_spent_minutes=time_spent_minutes,
                started_at=datetime.now() - timedelta(minutes=time_spent_minutes),
                completed_at=datetime.now()
            )

            # Update user progress
            progress.total_modules_completed += 1
            progress.total_time_spent += time_spent_minutes
            progress.overall_progress_percentage = (progress.total_modules_completed / 10.0) * 100  # Assuming 10 total modules
            progress.last_activity = datetime.now()

            logger.info(f"Module {module_id} completed for user {user_id}")
            return module_progress

        except Exception as e:
            logger.error(f"Error recording module completion: {e}")
            raise

    def record_assessment_result(self, user_id: str, assessment_id: str, score: float, time_taken: int, attempt: int) -> AssessmentResult:
        """Record assessment result"""
        try:
            if assessment_id not in self.assessments:
                raise ValueError("Assessment not found")

            assessment = self.assessments[assessment_id]
            passed = score >= assessment.passing_score

            result = AssessmentResult(
                id=f"{user_id}_{assessment_id}_{attempt}",
                user_id=user_id,
                assessment_id=assessment_id,
                score=score,
                passed=passed,
                attempt_number=attempt,
                time_taken_minutes=time_taken,
                feedback={"passed": passed, "areas_to_improve": [] if passed else ["Review basics"]}
            )

            if user_id not in self.assessment_results:
                self.assessment_results[user_id] = []
            self.assessment_results[user_id].append(result)

            if passed and user_id in self.user_progress:
                self.user_progress[user_id].total_assessments_passed += 1

            logger.info(f"Assessment {assessment_id} result recorded for user {user_id}: {'Passed' if passed else 'Failed'}")
            return result

        except Exception as e:
            logger.error(f"Error recording assessment result: {e}")
            raise

    def generate_certificate(self, user_id: str, certificate_type: CertificateType, related_id: Optional[str] = None) -> Certificate:
        """Generate certificate upon completion"""
        try:
            if user_id not in self.user_progress:
                raise ValueError("User progress not found")

            certificate = Certificate(
                id=f"cert_{user_id}_{certificate_type}_{datetime.now().timestamp()}",
                user_id=user_id,
                certificate_type=certificate_type,
                module_id=related_id if certificate_type == CertificateType.MODULE_COMPLETION else None,
                course_id=related_id if certificate_type == CertificateType.COURSE_COMPLETION else None,
                achievement_level="Excellent" if certificate_type == CertificateType.PROFICIENCY else "Completed",
                valid_until=datetime.now() + timedelta(days=365) if certificate_type == CertificateType.PROFICIENCY else None,
                verification_code=f"VER-{int(datetime.now().timestamp())}"
            )

            self.user_progress[user_id].certificates.append(certificate)

            logger.info(f"Certificate generated for user {user_id}: {certificate_type}")
            return certificate

        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            raise

    def get_user_progress(self, user_id: str) -> UserProgress:
        """Retrieve user progress"""
        if user_id not in self.user_progress:
            logger.warning(f"No progress found for user {user_id} - creating new")
            self.user_progress[user_id] = UserProgress(user_id=user_id)

        return self.user_progress[user_id]

    def get_learning_path(self, user_id: str) -> LearningPath:
        """Get or generate personalized learning path"""
        try:
            # Simple learning path generation based on progress
            progress = self.get_user_progress(user_id)

            modules = ["greeks_delta", "greeks_gamma", "strategy_long_call", "market_nse_fo"]
            current_index = progress.total_modules_completed

            learning_path = LearningPath(
                id=f"path_{user_id}",
                user_id=user_id,
                name="F&O Basics Path",
                modules=modules,
                current_module_index=current_index,
                estimated_completion_time=len(modules) * 2,  # 2 hours per module
                progress_percentage=(current_index / len(modules)) * 100
            )

            logger.info(f"Learning path generated for user {user_id}")
            return learning_path

        except Exception as e:
            logger.error(f"Error getting learning path: {e}")
            raise

    def get_recommendations(self, user_id: str) -> List[Recommendation]:
        """Get personalized recommendations"""
        try:
            progress = self.get_user_progress(user_id)

            recommendations = []
            if progress.total_modules_completed < 2:
                recommendations.append(Recommendation(
                    id="rec_1",
                    user_id=user_id,
                    recommendation_type="module",
                    content_id="greeks_delta",
                    priority=1,
                    reasoning="Start with basic Greeks understanding"
                ))

            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            raise

# Global instance
progress_tracker = ProgressTracker()



