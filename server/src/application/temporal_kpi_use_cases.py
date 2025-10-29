"""Temporal KPI use cases for time-based analysis and calculations."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass

from src.domain.entities import Project, User
from src.domain.temporal_kpi_entities import (
    ProjectActivityTimeline,
    TeamTemporalMetrics,
    ProjectVelocityAnalysis,
    StagnationAlert,
    TemporalKPIDashboard,
    ProjectLifecycleMetrics,
    WorkflowTemporalPatterns,
    ActivityLevel,
    StagnationRisk
)
from src.domain.repository_interfaces import ProjectRepository, UserRepository


class TemporalKPICalculator:
    """Calculator for temporal KPIs based on project activity timelines."""
    
    def __init__(
        self,
        project_repository: ProjectRepository,
        user_repository: UserRepository
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
    
    async def calculate_project_activity_timeline(
        self, 
        project: Project
    ) -> ProjectActivityTimeline:
        """Calculate detailed activity timeline for a project."""
        
        # Extract revision timestamps from project history
        revision_timestamps = []
        if project.project_history:
            for history_item in project.project_history:
                if history_item.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(
                            history_item["timestamp"].replace("Z", "+00:00")
                        )
                        revision_timestamps.append(timestamp)
                    except (ValueError, TypeError):
                        continue
        
        # Sort timestamps
        revision_timestamps.sort()
        
        # Calculate basic metrics
        total_revisions = len(revision_timestamps)
        first_activity = revision_timestamps[0] if revision_timestamps else None
        last_activity = revision_timestamps[-1] if revision_timestamps else None
        
        # Parse project dates
        project_start_date = None
        project_end_date = None
        
        if project.start_date:
            try:
                project_start_date = datetime.fromisoformat(
                    project.start_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, TypeError):
                pass
        
        if project.end_date:
            try:
                project_end_date = datetime.fromisoformat(
                    project.end_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, TypeError):
                pass
        
        # Calculate time metrics
        now = datetime.now()
        days_since_last_activity = 0
        total_project_days = 0
        active_days = 0
        
        if last_activity:
            days_since_last_activity = (now - last_activity).days
        
        if first_activity and last_activity:
            total_project_days = (last_activity - first_activity).days + 1
            # Count unique activity days
            activity_dates = set(ts.date() for ts in revision_timestamps)
            active_days = len(activity_dates)
        
        idle_days = max(0, total_project_days - active_days)
        
        # Calculate velocity metrics
        revisions_per_day = 0
        revisions_per_week = 0
        revisions_per_month = 0
        
        if total_project_days > 0:
            revisions_per_day = total_revisions / total_project_days
            revisions_per_week = revisions_per_day * 7
            revisions_per_month = revisions_per_day * 30
        
        # Calculate burst analysis
        max_revisions_per_day = 0
        avg_time_between_revisions = None
        
        if revision_timestamps:
            # Count revisions per day
            daily_counts = Counter(ts.date() for ts in revision_timestamps)
            max_revisions_per_day = max(daily_counts.values())
            
            # Calculate average time between revisions
            if len(revision_timestamps) > 1:
                intervals = []
                for i in range(1, len(revision_timestamps)):
                    interval = revision_timestamps[i] - revision_timestamps[i-1]
                    intervals.append(interval)
                
                if intervals:
                    avg_seconds = sum(i.total_seconds() for i in intervals) / len(intervals)
                    avg_time_between_revisions = timedelta(seconds=avg_seconds)
        
        # Simple completion prediction based on velocity
        estimated_completion_date = None
        days_to_completion_estimate = None
        
        if (project.completion_percentage is not None and 
            project.completion_percentage < 100 and 
            revisions_per_day > 0):
            
            remaining_percentage = 100 - project.completion_percentage
            # Assume similar revision rate needed for remaining work
            estimated_revisions_needed = (remaining_percentage / 100) * total_revisions
            estimated_days = estimated_revisions_needed / revisions_per_day
            
            days_to_completion_estimate = int(estimated_days)
            if last_activity:
                estimated_completion_date = (last_activity + timedelta(days=estimated_days)).date()
        
        return ProjectActivityTimeline(
            project_id=project.id,
            project_name=project.name,
            total_revisions=total_revisions,
            first_activity=first_activity,
            last_activity=last_activity,
            project_start_date=project_start_date,
            project_end_date=project_end_date,
            revisions_per_day=revisions_per_day,
            revisions_per_week=revisions_per_week,
            revisions_per_month=revisions_per_month,
            days_since_last_activity=days_since_last_activity,
            total_project_days=total_project_days,
            active_days=active_days,
            idle_days=idle_days,
            activity_level=ActivityLevel.INACTIVE,  # Will be set in __post_init__
            stagnation_risk=StagnationRisk.NONE,  # Will be set in __post_init__
            max_revisions_per_day=max_revisions_per_day,
            avg_time_between_revisions=avg_time_between_revisions,
            estimated_completion_date=estimated_completion_date,
            days_to_completion_estimate=days_to_completion_estimate
        )
    
    async def calculate_team_temporal_metrics(
        self, 
        projects: List[Project]
    ) -> TeamTemporalMetrics:
        """Calculate team-wide temporal metrics."""
        
        all_timestamps = []
        project_dates = set()
        
        # Collect all activity timestamps
        for project in projects:
            if project.project_history:
                for history_item in project.project_history:
                    if history_item.get("timestamp"):
                        try:
                            timestamp = datetime.fromisoformat(
                                history_item["timestamp"].replace("Z", "+00:00")
                            )
                            all_timestamps.append(timestamp)
                            project_dates.add(timestamp.date())
                        except (ValueError, TypeError):
                            continue
        
        # Calculate basic metrics
        total_active_days = len(project_dates)
        team_velocity_revisions_per_day = len(all_timestamps) / max(total_active_days, 1)
        
        # Calculate activity patterns
        activity_by_day_of_week = defaultdict(int)
        activity_by_hour = defaultdict(int)
        monthly_activity = defaultdict(int)
        
        for timestamp in all_timestamps:
            day_name = timestamp.strftime("%A")
            activity_by_day_of_week[day_name] += 1
            activity_by_hour[timestamp.hour] += 1
            month_key = timestamp.strftime("%Y-%m")
            monthly_activity[month_key] += 1
        
        # Find peak activity patterns
        peak_day = max(activity_by_day_of_week, key=activity_by_day_of_week.get) if activity_by_day_of_week else "Monday"
        peak_hour = max(activity_by_hour, key=activity_by_hour.get) if activity_by_hour else 9
        
        # Calculate team velocity for projects
        active_projects_per_month = len([p for p in projects if p.status == "ACTIVE"])
        team_velocity_projects_per_month = active_projects_per_month
        
        # Calculate concurrent activity
        concurrent_project_activity = len([p for p in projects if p.status == "ACTIVE"])
        avg_projects_per_active_day = concurrent_project_activity / max(total_active_days, 1)
        
        # Calculate quarterly productivity
        quarterly_productivity = {}
        for month_key, count in monthly_activity.items():
            year, month = map(int, month_key.split("-"))
            quarter = f"{year}-Q{(month-1)//3 + 1}"
            quarterly_productivity[quarter] = quarterly_productivity.get(quarter, 0) + count
        
        return TeamTemporalMetrics(
            total_active_days=total_active_days,
            avg_team_response_time=None,  # Would need more granular data
            peak_activity_day_of_week=peak_day,
            peak_activity_hour=peak_hour,
            activity_by_day_of_week=dict(activity_by_day_of_week),
            activity_by_hour=dict(activity_by_hour),
            team_velocity_revisions_per_day=team_velocity_revisions_per_day,
            team_velocity_projects_per_month=team_velocity_projects_per_month,
            concurrent_project_activity=concurrent_project_activity,
            avg_projects_per_active_day=avg_projects_per_active_day,
            monthly_activity_trend=dict(monthly_activity),
            quarterly_productivity=quarterly_productivity
        )
    
    async def analyze_project_velocity(
        self, 
        project: Project
    ) -> ProjectVelocityAnalysis:
        """Analyze project velocity trends and patterns."""
        
        # Extract and parse timestamps
        revision_timestamps = []
        if project.project_history:
            for history_item in project.project_history:
                if history_item.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(
                            history_item["timestamp"].replace("Z", "+00:00")
                        )
                        revision_timestamps.append(timestamp)
                    except (ValueError, TypeError):
                        continue
        
        revision_timestamps.sort()
        
        # Calculate daily velocities
        daily_counts = defaultdict(int)
        for ts in revision_timestamps:
            daily_counts[ts.date()] += 1
        
        daily_velocities = [(date_key, count) for date_key, count in sorted(daily_counts.items())]
        
        # Calculate weekly velocities
        weekly_counts = defaultdict(int)
        for ts in revision_timestamps:
            week_key = f"{ts.year}-W{ts.isocalendar()[1]:02d}"
            weekly_counts[week_key] += 1
        
        weekly_velocities = [(week_key, count) for week_key, count in sorted(weekly_counts.items())]
        
        # Calculate monthly velocities
        monthly_counts = defaultdict(int)
        for ts in revision_timestamps:
            month_key = f"{ts.year}-{ts.month:02d}"
            monthly_counts[month_key] += 1
        
        monthly_velocities = [(month_key, count) for month_key, count in sorted(monthly_counts.items())]
        
        # Analyze velocity trend
        velocity_trend = "stable"
        velocity_consistency_score = 50.0
        
        if len(weekly_velocities) >= 3:
            recent_weeks = [count for _, count in weekly_velocities[-3:]]
            early_weeks = [count for _, count in weekly_velocities[:3]]
            
            if len(early_weeks) > 0 and len(recent_weeks) > 0:
                early_avg = sum(early_weeks) / len(early_weeks)
                recent_avg = sum(recent_weeks) / len(recent_weeks)
                
                if recent_avg > early_avg * 1.2:
                    velocity_trend = "increasing"
                elif recent_avg < early_avg * 0.8:
                    velocity_trend = "decreasing"
                
                # Calculate consistency (inverse of coefficient of variation)
                all_counts = [count for _, count in weekly_velocities]
                if len(all_counts) > 1:
                    mean_count = statistics.mean(all_counts)
                    if mean_count > 0:
                        stdev_count = statistics.stdev(all_counts)
                        cv = stdev_count / mean_count
                        velocity_consistency_score = max(0, 100 - (cv * 50))
                        
                        if cv > 1.0:
                            velocity_trend = "erratic"
        
        # Identify activity sprints and idle periods
        activity_sprints = []
        idle_periods = []
        
        if daily_velocities:
            current_sprint = None
            current_idle = None
            
            for date_val, count in daily_velocities:
                if count >= 3:  # High activity threshold
                    if current_sprint is None:
                        current_sprint = {
                            "start_date": date_val,
                            "end_date": date_val,
                            "total_revisions": count,
                            "days": 1
                        }
                    else:
                        current_sprint["end_date"] = date_val
                        current_sprint["total_revisions"] += count
                        current_sprint["days"] += 1
                    
                    if current_idle:
                        idle_periods.append(current_idle)
                        current_idle = None
                else:
                    if current_sprint:
                        if current_sprint["days"] >= 2:  # Minimum sprint length
                            activity_sprints.append(current_sprint)
                        current_sprint = None
                    
                    if count == 0:  # Idle day
                        if current_idle is None:
                            current_idle = {
                                "start_date": date_val,
                                "end_date": date_val,
                                "days": 1
                            }
                        else:
                            current_idle["end_date"] = date_val
                            current_idle["days"] += 1
            
            # Close any open periods
            if current_sprint and current_sprint["days"] >= 2:
                activity_sprints.append(current_sprint)
            if current_idle and current_idle["days"] >= 3:  # Minimum idle period length
                idle_periods.append(current_idle)
        
        # Simple velocity forecasting
        velocity_forecast_next_week = 0.0
        velocity_forecast_next_month = 0.0
        
        if weekly_velocities:
            recent_velocities = [count for _, count in weekly_velocities[-4:]]  # Last 4 weeks
            if recent_velocities:
                velocity_forecast_next_week = statistics.mean(recent_velocities)
                velocity_forecast_next_month = velocity_forecast_next_week * 4
        
        return ProjectVelocityAnalysis(
            project_id=project.id,
            project_name=project.name,
            velocity_trend=velocity_trend,
            velocity_consistency_score=velocity_consistency_score,
            daily_velocities=daily_velocities,
            weekly_velocities=weekly_velocities,
            monthly_velocities=monthly_velocities,
            activity_sprints=activity_sprints,
            idle_periods=idle_periods,
            velocity_forecast_next_week=velocity_forecast_next_week,
            velocity_forecast_next_month=velocity_forecast_next_month,
            projected_completion_velocity=None  # Would need more sophisticated modeling
        )
    
    async def generate_stagnation_alerts(
        self, 
        project_timelines: List[ProjectActivityTimeline]
    ) -> List[StagnationAlert]:
        """Generate alerts for projects at risk of stagnation."""
        
        alerts = []
        
        for timeline in project_timelines:
            if timeline.stagnation_risk in [StagnationRisk.MODERATE, StagnationRisk.HIGH, StagnationRisk.CRITICAL]:
                
                # Determine previous activity level (simplified)
                previous_activity = ActivityLevel.MODERATE
                if timeline.total_revisions > 20:
                    previous_activity = ActivityLevel.HIGH
                elif timeline.total_revisions < 5:
                    previous_activity = ActivityLevel.LOW
                
                # Generate recommendations based on risk level
                recommendations = []
                urgency_score = 5
                
                if timeline.stagnation_risk == StagnationRisk.CRITICAL:
                    recommendations = [
                        "Immediate project review required",
                        "Contact project owner for status update",
                        "Consider project restructuring or cancellation",
                        "Assign dedicated project manager"
                    ]
                    urgency_score = 10
                elif timeline.stagnation_risk == StagnationRisk.HIGH:
                    recommendations = [
                        "Schedule project review meeting",
                        "Check for resource constraints",
                        "Identify blockers and dependencies",
                        "Set clear milestones and deadlines"
                    ]
                    urgency_score = 8
                elif timeline.stagnation_risk == StagnationRisk.MODERATE:
                    recommendations = [
                        "Monitor project progress closely",
                        "Send reminder to project team",
                        "Review project scope and priorities",
                        "Provide additional support if needed"
                    ]
                    urgency_score = 6
                
                alert = StagnationAlert(
                    project_id=timeline.project_id,
                    project_name=timeline.project_name,
                    risk_level=timeline.stagnation_risk,
                    days_since_activity=timeline.days_since_last_activity,
                    last_activity_date=timeline.last_activity,
                    previous_activity_level=previous_activity,
                    expected_activity_level=ActivityLevel.MODERATE,
                    recommended_actions=recommendations,
                    urgency_score=urgency_score
                )
                
                alerts.append(alert)
        
        # Sort by urgency score (highest first)
        alerts.sort(key=lambda x: x.urgency_score, reverse=True)
        
        return alerts
    
    async def generate_temporal_kpi_dashboard(
        self, 
        analysis_period_days: int = 90
    ) -> TemporalKPIDashboard:
        """Generate comprehensive temporal KPI dashboard."""
        
        # Fetch all projects
        projects = await self.project_repository.get_all_projects()
        
        # Calculate project timelines
        timeline_tasks = [
            self.calculate_project_activity_timeline(project) 
            for project in projects
        ]
        project_timelines = await asyncio.gather(*timeline_tasks)
        
        # Calculate team metrics
        team_temporal_metrics = await self.calculate_team_temporal_metrics(projects)
        
        # Analyze project velocities
        velocity_tasks = [
            self.analyze_project_velocity(project) 
            for project in projects
        ]
        velocity_analyses = await asyncio.gather(*velocity_tasks)
        
        # Generate stagnation alerts
        stagnation_alerts = await self.generate_stagnation_alerts(project_timelines)
        
        # Calculate aggregate metrics
        total_revisions = sum(timeline.total_revisions for timeline in project_timelines)
        avg_project_velocity = (
            sum(timeline.revisions_per_week for timeline in project_timelines) / 
            len(project_timelines) if project_timelines else 0
        )
        
        # Group projects by activity level and stagnation risk
        projects_by_activity = defaultdict(int)
        projects_by_stagnation = defaultdict(int)
        
        for timeline in project_timelines:
            projects_by_activity[timeline.activity_level] += 1
            projects_by_stagnation[timeline.stagnation_risk] += 1
        
        # Identify top projects
        most_active = sorted(
            project_timelines,
            key=lambda x: x.revisions_per_week,
            reverse=True
        )[:5]
        
        most_stagnant = sorted(
            project_timelines,
            key=lambda x: x.days_since_last_activity,
            reverse=True
        )[:5]
        
        projects_needing_attention = [
            timeline.project_name for timeline in project_timelines
            if timeline.stagnation_risk in [StagnationRisk.HIGH, StagnationRisk.CRITICAL]
        ]
        
        # Generate overall trends
        overall_velocity_trend = "stable"
        productivity_trend = "stable"
        
        if velocity_analyses:
            increasing_count = sum(1 for v in velocity_analyses if v.velocity_trend == "increasing")
            decreasing_count = sum(1 for v in velocity_analyses if v.velocity_trend == "decreasing")
            
            if increasing_count > decreasing_count * 1.5:
                overall_velocity_trend = "increasing"
            elif decreasing_count > increasing_count * 1.5:
                overall_velocity_trend = "decreasing"
        
        # Generate recommendations
        temporal_recommendations = []
        
        critical_stagnation_count = projects_by_stagnation[StagnationRisk.CRITICAL]
        if critical_stagnation_count > 0:
            temporal_recommendations.append(
                f"Urgent: {critical_stagnation_count} projects show critical stagnation risk"
            )
        
        low_activity_count = projects_by_activity[ActivityLevel.INACTIVE] + projects_by_activity[ActivityLevel.LOW]
        if low_activity_count > len(project_timelines) * 0.3:
            temporal_recommendations.append(
                "Consider resource reallocation - many projects show low activity"
            )
        
        if team_temporal_metrics.team_velocity_revisions_per_day < 1:
            temporal_recommendations.append(
                "Team velocity is below optimal - consider process improvements"
            )
        
        return TemporalKPIDashboard(
            generated_at=datetime.now(),
            analysis_period_days=analysis_period_days,
            total_projects_analyzed=len(project_timelines),
            total_revisions_in_period=total_revisions,
            avg_project_velocity=avg_project_velocity,
            projects_by_activity_level=dict(projects_by_activity),
            projects_by_stagnation_risk=dict(projects_by_stagnation),
            team_temporal_metrics=team_temporal_metrics,
            project_timelines=project_timelines,
            velocity_analyses=velocity_analyses,
            stagnation_alerts=stagnation_alerts,
            overall_velocity_trend=overall_velocity_trend,
            productivity_trend=productivity_trend,
            most_active_projects=[t.project_name for t in most_active],
            most_stagnant_projects=[t.project_name for t in most_stagnant],
            projects_needing_attention=projects_needing_attention,
            temporal_recommendations=temporal_recommendations
        )