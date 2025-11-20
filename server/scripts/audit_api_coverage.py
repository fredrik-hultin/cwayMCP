#!/usr/bin/env python3
"""Audit GraphQL API method coverage by MCP tools."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.presentation.tool_definitions import get_all_tools


def load_graphql_schema():
    """Load GraphQL schema."""
    schema_path = Path(__file__).parent.parent / "docs" / "graphql_schema_readable.json"
    with open(schema_path) as f:
        return json.load(f)


def get_implemented_tools() -> Set[str]:
    """Get list of implemented MCP tool names."""
    tools = get_all_tools()
    return {tool.name for tool in tools}


def analyze_coverage():
    """Analyze API coverage by tools."""
    schema = load_graphql_schema()
    tool_names = get_implemented_tools()
    
    print("=" * 80)
    print("CWAY MCP SERVER - API COVERAGE AUDIT")
    print("=" * 80)
    print()
    
    # Analyze Queries
    queries = schema.get("queries", [])
    print(f"📋 GRAPHQL QUERIES ({len(queries)} total)")
    print("-" * 80)
    
    covered_queries = []
    missing_queries = []
    
    for query in queries:
        name = query["name"]
        desc = query["description"] or "No description"
        
        # Check if tool exists (fuzzy match)
        has_tool = any(
            name.lower() in tool.lower() or
            tool.lower() in name.lower() or
            name.replace("get", "").replace("find", "").lower() in tool.lower()
            for tool in tool_names
        )
        
        if has_tool:
            covered_queries.append(name)
        else:
            missing_queries.append((name, desc))
    
    print(f"✅ Covered: {len(covered_queries)}/{len(queries)}")
    print(f"❌ Missing: {len(missing_queries)}/{len(queries)}")
    print()
    
    if missing_queries:
        print("Missing Query Coverage:")
        for name, desc in sorted(missing_queries):
            print(f"  • {name}")
            if len(desc) < 80:
                print(f"    {desc}")
            print()
    
    # Analyze Mutations
    print()
    print(f"🔧 GRAPHQL MUTATIONS ({len(schema.get('mutations', []))} total)")
    print("-" * 80)
    
    mutations = schema.get("mutations", [])
    covered_mutations = []
    missing_mutations = []
    
    for mutation in mutations:
        name = mutation["name"]
        desc = mutation["description"] or "No description"
        
        # Check if tool exists
        has_tool = any(
            name.lower() in tool.lower() or
            tool.lower() in name.lower()
            for tool in tool_names
        )
        
        if has_tool:
            covered_mutations.append(name)
        else:
            missing_mutations.append((name, desc))
    
    print(f"✅ Covered: {len(covered_mutations)}/{len(mutations)}")
    print(f"❌ Missing: {len(missing_mutations)}/{len(mutations)}")
    print()
    
    if missing_mutations:
        print("Missing Mutation Coverage:")
        for name, desc in sorted(missing_mutations):
            print(f"  • {name}")
            if len(desc) < 80:
                print(f"    {desc}")
            print()
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_api_methods = len(queries) + len(mutations)
    total_covered = len(covered_queries) + len(covered_mutations)
    coverage_percent = (total_covered / total_api_methods * 100) if total_api_methods > 0 else 0
    
    print(f"Total API Methods: {total_api_methods}")
    print(f"Covered by Tools: {total_covered}")
    print(f"Missing Tools: {total_api_methods - total_covered}")
    print(f"Coverage: {coverage_percent:.1f}%")
    print()
    
    # Priority recommendations
    print("=" * 80)
    print("HIGH PRIORITY MISSING TOOLS")
    print("=" * 80)
    
    high_priority = [
        ("projects", "Get all projects with detailed information"),
        ("projectHistory", "Get project event history"),
        ("artworkHistory", "Get artwork revision history"),
        ("openProjectsCountByMonth", "Monthly project trends"),
        ("mediaCenterStats", "Media center statistics"),
        ("createDownloadJob", "Create bulk download jobs"),
        ("artworkAIAnalysis", "Trigger AI analysis on artworks"),
        ("openAIProjectSummary", "Generate AI project summaries"),
    ]
    
    for api_name, description in high_priority:
        # Check if exists in missing
        if any(api_name.lower() in name.lower() for name, _ in missing_queries + missing_mutations):
            print(f"  🔴 {api_name} - {description}")
    
    print()


if __name__ == "__main__":
    analyze_coverage()
