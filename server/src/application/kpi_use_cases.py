"""KPI use cases for calculating business metrics."""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..domain.kpi_entities import (
    KPIMetric, KPICategory, HealthStatus, ProjectHealthScore,
    TeamProductivityMetrics, SystemKPIDashboard
)
from ..domain.cway_entities import PlannerProject, CwayUser, ProjectState
from ..infrastructure.cway_repositories import CwayUserRepository, CwayProjectRepository
from ..infrastructure.graphql_client import CwayGraphQLClient


logger = logging.getLogger(__name__)


class KPIUseCases:
    """Use cases for calculating and retrieving KPIs."""
    
    def __init__(
        self,
        user_repository: CwayUserRepository,
        project_repository: CwayProjectRepository,
        graphql_client: CwayGraphQLClient
    ):
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.graphql_client = graphql_client
        
    async def calculate_system_kpi_dashboard(self) -> SystemKPIDashboard:
        """Calculate comprehensive system KPI dashboard."""
        logger.info("Calculating system KPI dashboard")
        
        # Get all data
        users = await self.user_repository.find_all_users()
        projects = await self.project_repository.get_planner_projects()
        project_revisions = await self._get_all_project_revisions(projects)
        
        total_revisions = sum(project_revisions.values())
        
        # Calculate key KPIs
        project_completion_rate = self._calculate_completion_rate(projects)
        stalled_project_rate = self._calculate_stalled_rate(projects)
        system_utilization = self._calculate_system_utilization(projects)
        revision_efficiency = self._calculate_revision_efficiency(projects, project_revisions)
        team_engagement = self._calculate_team_engagement(users, len(projects))
        
        # Calculate project health scores
        project_health_scores = []
        for project in projects:
            health_score = await self._calculate_project_health_score(
                project, project_revisions.get(project.id, 0)
            )
            project_health_scores.append(health_score)
        
        # Calculate team productivity metrics
        team_productivity = self._calculate_team_productivity(
            users, projects, project_revisions
        )
        
        # Calculate distributions
        state_distribution = self._calculate_state_distribution(projects)
        revision_distribution = self._calculate_revision_distribution(project_revisions)
        
        # Identify critical projects and generate recommendations
        critical_projects = [
            p.project_name for p in project_health_scores 
            if p.health_status == HealthStatus.CRITICAL
        ]
        
        recommendations = self._generate_system_recommendations(
            projects, project_health_scores, team_productivity
        )
        
        return SystemKPIDashboard(
            generated_at=datetime.now(),
            total_projects=len(projects),
            total_users=len(users),
            total_revisions=total_revisions,
            project_completion_rate=project_completion_rate,
            stalled_project_rate=stalled_project_rate,
            system_utilization=system_utilization,
            revision_efficiency=revision_efficiency,
            team_engagement=team_engagement,
            project_health_scores=project_health_scores,
            team_productivity=team_productivity,
            project_state_distribution=state_distribution,
            revision_distribution=revision_distribution,
            critical_projects=critical_projects,
            recommendations=recommendations
        )
    
    async def get_project_health_scores(self) -> List[ProjectHealthScore]:
        """Get health scores for all projects."""
        logger.info("Calculating project health scores")
        
        projects = await self.project_repository.get_planner_projects()
        project_revisions = await self._get_all_project_revisions(projects)
        
        health_scores = []
        for project in projects:
            health_score = await self._calculate_project_health_score(
                project, project_revisions.get(project.id, 0)
            )
            health_scores.append(health_score)
        
        # Sort by health score (worst first for attention)
        health_scores.sort(key=lambda x: x.overall_score)
        return health_scores
    
    async def get_critical_projects(self) -> List[ProjectHealthScore]:
        """Get projects that need immediate attention."""
        health_scores = await self.get_project_health_scores()
        return [
            score for score in health_scores 
            if score.health_status in [HealthStatus.CRITICAL, HealthStatus.WARNING]
        ]
    
    async def get_top_performing_projects(self, limit: int = 10) -> List[ProjectHealthScore]:
        """Get top performing projects by health score."""
        health_scores = await self.get_project_health_scores()
        health_scores.sort(key=lambda x: x.overall_score, reverse=True)
        return health_scores[:limit]
    
    async def _get_all_project_revisions(self, projects: List[PlannerProject]) -> Dict[str, int]:
        """Get revision counts for all projects."""
        project_revisions = {}
        
        for project in projects:
            try:
                query = f'''
                query {{
                    projectHistory(projectId: "{project.id}") {{
                        id
                    }}
                }}
                '''
                result = await self.graphql_client.execute_query(query)
                revisions = len(result.get('projectHistory', []))
                project_revisions[project.id] = revisions
            except Exception as e:
                logger.warning(f"Failed to get revisions for project {project.id}: {e}")
                project_revisions[project.id] = 0
        
        return project_revisions
    
    async def _calculate_project_health_score(
        self, 
        project: PlannerProject, 
        revision_count: int
    ) -> ProjectHealthScore:
        """Calculate comprehensive health score for a project."""
        
        # Component scores (0-100)
        progress_score = self._calculate_progress_score(project.percentageDone)
        revision_efficiency_score = self._calculate_revision_efficiency_score(
            project.percentageDone, revision_count
        )
        state_score = self._calculate_state_score(project.state)
        activity_score = self._calculate_activity_score(revision_count)
        
        # Calculate revisions per progress point
        revisions_per_progress = None
        if project.percentageDone > 0:
            revisions_per_progress = revision_count / project.percentageDone
        
        # Generate recommendations
        recommendations = self._generate_project_recommendations(
            project, revision_count, progress_score, revision_efficiency_score
        )
        
        return ProjectHealthScore(
            project_id=project.id,
            project_name=project.name,
            overall_score=0,  # Will be calculated in __post_init__
            health_status=HealthStatus.HEALTHY,  # Will be calculated in __post_init__
            progress_score=progress_score,
            revision_efficiency_score=revision_efficiency_score,
            state_score=state_score,
            activity_score=activity_score,
            progress_percentage=project.percentageDone,
            total_revisions=revision_count,
            revisions_per_progress_point=revisions_per_progress,
            days_since_last_update=None,  # Would need timestamp data
            recommendations=recommendations
        )
    
    def _calculate_progress_score(self, progress_percentage: float) -> float:
        """Calculate score based on project progress."""
        if progress_percentage >= 90:
            return 100.0
        elif progress_percentage >= 70:
            return 85.0
        elif progress_percentage >= 50:
            return 70.0
        elif progress_percentage >= 25:
            return 55.0
        elif progress_percentage > 0:
            return 40.0
        else:
            return 10.0  # Stalled project
    
    def _calculate_revision_efficiency_score(self, progress: float, revisions: int) -> float:
        """Calculate score based on revision efficiency."""
        if progress == 0:
            # No progress but has revisions = inefficient
            return 20.0 if revisions > 0 else 50.0
        
        if revisions == 0:
            return 30.0  # No activity
        
        revisions_per_progress = revisions / progress
        
        # Optimal range: 0.5-2 revisions per progress point
        if 0.5 <= revisions_per_progress <= 2.0:
            return 100.0
        elif revisions_per_progress <= 5.0:
            return 80.0
        elif revisions_per_progress <= 10.0:
            return 60.0
        else:
            return 30.0  # Too many revisions per progress point
    
    def _calculate_state_score(self, state: ProjectState) -> float:
        """Calculate score based on project state."""
        if state == ProjectState.DELIVERED:
            return 100.0
        elif state == ProjectState.COMPLETED:
            return 95.0
        elif state == ProjectState.IN_PROGRESS:
            return 70.0
        elif state == ProjectState.PLANNED:
            return 50.0
        else:  # CANCELLED
            return 0.0
    
    def _calculate_activity_score(self, revision_count: int) -> float:
        """Calculate score based on project activity level."""
        if revision_count == 0:
            return 10.0  # No activity
        elif revision_count <= 5:
            return 60.0
        elif revision_count <= 20:
            return 85.0
        else:
            return 100.0  # High activity
    
    def _calculate_completion_rate(self, projects: List[PlannerProject]) -> KPIMetric:
        """Calculate project completion rate KPI."""
        completed = len([p for p in projects if p.state in [ProjectState.COMPLETED, ProjectState.DELIVERED]])
        rate = (completed / len(projects)) * 100 if projects else 0
        
        return KPIMetric(
            name="Project Completion Rate",
            value=rate,
            unit="%",
            category=KPICategory.PROJECT_HEALTH,
            description="Percentage of projects that are completed or delivered",
            threshold_warning=20.0,
            threshold_critical=5.0,
            last_updated=datetime.now()
        )
    
    def _calculate_stalled_rate(self, projects: List[PlannerProject]) -> KPIMetric:
        """Calculate stalled project rate KPI."""
        stalled = len([p for p in projects if p.percentageDone == 0])
        rate = (stalled / len(projects)) * 100 if projects else 0
        
        return KPIMetric(
            name="Stalled Project Rate",
            value=rate,
            unit="%",
            category=KPICategory.PROJECT_HEALTH,
            description="Percentage of projects with 0% progress",
            threshold_warning=50.0,
            threshold_critical=80.0,
            last_updated=datetime.now()
        )
    
    def _calculate_system_utilization(self, projects: List[PlannerProject]) -> KPIMetric:
        """Calculate system utilization rate KPI."""
        active = len([p for p in projects if p.percentageDone > 0])
        rate = (active / len(projects)) * 100 if projects else 0
        
        return KPIMetric(
            name="System Utilization",
            value=rate,
            unit="%",
            category=KPICategory.OPERATIONAL_METRICS,
            description="Percentage of projects with active progress",
            threshold_warning=40.0,
            threshold_critical=20.0,
            last_updated=datetime.now()
        )
    
    def _calculate_revision_efficiency(
        self, 
        projects: List[PlannerProject], 
        project_revisions: Dict[str, int]
    ) -> KPIMetric:
        """Calculate average revision efficiency KPI."""
        active_projects = [p for p in projects if p.percentageDone > 0]
        
        if not active_projects:
            return KPIMetric(
                name="Revision Efficiency",
                value=0,
                unit="revisions/progress",
                category=KPICategory.QUALITY_INDICATORS,
                description="Average revisions per progress percentage point",
                last_updated=datetime.now()
            )
        
        total_efficiency = sum(
            project_revisions.get(p.id, 0) / p.percentageDone 
            for p in active_projects
        )
        avg_efficiency = total_efficiency / len(active_projects)
        
        return KPIMetric(
            name="Revision Efficiency",
            value=avg_efficiency,
            unit="revisions/progress",
            category=KPICategory.QUALITY_INDICATORS,
            description="Average revisions per progress percentage point",
            threshold_warning=5.0,
            threshold_critical=10.0,
            last_updated=datetime.now()
        )
    
    def _calculate_team_engagement(self, users: List[CwayUser], project_count: int) -> KPIMetric:
        """Calculate team engagement rate KPI."""
        # Simple engagement based on user/project ratio
        engagement = min(100, (project_count / len(users)) * 100) if users else 0
        
        return KPIMetric(
            name="Team Engagement",
            value=engagement,
            unit="%",
            category=KPICategory.TEAM_PRODUCTIVITY,
            description="Team engagement based on project distribution",
            threshold_warning=30.0,
            threshold_critical=15.0,
            last_updated=datetime.now()
        )
    
    def _calculate_team_productivity(
        self, 
        users: List[CwayUser], 
        projects: List[PlannerProject], 
        project_revisions: Dict[str, int]
    ) -> TeamProductivityMetrics:
        """Calculate comprehensive team productivity metrics."""
        active_projects = len([p for p in projects if p.percentageDone > 0])
        stalled_projects = len([p for p in projects if p.percentageDone == 0])
        total_revisions = sum(project_revisions.values())
        
        return TeamProductivityMetrics(
            total_users=len(users),
            active_users=len(users),  # Assuming all users are active
            user_engagement_rate=(active_projects / len(projects)) * 100 if projects else 0,
            total_projects=len(projects),
            active_projects=active_projects,
            stalled_projects=stalled_projects,
            total_revisions=total_revisions,
            avg_revisions_per_project=total_revisions / len(projects) if projects else 0,
            avg_revisions_per_user=total_revisions / len(users) if users else 0,
            projects_per_user_ratio=len(projects) / len(users) if users else 0,
            utilization_rate=(active_projects / len(projects)) * 100 if projects else 0
        )
    
    def _calculate_state_distribution(self, projects: List[PlannerProject]) -> Dict[str, int]:
        """Calculate project state distribution."""
        distribution = {}
        for project in projects:
            state = project.state.value
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
    
    def _calculate_revision_distribution(self, project_revisions: Dict[str, int]) -> Dict[str, int]:
        """Calculate revision count distribution."""
        distribution = {
            "0": 0,
            "1-10": 0,
            "11-20": 0,
            "21-50": 0,
            "50+": 0
        }
        
        for revision_count in project_revisions.values():
            if revision_count == 0:
                distribution["0"] += 1
            elif revision_count <= 10:
                distribution["1-10"] += 1
            elif revision_count <= 20:
                distribution["11-20"] += 1
            elif revision_count <= 50:
                distribution["21-50"] += 1
            else:
                distribution["50+"] += 1
        
        return distribution
    
    def _generate_project_recommendations(
        self, 
        project: PlannerProject, 
        revision_count: int,
        progress_score: float,
        efficiency_score: float
    ) -> List[str]:
        """Generate recommendations for a specific project."""
        recommendations = []
        
        if project.percentageDone == 0:
            if revision_count > 0:
                recommendations.append("Project has activity but no progress - review blockers")
            else:
                recommendations.append("Project appears stalled - needs immediate attention")
        
        if progress_score < 40:
            recommendations.append("Low progress score - consider resource allocation review")
        
        if efficiency_score < 50:
            recommendations.append("Low revision efficiency - may indicate scope creep or technical issues")
        
        if revision_count > 50:
            recommendations.append("High revision count - consider process optimization")
        
        if project.state == ProjectState.IN_PROGRESS and project.percentageDone > 80:
            recommendations.append("Near completion - prioritize for delivery")
        
        return recommendations
    
    def _generate_system_recommendations(
        self, 
        projects: List[PlannerProject],
        health_scores: List[ProjectHealthScore],
        team_productivity: TeamProductivityMetrics
    ) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []
        
        if team_productivity.stalled_projects > len(projects) * 0.5:
            recommendations.append("High number of stalled projects - conduct project review session")
        
        critical_count = len([h for h in health_scores if h.health_status == HealthStatus.CRITICAL])
        if critical_count > 3:
            recommendations.append(f"{critical_count} projects in critical state - immediate management attention required")
        
        if team_productivity.utilization_rate < 30:
            recommendations.append("Low system utilization - consider resource reallocation or project prioritization")
        
        if team_productivity.avg_revisions_per_project > 20:
            recommendations.append("High average revision count - review development processes")
        
        return recommendations