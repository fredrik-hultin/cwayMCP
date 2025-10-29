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
from ..infrastructure.cway_repositories import (
    CwayUserRepository, 
    CwayProjectRepository, 
    CwaySystemRepository
)
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


# Set up logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


class CwayMCPServer:
    """MCP server for real Cway API integration."""
    
    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.server = Server("cway-mcp-server")
        self.graphql_client: Optional[CwayGraphQLClient] = None
        self.user_repo: Optional[CwayUserRepository] = None
        self.project_repo: Optional[CwayProjectRepository] = None
        self.system_repo: Optional[CwaySystemRepository] = None
        self.kpi_use_cases: Optional[KPIUseCases] = None
        self.temporal_kpi_calculator: Optional[TemporalKPICalculator] = None
        self.indexing_service = get_indexing_service()
        
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
            tools = [
                Tool(
                    name="list_projects",
                    description="List all Cway planner projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_project",
                    description="Get a specific Cway project by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The UUID of the project to retrieve"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="get_active_projects",
                    description="Get all active (in progress) projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_completed_projects", 
                    description="Get all completed projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="list_users",
                    description="List all Cway users",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_user",
                    description="Get a specific Cway user by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The UUID of the user to retrieve"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="find_user_by_email",
                    description="Find a Cway user by email address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "The email address of the user to find"
                            }
                        },
                        "required": ["email"]
                    }
                ),
                Tool(
                    name="get_users_page",
                    description="Get users with pagination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page": {
                                "type": "integer",
                                "description": "Page number (0-based)",
                                "default": 0
                            },
                            "size": {
                                "type": "integer",
                                "description": "Page size",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_system_status",
                    description="Get Cway system connection status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="analyze_project_velocity",
                    description="Analyze velocity trends and patterns for a specific project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The UUID of the project to analyze"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="get_temporal_dashboard",
                    description="Get comprehensive temporal KPI dashboard with velocity and stagnation analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_period_days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 90)",
                                "default": 90
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_stagnation_alerts",
                    description="Get projects at risk of stagnation with urgency scores and recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_urgency_score": {
                                "type": "integer",
                                "description": "Minimum urgency score (1-10, default: 5)",
                                "default": 5
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="index_all_content",
                    description="Index all documents and site pages to configured targets",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "targets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific target names to index to (default: all enabled)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="quick_backup",
                    description="Quick backup of all content to local files",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="index_project_content",
                    description="Index documents and pages for a specific project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The UUID of the project to index"
                            },
                            "targets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific target names to index to (optional)"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="configure_indexing_target",
                    description="Add or update an indexing target configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the indexing target"
                            },
                            "platform": {
                                "type": "string",
                                "description": "Platform type (elasticsearch, file, algolia, etc.)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of what this target is for"
                            },
                            "config": {
                                "type": "object",
                                "description": "Platform-specific configuration"
                            },
                            "enabled": {
                                "type": "boolean",
                                "description": "Whether this target is enabled",
                                "default": True
                            }
                        },
                        "required": ["name", "platform", "description"]
                    }
                ),
                Tool(
                    name="get_indexing_job_status",
                    description="Get status of a specific indexing job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {
                                "type": "string",
                                "description": "The ID of the indexing job to check"
                            }
                        },
                        "required": ["job_id"]
                    }
                )
            ]
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
                
    async def _ensure_initialized(self) -> None:
        """Ensure the server is initialized with all dependencies."""
        if not self.graphql_client:
            self.graphql_client = CwayGraphQLClient()
            await self.graphql_client.connect()
            
            # Initialize repositories
            self.user_repo = CwayUserRepository(self.graphql_client)
            self.project_repo = CwayProjectRepository(self.graphql_client)
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
        """Execute a specific tool."""
        if name == "list_projects":
            projects = await self.project_repo.get_planner_projects()
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
            project = await self.project_repo.find_project_by_id(arguments["project_id"])
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
            projects = await self.project_repo.get_active_projects()
            return {
                "active_projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_completed_projects":
            projects = await self.project_repo.get_completed_projects()
            return {
                "completed_projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "list_users":
            users = await self.user_repo.find_all_users()
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
            user = await self.user_repo.find_user_by_id(arguments["user_id"])
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
            user = await self.user_repo.find_user_by_email(arguments["email"])
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
            page_data = await self.user_repo.find_users_page(
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
            is_connected = await self.system_repo.validate_connection()
            login_info = await self.system_repo.get_login_info()
            
            return {
                "system_status": {
                    "connected": is_connected,
                    "api_url": settings.cway_api_url,
                    "login_info": login_info
                }
            }
            
        elif name == "analyze_project_velocity":
            project_id = arguments["project_id"]
            project = await self.project_repo.find_project_by_id(project_id)
            if not project:
                return {"error": "Project not found"}
                
            # Convert to domain project for analysis
            from ..infrastructure.repository_adapters import CwayProjectRepositoryAdapter
            adapter = CwayProjectRepositoryAdapter(self.project_repo)
            domain_project = await adapter.get_project_by_id(project_id)
            
            if domain_project:
                velocity_analysis = await self.temporal_kpi_calculator.analyze_project_velocity(domain_project)
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
            dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard(analysis_period)
            
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
            dashboard = await self.temporal_kpi_calculator.generate_temporal_kpi_dashboard()
            
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
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        from mcp.server.stdio import stdio_server
        
        logger.info("Starting Cway MCP Server...")
        
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
            
    async def cleanup(self) -> None:
        """Public cleanup method."""
        await self._cleanup()
            
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self.graphql_client:
            await self.graphql_client.disconnect()
            logger.info("GraphQL client disconnected")


def main() -> None:
    """Main entry point."""
    server = CwayMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
