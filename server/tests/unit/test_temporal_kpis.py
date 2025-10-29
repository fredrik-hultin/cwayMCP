"""Unit tests for temporal KPI functionality."""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock
from typing import List

from src.domain.entities import Project
from src.domain.temporal_kpi_entities import (
    ProjectActivityTimeline, 
    ActivityLevel, 
    StagnationRisk
)
from src.application.temporal_kpi_use_cases import TemporalKPICalculator


@pytest.fixture
def mock_project_repo():
    """Mock project repository."""
    repo = Mock()
    repo.get_all_projects = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    repo = Mock()
    repo.get_all_users = AsyncMock()
    return repo


@pytest.fixture
def temporal_kpi_calculator(mock_project_repo, mock_user_repo):
    """Temporal KPI calculator with mocked dependencies."""
    return TemporalKPICalculator(mock_project_repo, mock_user_repo)


@pytest.fixture
def sample_project_with_history():
    """Sample project with revision history."""
    now = datetime.now()
    history = [
        {
            "timestamp": (now - timedelta(days=30)).isoformat(),
            "action": "create",
            "description": "Project created"
        },
        {
            "timestamp": (now - timedelta(days=25)).isoformat(),
            "action": "update", 
            "description": "Progress update"
        },
        {
            "timestamp": (now - timedelta(days=20)).isoformat(),
            "action": "update",
            "description": "Progress update"
        },
        {
            "timestamp": (now - timedelta(days=15)).isoformat(),
            "action": "update",
            "description": "Progress update"
        },
        {
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "action": "update",
            "description": "Recent update"
        }
    ]
    
    return Project(
        id="test-project-1",
        name="Test Project",
        description="A test project with activity",
        status="ACTIVE",
        completion_percentage=60.0,
        start_date=(now - timedelta(days=35)).isoformat(),
        end_date=None,
        created_at=now - timedelta(days=35),
        updated_at=now - timedelta(days=5),
        project_history=history,
        assignees=["user1", "user2"],
        tags=["test", "development"],
        priority="HIGH"
    )


@pytest.fixture
def sample_stagnant_project():
    """Sample project with no recent activity."""
    now = datetime.now()
    history = [
        {
            "timestamp": (now - timedelta(days=120)).isoformat(),
            "action": "create",
            "description": "Project created"
        },
        {
            "timestamp": (now - timedelta(days=100)).isoformat(),
            "action": "update",
            "description": "Initial progress"
        },
        {
            "timestamp": (now - timedelta(days=95)).isoformat(),
            "action": "update",
            "description": "Last update"
        }
    ]
    
    return Project(
        id="test-project-2",
        name="Stagnant Project",
        description="A project with no recent activity",
        status="ACTIVE",
        completion_percentage=25.0,
        start_date=(now - timedelta(days=125)).isoformat(),
        end_date=None,
        created_at=now - timedelta(days=125),
        updated_at=now - timedelta(days=95),
        project_history=history,
        assignees=["user3"],
        tags=["legacy"],
        priority="LOW"
    )


@pytest.mark.asyncio
async def test_calculate_project_activity_timeline_active_project(
    temporal_kpi_calculator, 
    sample_project_with_history
):
    """Test activity timeline calculation for an active project."""
    
    timeline = await temporal_kpi_calculator.calculate_project_activity_timeline(
        sample_project_with_history
    )
    
    # Verify basic properties
    assert timeline.project_id == "test-project-1"
    assert timeline.project_name == "Test Project"
    assert timeline.total_revisions == 5
    
    # Verify timeline has activity and timing data
    assert timeline.first_activity is not None
    assert timeline.last_activity is not None
    assert timeline.days_since_last_activity <= 7  # Recent activity
    
    # Verify velocity calculations
    assert timeline.revisions_per_week > 0
    assert timeline.revisions_per_month > 0
    
    # Verify activity classification
    assert timeline.activity_level != ActivityLevel.INACTIVE
    assert timeline.stagnation_risk in [StagnationRisk.NONE, StagnationRisk.LOW]


@pytest.mark.asyncio
async def test_calculate_project_activity_timeline_stagnant_project(
    temporal_kpi_calculator,
    sample_stagnant_project
):
    """Test activity timeline calculation for a stagnant project."""
    
    timeline = await temporal_kpi_calculator.calculate_project_activity_timeline(
        sample_stagnant_project
    )
    
    # Verify basic properties
    assert timeline.project_id == "test-project-2"
    assert timeline.project_name == "Stagnant Project"
    assert timeline.total_revisions == 3
    
    # Verify stagnation indicators
    assert timeline.days_since_last_activity > 90  # Long time since activity
    assert timeline.stagnation_risk in [StagnationRisk.HIGH, StagnationRisk.CRITICAL]
    
    # Verify low activity level
    assert timeline.activity_level in [ActivityLevel.INACTIVE, ActivityLevel.LOW]


@pytest.mark.asyncio
async def test_analyze_project_velocity(
    temporal_kpi_calculator,
    sample_project_with_history
):
    """Test project velocity analysis."""
    
    velocity_analysis = await temporal_kpi_calculator.analyze_project_velocity(
        sample_project_with_history
    )
    
    # Verify basic properties
    assert velocity_analysis.project_id == "test-project-1"
    assert velocity_analysis.project_name == "Test Project"
    
    # Verify velocity data exists
    assert len(velocity_analysis.daily_velocities) > 0
    assert len(velocity_analysis.weekly_velocities) > 0
    assert len(velocity_analysis.monthly_velocities) > 0
    
    # Verify trend analysis
    assert velocity_analysis.velocity_trend in ["increasing", "decreasing", "stable", "erratic"]
    assert 0 <= velocity_analysis.velocity_consistency_score <= 100
    
    # Verify forecasting
    assert velocity_analysis.velocity_forecast_next_week >= 0
    assert velocity_analysis.velocity_forecast_next_month >= 0


@pytest.mark.asyncio
async def test_generate_stagnation_alerts(
    temporal_kpi_calculator,
    sample_project_with_history,
    sample_stagnant_project
):
    """Test stagnation alert generation."""
    
    # Create timelines for both projects
    active_timeline = await temporal_kpi_calculator.calculate_project_activity_timeline(
        sample_project_with_history
    )
    stagnant_timeline = await temporal_kpi_calculator.calculate_project_activity_timeline(
        sample_stagnant_project
    )
    
    # Generate alerts
    alerts = await temporal_kpi_calculator.generate_stagnation_alerts(
        [active_timeline, stagnant_timeline]
    )
    
    # Should have at least one alert (for stagnant project)
    assert len(alerts) >= 1
    
    # Find the stagnant project alert
    stagnant_alert = next(
        (alert for alert in alerts if alert.project_id == "test-project-2"),
        None
    )
    
    assert stagnant_alert is not None
    assert stagnant_alert.risk_level in [StagnationRisk.HIGH, StagnationRisk.CRITICAL]
    assert stagnant_alert.urgency_score >= 7
    assert len(stagnant_alert.recommended_actions) > 0
    
    # Verify alerts are sorted by urgency (highest first)
    if len(alerts) > 1:
        for i in range(len(alerts) - 1):
            assert alerts[i].urgency_score >= alerts[i + 1].urgency_score


@pytest.mark.asyncio
async def test_generate_temporal_kpi_dashboard(
    temporal_kpi_calculator,
    mock_project_repo,
    sample_project_with_history,
    sample_stagnant_project
):
    """Test temporal KPI dashboard generation."""
    
    # Mock the repository to return sample projects
    mock_project_repo.get_all_projects.return_value = [
        sample_project_with_history,
        sample_stagnant_project
    ]
    
    # Generate dashboard
    dashboard = await temporal_kpi_calculator.generate_temporal_kpi_dashboard()
    
    # Verify dashboard structure
    assert dashboard.generated_at is not None
    assert dashboard.analysis_period_days == 90  # default
    assert dashboard.total_projects_analyzed == 2
    assert dashboard.total_revisions_in_period > 0
    
    # Verify activity level distribution
    assert len(dashboard.projects_by_activity_level) > 0
    assert len(dashboard.projects_by_stagnation_risk) > 0
    
    # Verify we have both project timelines
    assert len(dashboard.project_timelines) == 2
    
    # Verify team metrics exist
    assert dashboard.team_temporal_metrics is not None
    assert dashboard.team_temporal_metrics.total_active_days > 0
    
    # Verify trends are calculated
    assert dashboard.overall_velocity_trend in ["increasing", "decreasing", "stable"]
    assert dashboard.productivity_trend in ["increasing", "decreasing", "stable"]
    
    # Verify recommendations exist
    assert isinstance(dashboard.temporal_recommendations, list)
    
    # Verify project categorization
    assert isinstance(dashboard.most_active_projects, list)
    assert isinstance(dashboard.most_stagnant_projects, list)
    assert isinstance(dashboard.projects_needing_attention, list)


def test_activity_level_classification():
    """Test activity level classification logic."""
    now = datetime.now()
    
    # Test inactive project
    timeline_inactive = ProjectActivityTimeline(
        project_id="test",
        project_name="Test",
        total_revisions=0,
        first_activity=None,
        last_activity=None,
        project_start_date=None,
        project_end_date=None,
        revisions_per_day=0,
        revisions_per_week=0,
        revisions_per_month=0,
        days_since_last_activity=0,
        total_project_days=0,
        active_days=0,
        idle_days=0,
        activity_level=ActivityLevel.INACTIVE,
        stagnation_risk=StagnationRisk.NONE,
        max_revisions_per_day=0,
        avg_time_between_revisions=None,
        estimated_completion_date=None,
        days_to_completion_estimate=None
    )
    
    # __post_init__ should classify this as inactive
    assert timeline_inactive.activity_level == ActivityLevel.INACTIVE
    assert timeline_inactive.stagnation_risk == StagnationRisk.NONE


def test_stagnation_risk_classification():
    """Test stagnation risk classification logic."""
    now = datetime.now()
    
    # Test critical stagnation (>90 days)
    timeline_critical = ProjectActivityTimeline(
        project_id="test",
        project_name="Test",
        total_revisions=5,
        first_activity=now - timedelta(days=100),
        last_activity=now - timedelta(days=95),
        project_start_date=None,
        project_end_date=None,
        revisions_per_day=0.1,
        revisions_per_week=0.7,
        revisions_per_month=3.0,
        days_since_last_activity=95,
        total_project_days=100,
        active_days=5,
        idle_days=95,
        activity_level=ActivityLevel.LOW,
        stagnation_risk=StagnationRisk.NONE,
        max_revisions_per_day=1,
        avg_time_between_revisions=timedelta(days=20),
        estimated_completion_date=None,
        days_to_completion_estimate=None
    )
    
    # __post_init__ should classify this as critical
    assert timeline_critical.stagnation_risk == StagnationRisk.CRITICAL