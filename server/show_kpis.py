#!/usr/bin/env python3
"""
Show real KPI data from the Cway MCP Server.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.graphql_client import CwayGraphQLClient
from infrastructure.cway_repositories import CwayUserRepository, CwayProjectRepository, CwaySystemRepository
from application.kpi_use_cases import KPIUseCases


async def show_real_kpis():
    """Fetch and display real KPI data from Cway."""
    
    print('🎨 CWAY MCP SERVER - REAL KPI DATA')
    print('=' * 60)
    
    # Initialize GraphQL client
    graphql_client = CwayGraphQLClient()
    
    try:
        # Connect to Cway API
        print('🔗 Connecting to Cway API...')
        await graphql_client.connect()
        print('✅ Connected to Cway API successfully')
        print()
        
        # Initialize repositories
        user_repo = CwayUserRepository(graphql_client)
        project_repo = CwayProjectRepository(graphql_client)
        system_repo = CwaySystemRepository(graphql_client)
        
        # Initialize KPI use cases
        kpi_use_cases = KPIUseCases(user_repo, project_repo, graphql_client)
        
        # Get system status first
        print('🌐 SYSTEM STATUS')
        print('-' * 40)
        try:
            is_connected = await system_repo.validate_connection()
            print(f'Connection Status: {"✅ Connected" if is_connected else "❌ Disconnected"}')
            
            login_info = await system_repo.get_login_info()
            if login_info:
                print(f'API User: {login_info.get("username", "Unknown")}')
                print(f'Organization: {login_info.get("organization", "Unknown")}')
            print()
        except Exception as e:
            print(f'❌ Error checking system status: {e}')
            print()
        
        # Get basic project and user counts
        print('📊 BASIC METRICS')
        print('-' * 40)
        try:
            projects = await project_repo.get_planner_projects()
            users = await user_repo.find_all_users()
            
            print(f'📁 Total Projects: {len(projects)}')
            print(f'👥 Total Users: {len(users)}')
            print()
            
            # Show project distribution by state
            state_counts = {}
            for project in projects:
                state = project.state.value if project.state else 'UNKNOWN'
                state_counts[state] = state_counts.get(state, 0) + 1
            
            print('📋 PROJECT STATE DISTRIBUTION:')
            for state, count in state_counts.items():
                print(f'  📊 {state}: {count} projects')
            print()
            
            # Show active vs total projects
            active_projects = await project_repo.get_active_projects()
            completed_projects = await project_repo.get_completed_projects()
            
            print('🎯 PROJECT STATUS BREAKDOWN:')
            print(f'  🟢 Active Projects: {len(active_projects)}')
            print(f'  ✅ Completed Projects: {len(completed_projects)}')
            print(f'  📈 Completion Rate: {(len(completed_projects) / len(projects) * 100) if projects else 0:.1f}%')
            print()
            
            # Show some sample projects
            print('📁 SAMPLE ACTIVE PROJECTS:')
            for i, project in enumerate(active_projects[:5], 1):
                print(f'  {i}. {project.name}')
                print(f'     Progress: {project.percentageDone:.1%}')
                print(f'     State: {project.state.value if project.state else "Unknown"}')
                print(f'     Dates: {project.startDate} → {project.endDate or "Ongoing"}')
                print()
                
        except Exception as e:
            print(f'❌ Error getting basic metrics: {e}')
            import traceback
            print(f'Details: {traceback.format_exc()[:200]}...')
            print()
        
        # Try to get system KPI dashboard
        print('📊 SYSTEM KPI DASHBOARD')
        print('-' * 40)
        try:
            dashboard = await kpi_use_cases.calculate_system_kpi_dashboard()
            
            print(f'Generated: {dashboard.generated_at.strftime("%Y-%m-%d %H:%M:%S")}')
            print()
            
            # Key metrics
            print('📈 SUMMARY METRICS:')
            print(f'  📁 Total Projects: {dashboard.total_projects}')
            print(f'  👥 Total Users: {dashboard.total_users}')
            print(f'  🔄 Total Revisions: {dashboard.total_revisions:,}')
            print()
            
            # Core KPIs
            print('🎯 CORE KPIs:')
            kpis = [
                ('Project Completion Rate', dashboard.project_completion_rate),
                ('Stalled Project Rate', dashboard.stalled_project_rate),
                ('System Utilization', dashboard.system_utilization),
                ('Revision Efficiency', dashboard.revision_efficiency),
                ('Team Engagement', dashboard.team_engagement)
            ]
            
            for name, kpi in kpis:
                status_emoji = {
                    'critical': '🔴', 
                    'warning': '🟡', 
                    'healthy': '🟢', 
                    'excellent': '⭐'
                }.get(kpi.status.value, '⚪')
                
                print(f'  {status_emoji} {name}:')
                print(f'     📊 Value: {kpi.value:.1f}{kpi.unit}')
                print(f'     📈 Status: {kpi.status.value.title()}')
                print(f'     📝 Description: {kpi.description}')
                
                # Show thresholds if available
                if kpi.threshold_warning or kpi.threshold_critical:
                    thresholds = []
                    if kpi.threshold_critical:
                        thresholds.append(f'Critical: <{kpi.threshold_critical}')
                    if kpi.threshold_warning:
                        thresholds.append(f'Warning: <{kpi.threshold_warning}')
                    if thresholds:
                        print(f'     ⚠️ Thresholds: {", ".join(thresholds)}')
                print()
            
            # Project health summary
            if hasattr(dashboard, 'health_summary'):
                health_summary = dashboard.health_summary
                print('🏥 PROJECT HEALTH SUMMARY:')
                health_emojis = {'critical': '🔴', 'warning': '🟡', 'healthy': '🟢', 'excellent': '⭐'}
                for status, count in health_summary.items():
                    emoji = health_emojis.get(status, '⚪')
                    percentage = (count / dashboard.total_projects * 100) if dashboard.total_projects else 0
                    print(f'  {emoji} {status.title()}: {count} projects ({percentage:.1f}%)')
                print()
            
            # Team productivity metrics
            if hasattr(dashboard, 'team_productivity'):
                team = dashboard.team_productivity
                print('👥 TEAM PRODUCTIVITY ANALYSIS:')
                print(f'  📊 Total Users: {team.total_users}')
                print(f'  🟢 Active Users: {team.active_users}')
                print(f'  📈 User Engagement Rate: {team.user_engagement_rate:.1f}%')
                print(f'  📋 Total Projects: {team.total_projects}')
                print(f'  🔄 Active Projects: {team.active_projects}')
                print(f'  😴 Stalled Projects: {team.stalled_projects}')
                print(f'  ⚖️ Projects per User Ratio: {team.projects_per_user_ratio:.1f}')
                print(f'  ⚡ Utilization Rate: {team.utilization_rate:.1f}%')
                print()
            
            # Recommendations
            if hasattr(dashboard, 'recommendations') and dashboard.recommendations:
                print('💡 KEY RECOMMENDATIONS:')
                for i, rec in enumerate(dashboard.recommendations[:5], 1):
                    print(f'  {i}. {rec}')
                print()
            
        except Exception as e:
            print(f'❌ Error generating KPI dashboard: {e}')
            import traceback
            print(f'Details: {traceback.format_exc()[:300]}...')
            print()
        
        # Try to get project health scores
        print('🏥 PROJECT HEALTH ANALYSIS')
        print('-' * 40)
        try:
            health_scores = await kpi_use_cases.get_project_health_scores()
            
            if health_scores:
                print(f'📊 Total Projects Analyzed: {len(health_scores)}')
                print()
                
                # Sort by health score (worst first for attention)
                health_scores_sorted = sorted(health_scores, key=lambda x: x.overall_score)
                
                print('🔍 PROJECTS NEEDING ATTENTION (Lowest Health Scores):')
                for i, score in enumerate(health_scores_sorted[:5], 1):
                    status_emoji = {
                        'critical': '🔴',
                        'warning': '🟡', 
                        'healthy': '🟢',
                        'excellent': '⭐'
                    }.get(score.health_status.value, '⚪')
                    
                    print(f'{i:2d}. {status_emoji} {score.project_name}')
                    print(f'    📊 Overall Health Score: {score.overall_score:.1f}/100')
                    print(f'    📈 Progress: {score.progress_percentage:.1f}%')
                    print(f'    🔄 Total Revisions: {score.total_revisions}')
                    print(f'    🎯 Status: {score.health_status.value.upper()}')
                    
                    # Show component scores
                    print(f'    📋 Component Scores:')
                    print(f'       Progress: {score.progress_score:.1f}/100')
                    print(f'       Revision Efficiency: {score.revision_efficiency_score:.1f}/100')
                    print(f'       State Health: {score.state_score:.1f}/100')
                    print(f'       Activity Level: {score.activity_score:.1f}/100')
                    
                    if hasattr(score, 'recommendations') and score.recommendations:
                        print(f'    💡 Recommendations:')
                        for rec in score.recommendations[:2]:
                            print(f'       • {rec}')
                    print()
                
                # Show top performing projects
                print('⭐ TOP PERFORMING PROJECTS (Highest Health Scores):')
                health_scores_top = sorted(health_scores, key=lambda x: x.overall_score, reverse=True)
                for i, score in enumerate(health_scores_top[:3], 1):
                    status_emoji = '⭐' if score.health_status.value == 'excellent' else '🟢'
                    print(f'{i}. {status_emoji} {score.project_name} - {score.overall_score:.1f}/100')
                print()
            else:
                print('⚠️ No project health data available')
                print()
                
        except Exception as e:
            print(f'❌ Error getting project health scores: {e}')
            import traceback
            print(f'Details: {traceback.format_exc()[:300]}...')
            print()
            
    except Exception as e:
        print(f'❌ Failed to connect to Cway API: {e}')
        print()
        print('🔧 TROUBLESHOOTING:')
        print('1. Check that CWAY_API_TOKEN is set in your .env file')
        print('2. Verify the API token is valid and has proper permissions')
        print('3. Ensure network connectivity to https://app.cway.se/graphql')
        print('4. Check if the Cway service is operational')
        return
    
    finally:
        # Cleanup
        try:
            await graphql_client.disconnect()
            print('🔌 Disconnected from Cway API')
        except:
            pass
    
    print()
    print('🎉 KPI Analysis Complete!')
    print('=' * 60)
    print('📈 This data provides insights into:')
    print('   • Project health and completion status')
    print('   • Team productivity and engagement')
    print('   • System utilization and efficiency')
    print('   • Areas requiring attention or improvement')
    print()
    print('🚀 Use this data to make informed decisions about:')
    print('   • Resource allocation and project prioritization')
    print('   • Team workload balancing and support needs')
    print('   • Process improvements and workflow optimization')
    print('   • Early intervention for at-risk projects')


if __name__ == "__main__":
    asyncio.run(show_real_kpis())