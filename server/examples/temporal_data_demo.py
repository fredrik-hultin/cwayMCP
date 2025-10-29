#!/usr/bin/env python3
"""
Demonstration script for temporal data capabilities in the Cway MCP Server.

This script shows how to:
1. Create entities with temporal metadata
2. Track activities and timelines
3. Analyze temporal patterns
4. Generate temporal KPIs

Run this script to see the temporal data system in action.
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import List
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_temporal_data_system():
    """Demonstrate the temporal data capabilities."""
    
    print("🎨 Cway MCP Server - Temporal Data System Demo")
    print("=" * 60)
    
    # This demo shows the conceptual model of our temporal data system
    
    # Demo 1: Temporal Data Overview
    print("\n📊 Demo 1: Temporal Data Architecture Overview")
    print("-" * 50)
    print("\n✨ Our temporal data system tracks comprehensive information for:")
    print("   📁 PROJECTS: Timeline, progress, activities, team collaboration")
    print("   🎨 ARTWORKS: Version history, revisions, creative process")
    print("   📝 REVISIONS: Review workflow, approval times, feedback")
    print("   👥 USERS: Activity patterns, performance metrics, collaboration")
    
    # Demo 2: Sample Project Data Structure
    print("\n📈 Demo 2: Sample Project with Temporal Data")
    print("-" * 50)
    
    now = datetime.now()
    project_start = now - timedelta(days=30)
    
    sample_project_data = {
        "id": "proj_mobile_app_001",
        "name": "Mobile App UI Redesign",
        "status": "IN_PROGRESS", 
        "completion_percentage": 75.0,
        "start_date": project_start.isoformat(),
        "team_size": 3,
        "activity_timeline": [
            {"day": 1, "activity": "Project created", "user": "Project Manager"},
            {"day": 3, "activity": "Initial wireframes", "user": "UI Designer"},
            {"day": 7, "activity": "Design mockups completed", "user": "UI Designer"},
            {"day": 12, "activity": "First revision submitted", "user": "UI Designer"},
            {"day": 15, "activity": "Client feedback received", "user": "Project Manager"},
            {"day": 20, "activity": "Revisions implemented", "user": "UI Designer"},
            {"day": 25, "activity": "Second revision approved", "user": "Client"}
        ]
    }
    
    print(f"✅ Project: {sample_project_data['name']}")
    print(f"   📅 Duration: {(now - project_start).days} days")
    print(f"   📈 Progress: {sample_project_data['completion_percentage']}%")
    print(f"   👥 Team: {sample_project_data['team_size']} members")
    print(f"   📝 Activities: {len(sample_project_data['activity_timeline'])} logged")
    
    print(f"\n   📊 Recent Activities:")
    for activity in sample_project_data['activity_timeline'][-3:]:
        print(f"      Day {activity['day']:2d}: {activity['activity']} ({activity['user']})")
    
    # Demo 3: Temporal KPI Analysis
    print("\n📊 Demo 3: Temporal KPI Analysis")
    print("-" * 50)
    
    # Calculate sample metrics
    total_days = (now - project_start).days
    activities_per_week = len(sample_project_data['activity_timeline']) / (total_days / 7)
    days_since_last = 5  # Sample value
    
    print(f"🔥 Activity Analysis:")
    print(f"   📈 Velocity: {activities_per_week:.1f} activities/week")
    print(f"   ⏰ Days since last activity: {days_since_last}")
    print(f"   📅 Active days: {len(sample_project_data['activity_timeline'])} / {total_days}")
    
    # Determine activity level
    if activities_per_week >= 3:
        activity_level = "HIGH"
        activity_emoji = "🚀"
    elif activities_per_week >= 1.5:
        activity_level = "MODERATE" 
        activity_emoji = "🚶"
    elif activities_per_week >= 0.5:
        activity_level = "LOW"
        activity_emoji = "🐌"
    else:
        activity_level = "INACTIVE"
        activity_emoji = "😴"
        
    # Determine stagnation risk
    if days_since_last <= 3:
        stagnation_risk = "NONE"
        risk_emoji = "✅"
    elif days_since_last <= 7:
        stagnation_risk = "LOW"
        risk_emoji = "🟡"
    elif days_since_last <= 14:
        stagnation_risk = "MODERATE"
        risk_emoji = "🟠"
    else:
        stagnation_risk = "HIGH"
        risk_emoji = "🔴"
    
    print(f"   {activity_emoji} Activity Level: {activity_level}")
    print(f"   {risk_emoji} Stagnation Risk: {stagnation_risk}")
    
    # Demo 4: Team Insights
    print("\n👥 Demo 4: Team Temporal Insights")
    print("-" * 50)
    
    team_insights = {
        "peak_activity_day": "Tuesday",
        "peak_activity_hour": "10:00",
        "avg_revision_time": "2.5 days",
        "avg_approval_time": "1.2 days",
        "collaboration_score": 85,
        "productivity_trend": "Increasing"
    }
    
    print(f"📊 Team Performance:")
    print(f"   📅 Peak activity day: {team_insights['peak_activity_day']}")
    print(f"   🕐 Peak activity hour: {team_insights['peak_activity_hour']}")
    print(f"   ⏱️ Avg revision time: {team_insights['avg_revision_time']}")
    print(f"   ✅ Avg approval time: {team_insights['avg_approval_time']}")
    print(f"   🤝 Collaboration score: {team_insights['collaboration_score']}/100")
    print(f"   📈 Productivity trend: {team_insights['productivity_trend']}")
    
    # Demo 5: Predictive Insights
    print("\n🔮 Demo 5: Predictive Insights")
    print("-" * 50)
    
    # Sample predictions based on current velocity
    current_progress = sample_project_data['completion_percentage']
    remaining_work = 100 - current_progress
    estimated_days_remaining = int((remaining_work / current_progress) * total_days)
    estimated_completion = now + timedelta(days=estimated_days_remaining)
    
    print(f"🎯 Project Predictions:")
    print(f"   📊 Current progress: {current_progress}%")
    print(f"   📈 Estimated completion: {estimated_completion.strftime('%Y-%m-%d')}")
    print(f"   ⏰ Days remaining: ~{estimated_days_remaining} days")
    
    if estimated_days_remaining > 14:
        completion_status = "🔴 Behind schedule - consider resource reallocation"
    elif estimated_days_remaining > 7:
        completion_status = "🟡 On track - monitor closely"
    else:
        completion_status = "🟢 Ahead of schedule - excellent progress"
        
    print(f"   {completion_status}")
    
    # Demo 6: Available MCP Resources
    print("\n🔗 Demo 6: Available MCP Resources & Tools")
    print("-" * 50)
    
    print("📁 Temporal KPI Resources:")
    resources = [
        ("cway://temporal-kpis/dashboard", "Comprehensive temporal dashboard"),
        ("cway://temporal-kpis/project-timelines", "Project activity timelines"),
        ("cway://temporal-kpis/stagnation-alerts", "Project stagnation alerts"),
        ("cway://temporal-kpis/team-metrics", "Team temporal patterns")
    ]
    
    for uri, description in resources:
        print(f"   🔗 {uri}")
        print(f"      📝 {description}")
    
    print("\n🔧 Temporal KPI Tools:")
    tools = [
        ("analyze_project_velocity", "Detailed velocity analysis for specific projects"),
        ("get_temporal_dashboard", "Generate comprehensive temporal KPI dashboard"), 
        ("get_stagnation_alerts", "Retrieve stagnation alerts with filtering")
    ]
    
    for tool_name, description in tools:
        print(f"   ⚙️ {tool_name}")
        print(f"      📝 {description}")
    
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    print("🎨 The Cway MCP Server temporal data system provides:")
    print("   • Comprehensive activity tracking for all entities")
    print("   • Real-time insights and predictive analytics")
    print("   • Proactive stagnation and risk detection")
    print("   • Team productivity and collaboration insights")
    print("   • Data-driven decision making capabilities")
    print("")
    print("🚀 This enables organizations to optimize their creative")
    print("   workflows, improve team productivity, and deliver")
    print("   projects more efficiently with actionable insights.")


if __name__ == "__main__":
    print("Starting temporal data system demonstration...")
    demo_temporal_data_system()
