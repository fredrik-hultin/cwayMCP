"""Temporal KPI entities for time-based analysis."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from enum import Enum


class ActivityLevel(Enum):
    """Activity level enumeration."""
    INACTIVE = "inactive"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    BURST = "burst"


class StagnationRisk(Enum):
    """Project stagnation risk levels."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProjectActivityTimeline:
    """Timeline of project activity with temporal analysis."""
    
    project_id: str
    project_name: str
    total_revisions: int
    
    # Temporal boundaries
    first_activity: Optional[datetime]
    last_activity: Optional[datetime]
    project_start_date: Optional[date]
    project_end_date: Optional[date]
    
    # Velocity metrics
    revisions_per_day: float
    revisions_per_week: float
    revisions_per_month: float
    
    # Timing analysis
    days_since_last_activity: int
    total_project_days: int
    active_days: int
    idle_days: int
    
    # Activity patterns
    activity_level: ActivityLevel
    stagnation_risk: StagnationRisk
    
    # Burst analysis
    max_revisions_per_day: int
    avg_time_between_revisions: Optional[timedelta]
    
    # Predictions
    estimated_completion_date: Optional[date]
    days_to_completion_estimate: Optional[int]
    
    def __post_init__(self):
        """Calculate derived metrics."""
        # Calculate activity level
        if self.revisions_per_week == 0:
            self.activity_level = ActivityLevel.INACTIVE
        elif self.revisions_per_week < 1:
            self.activity_level = ActivityLevel.LOW
        elif self.revisions_per_week < 5:
            self.activity_level = ActivityLevel.MODERATE
        elif self.revisions_per_week < 15:
            self.activity_level = ActivityLevel.HIGH
        else:
            self.activity_level = ActivityLevel.BURST
        
        # Calculate stagnation risk
        if self.days_since_last_activity == 0:
            self.stagnation_risk = StagnationRisk.NONE
        elif self.days_since_last_activity <= 7:
            self.stagnation_risk = StagnationRisk.LOW
        elif self.days_since_last_activity <= 30:
            self.stagnation_risk = StagnationRisk.MODERATE
        elif self.days_since_last_activity <= 90:
            self.stagnation_risk = StagnationRisk.HIGH
        else:
            self.stagnation_risk = StagnationRisk.CRITICAL


@dataclass
class TeamTemporalMetrics:
    """Team-wide temporal productivity metrics."""
    
    # Overall timing
    total_active_days: int
    avg_team_response_time: Optional[timedelta]
    
    # Activity distribution
    peak_activity_day_of_week: str
    peak_activity_hour: int
    activity_by_day_of_week: Dict[str, int]
    activity_by_hour: Dict[int, int]
    
    # Team velocity
    team_velocity_revisions_per_day: float
    team_velocity_projects_per_month: float
    
    # Collaboration patterns
    concurrent_project_activity: int
    avg_projects_per_active_day: float
    
    # Seasonal patterns
    monthly_activity_trend: Dict[str, int]
    quarterly_productivity: Dict[str, float]


@dataclass
class ProjectVelocityAnalysis:
    """Detailed velocity analysis for a project."""
    
    project_id: str
    project_name: str
    
    # Velocity trends
    velocity_trend: str  # "increasing", "decreasing", "stable", "erratic"
    velocity_consistency_score: float  # 0-100
    
    # Time periods analysis
    daily_velocities: List[Tuple[date, int]]  # (date, revision_count)
    weekly_velocities: List[Tuple[str, int]]  # (week_string, revision_count)
    monthly_velocities: List[Tuple[str, int]]  # (month_string, revision_count)
    
    # Sprint-like analysis
    activity_sprints: List[Dict[str, any]]  # Periods of high activity
    idle_periods: List[Dict[str, any]]  # Periods of no activity
    
    # Predictions
    velocity_forecast_next_week: float
    velocity_forecast_next_month: float
    projected_completion_velocity: Optional[float]


@dataclass
class StagnationAlert:
    """Alert for projects at risk of stagnation."""
    
    project_id: str
    project_name: str
    risk_level: StagnationRisk
    days_since_activity: int
    last_activity_date: Optional[datetime]
    
    # Context
    previous_activity_level: ActivityLevel
    expected_activity_level: ActivityLevel
    
    # Recommendations
    recommended_actions: List[str]
    urgency_score: int  # 1-10


@dataclass
class TemporalKPIDashboard:
    """Comprehensive temporal KPI dashboard."""
    
    generated_at: datetime
    analysis_period_days: int
    
    # High-level metrics
    total_projects_analyzed: int
    total_revisions_in_period: int
    avg_project_velocity: float
    
    # Activity distribution
    projects_by_activity_level: Dict[ActivityLevel, int]
    projects_by_stagnation_risk: Dict[StagnationRisk, int]
    
    # Team patterns
    team_temporal_metrics: TeamTemporalMetrics
    
    # Project analyses
    project_timelines: List[ProjectActivityTimeline]
    velocity_analyses: List[ProjectVelocityAnalysis]
    stagnation_alerts: List[StagnationAlert]
    
    # Trends
    overall_velocity_trend: str
    productivity_trend: str
    
    # Insights
    most_active_projects: List[str]
    most_stagnant_projects: List[str]
    projects_needing_attention: List[str]
    
    # Recommendations
    temporal_recommendations: List[str]


@dataclass
class ProjectLifecycleMetrics:
    """Metrics for project lifecycle timing."""
    
    project_id: str
    project_name: str
    
    # Lifecycle stages
    time_to_first_revision: Optional[timedelta]
    time_to_first_progress: Optional[timedelta]
    time_to_50_percent: Optional[timedelta]
    time_to_completion: Optional[timedelta]
    
    # Phase analysis
    planning_phase_duration: Optional[timedelta]
    development_phase_duration: Optional[timedelta]
    completion_phase_duration: Optional[timedelta]
    
    # Efficiency metrics
    time_efficiency_score: float  # 0-100
    lifecycle_health_score: float  # 0-100
    
    # Comparisons
    faster_than_average: bool
    lifecycle_percentile: int  # 0-100
    
    # Predictions
    predicted_total_duration: Optional[timedelta]
    predicted_completion_date: Optional[date]


@dataclass
class WorkflowTemporalPatterns:
    """Analysis of workflow patterns over time."""
    
    # Workflow timing
    avg_revision_to_revision_time: timedelta
    median_revision_to_revision_time: timedelta
    
    # Workflow efficiency
    workflow_efficiency_score: float
    bottleneck_indicators: List[str]
    
    # Patterns
    common_activity_patterns: List[Dict[str, any]]
    unusual_activity_patterns: List[Dict[str, any]]
    
    # Optimization opportunities
    suggested_workflow_improvements: List[str]