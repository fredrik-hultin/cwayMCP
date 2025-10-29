"""Data extractor for indexing pipeline using MCP server data."""

import asyncio
import json
import hashlib
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Iterator, AsyncIterator
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from ..infrastructure.graphql_client import CwayGraphQLClient
from ..infrastructure.cway_repositories import (
    CwayUserRepository, 
    CwayProjectRepository, 
    CwaySystemRepository
)
from ..application.kpi_use_cases import KPIUseCases
from ..infrastructure.repository_adapters import CwayProjectRepositoryAdapter, CwayUserRepositoryAdapter
from ..application.temporal_kpi_use_cases import TemporalKPICalculator

logger = logging.getLogger(__name__)


@dataclass
class IndexableDocument:
    """Represents a document ready for indexing."""
    
    id: str
    document_type: str  # 'project', 'user', 'kpi', 'temporal_kpi'
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    url: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    
    def __post_init__(self):
        """Generate content hash for deduplication."""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        self.metadata['content_hash'] = content_hash
        self.metadata['extraction_timestamp'] = datetime.now().isoformat()


class CwayDataExtractor:
    """Extracts and prepares data from Cway MCP Server for indexing."""
    
    def __init__(self):
        self.client: Optional[CwayGraphQLClient] = None
        self.user_repo: Optional[CwayUserRepository] = None
        self.project_repo: Optional[CwayProjectRepository] = None
        self.system_repo: Optional[CwaySystemRepository] = None
        self.kpi_use_cases: Optional[KPIUseCases] = None
        self.temporal_calculator: Optional[TemporalKPICalculator] = None
    
    async def initialize(self):
        """Initialize the data extractor."""
        self.client = CwayGraphQLClient()
        await self.client.connect()
        
        # Initialize repositories
        self.user_repo = CwayUserRepository(self.client)
        self.project_repo = CwayProjectRepository(self.client)
        self.system_repo = CwaySystemRepository(self.client)
        
        # Initialize use cases
        self.kpi_use_cases = KPIUseCases(self.user_repo, self.project_repo, self.client)
        
        # Initialize temporal KPI calculator
        project_adapter = CwayProjectRepositoryAdapter(self.project_repo)
        user_adapter = CwayUserRepositoryAdapter(self.user_repo)
        self.temporal_calculator = TemporalKPICalculator(project_adapter, user_adapter)
        
        logger.info("Data extractor initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.disconnect()
    
    async def extract_all_data(self) -> AsyncIterator[IndexableDocument]:
        """Extract all data types for indexing."""
        
        logger.info("Starting comprehensive data extraction for indexing")
        
        # Extract projects
        async for doc in self.extract_projects():
            yield doc
        
        # Extract users
        async for doc in self.extract_users():
            yield doc
        
        # Extract KPI data
        async for doc in self.extract_kpi_data():
            yield doc
        
        # Extract temporal KPI data
        async for doc in self.extract_temporal_kpi_data():
            yield doc
        
        logger.info("Data extraction completed")
    
    async def extract_projects(self) -> AsyncIterator[IndexableDocument]:
        """Extract project data for indexing."""
        
        logger.info("Extracting project data")
        
        try:
            projects = await self.project_repo.get_planner_projects()
            
            for project in projects:
                # Create detailed content for the project
                content_parts = [
                    f"Project: {project.name}",
                    f"Status: {project.state.value if project.state else 'Unknown'}",
                    f"Progress: {project.percentageDone:.1%}" if project.percentageDone else "Progress: 0%",
                ]
                
                # Add dates if available
                if project.startDate:
                    content_parts.append(f"Start Date: {project.startDate}")
                if project.endDate:
                    content_parts.append(f"End Date: {project.endDate}")
                
                # Add description or generate summary
                description = getattr(project, 'description', None) or f"Project in {project.state.value if project.state else 'unknown'} state"
                content_parts.append(f"Description: {description}")
                
                content = "\n".join(content_parts)
                
                # Create metadata
                metadata = {
                    'project_id': project.id,
                    'state': project.state.value if project.state else None,
                    'progress_percentage': project.percentageDone * 100 if project.percentageDone else 0,
                    'start_date': str(project.startDate) if project.startDate else None,
                    'end_date': str(project.endDate) if project.endDate else None,
                    'is_active': project.is_active,
                    'is_completed': project.is_completed,
                    'data_source': 'cway_api',
                    'extraction_method': 'mcp_server'
                }
                
                # Generate tags
                tags = ['project', project.state.value.lower() if project.state else 'unknown']
                if project.is_active:
                    tags.append('active')
                if project.is_completed:
                    tags.append('completed')
                
                # Create indexable document
                doc = IndexableDocument(
                    id=f"project_{project.id}",
                    document_type="project",
                    title=project.name,
                    content=content,
                    metadata=metadata,
                    created_at=datetime.now(),  # We don't have exact creation time
                    updated_at=datetime.now(),
                    tags=tags,
                    url=f"cway://projects/{project.id}"
                )
                
                yield doc
                
        except Exception as e:
            logger.error(f"Error extracting projects: {e}")
    
    async def extract_users(self) -> AsyncIterator[IndexableDocument]:
        """Extract user data for indexing."""
        
        logger.info("Extracting user data")
        
        try:
            users = await self.user_repo.find_all_users()
            
            for user in users:
                # Create content for the user
                content_parts = [
                    f"User: {user.full_name or user.name}",
                    f"Email: {user.email}",
                    f"Username: {user.username}",
                    f"Status: {'Active' if user.enabled else 'Inactive'}",
                ]
                
                if user.firstName and user.lastName:
                    content_parts.append(f"Full Name: {user.firstName} {user.lastName}")
                
                content = "\n".join(content_parts)
                
                # Create metadata
                metadata = {
                    'user_id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.firstName,
                    'last_name': user.lastName,
                    'enabled': user.enabled,
                    'is_sso': user.isSSO,
                    'has_avatar': user.avatar,
                    'accepted_terms': user.acceptedTerms,
                    'data_source': 'cway_api',
                    'extraction_method': 'mcp_server'
                }
                
                # Generate tags
                tags = ['user']
                if user.enabled:
                    tags.append('active')
                if user.isSSO:
                    tags.append('sso')
                
                # Create indexable document
                doc = IndexableDocument(
                    id=f"user_{user.id}",
                    document_type="user",
                    title=user.full_name or user.email,
                    content=content,
                    metadata=metadata,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tags=tags,
                    url=f"cway://users/{user.id}"
                )
                
                yield doc
                
        except Exception as e:
            logger.error(f"Error extracting users: {e}")
    
    async def extract_kpi_data(self) -> AsyncIterator[IndexableDocument]:
        """Extract KPI data for indexing."""
        
        logger.info("Extracting KPI data")
        
        try:
            # Get system KPI dashboard
            dashboard = await self.kpi_use_cases.calculate_system_kpi_dashboard()
            
            # Create document for system KPIs
            content_parts = [
                f"System KPI Dashboard - Generated: {dashboard.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Projects: {dashboard.total_projects}",
                f"Total Users: {dashboard.total_users}",
                f"Total Revisions: {dashboard.total_revisions:,}",
                "",
                "Core KPIs:",
                f"• Project Completion Rate: {dashboard.project_completion_rate.value:.1f}% ({dashboard.project_completion_rate.status.value})",
                f"• Stalled Project Rate: {dashboard.stalled_project_rate.value:.1f}% ({dashboard.stalled_project_rate.status.value})",
                f"• System Utilization: {dashboard.system_utilization.value:.1f}% ({dashboard.system_utilization.status.value})",
                f"• Revision Efficiency: {dashboard.revision_efficiency.value:.1f} ({dashboard.revision_efficiency.status.value})",
                f"• Team Engagement: {dashboard.team_engagement.value:.1f}% ({dashboard.team_engagement.status.value})",
            ]
            
            # Add project health summary
            health_summary = dashboard.health_summary
            content_parts.extend([
                "",
                "Project Health Distribution:",
                f"• Critical: {health_summary.get('critical', 0)} projects",
                f"• Warning: {health_summary.get('warning', 0)} projects", 
                f"• Healthy: {health_summary.get('healthy', 0)} projects",
                f"• Excellent: {health_summary.get('excellent', 0)} projects",
            ])
            
            # Add recommendations
            if dashboard.recommendations:
                content_parts.extend([
                    "",
                    "Key Recommendations:"
                ] + [f"• {rec}" for rec in dashboard.recommendations[:5]])
            
            content = "\n".join(content_parts)
            
            # Create metadata
            metadata = {
                'generation_timestamp': dashboard.generated_at.isoformat(),
                'total_projects': dashboard.total_projects,
                'total_users': dashboard.total_users,
                'total_revisions': dashboard.total_revisions,
                'kpi_scores': {
                    'completion_rate': dashboard.project_completion_rate.value,
                    'stalled_rate': dashboard.stalled_project_rate.value,
                    'utilization': dashboard.system_utilization.value,
                    'revision_efficiency': dashboard.revision_efficiency.value,
                    'team_engagement': dashboard.team_engagement.value,
                },
                'health_distribution': health_summary,
                'data_source': 'kpi_calculation',
                'extraction_method': 'mcp_server'
            }
            
            # Generate tags
            tags = ['kpi', 'dashboard', 'system_metrics']
            
            # Add status-based tags
            for kpi_name, kpi in [
                ('completion', dashboard.project_completion_rate),
                ('stagnation', dashboard.stalled_project_rate),
                ('utilization', dashboard.system_utilization),
                ('efficiency', dashboard.revision_efficiency),
                ('engagement', dashboard.team_engagement)
            ]:
                tags.append(f"{kpi_name}_{kpi.status.value}")
            
            doc = IndexableDocument(
                id="system_kpi_dashboard",
                document_type="kpi",
                title="System KPI Dashboard",
                content=content,
                metadata=metadata,
                created_at=dashboard.generated_at,
                updated_at=dashboard.generated_at,
                tags=tags,
                url="cway://kpis/dashboard"
            )
            
            yield doc
            
            # Get project health scores
            health_scores = await self.kpi_use_cases.get_project_health_scores()
            
            for score in health_scores:
                content_parts = [
                    f"Project Health Analysis: {score.project_name}",
                    f"Overall Health Score: {score.overall_score:.1f}/100 ({score.health_status.value})",
                    f"Progress: {score.progress_percentage:.1f}%",
                    f"Total Revisions: {score.total_revisions}",
                    "",
                    "Component Scores:",
                    f"• Progress Score: {score.progress_score:.1f}/100",
                    f"• Revision Efficiency: {score.revision_efficiency_score:.1f}/100",
                    f"• State Score: {score.state_score:.1f}/100",
                    f"• Activity Score: {score.activity_score:.1f}/100",
                ]
                
                if score.recommendations:
                    content_parts.extend([
                        "",
                        "Recommendations:"
                    ] + [f"• {rec}" for rec in score.recommendations])
                
                content = "\n".join(content_parts)
                
                # Create metadata
                metadata = {
                    'project_id': score.project_id,
                    'overall_score': score.overall_score,
                    'health_status': score.health_status.value,
                    'progress_percentage': score.progress_percentage,
                    'total_revisions': score.total_revisions,
                    'component_scores': {
                        'progress': score.progress_score,
                        'efficiency': score.revision_efficiency_score,
                        'state': score.state_score,
                        'activity': score.activity_score
                    },
                    'data_source': 'kpi_calculation',
                    'extraction_method': 'mcp_server'
                }
                
                # Generate tags
                tags = ['kpi', 'project_health', score.health_status.value]
                
                doc = IndexableDocument(
                    id=f"project_health_{score.project_id}",
                    document_type="kpi",
                    title=f"Health Analysis: {score.project_name}",
                    content=content,
                    metadata=metadata,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tags=tags,
                    url=f"cway://kpis/project-health/{score.project_id}"
                )
                
                yield doc
                
        except Exception as e:
            logger.error(f"Error extracting KPI data: {e}")
    
    async def extract_temporal_kpi_data(self) -> AsyncIterator[IndexableDocument]:
        """Extract temporal KPI data for indexing."""
        
        logger.info("Extracting temporal KPI data")
        
        try:
            # Get temporal KPI dashboard
            dashboard = await self.temporal_calculator.generate_temporal_kpi_dashboard()
            
            # Create document for temporal KPIs
            content_parts = [
                f"Temporal KPI Dashboard - Generated: {dashboard.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Analysis Period: {dashboard.analysis_period_days} days",
                f"Projects Analyzed: {dashboard.total_projects_analyzed}",
                f"Total Revisions in Period: {dashboard.total_revisions_in_period:,}",
                f"Average Project Velocity: {dashboard.avg_project_velocity:.1f} revisions/week",
                "",
                "Activity Level Distribution:",
            ]
            
            # Add activity levels
            for level, count in dashboard.projects_by_activity_level.items():
                percentage = (count / dashboard.total_projects_analyzed * 100) if dashboard.total_projects_analyzed else 0
                content_parts.append(f"• {level.value.title()}: {count} projects ({percentage:.1f}%)")
            
            content_parts.extend([
                "",
                "Stagnation Risk Distribution:",
            ])
            
            # Add stagnation risks
            for risk, count in dashboard.projects_by_stagnation_risk.items():
                percentage = (count / dashboard.total_projects_analyzed * 100) if dashboard.total_projects_analyzed else 0
                content_parts.append(f"• {risk.value.title()}: {count} projects ({percentage:.1f}%)")
            
            # Add team temporal patterns
            team_metrics = dashboard.team_temporal_metrics
            content_parts.extend([
                "",
                "Team Temporal Patterns:",
                f"• Peak Activity Day: {team_metrics.peak_activity_day_of_week}",
                f"• Peak Activity Hour: {team_metrics.peak_activity_hour}:00",
                f"• Team Velocity: {team_metrics.team_velocity_revisions_per_day:.2f} rev/day",
                f"• Concurrent Projects: {team_metrics.concurrent_project_activity}",
            ])
            
            # Add trends
            content_parts.extend([
                "",
                "Trends:",
                f"• Overall Velocity Trend: {dashboard.overall_velocity_trend}",
                f"• Productivity Trend: {dashboard.productivity_trend}",
            ])
            
            # Add recommendations
            if dashboard.temporal_recommendations:
                content_parts.extend([
                    "",
                    "Temporal Recommendations:"
                ] + [f"• {rec}" for rec in dashboard.temporal_recommendations])
            
            content = "\n".join(content_parts)
            
            # Create metadata
            metadata = {
                'generation_timestamp': dashboard.generated_at.isoformat(),
                'analysis_period_days': dashboard.analysis_period_days,
                'total_projects_analyzed': dashboard.total_projects_analyzed,
                'total_revisions': dashboard.total_revisions_in_period,
                'avg_velocity': dashboard.avg_project_velocity,
                'activity_distribution': {level.value: count for level, count in dashboard.projects_by_activity_level.items()},
                'stagnation_distribution': {risk.value: count for risk, count in dashboard.projects_by_stagnation_risk.items()},
                'team_patterns': {
                    'peak_day': team_metrics.peak_activity_day_of_week,
                    'peak_hour': team_metrics.peak_activity_hour,
                    'team_velocity': team_metrics.team_velocity_revisions_per_day,
                    'concurrent_projects': team_metrics.concurrent_project_activity
                },
                'trends': {
                    'velocity': dashboard.overall_velocity_trend,
                    'productivity': dashboard.productivity_trend
                },
                'data_source': 'temporal_kpi_calculation',
                'extraction_method': 'mcp_server'
            }
            
            # Generate tags
            tags = ['temporal_kpi', 'dashboard', 'velocity', 'activity', 'trends']
            
            doc = IndexableDocument(
                id="temporal_kpi_dashboard",
                document_type="temporal_kpi",
                title="Temporal KPI Dashboard",
                content=content,
                metadata=metadata,
                created_at=dashboard.generated_at,
                updated_at=dashboard.generated_at,
                tags=tags,
                url="cway://temporal-kpis/dashboard"
            )
            
            yield doc
            
            # Create documents for stagnation alerts
            if dashboard.stagnation_alerts:
                for alert in dashboard.stagnation_alerts:
                    content_parts = [
                        f"Stagnation Alert: {alert.project_name}",
                        f"Risk Level: {alert.risk_level.value.upper()}",
                        f"Urgency Score: {alert.urgency_score}/10",
                        f"Days Since Activity: {alert.days_since_activity}",
                        f"Last Activity: {alert.last_activity_date.strftime('%Y-%m-%d %H:%M:%S') if alert.last_activity_date else 'Unknown'}",
                        f"Previous Activity Level: {alert.previous_activity_level.value}",
                        f"Expected Activity Level: {alert.expected_activity_level.value}",
                    ]
                    
                    if alert.recommended_actions:
                        content_parts.extend([
                            "",
                            "Recommended Actions:"
                        ] + [f"• {action}" for action in alert.recommended_actions])
                    
                    content = "\n".join(content_parts)
                    
                    # Create metadata
                    metadata = {
                        'project_id': alert.project_id,
                        'risk_level': alert.risk_level.value,
                        'urgency_score': alert.urgency_score,
                        'days_since_activity': alert.days_since_activity,
                        'last_activity_date': alert.last_activity_date.isoformat() if alert.last_activity_date else None,
                        'previous_activity_level': alert.previous_activity_level.value,
                        'expected_activity_level': alert.expected_activity_level.value,
                        'data_source': 'stagnation_analysis',
                        'extraction_method': 'mcp_server'
                    }
                    
                    # Generate tags
                    tags = ['stagnation_alert', alert.risk_level.value, f'urgency_{alert.urgency_score}']
                    
                    doc = IndexableDocument(
                        id=f"stagnation_alert_{alert.project_id}",
                        document_type="temporal_kpi",
                        title=f"Stagnation Alert: {alert.project_name}",
                        content=content,
                        metadata=metadata,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        tags=tags,
                        url=f"cway://temporal-kpis/stagnation-alerts/{alert.project_id}"
                    )
                    
                    yield doc
                    
        except Exception as e:
            logger.error(f"Error extracting temporal KPI data: {e}")
    
    def serialize_document(self, doc: IndexableDocument) -> str:
        """Serialize a document to JSON for indexing."""
        
        # Convert to dictionary
        doc_dict = asdict(doc)
        
        # Handle datetime serialization
        for key, value in doc_dict.items():
            if isinstance(value, datetime):
                doc_dict[key] = value.isoformat()
            elif isinstance(value, date):
                doc_dict[key] = value.isoformat()
        
        return json.dumps(doc_dict, ensure_ascii=False, indent=2)
    
    async def export_to_jsonl(self, output_path: Path) -> int:
        """Export all data to JSONL format for bulk indexing."""
        
        logger.info(f"Exporting data to {output_path}")
        
        document_count = 0
        
        with open(output_path, 'w', encoding='utf-8') as f:
            async for doc in self.extract_all_data():
                # Write as single-line JSON
                doc_dict = asdict(doc)
                
                # Handle datetime serialization
                for key, value in doc_dict.items():
                    if isinstance(value, datetime):
                        doc_dict[key] = value.isoformat()
                    elif isinstance(value, date):
                        doc_dict[key] = value.isoformat()
                
                f.write(json.dumps(doc_dict, ensure_ascii=False) + '\n')
                document_count += 1
        
        logger.info(f"Exported {document_count} documents to {output_path}")
        return document_count


async def main():
    """Main function to demonstrate data extraction."""
    
    extractor = CwayDataExtractor()
    
    try:
        await extractor.initialize()
        
        # Export all data
        output_path = Path("cway_indexed_data.jsonl")
        count = await extractor.export_to_jsonl(output_path)
        
        print(f"✅ Successfully extracted and exported {count} documents")
        print(f"📁 Data saved to: {output_path}")
        
        # Show sample document
        print("\n📄 Sample document:")
        async for doc in extractor.extract_projects():
            print(extractor.serialize_document(doc))
            break
            
    finally:
        await extractor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())