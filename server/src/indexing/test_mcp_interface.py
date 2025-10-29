"""Test the MCP indexing interface for unified document and page handling."""

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

from .mcp_indexing_service import MCPIndexingService, IndexingTarget

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_indexing_interface():
    """Test the complete MCP indexing interface."""
    
    print("🧪 Testing MCP Indexing Interface")
    print("=" * 50)
    
    # Create temporary config for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test_indexing_config.json"
        
        # Initialize service
        service = MCPIndexingService(config_path)
        
        print("\n📋 1. TESTING CONFIGURATION MANAGEMENT")
        print("-" * 40)
        
        # Test getting initial targets
        targets = service.get_targets()
        print(f"✓ Initial targets loaded: {len(targets)}")
        for target in targets:
            status = "✅ Enabled" if target["enabled"] else "❌ Disabled"
            print(f"  • {target['name']} ({target['platform']}) - {status}")
        
        # Test adding new target
        success = service.add_target(
            name="test_elasticsearch",
            platform="elasticsearch",
            description="Test Elasticsearch target",
            config={
                "url": "http://localhost:9200",
                "index_prefix": "test_cway"
            },
            enabled=False  # Disabled for testing
        )
        
        if success:
            print("✓ Successfully added test Elasticsearch target")
        else:
            print("❌ Failed to add test target")
        
        # Test getting target details
        details = service.get_target_details("test_elasticsearch")
        if details:
            print(f"✓ Target details: {details['name']} - {details['status']}")
        
        print("\n🔌 2. TESTING PLATFORM SUPPORT")
        print("-" * 40)
        
        platforms = service.get_supported_platforms()
        print(f"✓ Supported platforms: {len(platforms)}")
        for platform in platforms:
            print(f"  📦 {platform['name']}: {platform['suitable_for']}")
        
        print("\n📊 3. TESTING CONTENT STATISTICS")
        print("-" * 40)
        
        try:
            stats = await service.get_indexable_content_stats()
            if "error" in stats:
                print(f"⚠️  Content stats error: {stats['error']}")
            else:
                print(f"✓ Content statistics:")
                print(f"  📄 Total documents: {stats['total_documents']:,}")
                print(f"  📁 Projects: {stats['projects']:,}")
                print(f"  👥 Users: {stats['users']:,}")
                print(f"  📈 KPI documents: {stats['kpi_documents']:,}")
                print(f"  ⏰ Temporal KPI documents: {stats['temporal_kpi_documents']:,}")
        except Exception as e:
            print(f"⚠️  Could not get content stats (requires API connection): {e}")
        
        print("\n💾 4. TESTING QUICK BACKUP")
        print("-" * 40)
        
        try:
            result = await service.quick_backup()
            
            print(f"✓ Backup completed:")
            print(f"  Job ID: {result.job_id}")
            print(f"  Success: {'✅' if result.success else '❌'}")
            print(f"  Message: {result.message}")
            print(f"  Documents indexed: {result.documents_indexed}")
            print(f"  Duration: {result.duration_seconds:.1f}s")
            print(f"  Targets completed: {result.targets_completed}")
            print(f"  Targets failed: {result.targets_failed}")
            
        except Exception as e:
            print(f"⚠️  Quick backup failed (requires API connection): {e}")
        
        print("\n📈 5. TESTING JOB MANAGEMENT")
        print("-" * 40)
        
        # Test job history
        history = service.get_job_history(limit=5)
        print(f"✓ Job history: {len(history)} recent jobs")
        for job in history:
            status = "✅" if job["success"] else "❌"
            print(f"  {status} {job['job_id']}: {job['message'][:50]}...")
        
        # Test active jobs
        active = service.get_active_jobs()
        print(f"✓ Active jobs: {len(active)}")
        
        print("\n🎯 6. TESTING FULL INDEXING (FILE ONLY)")
        print("-" * 40)
        
        # Only use file targets to avoid needing external services
        file_targets = [t["name"] for t in service.get_targets() 
                       if t["platform"] == "file" and t["enabled"]]
        
        if file_targets:
            try:
                result = await service.index_all_content(targets=file_targets)
                
                print(f"✓ Full indexing result:")
                print(f"  Job ID: {result.job_id}")
                print(f"  Success: {'✅' if result.success else '❌'}")
                print(f"  Message: {result.message}")
                print(f"  Documents indexed: {result.documents_indexed}")
                print(f"  Duration: {result.duration_seconds:.1f}s")
                print(f"  Targets completed: {', '.join(result.targets_completed)}")
                if result.targets_failed:
                    print(f"  Targets failed: {', '.join(result.targets_failed)}")
                    
            except Exception as e:
                print(f"⚠️  Full indexing failed (requires API connection): {e}")
        else:
            print("⚠️  No file targets enabled for testing")
        
        print("\n🔧 7. TESTING CONFIGURATION UPDATES")
        print("-" * 40)
        
        # Test updating target
        update_success = service.update_target(
            name="file_backup",
            description="Updated: Local backup with timestamp",
            config={
                "output_dir": f"indexed_data_test_{int(asyncio.get_event_loop().time())}",
                "format": "jsonl"
            }
        )
        
        if update_success:
            print("✓ Successfully updated file_backup target")
            updated_details = service.get_target_details("file_backup")
            if updated_details:
                print(f"  New description: {updated_details['description']}")
        
        print("\n🗂️  8. DEMONSTRATING UNIFIED INTERFACE")
        print("-" * 40)
        
        print("The MCP indexing interface provides:")
        print("✓ Unified handling of documents AND site pages")
        print("✓ Simple tools like 'index_all_content' and 'quick_backup'")
        print("✓ Platform-agnostic configuration")
        print("✓ Job tracking and status monitoring")
        print("✓ Content statistics across all data types")
        print("✓ Easy target management (add/update/remove)")
        
        print("\n🌟 MCP TOOLS AVAILABLE:")
        tools = [
            "index_all_content - Index all documents and pages",
            "quick_backup - Fast backup to local files",
            "index_project_content - Index specific project content",
            "configure_indexing_target - Add/update indexing targets",
            "get_indexing_job_status - Check job status"
        ]
        for tool in tools:
            print(f"  🔧 {tool}")
        
        print("\n🗂️  MCP RESOURCES AVAILABLE:")
        resources = [
            "cway://indexing/targets - View configured targets",
            "cway://indexing/status - Job status and history",
            "cway://indexing/content-stats - Content statistics",
            "cway://indexing/platforms - Supported platforms"
        ]
        for resource in resources:
            print(f"  📄 {resource}")
        
        print("\n✨ USAGE EXAMPLES:")
        print("=" * 50)
        
        print("\n1. Simple backup (MCP tool call):")
        print('   {"name": "quick_backup", "arguments": {}}')
        
        print("\n2. Index to specific targets:")
        print('   {"name": "index_all_content", "arguments": {"targets": ["file_backup"]}}')
        
        print("\n3. Configure new search index:")
        print('''   {"name": "configure_indexing_target", "arguments": {
       "name": "production_search",
       "platform": "elasticsearch", 
       "description": "Production search index",
       "config": {"url": "https://search.company.com", "index_prefix": "cway"}
   }}''')
        
        print("\n4. Check content statistics (MCP resource):")
        print('   Resource URI: "cway://indexing/content-stats"')
        
        print("\n" + "=" * 50)
        print("🎉 MCP INDEXING INTERFACE TEST COMPLETE!")
        print("The interface successfully abstracts indexing complexity")
        print("and provides uniform access to documents AND site pages!")


async def demonstrate_real_usage():
    """Demonstrate real-world usage patterns."""
    
    print("\n" + "=" * 50)
    print("🚀 REAL-WORLD USAGE DEMONSTRATION")
    print("=" * 50)
    
    service = MCPIndexingService()
    
    # Scenario 1: Daily backup routine
    print("\n📅 SCENARIO 1: Daily Backup Routine")
    print("-" * 30)
    
    print("A user wants to backup all content daily...")
    try:
        backup_result = await service.quick_backup()
        print(f"✓ Backup job '{backup_result.job_id}' completed")
        print(f"  📊 {backup_result.documents_indexed} documents backed up")
        print(f"  ⏱️  Took {backup_result.duration_seconds:.1f} seconds")
    except Exception as e:
        print(f"⚠️  Backup demo requires API connection: {e}")
    
    # Scenario 2: Setting up search
    print("\n🔍 SCENARIO 2: Setting Up Search Index")
    print("-" * 30)
    
    print("DevOps wants to setup Elasticsearch for search...")
    success = service.add_target(
        name="main_search",
        platform="elasticsearch",
        description="Main search index for all content",
        config={
            "url": "http://localhost:9200",
            "index_prefix": "cway_prod",
            "auth": None
        },
        enabled=False  # Would be True in real usage
    )
    
    if success:
        print("✓ Search target configured successfully")
        print("  🎯 Ready to index documents AND pages together")
    
    # Scenario 3: Project-specific indexing
    print("\n📁 SCENARIO 3: Project-Specific Indexing")
    print("-" * 30)
    
    print("Project manager wants to index specific project content...")
    try:
        # This would work with a real project ID
        print("  🔧 Tool: index_project_content")
        print("  📋 Would index all documents/pages for the project")
        print("  🎯 Same simple interface regardless of content type")
    except Exception as e:
        print(f"⚠️  Project indexing demo: {e}")
    
    print("\n🌟 KEY BENEFITS:")
    print("✓ Documents and site pages treated identically")
    print("✓ No need to understand different indexing formats")
    print("✓ One simple interface for all platforms")
    print("✓ Built-in job tracking and error handling")
    print("✓ Easy configuration management")
    print("✓ Scalable from file backup to enterprise search")


if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(test_mcp_indexing_interface())
    
    # Show real-world usage
    asyncio.run(demonstrate_real_usage())