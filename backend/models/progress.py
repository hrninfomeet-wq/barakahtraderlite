"""
User progress and assessment models for F&O Educational Learning System
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AssessmentType(str, Enum):
    """Types of assessments"""
    QUIZ = "quiz"
    PRACTICAL = "practical"
    SIMULATION = "simulation"
    MODULE = "module"  # Added
    FINAL = "final"    # Added
    PRACTICE = "practice"  # Added

class CertificateType(str, Enum):
    """Types of certificates"""
    MODULE_COMPLETION = "module_completion"
    COURSE_COMPLETION = "course_completion"
    PROFICIENCY = "proficiency"

class CompletionStatus(str, Enum):
    """Module completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ModuleProgress(BaseModel):
    """Progress for a single module"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Unique progress ID")
    user_id: str = Field(..., description="User ID")
    module_id: str = Field(..., description="Module ID")
    status: CompletionStatus = Field(..., description="Completion status")
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    time_spent_minutes: int = Field(..., description="Time spent in minutes")
    last_accessed: datetime = Field(default_factory=datetime.now, description="Last access timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    notes: Optional[List[str]] = Field(default_factory=list, description="User notes")
    
    @field_validator('progress_percentage')
    @classmethod
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v
    
    @field_validator('time_spent_minutes')
    @classmethod
    def validate_time_spent(cls, v):
        if v < 0:
            raise ValueError('Time spent cannot be negative')
        return v

class Assessment(BaseModel):
    """Assessment configuration"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Assessment ID")
    module_id: str = Field(..., description="Associated module ID")
    assessment_type: AssessmentType = Field(..., description="Type of assessment")
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="Assessment questions")
    passing_score: float = Field(..., description="Passing score percentage")
    time_limit_minutes: Optional[int] = Field(None, description="Time limit in minutes")
    attempts_allowed: int = Field(default=3, description="Number of attempts allowed")
    difficulty_level: int = Field(..., description="Difficulty level (1-5)")
    
    @field_validator('passing_score')
    @classmethod
    def validate_passing_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Passing score must be between 0 and 100')
        return v
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Difficulty level must be between 1 and 5')
        return v

class AssessmentResult(BaseModel):
    """Assessment result"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Result ID")
    user_id: str = Field(..., description="User ID")
    assessment_id: str = Field(..., description="Assessment ID")
    score: float = Field(..., description="Achieved score percentage")
    passed: bool = Field(..., description="Whether passed")
    attempt_number: int = Field(..., description="Attempt number")
    time_taken_minutes: int = Field(..., description="Time taken in minutes")
    completed_at: datetime = Field(default_factory=datetime.now, description="Completion timestamp")
    feedback: Optional[Dict[str, Any]] = Field(None, description="Detailed feedback")
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Score must be between 0 and 100')
        return v

class Certificate(BaseModel):
    """Learning certificate"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Certificate ID")
    user_id: str = Field(..., description="User ID")
    certificate_type: CertificateType = Field(..., description="Type of certificate")
    module_id: Optional[str] = Field(None, description="Associated module ID")
    course_id: Optional[str] = Field(None, description="Associated course ID")
    achievement_level: str = Field(..., description="Achievement level")
    issued_at: datetime = Field(default_factory=datetime.now, description="Issue timestamp")
    valid_until: Optional[datetime] = Field(None, description="Validity end date")
    verification_code: str = Field(..., description="Verification code")

class UserProgress(BaseModel):
    """User learning progress"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    user_id: str = Field(..., description="User ID")
    total_modules_completed: int = Field(default=0, description="Total modules completed")
    total_assessments_passed: int = Field(default=0, description="Total assessments passed")
    overall_progress_percentage: float = Field(default=0.0, description="Overall progress percentage")
    current_level: int = Field(default=1, description="Current learning level")
    total_time_spent: int = Field(default=0, description="Total time spent in minutes")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")
    learning_paths: List[Dict[str, Any]] = Field(default_factory=list, description="Active learning paths")
    certificates: List[Certificate] = Field(default_factory=list, description="Earned certificates")
    recommendations: List[str] = Field(default_factory=list, description="Personalized recommendations")
    
    @field_validator('overall_progress_percentage')
    @classmethod
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v
    
    @field_validator('current_level')
    @classmethod
    def validate_level(cls, v):
        if v < 1:
            raise ValueError('Level must be at least 1')
        return v

class ProgressUpdateRequest(BaseModel):
    """Request to update progress"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    user_id: str = Field(..., description="User ID")
    module_id: str = Field(..., description="Module ID")
    progress_percentage: float = Field(..., description="New progress percentage")
    time_spent_minutes: int = Field(..., description="Time spent in this session")
    status: Optional[CompletionStatus] = Field(None, description="New status")
    notes: Optional[str] = Field(None, description="Progress notes")
    
    @field_validator('progress_percentage')
    @classmethod
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v
    
    @field_validator('time_spent_minutes')
    @classmethod
    def validate_time_spent(cls, v):
        if v < 0:
            raise ValueError('Time spent cannot be negative')
        return v

class LearningPath(BaseModel):
    """Personalized learning path"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Path ID")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Path name")
    modules: List[str] = Field(..., description="Module IDs in sequence")
    current_module_index: int = Field(default=0, description="Current module index")
    estimated_completion_time: int = Field(..., description="Estimated time in hours")
    progress_percentage: float = Field(default=0.0, description="Path progress")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @field_validator('progress_percentage')
    @classmethod
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v

class Recommendation(BaseModel):
    """Learning recommendation"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: str = Field(..., description="Recommendation ID")
    user_id: str = Field(..., description="User ID")
    recommendation_type: str = Field(..., description="Type of recommendation")
    content_id: str = Field(..., description="Recommended content ID")
    priority: int = Field(..., description="Priority level (1-5)")
    reasoning: str = Field(..., description="Reason for recommendation")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Priority must be between 1 and 5')
        return v
