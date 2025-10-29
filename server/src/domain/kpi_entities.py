"""KPI domain entities for Cway business metrics."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class KPICategory(Enum):
    """KPI category enumeration."""
    PROJECT_HEALTH = "project_health"
    TEAM_PRODUCTIVITY = "team_productivity"
    OPERATIONAL_METRICS = "operational_metrics"
    QUALITY_INDICATORS = "quality_indicators"


class HealthStatus(Enum):
    """Project health status enumeration."""
    CRITICAL = "critical"
    WARNING = "warning"
    HEALTHY = "healthy"
    EXCELLENT = "excellent"


@dataclass
class KPIMetric:
    """Individual KPI metric."""
    
    name: str
    value: float
    unit: str
    category: KPICategory
    description: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    last_updated: Optional[datetime] = None
    
    @property
    def status(self) -> HealthStatus:
        """Determine health status based on thresholds."""
        if self.threshold_critical is not None and self.value <= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.threshold_warning is not None and self.value <= self.threshold_warning:
            return HealthStatus.WARNING
        elif self.value >= 90:  # Default excellence threshold
            return HealthStatus.EXCELLENT
        else:
            return HealthStatus.HEALTHY


@dataclass
class ProjectHealthScore:
    """Comprehensive project health assessment."""
    
    project_id: str
    project_name: str
    overall_score: float  # 0-100
    health_status: HealthStatus
    
    # Component scores
    progress_score: float
    revision_efficiency_score: float
    state_score: float
    activity_score: float
    
    # Supporting metrics
    progress_percentage: float
    total_revisions: int
    revisions_per_progress_point: Optional[float]
    days_since_last_update: Optional[int]
    
    # Recommendations
    recommendations: List[str]
    
    def __post_init__(self):
        """Calculate overall score and status after initialization."""
        if not hasattr(self, '_calculated'):
            self._calculated = True
            self._calculate_overall_score()
    
    def _calculate_overall_score(self):
        """Calculate weighted overall health score."""
        weights = {
            'progress': 0.30,
            'revision_efficiency': 0.25,
            'state': 0.25,
            'activity': 0.20
        }
        
        self.overall_score = (
            self.progress_score * weights['progress'] +
            self.revision_efficiency_score * weights['revision_efficiency'] +
            self.state_score * weights['state'] +
            self.activity_score * weights['activity']
        )
        
        # Determine health status
        if self.overall_score >= 85:
            self.health_status = HealthStatus.EXCELLENT
        elif self.overall_score >= 70:
            self.health_status = HealthStatus.HEALTHY
        elif self.overall_score >= 50:
            self.health_status = HealthStatus.WARNING
        else:
            self.health_status = HealthStatus.CRITICAL


@dataclass
class TeamProductivityMetrics:
    """Team productivity analytics."""
    
    total_users: int
    active_users: int
    user_engagement_rate: float
    
    total_projects: int
    active_projects: int
    stalled_projects: int
    
    total_revisions: int
    avg_revisions_per_project: float
    avg_revisions_per_user: float
    
    projects_per_user_ratio: float
    utilization_rate: float


@dataclass
class SystemKPIDashboard:
    """Complete system KPI dashboard."""
    
    # Timestamp
    generated_at: datetime
    
    # Summary metrics
    total_projects: int
    total_users: int
    total_revisions: int
    
    # Key KPIs
    project_completion_rate: KPIMetric
    stalled_project_rate: KPIMetric
    system_utilization: KPIMetric
    revision_efficiency: KPIMetric
    team_engagement: KPIMetric
    
    # Detailed breakdowns
    project_health_scores: List[ProjectHealthScore]
    team_productivity: TeamProductivityMetrics
    
    # State distributions
    project_state_distribution: Dict[str, int]
    revision_distribution: Dict[str, int]
    
    # Alerts and recommendations
    critical_projects: List[str]
    recommendations: List[str]
    
    @property
    def health_summary(self) -> Dict[str, int]:
        """Get count of projects by health status."""
        summary = {status.value: 0 for status in HealthStatus}
        for project in self.project_health_scores:
            summary[project.health_status.value] += 1
        return summary


@dataclass
class KPITrend:
    """KPI trend data over time."""
    
    metric_name: str
    values: List[float]
    timestamps: List[datetime]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, how strong the trend is
    
    @property
    def latest_value(self) -> Optional[float]:
        """Get the most recent value."""
        return self.values[-1] if self.values else None
    
    @property
    def change_percentage(self) -> Optional[float]:
        """Calculate percentage change from first to last value."""
        if len(self.values) >= 2:
            first, last = self.values[0], self.values[-1]
            if first != 0:
                return ((last - first) / first) * 100
        return None