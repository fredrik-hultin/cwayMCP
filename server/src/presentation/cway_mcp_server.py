"""Updated MCP server implementation with real Cway API integration."""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    TextResourceContents,
    ReadResourceResult,
    ListToolsResult,
    CallToolResult,
    ListResourcesResult,
)

from config.settings import settings
from ..infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError
from ..infrastructure.repositories import (
    UserRepository,
    ProjectRepository,
    ArtworkRepository,
    MediaRepository,
    ShareRepository,
    TeamRepository,
    SearchRepository,
    CategoryRepository
)
from ..infrastructure.cway_repositories import CwaySystemRepository
from ..domain.cway_entities import ProjectState
from ..application.kpi_use_cases import KPIUseCases
from ..application.temporal_kpi_use_cases import TemporalKPICalculator
from ..domain.kpi_entities import SystemKPIDashboard, ProjectHealthScore
from ..domain.temporal_kpi_entities import (
    TemporalKPIDashboard,
    ProjectActivityTimeline,
    StagnationAlert
)
from ..indexing.mcp_indexing_service import get_indexing_service
from .tool_definitions import get_all_tools
from ..application.services import ConfirmationService
from ..infrastructure.auth.token_manager import TokenManager, TokenManagerError


# Set up logging - redirect to file and stderr to avoid interfering with stdio protocol
import sys
from pathlib import Path

# Ensure log directory exists
log_dir = Path(settings.log_dir)
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "mcp_server.log"

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Log to stderr, not stdout
    ]
)
logger = logging.getLogger(__name__)


class CwayMCPServer:
    """MCP server for real Cway API integration."""
    
    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.server = Server("cway-mcp-server")
        self.graphql_client: Optional[CwayGraphQLClient] = None
        self.user_repo: Optional[UserRepository] = None
        self.project_repo: Optional[ProjectRepository] = None
        self.artwork_repo: Optional[ArtworkRepository] = None
        self.media_repo: Optional[MediaRepository] = None
        self.share_repo: Optional[ShareRepository] = None
        self.team_repo: Optional[TeamRepository] = None
        self.search_repo: Optional[SearchRepository] = None
        self.category_repo: Optional[CategoryRepository] = None
        self.system_repo: Optional[CwaySystemRepository] = None
        self.kpi_use_cases: Optional[KPIUseCases] = None
        self.temporal_kpi_calculator: Optional[TemporalKPICalculator] = None
        self.indexing_service = get_indexing_service()
        self.confirmation_service = ConfirmationService(
            secret_key=settings.secret_key if hasattr(settings, 'secret_key') else None,
            default_expiry_minutes=5
        )
        
        # Per-user authentication support
        self.token_manager: Optional[TokenManager] = None
        if settings.auth_method == "oauth2":
            self.token_manager = TokenManager(
                api_url=settings.cway_api_url,
                tenant_id=settings.azure_tenant_id,
                client_id=settings.azure_client_id
            )
            logger.info("🔐 Token Manager initialized for per-user authentication")
        
        # Register handlers
        self._register_handlers()
        
    def _register_handlers(self) -> None:
        """Register MCP handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            logger.info("📋 list_resources called")
            resources = [
                Resource(
                    uri="cway://projects",
                    name="Cway Projects",
                    description="Access to all Cway planner projects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://users", 
                    name="Cway Users",
                    description="Access to all Cway users",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://projects/active",
                    name="Active Projects",
                    description="Currently active projects only",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://projects/completed",
                    name="Completed Projects", 
                    description="Completed projects only",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://system/status",
                    name="System Status",
                    description="Cway system connection status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://kpis/dashboard",
                    name="KPI Dashboard",
                    description="Comprehensive system KPI dashboard with health scores",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://kpis/project-health",
                    name="Project Health Scores",
                    description="Health scores and metrics for all projects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://kpis/critical-projects",
                    name="Critical Projects",
                    description="Projects requiring immediate attention",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://temporal-kpis/dashboard",
                    name="Temporal KPI Dashboard",
                    description="Comprehensive temporal analysis dashboard with velocity, stagnation, and activity metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://temporal-kpis/project-timelines",
                    name="Project Activity Timelines",
                    description="Detailed activity timelines for all projects with velocity analysis",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://temporal-kpis/stagnation-alerts",
                    name="Stagnation Alerts",
                    description="Projects at risk of stagnation with actionable recommendations",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://temporal-kpis/team-metrics",
                    name="Team Temporal Metrics",
                    description="Team-wide activity patterns and productivity insights",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://indexing/targets",
                    name="Indexing Targets",
                    description="Available indexing targets and configurations",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://indexing/status",
                    name="Indexing Status",
                    description="Current indexing job status and history",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://indexing/content-stats",
                    name="Content Statistics",
                    description="Statistics about indexable content (documents and pages)",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://indexing/platforms",
                    name="Supported Platforms",
                    description="List of supported indexing platforms and their capabilities",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)
            
        @self.server.read_resource()
        async def read_resource(uri: str) -> list[TextResourceContents]:
            """Get a specific resource."""
            logger.info(f"📖 read_resource called with URI: {uri}")
            await self._ensure_initialized()
            
            try:
                if uri == "cway://projects":
                    projects = await self.project_repo.get_planner_projects()
                    content = "\n".join([
                        f"Project: {p.name} (ID: {p.id})\n"
                        f"  State: {p.state.value}\n"
                        f"  Progress: {p.percentageDone:.1%}\n"
                        f"  Dates: {p.startDate} to {p.endDate}\n"
                        for p in projects
                    ])
                    
                elif uri == "cway://users":
                    users = await self.user_repo.find_all_users()
                    content = "\n".join([
                        f"User: {u.full_name} (ID: {u.id})\n"
                        f"  Email: {u.email}\n"
                        f"  Username: {u.username}\n"
                        f"  Enabled: {u.enabled}\n"
                        for u in users
                    ])
                    
                elif uri == "cway://projects/active":
                    projects = await self.project_repo.get_active_projects()
                    content = f"Active Projects ({len(projects)}):\n\n" + "\n".join([
                        f"• {p.name} - {p.percentageDone:.1%} complete"
                        for p in projects
                    ])
                    
                elif uri == "cway://projects/completed":
                    projects = await self.project_repo.get_completed_projects()
                    content = f"Completed Projects ({len(projects)}):\n\n" + "\n".join([
                        f"• {p.name} - completed"
                        for p in projects
                    ])
                    
                elif uri == "cway://system/status":
                    is_connected = await self.system_repo.validate_connection()
                    login_info = await self.system_repo.get_login_info()
                    content = f"Cway System Status:\n"
                    content += f"  Connection: {'✅ Connected' if is_connected else '❌ Disconnected'}\n"
                    content += f"  Login Info: {json.dumps(login_info, indent=2) if login_info else 'Not available'}\n"
                    content += f"  API URL: {settings.cway_api_url}\n"
                    
                elif uri == "cway://kpis/dashboard":
                    dashboard = await self.kpi_use_cases.calculate_system_kpi_dashboard()
                    content = f"📊 CWAY SYSTEM KPI DASHBOARD\n"
                    content += f"Generated: {dashboard.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    
                    # Key metrics
                    content += f"📈 KEY METRICS:\n"
                    content += f"  Projects: {dashboard.total_projects} | Users: {dashboard.total_users} | Revisions: {dashboard.total_revisions:,}\n\n"
                    
                    # Critical KPIs with status indicators
                    kpis = [
                        ("Project Completion Rate", dashboard.project_completion_rate),
                        ("Stalled Project Rate", dashboard.stalled_project_rate),
                        ("System Utilization", dashboard.system_utilization),
                        ("Team Engagement", dashboard.team_engagement)
                    ]
                    
                    content += f"🎯 CRITICAL KPIs:\n"
                    for name, kpi in kpis:
                        status_emoji = {"critical": "🔴", "warning": "🟡", "healthy": "🟢", "excellent": "⭐"}.get(kpi.status.value, "⚪")
                        content += f"  {status_emoji} {name}: {kpi.value:.1f}{kpi.unit} ({kpi.status.value.title()})\n"
                    
                    # Health summary
                    health_summary = dashboard.health_summary
                    content += f"\n🏥 PROJECT HEALTH SUMMARY:\n"
                    content += f"  🔴 Critical: {health_summary.get('critical', 0)} projects\n"
                    content += f"  🟡 Warning: {health_summary.get('warning', 0)} projects\n"
                    content += f"  🟢 Healthy: {health_summary.get('healthy', 0)} projects\n"
                    content += f"  ⭐ Excellent: {health_summary.get('excellent', 0)} projects\n"
                    
                    # Recommendations
                    if dashboard.recommendations:
                        content += f"\n💡 RECOMMENDATIONS:\n"
                        for rec in dashboard.recommendations[:3]:  # Top 3
                            content += f"  • {rec}\n"
                    
                elif uri == "cway://kpis/project-health":
                    health_scores = await self.kpi_use_cases.get_project_health_scores()
                    content = f"🏥 PROJECT HEALTH SCORES ({len(health_scores)} projects)\n\n"
                    
                    for i, score in enumerate(health_scores[:10], 1):  # Top 10 worst
                        status_emoji = {"critical": "🔴", "warning": "🟡", "healthy": "🟢", "excellent": "⭐"}.get(score.health_status.value, "⚪")
                        content += f"{i:2d}. {status_emoji} {score.project_name}\n"
                        content += f"    Overall Score: {score.overall_score:.1f}/100\n"
                        content += f"    Progress: {score.progress_percentage:.1f}% | Revisions: {score.total_revisions}\n"
                        if score.recommendations:
                            content += f"    💡 {score.recommendations[0]}\n"
                        content += "\n"
                    
                elif uri == "cway://kpis/critical-projects":
                    critical_projects = await self.kpi_use_cases.get_critical_projects()
                    content = f"🚨 CRITICAL PROJECTS REQUIRING ATTENTION ({len(critical_projects)} projects)\n\n"
                    
                    for i, score in enumerate(critical_projects, 1):
                        status_emoji = "🔴" if score.health_status.value == "critical" else "🟡"
                        content += f"{i}. {status_emoji} {score.project_name}\n"
                        content += f"   Health Score: {score.overall_score:.1f}/100 ({score.health_status.value.upper()})\n"
                        content += f"   Progress: {score.progress_percentage:.1f}% | Revisions: {score.total_revisions}\n"
                        
                        if score.recommendations:
                            content += f"   🎯 Actions needed:\n"
                            for rec in score.recommendations[:2]:  # Top 2 recommendations
                                content += f"      • {rec}\n"
                        content += "\n"
                    
                elif uri == "cway://temporal-kpis/dashboard":
                    dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard()
                    content = f"⏰ TEMPORAL KPI DASHBOARD\n"
                    content += f"Generated: {dashboard.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    
                    # Overview metrics
                    content += f"📊 OVERVIEW ({dashboard.analysis_period_days} days analysis):\n"
                    content += f"  Projects Analyzed: {dashboard.total_projects_analyzed}\n"
                    content += f"  Total Revisions: {dashboard.total_revisions_in_period:,}\n"
                    content += f"  Avg Project Velocity: {dashboard.avg_project_velocity:.1f} rev/week\n\n"
                    
                    # Activity distribution
                    content += f"🚀 PROJECT ACTIVITY LEVELS:\n"
                    for level, count in dashboard.projects_by_activity_level.items():
                        level_emoji = {
                            "inactive": "⚪",
                            "low": "🔵", 
                            "moderate": "🟡",
                            "high": "🟠",
                            "burst": "🔴"
                        }.get(level.value, "⚪")
                        content += f"  {level_emoji} {level.value.title()}: {count} projects\n"
                    
                    # Stagnation risks
                    content += f"\n⚠️ STAGNATION RISK LEVELS:\n"
                    for risk, count in dashboard.projects_by_stagnation_risk.items():
                        risk_emoji = {
                            "none": "🟢",
                            "low": "🟡",
                            "moderate": "🟠",
                            "high": "🔴",
                            "critical": "💀"
                        }.get(risk.value, "⚪")
                        content += f"  {risk_emoji} {risk.value.title()}: {count} projects\n"
                    
                    # Team metrics
                    team_metrics = dashboard.team_temporal_metrics
                    content += f"\n👥 TEAM TEMPORAL PATTERNS:\n"
                    content += f"  Peak Activity Day: {team_metrics.peak_activity_day_of_week}\n"
                    content += f"  Peak Activity Hour: {team_metrics.peak_activity_hour}:00\n"
                    content += f"  Team Velocity: {team_metrics.team_velocity_revisions_per_day:.1f} rev/day\n"
                    
                    # Trends
                    content += f"\n📈 VELOCITY TRENDS:\n"
                    content += f"  Overall Trend: {dashboard.overall_velocity_trend.title()}\n"
                    content += f"  Productivity Trend: {dashboard.productivity_trend.title()}\n"
                    
                    # Top projects
                    if dashboard.most_active_projects:
                        content += f"\n🌟 MOST ACTIVE PROJECTS:\n"
                        for i, project in enumerate(dashboard.most_active_projects[:5], 1):
                            content += f"  {i}. {project}\n"
                    
                    # Stagnant projects
                    if dashboard.most_stagnant_projects:
                        content += f"\n😴 MOST STAGNANT PROJECTS:\n"
                        for i, project in enumerate(dashboard.most_stagnant_projects[:5], 1):
                            content += f"  {i}. {project}\n"
                    
                    # Alerts summary
                    if dashboard.stagnation_alerts:
                        urgent_alerts = [a for a in dashboard.stagnation_alerts if a.urgency_score >= 8]
                        content += f"\n🚨 URGENT ALERTS: {len(urgent_alerts)} projects need immediate attention\n"
                    
                    # Recommendations
                    if dashboard.temporal_recommendations:
                        content += f"\n💡 KEY RECOMMENDATIONS:\n"
                        for rec in dashboard.temporal_recommendations[:3]:
                            content += f"  • {rec}\n"
                            
                elif uri == "cway://temporal-kpis/project-timelines":
                    dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard()
                    content = f"📅 PROJECT ACTIVITY TIMELINES ({len(dashboard.project_timelines)} projects)\n\n"
                    
                    for timeline in dashboard.project_timelines[:15]:  # Show top 15
                        activity_emoji = {
                            "inactive": "⚪",
                            "low": "🔵",
                            "moderate": "🟡",
                            "high": "🟠",
                            "burst": "🔴"
                        }.get(timeline.activity_level.value, "⚪")
                        
                        risk_emoji = {
                            "none": "🟢",
                            "low": "🟡", 
                            "moderate": "🟠",
                            "high": "🔴",
                            "critical": "💀"
                        }.get(timeline.stagnation_risk.value, "⚪")
                        
                        content += f"{activity_emoji} {timeline.project_name}\n"
                        content += f"  Activity: {timeline.activity_level.value.title()} ({timeline.revisions_per_week:.1f} rev/week)\n"
                        content += f"  Stagnation Risk: {risk_emoji} {timeline.stagnation_risk.value.title()}\n"
                        content += f"  Last Activity: {timeline.days_since_last_activity} days ago\n"
                        content += f"  Total Revisions: {timeline.total_revisions}\n"
                        if timeline.estimated_completion_date:
                            content += f"  Est. Completion: {timeline.estimated_completion_date}\n"
                        content += "\n"
                        
                elif uri == "cway://temporal-kpis/stagnation-alerts":
                    dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard()
                    alerts = dashboard.stagnation_alerts
                    content = f"🚨 STAGNATION ALERTS ({len(alerts)} projects at risk)\n\n"
                    
                    for i, alert in enumerate(alerts[:10], 1):  # Top 10 most urgent
                        risk_emoji = {
                            "moderate": "🟠",
                            "high": "🔴",
                            "critical": "💀"
                        }.get(alert.risk_level.value, "⚪")
                        
                        urgency_bar = "🔥" * min(alert.urgency_score, 10)
                        
                        content += f"{i:2d}. {risk_emoji} {alert.project_name}\n"
                        content += f"     Risk Level: {alert.risk_level.value.upper()}\n"
                        content += f"     Urgency: {urgency_bar} ({alert.urgency_score}/10)\n"
                        content += f"     Stagnant for: {alert.days_since_activity} days\n"
                        content += f"     Last Activity: {alert.last_activity_date.strftime('%Y-%m-%d') if alert.last_activity_date else 'Unknown'}\n"
                        
                        if alert.recommended_actions:
                            content += f"     🎯 Recommended Actions:\n"
                            for action in alert.recommended_actions[:2]:
                                content += f"        • {action}\n"
                        content += "\n"
                        
                elif uri == "cway://temporal-kpis/team-metrics":
                    dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard()
                    team_metrics = dashboard.team_temporal_metrics
                    content = f"👥 TEAM TEMPORAL METRICS\n\n"
                    
                    # Activity patterns
                    content += f"🗓️ ACTIVITY PATTERNS:\n"
                    content += f"  Peak Day: {team_metrics.peak_activity_day_of_week}\n"
                    content += f"  Peak Hour: {team_metrics.peak_activity_hour}:00\n"
                    content += f"  Total Active Days: {team_metrics.total_active_days}\n\n"
                    
                    # Velocity metrics
                    content += f"⚡ TEAM VELOCITY:\n"
                    content += f"  Revisions/Day: {team_metrics.team_velocity_revisions_per_day:.2f}\n"
                    content += f"  Projects/Month: {team_metrics.team_velocity_projects_per_month}\n"
                    content += f"  Concurrent Projects: {team_metrics.concurrent_project_activity}\n"
                    content += f"  Projects/Active Day: {team_metrics.avg_projects_per_active_day:.1f}\n\n"
                    
                    # Day of week breakdown
                    if team_metrics.activity_by_day_of_week:
                        content += f"📊 ACTIVITY BY DAY OF WEEK:\n"
                        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        for day in days_order:
                            count = team_metrics.activity_by_day_of_week.get(day, 0)
                            bar = "█" * min(count // 10, 20) if count > 0 else ""
                            content += f"  {day:10s}: {count:3d} {bar}\n"
                    
                    # Monthly trends
                    if team_metrics.monthly_activity_trend:
                        content += f"\n📈 MONTHLY ACTIVITY TREND:\n"
                        sorted_months = sorted(team_metrics.monthly_activity_trend.items())
                        for month, count in sorted_months[-6:]:  # Last 6 months
                            bar = "█" * min(count // 50, 20) if count > 0 else ""
                            content += f"  {month}: {count:4d} {bar}\n"
                    
                elif uri == "cway://indexing/targets":
                    targets = self.indexing_service.get_targets()
                    content = f"📇 INDEXING TARGETS ({len(targets)} configured)\n\n"
                    
                    for target in targets:
                        status_emoji = "✅" if target["enabled"] else "❌"
                        content += f"{status_emoji} {target['name']} ({target['platform']})\n"
                        content += f"   {target['description']}\n"
                        content += f"   Config: {'✓' if target['has_config'] else '⚠️  Missing'}\n\n"
                    
                elif uri == "cway://indexing/status":
                    active_jobs = self.indexing_service.get_active_jobs()
                    recent_history = self.indexing_service.get_job_history(limit=10)
                    
                    content = f"⚙️  INDEXING STATUS\n\n"
                    
                    if active_jobs:
                        content += f"🔄 ACTIVE JOBS ({len(active_jobs)}):\n"
                        for job in active_jobs:
                            content += f"  • {job['job_id']}: {job['message']}\n"
                            content += f"    Running for: {job['duration_seconds']:.1f}s\n\n"
                    else:
                        content += f"🔄 ACTIVE JOBS: None\n\n"
                    
                    content += f"📊 RECENT HISTORY ({len(recent_history)} jobs):\n"
                    for job in recent_history:
                        status_emoji = "✅" if job["success"] else "❌"
                        content += f"{status_emoji} {job['job_id']}\n"
                        content += f"   {job['message']}\n"
                        content += f"   Indexed: {job['documents_indexed']} docs | Duration: {job['duration_seconds']:.1f}s\n"
                        content += f"   Targets: {job['targets_completed']} ✅, {job['targets_failed']} ❌\n\n"
                    
                elif uri == "cway://indexing/content-stats":
                    stats = await self.indexing_service.get_indexable_content_stats()
                    
                    if "error" in stats:
                        content = f"❌ Error getting content stats: {stats['error']}"
                    else:
                        content = f"📊 INDEXABLE CONTENT STATISTICS\n\n"
                        content += f"📄 Total Documents: {stats['total_documents']:,}\n"
                        content += f"📁 Projects: {stats['projects']:,}\n"
                        content += f"👥 Users: {stats['users']:,}\n"
                        content += f"📈 KPI Documents: {stats['kpi_documents']:,}\n"
                        content += f"⏰ Temporal KPI Documents: {stats['temporal_kpi_documents']:,}\n\n"
                        
                        total = stats['total_documents']
                        if total > 0:
                            content += f"📊 DISTRIBUTION:\n"
                            content += f"  Projects: {stats['projects']/total*100:.1f}%\n"
                            content += f"  Users: {stats['users']/total*100:.1f}%\n"
                            content += f"  KPIs: {stats['kpi_documents']/total*100:.1f}%\n"
                            content += f"  Temporal KPIs: {stats['temporal_kpi_documents']/total*100:.1f}%\n"
                    
                elif uri == "cway://indexing/platforms":
                    platforms = self.indexing_service.get_supported_platforms()
                    content = f"🔌 SUPPORTED INDEXING PLATFORMS ({len(platforms)} available)\n\n"
                    
                    for platform in platforms:
                        content += f"📦 {platform['name']} ({platform['platform']})\n"
                        content += f"   {platform['description']}\n"
                        content += f"   Config fields: {', '.join(platform['config_fields'])}\n"
                        content += f"   Best for: {platform['suitable_for']}\n\n"
                    
                else:
                    content = f"Resource not found: {uri}"
                    
                return [TextResourceContents(uri=uri, text=content, mimeType="text/plain")]
                
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return [TextResourceContents(uri=uri, text=f"Error: {e}", mimeType="text/plain")]
                
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            logger.info("🔧 list_tools called")
            # Use modular tool definitions from tool_definitions.py
            tools = get_all_tools()
            return ListToolsResult(tools=tools)
            
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> CallToolResult:
            """Call a specific tool."""
            logger.info(f"🛠️  call_tool invoked: {name} with arguments: {arguments}")
            await self._ensure_initialized()
            
            if arguments is None:
                arguments = {}
                
            try:
                result = await self._execute_tool(name, arguments)
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))],
                    isError=False
                )
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {e}")],
                    isError=True
                )
                
    def _get_current_username(self) -> str:
        """Get current username for per-user authentication.
        
        Priority:
        1. Environment variable CWAY_USERNAME
        2. Default to 'default' for single-user scenarios
        """
        import os
        return os.environ.get("CWAY_USERNAME", "default")
    
    async def _get_authenticated_client(self, username: str) -> CwayGraphQLClient:
        """Get GraphQL client with valid token for user.
        
        Args:
            username: User identifier
            
        Returns:
            GraphQL client with valid authentication
            
        Raises:
            TokenManagerError: If user is not authenticated
        """
        if self.token_manager:
            # Get valid token (auto-refreshes if needed)
            access_token = await self.token_manager.get_valid_token(username)
            return self._create_graphql_client_for_user(access_token)
        else:
            # Fall back to static token from settings
            if not self.graphql_client:
                self.graphql_client = CwayGraphQLClient()
                await self.graphql_client.connect()
            return self.graphql_client
    
    def _create_graphql_client_for_user(self, access_token: str) -> CwayGraphQLClient:
        """Create a new GraphQL client with specific access token.
        
        Args:
            access_token: User-specific access token
            
        Returns:
            New GraphQL client instance
        """
        # Create client with specific token (don't use global token provider)
        client = CwayGraphQLClient(api_token=access_token)
        return client
    
    async def _ensure_initialized(self) -> None:
        """Ensure the server is initialized with all dependencies.
        
        For per-user auth (oauth2), this only validates configuration.
        For static auth, this initializes the shared GraphQL client.
        """
        if self.token_manager:
            # Per-user authentication mode - client created per-request
            # Just validate that auth config is correct
            username = self._get_current_username()
            if not self.token_manager.is_user_authenticated(username):
                raise TokenManagerError(
                    f"User '{username}' is not authenticated. "
                    "Please run authentication using the login tool."
                )
            logger.info(f"✅ User '{username}' is authenticated")
        else:
            # Static token mode - backward compatibility
            if not self.graphql_client:
                self.graphql_client = CwayGraphQLClient()
                await self.graphql_client.connect()
                
                # Initialize repositories
                self.user_repo = UserRepository(self.graphql_client)
                self.project_repo = ProjectRepository(self.graphql_client)
                self.artwork_repo = ArtworkRepository(self.graphql_client)
                self.media_repo = MediaRepository(self.graphql_client)
                self.share_repo = ShareRepository(self.graphql_client)
                self.team_repo = TeamRepository(self.graphql_client)
                self.search_repo = SearchRepository(self.graphql_client)
                self.category_repo = CategoryRepository(self.graphql_client)
                self.system_repo = CwaySystemRepository(self.graphql_client)
                
                # Initialize KPI use cases
                self.kpi_use_cases = KPIUseCases(
                    self.user_repo,
                    self.project_repo,
                    self.graphql_client
                )
                
                # Initialize temporal KPI calculator
                # Convert repositories to domain interfaces
                from ..infrastructure.repository_adapters import CwayProjectRepositoryAdapter, CwayUserRepositoryAdapter
                project_repo_adapter = CwayProjectRepositoryAdapter(self.project_repo)
                user_repo_adapter = CwayUserRepositoryAdapter(self.user_repo)
                
                self.temporal_kpi_calculator = TemporalKPICalculator(
                    project_repo_adapter,
                    user_repo_adapter
                )
            
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool.
        
        For per-user auth mode, this gets a fresh token for each request.
        For static auth mode, this uses the shared client.
        """
        # Get user-specific client if using per-user auth
        if self.token_manager:
            username = self._get_current_username()
            try:
                graphql_client = await self._get_authenticated_client(username)
            except TokenManagerError as e:
                logger.error(f"Authentication error for user '{username}': {e}")
                return {
                    "error": "Authentication required",
                    "message": str(e),
                    "action": "Please authenticate using the login tool"
                }
            
            # Initialize repositories with user-specific client
            user_repo = UserRepository(graphql_client)
            project_repo = ProjectRepository(graphql_client)
            artwork_repo = ArtworkRepository(graphql_client)
            media_repo = MediaRepository(graphql_client)
            share_repo = ShareRepository(graphql_client)
            team_repo = TeamRepository(graphql_client)
            search_repo = SearchRepository(graphql_client)
            category_repo = CategoryRepository(graphql_client)
            system_repo = CwaySystemRepository(graphql_client)
            
            # Initialize use cases
            kpi_use_cases = KPIUseCases(user_repo, project_repo, graphql_client)
            
            from ..infrastructure.repository_adapters import CwayProjectRepositoryAdapter, CwayUserRepositoryAdapter
            project_repo_adapter = CwayProjectRepositoryAdapter(project_repo)
            user_repo_adapter = CwayUserRepositoryAdapter(user_repo)
            temporal_kpi_calculator = TemporalKPICalculator(project_repo_adapter, user_repo_adapter)
        else:
            # Static auth mode - use shared instances
            graphql_client = self.graphql_client
            user_repo = user_repo
            project_repo = project_repo
            artwork_repo = artwork_repo
            media_repo = media_repo
            share_repo = share_repo
            team_repo = team_repo
            search_repo = search_repo
            category_repo = category_repo
            system_repo = system_repo
            kpi_use_cases = kpi_use_cases
            temporal_kpi_calculator = temporal_kpi_calculator
        
        # Tool name aliases for consistency
        if name == "list_all_users":
            name = "list_users"
        elif name == "get_planner_projects":
            name = "list_projects"
        elif name == "get_project_details":
            name = "get_project_by_id"
        elif name == "create_cway_user":
            name = "create_user"
        elif name == "create_cway_project":
            name = "create_project"
        elif name == "update_cway_project":
            name = "update_project"
        
        if name == "list_projects":
            projects = await project_repo.get_planner_projects()
            return {
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "state": p.state.value,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None,
                        "isActive": p.is_active,
                        "isCompleted": p.is_completed
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_project":
            project = await project_repo.find_project_by_id(arguments["project_id"])
            if project:
                return {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "state": project.state.value,
                        "percentageDone": project.percentageDone,
                        "startDate": str(project.startDate) if project.startDate else None,
                        "endDate": str(project.endDate) if project.endDate else None,
                        "isActive": project.is_active,
                        "isCompleted": project.is_completed
                    }
                }
            return {"project": None, "message": "Project not found"}
            
        elif name == "get_active_projects":
            projects = await project_repo.get_active_projects()
            return {
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "state": p.state.value,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_completed_projects":
            projects = await project_repo.get_completed_projects()
            return {
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "state": p.state.value,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "list_users":
            users = await user_repo.find_all_users()
            return {
                "users": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "fullName": u.full_name,
                        "email": u.email,
                        "username": u.username,
                        "firstName": u.firstName,
                        "lastName": u.lastName,
                        "enabled": u.enabled,
                        "avatar": u.avatar,
                        "isSSO": u.isSSO
                    }
                    for u in users
                ]
            }
            
        elif name == "get_user":
            user = await user_repo.find_user_by_id(arguments["user_id"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "fullName": user.full_name,
                        "email": user.email,
                        "username": user.username,
                        "firstName": user.firstName,
                        "lastName": user.lastName,
                        "enabled": user.enabled,
                        "avatar": user.avatar,
                        "isSSO": user.isSSO,
                        "acceptedTerms": user.acceptedTerms,
                        "earlyAccessProgram": user.earlyAccessProgram
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "find_user_by_email":
            user = await user_repo.find_user_by_email(arguments["email"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "fullName": user.full_name,
                        "email": user.email,
                        "username": user.username,
                        "enabled": user.enabled
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "get_users_page":
            page_data = await user_repo.find_users_page(
                page=arguments.get("page", 0),
                size=arguments.get("size", 10)
            )
            return {
                "users": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "fullName": u.full_name,
                        "email": u.email,
                        "username": u.username,
                        "enabled": u.enabled
                    }
                    for u in page_data["users"]
                ],
                "page": page_data["page"],
                "totalHits": page_data["totalHits"]
            }
            
        elif name == "get_system_status":
            is_connected = await system_repo.validate_connection()
            login_info = await system_repo.get_login_info()
            
            return {
                "connected": is_connected,
                "status": "online" if is_connected else "offline",
                "api_url": settings.cway_api_url,
                "login_info": login_info
            }
            
        elif name == "analyze_project_velocity":
            project_id = arguments["project_id"]
            project = await project_repo.find_project_by_id(project_id)
            if not project:
                return {"error": "Project not found"}
                
            # Convert to domain project for analysis
            from ..infrastructure.repository_adapters import CwayProjectRepositoryAdapter
            adapter = CwayProjectRepositoryAdapter(project_repo)
            domain_project = await adapter.get_project_by_id(project_id)
            
            if domain_project:
                velocity_analysis = await temporal_kpi_calculator.analyze_project_velocity(domain_project)
                return {
                    "project_velocity_analysis": {
                        "project_id": velocity_analysis.project_id,
                        "project_name": velocity_analysis.project_name,
                        "velocity_trend": velocity_analysis.velocity_trend,
                        "velocity_consistency_score": velocity_analysis.velocity_consistency_score,
                        "daily_velocities": [(str(date), count) for date, count in velocity_analysis.daily_velocities[-30:]],  # Last 30 days
                        "weekly_velocities": velocity_analysis.weekly_velocities[-12:],  # Last 12 weeks
                        "monthly_velocities": velocity_analysis.monthly_velocities[-6:],  # Last 6 months
                        "activity_sprints": velocity_analysis.activity_sprints,
                        "idle_periods": velocity_analysis.idle_periods,
                        "velocity_forecast_next_week": velocity_analysis.velocity_forecast_next_week,
                        "velocity_forecast_next_month": velocity_analysis.velocity_forecast_next_month
                    }
                }
            return {"error": "Could not analyze project velocity"}
            
        elif name == "get_temporal_dashboard":
            analysis_period = arguments.get("analysis_period_days", 90)
            dashboard = await temporal_kpi_calculator.generate_temporal_kpi_dashboard(analysis_period)
            
            return {
                "temporal_kpi_dashboard": {
                    "generated_at": dashboard.generated_at.isoformat(),
                    "analysis_period_days": dashboard.analysis_period_days,
                    "total_projects_analyzed": dashboard.total_projects_analyzed,
                    "total_revisions_in_period": dashboard.total_revisions_in_period,
                    "avg_project_velocity": dashboard.avg_project_velocity,
                    "projects_by_activity_level": {level.value: count for level, count in dashboard.projects_by_activity_level.items()},
                    "projects_by_stagnation_risk": {risk.value: count for risk, count in dashboard.projects_by_stagnation_risk.items()},
                    "team_temporal_metrics": {
                        "total_active_days": dashboard.team_temporal_metrics.total_active_days,
                        "peak_activity_day_of_week": dashboard.team_temporal_metrics.peak_activity_day_of_week,
                        "peak_activity_hour": dashboard.team_temporal_metrics.peak_activity_hour,
                        "team_velocity_revisions_per_day": dashboard.team_temporal_metrics.team_velocity_revisions_per_day,
                        "team_velocity_projects_per_month": dashboard.team_temporal_metrics.team_velocity_projects_per_month,
                        "concurrent_project_activity": dashboard.team_temporal_metrics.concurrent_project_activity
                    },
                    "overall_velocity_trend": dashboard.overall_velocity_trend,
                    "productivity_trend": dashboard.productivity_trend,
                    "most_active_projects": dashboard.most_active_projects,
                    "most_stagnant_projects": dashboard.most_stagnant_projects,
                    "projects_needing_attention": dashboard.projects_needing_attention,
                    "temporal_recommendations": dashboard.temporal_recommendations,
                    "stagnation_alerts_count": len(dashboard.stagnation_alerts)
                }
            }
            
        elif name == "get_stagnation_alerts":
            min_urgency = arguments.get("min_urgency_score", 5)
            dashboard = await temporal_kpi_calculator.generate_temporal_kpi_dashboard()
            
            filtered_alerts = [
                alert for alert in dashboard.stagnation_alerts 
                if alert.urgency_score >= min_urgency
            ]
            
            return {
                "stagnation_alerts": [
                    {
                        "project_id": alert.project_id,
                        "project_name": alert.project_name,
                        "risk_level": alert.risk_level.value,
                        "days_since_activity": alert.days_since_activity,
                        "last_activity_date": alert.last_activity_date.isoformat() if alert.last_activity_date else None,
                        "previous_activity_level": alert.previous_activity_level.value,
                        "expected_activity_level": alert.expected_activity_level.value,
                        "urgency_score": alert.urgency_score,
                        "recommended_actions": alert.recommended_actions
                    }
                    for alert in filtered_alerts
                ],
                "total_alerts": len(filtered_alerts),
                "min_urgency_filter": min_urgency
            }
            
        elif name == "index_all_content":
            targets = arguments.get("targets")
            result = await self.indexing_service.index_all_content(targets=targets)
            return {
                "indexing_result": {
                    "job_id": result.job_id,
                    "success": result.success,
                    "message": result.message,
                    "documents_indexed": result.documents_indexed,
                    "duration_seconds": result.duration_seconds,
                    "targets_completed": result.targets_completed,
                    "targets_failed": result.targets_failed,
                    "started_at": result.started_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None
                }
            }
            
        elif name == "quick_backup":
            result = await self.indexing_service.quick_backup()
            return {
                "backup_result": {
                    "job_id": result.job_id,
                    "success": result.success,
                    "message": result.message,
                    "documents_indexed": result.documents_indexed,
                    "duration_seconds": result.duration_seconds,
                    "started_at": result.started_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None
                }
            }
            
        elif name == "index_project_content":
            project_id = arguments["project_id"]
            targets = arguments.get("targets")
            result = await self.indexing_service.index_project_documents(project_id, targets=targets)
            return {
                "project_indexing_result": {
                    "job_id": result.job_id,
                    "success": result.success,
                    "message": result.message,
                    "documents_indexed": result.documents_indexed,
                    "duration_seconds": result.duration_seconds,
                    "targets_completed": result.targets_completed,
                    "targets_failed": result.targets_failed,
                    "started_at": result.started_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None
                }
            }
            
        elif name == "configure_indexing_target":
            name_arg = arguments["name"]
            platform = arguments["platform"]
            description = arguments["description"]
            config = arguments.get("config")
            enabled = arguments.get("enabled", True)
            
            success = self.indexing_service.add_target(
                name=name_arg,
                platform=platform,
                description=description,
                config=config,
                enabled=enabled
            )
            
            if not success:
                # Try updating existing target
                success = self.indexing_service.update_target(
                    name=name_arg,
                    description=description,
                    config=config,
                    enabled=enabled
                )
                action = "updated" if success else "failed to update"
            else:
                action = "created"
            
            return {
                "configuration_result": {
                    "success": success,
                    "action": action,
                    "target_name": name_arg,
                    "platform": platform
                }
            }
            
        elif name == "get_indexing_job_status":
            job_id = arguments["job_id"]
            status = self.indexing_service.get_job_status(job_id)
            
            if status:
                return {"job_status": status}
            else:
                return {"job_status": None, "message": "Job not found"}
        
        elif name == "get_login_info":
            login_info = await system_repo.get_login_info()
            if login_info:
                return {"login_info": login_info}
            return {"login_info": None, "message": "Login info not available"}
        
        elif name == "search_users":
            query = arguments.get("query")
            users = await user_repo.search_users(query)
            return {
                "users": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "username": u.username,
                        "email": u.email,
                        "firstName": u.firstName,
                        "lastName": u.lastName,
                        "enabled": u.enabled
                    }
                    for u in users
                ]
            }
        
        elif name == "search_projects":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            result = await project_repo.search_projects(query, limit)
            return {
                "projects": result.get("projects", []),
                "total_hits": result.get("total_hits", 0)
            }
        
        elif name == "get_project_by_id":
            project_id = arguments["project_id"]
            project = await project_repo.get_project_by_id(project_id)
            if project:
                return {"project": project}
            return {"project": None, "message": "Project not found"}
        
        elif name == "create_user":
            email = arguments["email"]
            username = arguments["username"]
            first_name = arguments.get("first_name") or arguments.get("firstName")
            last_name = arguments.get("last_name") or arguments.get("lastName")
            user = await user_repo.create_user(email, username, first_name, last_name)
            return {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "firstName": user.firstName,
                    "lastName": user.lastName,
                    "enabled": user.enabled
                },
                "message": "User created successfully"
            }
        
        elif name == "update_user_name":
            username = arguments["username"]
            first_name = arguments.get("first_name") or arguments.get("firstName")
            last_name = arguments.get("last_name") or arguments.get("lastName")
            user = await user_repo.update_user_name(username, first_name, last_name)
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "firstName": user.firstName,
                        "lastName": user.lastName,
                        "name": user.name,
                        "email": user.email,
                        "enabled": user.enabled
                    },
                    "message": "User updated successfully"
                }
            return {"user": None, "message": "User not found"}
        
        elif name == "prepare_delete_user":
            username = arguments["username"]
            
            # Fetch user details for preview
            users = await user_repo.search_users(username)
            user = None
            for u in users:
                if u.username == username:
                    user = u
                    break
            
            if not user:
                return {
                    "action": "error",
                    "message": f"User '{username}' not found",
                    "warnings": [f"User '{username}' does not exist"]
                }
            
            user_info = {
                "username": user.username,
                "name": user.name,
                "email": user.email,
                "enabled": user.enabled,
                "is_sso": user.isSSO if hasattr(user, 'isSSO') else False
            }
            
            # Generate warnings
            warnings = [
                f"⚠️ DESTRUCTIVE ACTION: Will permanently delete user '{username}'",
                "🚨 THIS ACTION CANNOT BE UNDONE",
                f"User email: {user.email}",
                "All user data and associations will be permanently lost",
                "User will lose access to all projects and artworks"
            ]
            
            if user.isSSO if hasattr(user, 'isSSO') else False:
                warnings.append("⚠️ This is an SSO user - deletion may affect external authentication")
            
            # Generate confirmation token
            token_info = self.confirmation_service.generate_token(
                action="delete_user",
                data={"username": username}
            )
            
            return self.confirmation_service.create_preview_response(
                action="delete",
                items=[user_info],
                item_type="user",
                warnings=warnings,
                token_info=token_info
            )
        
        elif name == "confirm_delete_user":
            confirmation_token = arguments["confirmation_token"]
            
            try:
                # Validate token and extract data
                validated = self.confirmation_service.validate_token(confirmation_token)
                if validated["action"] != "delete_user":
                    return {
                        "success": False,
                        "message": "Invalid token: wrong action type"
                    }
                
                username = validated["data"]["username"]
                
                # Execute the delete operation
                success = await user_repo.delete_user(username)
                
                return {
                    "success": success,
                    "action": "deleted",
                    "username": username,
                    "message": f"User '{username}' deleted successfully" if success else f"Failed to delete user '{username}'"
                }
            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Confirmation failed: {str(e)}"
                }
        
        elif name == "find_users_and_teams":
            search = arguments.get("search")
            page = arguments.get("page", 0)
            size = arguments.get("size", 10)
            result = await user_repo.find_users_and_teams(search, page, size)
            return {
                "items": result["items"],
                "page": result["page"],
                "total_hits": result["totalHits"],
                "message": f"Found {result['totalHits']} users and teams"
            }
        
        elif name == "get_permission_groups":
            groups = await user_repo.get_permission_groups()
            return {
                "permission_groups": groups,
                "count": len(groups),
                "message": f"Retrieved {len(groups)} permission groups"
            }
        
        elif name == "set_user_permissions":
            usernames = arguments["usernames"]
            permission_group_id = arguments["permission_group_id"]
            success = await user_repo.set_user_permissions(usernames, permission_group_id)
            return {
                "success": success,
                "users_updated": len(usernames) if success else 0,
                "message": f"Updated permissions for {len(usernames)} users" if success else "Failed to update permissions"
            }
        
        elif name == "create_project":
            name_val = arguments["name"]
            description = arguments.get("description")
            project = await project_repo.create_project(name_val, description)
            return {"project": project, "message": "Project created successfully"}
        
        elif name == "update_project":
            project_id = arguments["project_id"]
            name_val = arguments.get("name")
            description = arguments.get("description")
            project = await project_repo.update_project(project_id, name_val, description)
            return {"project": project, "message": "Project updated successfully"}
        
        # Project workflow tools with confirmation
        elif name == "prepare_close_projects":
            project_ids = arguments["project_ids"]
            force = arguments.get("force", False)
            
            # Fetch project details for preview
            projects = []
            warnings = []
            for pid in project_ids:
                project = await project_repo.get_project_by_id(pid)
                if project:
                    projects.append({
                        "id": project["id"],
                        "name": project["name"],
                        "status": project.get("status", "unknown"),
                        "artwork_count": len(project.get("artworks", [])) if "artworks" in project else 0
                    })
                else:
                    warnings.append(f"Project {pid} not found")
            
            if not projects:
                return {
                    "action": "error",
                    "message": "No valid projects found to close",
                    "warnings": warnings
                }
            
            # Generate warnings
            warnings.append(f"Will close {len(projects)} project(s)")
            if not force:
                warnings.append("Artworks must be complete or approved to close")
            else:
                warnings.append("⚠️ Force close enabled - will close even with incomplete artworks")
            warnings.append("This action can be reversed using reopen_projects")
            
            # Generate confirmation token
            token_info = self.confirmation_service.generate_token(
                action="close_projects",
                data={"project_ids": project_ids, "force": force}
            )
            
            return self.confirmation_service.create_preview_response(
                action="close",
                items=projects,
                item_type="projects",
                warnings=warnings,
                token_info=token_info
            )
        
        elif name == "confirm_close_projects":
            confirmation_token = arguments["confirmation_token"]
            
            try:
                # Validate token and extract data
                validated = self.confirmation_service.validate_token(confirmation_token)
                if validated["action"] != "close_projects":
                    return {
                        "success": False,
                        "message": "Invalid token: wrong action type"
                    }
                
                project_ids = validated["data"]["project_ids"]
                force = validated["data"]["force"]
                
                # Execute the close operation
                success = await project_repo.close_projects(project_ids, force)
                
                return {
                    "success": success,
                    "action": "closed",
                    "closed_count": len(project_ids) if success else 0,
                    "project_ids": project_ids,
                    "message": f"Successfully closed {len(project_ids)} project(s)" if success else "Failed to close projects"
                }
            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Confirmation failed: {str(e)}"
                }
        
        elif name == "reopen_projects":
            project_ids = arguments["project_ids"]
            success = await project_repo.reopen_projects(project_ids)
            return {
                "success": success,
                "reopened_count": len(project_ids) if success else 0,
                "message": f"Successfully reopened {len(project_ids)} projects" if success else "Failed to reopen projects"
            }
        
        elif name == "prepare_delete_projects":
            project_ids = arguments["project_ids"]
            force = arguments.get("force", False)
            
            # Fetch project details for preview
            projects = []
            warnings = []
            for pid in project_ids:
                project = await project_repo.get_project_by_id(pid)
                if project:
                    projects.append({
                        "id": project["id"],
                        "name": project["name"],
                        "status": project.get("status", "unknown"),
                        "artwork_count": len(project.get("artworks", [])) if "artworks" in project else 0
                    })
                else:
                    warnings.append(f"Project {pid} not found")
            
            if not projects:
                return {
                    "action": "error",
                    "message": "No valid projects found to delete",
                    "warnings": warnings
                }
            
            # Generate warnings
            warnings.append(f"⚠️ DESTRUCTIVE ACTION: Will permanently delete {len(projects)} project(s)")
            warnings.append("🚨 THIS ACTION CANNOT BE UNDONE")
            if not force:
                warnings.append("Projects must be empty (no artworks) to delete")
            else:
                warnings.append("⚠️ Force delete enabled - will delete even if projects are not empty")
            warnings.append("All associated artworks and data will be permanently lost")
            
            # Generate confirmation token
            token_info = self.confirmation_service.generate_token(
                action="delete_projects",
                data={"project_ids": project_ids, "force": force}
            )
            
            return self.confirmation_service.create_preview_response(
                action="delete",
                items=projects,
                item_type="projects",
                warnings=warnings,
                token_info=token_info
            )
        
        elif name == "confirm_delete_projects":
            confirmation_token = arguments["confirmation_token"]
            
            try:
                # Validate token and extract data
                validated = self.confirmation_service.validate_token(confirmation_token)
                if validated["action"] != "delete_projects":
                    return {
                        "success": False,
                        "message": "Invalid token: wrong action type"
                    }
                
                project_ids = validated["data"]["project_ids"]
                force = validated["data"]["force"]
                
                # Execute the delete operation
                success = await project_repo.delete_projects(project_ids, force)
                
                return {
                    "success": success,
                    "action": "deleted",
                    "deleted_count": len(project_ids) if success else 0,
                    "project_ids": project_ids,
                    "message": f"Successfully deleted {len(project_ids)} project(s)" if success else "Failed to delete projects"
                }
            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Confirmation failed: {str(e)}"
                }
        
        # Artwork tools
        elif name == "get_artwork":
            artwork_id = arguments["artwork_id"]
            artwork = await project_repo.get_artwork(artwork_id)
            if artwork:
                return {"artwork": artwork}
            return {"artwork": None, "message": "Artwork not found"}
        
        elif name == "create_artwork":
            project_id = arguments["project_id"]
            artwork_name = arguments["name"]
            description = arguments.get("description")
            artwork = await project_repo.create_artwork(project_id, artwork_name, description)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Artwork created successfully"
            }
        
        elif name == "approve_artwork":
            artwork_id = arguments["artwork_id"]
            artwork = await project_repo.approve_artwork(artwork_id)
            return {
                "artwork": artwork,
                "success": artwork is not None,
                "message": "Artwork approved successfully" if artwork else "Failed to approve artwork"
            }
        
        elif name == "reject_artwork":
            artwork_id = arguments["artwork_id"]
            reason = arguments.get("reason")
            artwork = await project_repo.reject_artwork(artwork_id, reason)
            return {
                "artwork": artwork,
                "success": artwork is not None,
                "message": "Artwork rejected successfully" if artwork else "Failed to reject artwork"
            }
        
        elif name == "get_my_artworks":
            result = await project_repo.get_my_artworks()
            return {
                "artworks": result,
                "message": f"Found {result['total_count']} artworks requiring action"
            }
        
        elif name == "get_artworks_to_approve":
            artworks = await project_repo.get_artworks_to_approve()
            return {
                "artworks": artworks,
                "count": len(artworks),
                "message": f"Found {len(artworks)} artworks awaiting approval"
            }
        
        elif name == "get_artworks_to_upload":
            artworks = await project_repo.get_artworks_to_upload()
            return {
                "artworks": artworks,
                "count": len(artworks),
                "message": f"Found {len(artworks)} artworks requiring upload"
            }
        
        elif name == "download_artworks":
            artwork_ids = arguments["artwork_ids"]
            zip_name = arguments.get("zip_name")
            job_id = await project_repo.create_artwork_download_job(artwork_ids, zip_name)
            return {
                "job_id": job_id,
                "artwork_count": len(artwork_ids),
                "success": True,
                "message": f"Download job created for {len(artwork_ids)} artworks. Job ID: {job_id}"
            }
        
        elif name == "get_artwork_preview":
            artwork_id = arguments["artwork_id"]
            preview = await project_repo.get_artwork_preview(artwork_id)
            if preview:
                return {
                    "preview": preview,
                    "message": "Preview file retrieved successfully"
                }
            return {
                "preview": None,
                "message": "No preview available for this artwork"
            }
        
        elif name == "get_artwork_history":
            artwork_id = arguments["artwork_id"]
            history = await project_repo.get_artwork_history(artwork_id)
            return {
                "history": history,
                "event_count": len(history),
                "message": f"Retrieved {len(history)} artwork events"
            }
        
        elif name == "analyze_artwork_ai":
            artwork_id = arguments["artwork_id"]
            thread_id = await project_repo.analyze_artwork_ai(artwork_id)
            return {
                "thread_id": thread_id,
                "success": True,
                "message": f"AI analysis started. Thread ID: {thread_id}"
            }
        
        elif name == "generate_project_summary_ai":
            project_id = arguments["project_id"]
            audience = arguments.get("audience", "PROJECT_MANAGER")
            summary = await project_repo.generate_project_summary_ai(project_id, audience)
            return {
                "summary": summary,
                "audience": audience,
                "success": True,
                "message": "AI summary generated successfully"
            }
        
        # Artwork workflow tools
        elif name == "submit_artwork_for_review":
            artwork_id = arguments["artwork_id"]
            artwork = await project_repo.submit_artwork_for_review(artwork_id)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Artwork submitted for review"
            }
        
        elif name == "request_artwork_changes":
            artwork_id = arguments["artwork_id"]
            reason = arguments["reason"]
            artwork = await project_repo.request_artwork_changes(artwork_id, reason)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Changes requested on artwork"
            }
        
        elif name == "get_artwork_comments":
            artwork_id = arguments["artwork_id"]
            limit = arguments.get("limit", 50)
            comments = await project_repo.get_artwork_comments(artwork_id, limit)
            return {
                "comments": comments,
                "comment_count": len(comments),
                "message": f"Retrieved {len(comments)} comments"
            }
        
        elif name == "add_artwork_comment":
            artwork_id = arguments["artwork_id"]
            text = arguments["text"]
            comment = await project_repo.add_artwork_comment(artwork_id, text)
            return {
                "comment": comment,
                "success": True,
                "message": "Comment added to artwork"
            }
        
        elif name == "get_artwork_versions":
            artwork_id = arguments["artwork_id"]
            versions = await project_repo.get_artwork_versions(artwork_id)
            return {
                "versions": versions,
                "version_count": len(versions),
                "message": f"Retrieved {len(versions)} versions"
            }
        
        elif name == "restore_artwork_version":
            artwork_id = arguments["artwork_id"]
            version_id = arguments["version_id"]
            artwork = await project_repo.restore_artwork_version(artwork_id, version_id)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Artwork rolled back to previous version"
            }
        
        elif name == "assign_artwork":
            artwork_id = arguments["artwork_id"]
            user_id = arguments["user_id"]
            artwork = await project_repo.assign_artwork(artwork_id, user_id)
            return {
                "artwork": artwork,
                "success": True,
                "message": f"Artwork assigned to user {user_id}"
            }
        
        elif name == "duplicate_artwork":
            artwork_id = arguments["artwork_id"]
            new_name = arguments.get("new_name")
            artwork = await project_repo.duplicate_artwork(artwork_id, new_name)
            return {
                "artwork": artwork,
                "success": True,
                "message": f"Artwork duplicated successfully. New ID: {artwork.get('id')}"
            }
        
        elif name == "archive_artwork":
            artwork_id = arguments["artwork_id"]
            artwork = await project_repo.archive_artwork(artwork_id)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Artwork archived successfully"
            }
        
        elif name == "unarchive_artwork":
            artwork_id = arguments["artwork_id"]
            artwork = await project_repo.unarchive_artwork(artwork_id)
            return {
                "artwork": artwork,
                "success": True,
                "message": "Artwork unarchived successfully"
            }
        
        # Team management tools
        elif name == "get_team_members":
            project_id = arguments["project_id"]
            team_members = await project_repo.get_team_members(project_id)
            return {
                "team_members": team_members,
                "member_count": len(team_members),
                "message": f"Retrieved {len(team_members)} team members"
            }
        
        elif name == "add_team_member":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            role = arguments.get("role")
            team_member = await project_repo.add_team_member(project_id, user_id, role)
            return {
                "team_member": team_member,
                "success": True,
                "message": f"User added to team with role: {team_member.get('role', 'Member')}"
            }
        
        elif name == "remove_team_member":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            result = await project_repo.remove_team_member(project_id, user_id)
            return {
                "success": result.get("success", False),
                "message": result.get("message", "Team member removed successfully")
            }
        
        elif name == "update_team_member_role":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            role = arguments["role"]
            team_member = await project_repo.update_team_member_role(project_id, user_id, role)
            return {
                "team_member": team_member,
                "success": True,
                "message": f"Team member role updated to: {role}"
            }
        
        elif name == "get_user_roles":
            roles = await project_repo.get_user_roles()
            return {
                "roles": roles,
                "role_count": len(roles),
                "message": f"Retrieved {len(roles)} user roles"
            }
        
        elif name == "transfer_project_ownership":
            project_id = arguments["project_id"]
            new_owner_id = arguments["new_owner_id"]
            project = await project_repo.transfer_project_ownership(project_id, new_owner_id)
            return {
                "project": project,
                "success": True,
                "message": f"Project ownership transferred to user {new_owner_id}"
            }
        
        # Search and activity tools
        elif name == "search_artworks":
            query = arguments.get("query")
            project_id = arguments.get("project_id")
            status = arguments.get("status")
            limit = arguments.get("limit", 50)
            page = arguments.get("page", 0)
            result = await project_repo.search_artworks(query, project_id, status, limit, page)
            return {
                "artworks": result.get("artworks", []),
                "total_hits": result.get("totalHits", 0),
                "page": result.get("page", 0),
                "message": f"Found {result.get('totalHits', 0)} artworks matching criteria"
            }
        
        elif name == "get_project_timeline":
            project_id = arguments["project_id"]
            limit = arguments.get("limit", 100)
            timeline = await project_repo.get_project_timeline(project_id, limit)
            return {
                "timeline": timeline,
                "event_count": len(timeline),
                "message": f"Retrieved {len(timeline)} timeline events"
            }
        
        elif name == "get_user_activity":
            user_id = arguments["user_id"]
            days = arguments.get("days", 30)
            limit = arguments.get("limit", 100)
            activities = await project_repo.get_user_activity(user_id, days, limit)
            return {
                "activities": activities,
                "activity_count": len(activities),
                "message": f"Retrieved {len(activities)} user activities from last {days} days"
            }
        
        elif name == "bulk_update_artwork_status":
            artwork_ids = arguments["artwork_ids"]
            status = arguments["status"]
            result = await project_repo.bulk_update_artwork_status(artwork_ids, status)
            return {
                "updated_artworks": result.get("updatedArtworks", []),
                "success_count": result.get("successCount", 0),
                "failed_count": result.get("failedCount", 0),
                "success": True,
                "message": f"Updated {result.get('successCount', 0)} artworks to status: {status}"
            }
        
        # Folder tools
        elif name == "get_folder_tree":
            folders = await project_repo.get_folder_tree()
            return {"folders": folders}
        
        elif name == "get_folder":
            folder_id = arguments["folder_id"]
            folder = await project_repo.get_folder(folder_id)
            if folder:
                return {"folder": folder}
            return {"folder": None, "message": "Folder not found"}
        
        elif name == "get_folder_items":
            folder_id = arguments["folder_id"]
            page = arguments.get("page", 0)
            size = arguments.get("size", 20)
            result = await project_repo.get_folder_items(folder_id, page, size)
            return {
                "items": result.get("items", []),
                "total_hits": result.get("totalHits", 0),
                "page": result.get("page", 0)
            }
        
        # Project status tools
        elif name == "get_project_status_summary":
            summary = await project_repo.get_project_status_summary()
            return {
                "summary": summary,
                "message": f"Analyzed {summary['total']} projects"
            }
        
        elif name == "compare_projects":
            project_ids = arguments["project_ids"]
            comparison = await project_repo.compare_projects(project_ids)
            return {
                "comparison": comparison,
                "project_count": len(comparison['projects']),
                "message": f"Compared {len(comparison['projects'])} projects"
            }
        
        elif name == "get_project_history":
            project_id = arguments["project_id"]
            history = await project_repo.get_project_history(project_id)
            return {
                "history": history,
                "event_count": len(history),
                "message": f"Retrieved {len(history)} events"
            }
        
        elif name == "get_monthly_project_trends":
            trends = await project_repo.get_monthly_project_trends()
            return {
                "trends": trends,
                "month_count": len(trends),
                "message": f"Retrieved {len(trends)} months of project data"
            }
        
        # Media center tools
        elif name == "search_media_center":
            query = arguments.get("query")
            folder_id = arguments.get("folder_id")
            limit = arguments.get("limit", 50)
            result = await project_repo.search_media_center(query, folder_id, limit=limit)
            return {
                "results": result,
                "message": f"Found {result['total_hits']} items matching search"
            }
        
        elif name == "get_media_center_stats":
            stats = await project_repo.get_media_center_stats()
            return {
                "stats": stats,
                "message": "Media center statistics retrieved"
            }
        
        elif name == "download_folder_contents":
            folder_id = arguments["folder_id"]
            zip_name = arguments.get("zip_name")
            job_id = await project_repo.download_folder_contents(folder_id, zip_name)
            return {
                "job_id": job_id,
                "success": True,
                "message": f"Download job created for folder. Job ID: {job_id}"
            }
        
        elif name == "download_project_media":
            project_id = arguments["project_id"]
            zip_name = arguments.get("zip_name")
            job_id = await project_repo.download_project_media(project_id, zip_name)
            return {
                "job_id": job_id,
                "success": True,
                "message": f"Download job created for project media. Job ID: {job_id}"
            }
        
        # File tools
        elif name == "get_file":
            file_id = arguments["file_id"]
            file = await project_repo.get_file(file_id)
            if file:
                return {"file": file}
            return {"file": None, "message": "File not found"}
        
        # Project collaboration tools
        elif name == "get_project_members":
            project_id = arguments["project_id"]
            members = await project_repo.get_project_members(project_id)
            return {
                "members": members,
                "member_count": len(members),
                "message": f"Retrieved {len(members)} team members"
            }
        
        elif name == "add_project_member":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            role = arguments.get("role", "MEMBER")
            result = await project_repo.add_project_member(project_id, user_id, role)
            return {
                "member": result,
                "success": True,
                "message": f"User added to project with role: {role}"
            }
        
        elif name == "remove_project_member":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            success = await project_repo.remove_project_member(project_id, user_id)
            return {
                "success": success,
                "message": "User removed from project" if success else "Failed to remove user"
            }
        
        elif name == "update_project_member_role":
            project_id = arguments["project_id"]
            user_id = arguments["user_id"]
            role = arguments["role"]
            result = await project_repo.update_project_member_role(project_id, user_id, role)
            return {
                "member": result,
                "success": True,
                "message": f"User role updated to: {role}"
            }
        
        elif name == "get_project_comments":
            project_id = arguments["project_id"]
            limit = arguments.get("limit", 50)
            comments = await project_repo.get_project_comments(project_id, limit)
            return {
                "comments": comments,
                "comment_count": len(comments),
                "message": f"Retrieved {len(comments)} comments"
            }
        
        elif name == "add_project_comment":
            project_id = arguments["project_id"]
            text = arguments["text"]
            comment = await project_repo.add_project_comment(project_id, text)
            return {
                "comment": comment,
                "success": True,
                "message": "Comment added to project"
            }
        
        elif name == "get_project_attachments":
            project_id = arguments["project_id"]
            attachments = await project_repo.get_project_attachments(project_id)
            return {
                "attachments": attachments,
                "attachment_count": len(attachments),
                "message": f"Retrieved {len(attachments)} attachments"
            }
        
        elif name == "upload_project_attachment":
            project_id = arguments["project_id"]
            file_id = arguments["file_id"]
            name = arguments["name"]
            attachment = await project_repo.upload_project_attachment(project_id, file_id, name)
            return {
                "attachment": attachment,
                "success": True,
                "message": f"File '{name}' attached to project"
            }
        
        # Category, brand, and specification tools
        elif name == "get_categories":
            categories = await category_repo.get_categories()
            return {
                "categories": categories,
                "count": len(categories),
                "message": f"Retrieved {len(categories)} categories"
            }
        
        elif name == "get_brands":
            brands = await category_repo.get_brands()
            return {
                "brands": brands,
                "count": len(brands),
                "message": f"Retrieved {len(brands)} brands"
            }
        
        elif name == "get_print_specifications":
            specs = await category_repo.get_print_specifications()
            return {
                "specifications": specs,
                "count": len(specs),
                "message": f"Retrieved {len(specs)} print specifications"
            }
        
        elif name == "create_category":
            name_arg = arguments["name"]
            description = arguments.get("description")
            color = arguments.get("color")
            category = await category_repo.create_category(name_arg, description, color)
            return {
                "category": category,
                "success": True,
                "message": f"Category '{name_arg}' created successfully"
            }
        
        elif name == "create_brand":
            name_arg = arguments["name"]
            description = arguments.get("description")
            brand = await category_repo.create_brand(name_arg, description)
            return {
                "brand": brand,
                "success": True,
                "message": f"Brand '{name_arg}' created successfully"
            }
        
        elif name == "create_print_specification":
            name_arg = arguments["name"]
            width = arguments["width"]
            height = arguments["height"]
            unit = arguments.get("unit", "mm")
            description = arguments.get("description")
            spec = await category_repo.create_print_specification(name_arg, width, height, unit, description)
            return {
                "specification": spec,
                "success": True,
                "message": f"Print specification '{name_arg}' created successfully"
            }
        
        # Share tools
        elif name == "find_shares":
            limit = arguments.get("limit", 50)
            shares = await project_repo.find_shares(limit)
            return {
                "shares": shares,
                "count": len(shares),
                "message": f"Retrieved {len(shares)} shares"
            }
        
        elif name == "get_share":
            share_id = arguments["share_id"]
            share = await project_repo.get_share(share_id)
            if share:
                return {
                    "share": share,
                    "message": "Share retrieved successfully"
                }
            return {"share": None, "message": "Share not found"}
        
        elif name == "create_share":
            name_arg = arguments["name"]
            file_ids = arguments["file_ids"]
            description = arguments.get("description")
            expires_at = arguments.get("expires_at")
            max_downloads = arguments.get("max_downloads")
            password = arguments.get("password")
            share = await project_repo.create_share(
                name_arg, file_ids, description, expires_at, max_downloads, password
            )
            return {
                "share": share,
                "success": True,
                "message": f"Share '{name_arg}' created with {len(file_ids)} files"
            }
        
        elif name == "delete_share":
            share_id = arguments["share_id"]
            success = await project_repo.delete_share(share_id)
            return {
                "success": success,
                "message": "Share deleted successfully" if success else "Failed to delete share"
            }
        
        # Media management tools
        elif name == "create_folder":
            name_arg = arguments["name"]
            parent_folder_id = arguments.get("parent_folder_id")
            description = arguments.get("description")
            folder = await project_repo.create_folder(name_arg, parent_folder_id, description)
            return {
                "folder": folder,
                "success": True,
                "message": f"Folder '{name_arg}' created successfully"
            }
        
        elif name == "rename_file":
            file_id = arguments["file_id"]
            new_name = arguments["new_name"]
            file = await project_repo.rename_file(file_id, new_name)
            return {
                "file": file,
                "success": True,
                "message": f"File renamed to '{new_name}'"
            }
        
        elif name == "rename_folder":
            folder_id = arguments["folder_id"]
            new_name = arguments["new_name"]
            folder = await project_repo.rename_folder(folder_id, new_name)
            return {
                "folder": folder,
                "success": True,
                "message": f"Folder renamed to '{new_name}'"
            }
        
        elif name == "move_files":
            file_ids = arguments["file_ids"]
            target_folder_id = arguments["target_folder_id"]
            result = await project_repo.move_files(file_ids, target_folder_id)
            return {
                "success": result.get("success", False),
                "moved_count": result.get("movedCount", 0),
                "message": f"Moved {result.get('movedCount', 0)} files" if result.get("success") else "Failed to move files"
            }
        
        elif name == "delete_file":
            file_id = arguments["file_id"]
            success = await project_repo.delete_file(file_id)
            return {
                "success": success,
                "message": "File deleted successfully" if success else "Failed to delete file"
            }
        
        elif name == "delete_folder":
            folder_id = arguments["folder_id"]
            force = arguments.get("force", False)
            success = await project_repo.delete_folder(folder_id, force)
            return {
                "success": success,
                "message": "Folder deleted successfully" if success else "Failed to delete folder"
            }
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    async def run_stdio(self) -> None:
        """Run the MCP server with stdio transport."""
        from mcp.server.stdio import stdio_server
        
        logger.info("Starting Cway MCP Server (stdio)...")
        
        try:
            await self._ensure_initialized()
            logger.info(f"Server initialized and ready")
            logger.info(f"Connected to Cway API at {settings.cway_api_url}")
            
            # Run the MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self._cleanup()
            
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self.graphql_client:
            await self.graphql_client.disconnect()
            logger.info("GraphQL client disconnected")


def main() -> None:
    """Main entry point for stdio mode."""
    server = CwayMCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
