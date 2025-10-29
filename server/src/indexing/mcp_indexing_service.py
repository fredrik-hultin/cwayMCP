"""MCP Indexing Service - Unified interface for indexing documents and site pages."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from .indexer import IndexingPipeline, IndexingConfig, IndexingResult
from .data_extractor import CwayDataExtractor

logger = logging.getLogger(__name__)


@dataclass
class IndexingTarget:
    """Represents a configured indexing target."""
    
    name: str  # User-friendly name like "main_search", "analytics", "backup"
    platform: str  # elasticsearch, file, algolia, etc.
    description: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


@dataclass
class IndexingJobResult:
    """Simplified result for MCP consumers."""
    
    job_id: str
    success: bool
    message: str
    documents_indexed: int
    duration_seconds: float
    targets_completed: List[str]
    targets_failed: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None


class MCPIndexingService:
    """Simplified indexing service for MCP consumers."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("indexing_config.json")
        self.targets: Dict[str, IndexingTarget] = {}
        self.active_jobs: Dict[str, IndexingJobResult] = {}
        self.job_history: List[IndexingJobResult] = []
        self.max_history = 100
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load indexing configuration from file or create defaults."""
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                self.targets = {}
                for target_data in config_data.get('targets', []):
                    target = IndexingTarget(**target_data)
                    self.targets[target.name] = target
                
                logger.info(f"Loaded {len(self.targets)} indexing targets from {self.config_path}")
                
            except Exception as e:
                logger.error(f"Error loading indexing configuration: {e}")
                self._create_default_configuration()
        else:
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create default indexing configuration."""
        
        self.targets = {
            "file_backup": IndexingTarget(
                name="file_backup",
                platform="file",
                description="Local JSON file backup for all documents and pages",
                config={
                    "output_dir": "indexed_data",
                    "format": "jsonl"
                }
            ),
            "search_index": IndexingTarget(
                name="search_index",
                platform="elasticsearch",
                description="Main search index for documents and pages",
                enabled=False,  # Disabled by default since it requires ES setup
                config={
                    "url": "http://localhost:9200",
                    "auth": None,
                    "verify_ssl": True
                }
            )
        }
        
        self._save_configuration()
        logger.info("Created default indexing configuration")
    
    def _save_configuration(self):
        """Save current configuration to file."""
        
        try:
            config_data = {
                "targets": [asdict(target) for target in self.targets.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving indexing configuration: {e}")
    
    # Configuration Management
    
    def get_targets(self) -> List[Dict[str, Any]]:
        """Get all configured indexing targets."""
        
        return [
            {
                "name": target.name,
                "platform": target.platform,
                "description": target.description,
                "enabled": target.enabled,
                "has_config": target.config is not None
            }
            for target in self.targets.values()
        ]
    
    def get_target_details(self, target_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific target."""
        
        target = self.targets.get(target_name)
        if not target:
            return None
        
        return {
            "name": target.name,
            "platform": target.platform,
            "description": target.description,
            "enabled": target.enabled,
            "config": target.config or {},
            "status": "ready" if target.enabled else "disabled"
        }
    
    def add_target(
        self,
        name: str,
        platform: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ) -> bool:
        """Add a new indexing target."""
        
        if name in self.targets:
            return False
        
        self.targets[name] = IndexingTarget(
            name=name,
            platform=platform,
            description=description,
            config=config,
            enabled=enabled
        )
        
        self._save_configuration()
        return True
    
    def update_target(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """Update an existing indexing target."""
        
        target = self.targets.get(name)
        if not target:
            return False
        
        if description is not None:
            target.description = description
        if config is not None:
            target.config = config
        if enabled is not None:
            target.enabled = enabled
        
        self._save_configuration()
        return True
    
    def remove_target(self, name: str) -> bool:
        """Remove an indexing target."""
        
        if name not in self.targets:
            return False
        
        del self.targets[name]
        self._save_configuration()
        return True
    
    # Indexing Operations
    
    async def index_all_content(
        self,
        targets: Optional[List[str]] = None,
        job_id: Optional[str] = None
    ) -> IndexingJobResult:
        """Index all documents and site pages to specified targets."""
        
        job_id = job_id or f"index_all_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        # Create job result
        result = IndexingJobResult(
            job_id=job_id,
            success=False,
            message="Starting indexing job...",
            documents_indexed=0,
            duration_seconds=0,
            targets_completed=[],
            targets_failed=[],
            started_at=start_time
        )
        
        self.active_jobs[job_id] = result
        
        try:
            # Determine which targets to use
            target_names = targets or [name for name, target in self.targets.items() if target.enabled]
            
            if not target_names:
                result.message = "No enabled targets found"
                result.completed_at = datetime.now()
                result.duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Convert targets to indexing configs
            indexing_configs = []
            for target_name in target_names:
                target = self.targets.get(target_name)
                if not target or not target.enabled:
                    result.targets_failed.append(target_name)
                    continue
                
                try:
                    config = IndexingConfig(
                        platform=target.platform,
                        connection_config=target.config or {},
                        batch_size=100,
                        max_retries=3
                    )
                    indexing_configs.append(config)
                    
                except Exception as e:
                    logger.error(f"Error creating config for target {target_name}: {e}")
                    result.targets_failed.append(target_name)
            
            if not indexing_configs:
                result.message = "No valid target configurations"
                result.completed_at = datetime.now()
                result.duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Run indexing pipeline
            pipeline = IndexingPipeline(indexing_configs)
            indexing_results = await pipeline.run_full_pipeline()
            
            # Process results
            total_indexed = 0
            for i, indexing_result in enumerate(indexing_results):
                target_name = target_names[i] if i < len(target_names) else f"target_{i}"
                
                if indexing_result.success:
                    result.targets_completed.append(target_name)
                    total_indexed += indexing_result.documents_indexed
                else:
                    result.targets_failed.append(target_name)
            
            result.documents_indexed = total_indexed
            result.success = len(result.targets_completed) > 0
            
            if result.success:
                if result.targets_failed:
                    result.message = f"Partially successful: {len(result.targets_completed)} targets completed, {len(result.targets_failed)} failed"
                else:
                    result.message = f"Successfully indexed to {len(result.targets_completed)} targets"
            else:
                result.message = f"Failed to index to any targets: {', '.join(result.targets_failed)}"
            
        except Exception as e:
            logger.error(f"Error in indexing job {job_id}: {e}")
            result.message = f"Indexing job failed: {str(e)}"
            result.error_details = str(e)
            result.targets_failed.extend([name for name in target_names if name not in result.targets_completed])
        
        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = (result.completed_at - start_time).total_seconds()
            
            # Move to history
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            self.job_history.insert(0, result)
            if len(self.job_history) > self.max_history:
                self.job_history = self.job_history[:self.max_history]
        
        return result
    
    async def index_project_documents(
        self,
        project_id: str,
        targets: Optional[List[str]] = None
    ) -> IndexingJobResult:
        """Index documents for a specific project."""
        
        # For now, this will index all content but could be extended to filter by project
        job_id = f"index_project_{project_id}_{int(datetime.now().timestamp())}"
        
        result = await self.index_all_content(targets=targets, job_id=job_id)
        result.message = f"Project {project_id}: {result.message}"
        
        return result
    
    async def index_user_content(
        self,
        user_id: str,
        targets: Optional[List[str]] = None
    ) -> IndexingJobResult:
        """Index content for a specific user."""
        
        # For now, this will index all content but could be extended to filter by user
        job_id = f"index_user_{user_id}_{int(datetime.now().timestamp())}"
        
        result = await self.index_all_content(targets=targets, job_id=job_id)
        result.message = f"User {user_id}: {result.message}"
        
        return result
    
    async def quick_backup(self) -> IndexingJobResult:
        """Quick backup to file storage."""
        
        # Find file-based target or create temporary one
        file_targets = [name for name, target in self.targets.items() 
                      if target.platform in ['file', 'json', 'jsonl'] and target.enabled]
        
        if not file_targets:
            # Create temporary file target
            temp_target = IndexingTarget(
                name="temp_backup",
                platform="file",
                description="Temporary backup target",
                config={
                    "output_dir": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "format": "jsonl"
                }
            )
            self.targets["temp_backup"] = temp_target
            file_targets = ["temp_backup"]
        
        return await self.index_all_content(targets=file_targets[:1])
    
    # Status and History
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        
        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                "job_id": job.job_id,
                "status": "running",
                "message": job.message,
                "started_at": job.started_at.isoformat(),
                "duration_seconds": (datetime.now() - job.started_at).total_seconds()
            }
        
        # Check job history
        for job in self.job_history:
            if job.job_id == job_id:
                return {
                    "job_id": job.job_id,
                    "status": "completed" if job.success else "failed",
                    "message": job.message,
                    "documents_indexed": job.documents_indexed,
                    "duration_seconds": job.duration_seconds,
                    "started_at": job.started_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "targets_completed": job.targets_completed,
                    "targets_failed": job.targets_failed,
                    "error_details": job.error_details
                }
        
        return None
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active indexing jobs."""
        
        return [
            {
                "job_id": job.job_id,
                "message": job.message,
                "started_at": job.started_at.isoformat(),
                "duration_seconds": (datetime.now() - job.started_at).total_seconds()
            }
            for job in self.active_jobs.values()
        ]
    
    def get_job_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent job history."""
        
        return [
            {
                "job_id": job.job_id,
                "success": job.success,
                "message": job.message,
                "documents_indexed": job.documents_indexed,
                "duration_seconds": job.duration_seconds,
                "started_at": job.started_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "targets_completed": len(job.targets_completed),
                "targets_failed": len(job.targets_failed)
            }
            for job in self.job_history[:limit]
        ]
    
    # Content Statistics
    
    async def get_indexable_content_stats(self) -> Dict[str, Any]:
        """Get statistics about indexable content."""
        
        extractor = CwayDataExtractor()
        
        try:
            await extractor.initialize()
            
            stats = {
                "projects": 0,
                "users": 0,
                "kpi_documents": 0,
                "temporal_kpi_documents": 0,
                "total_documents": 0
            }
            
            async for doc in extractor.extract_all_data():
                stats["total_documents"] += 1
                
                if doc.document_type == "project":
                    stats["projects"] += 1
                elif doc.document_type == "user":
                    stats["users"] += 1
                elif doc.document_type == "kpi":
                    stats["kpi_documents"] += 1
                elif doc.document_type == "temporal_kpi":
                    stats["temporal_kpi_documents"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting content stats: {e}")
            return {"error": str(e)}
            
        finally:
            await extractor.cleanup()
    
    # Platform Support
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """Get list of supported indexing platforms."""
        
        return [
            {
                "platform": "file",
                "name": "File Storage",
                "description": "Store documents as JSON/JSONL files locally",
                "config_fields": ["output_dir", "format"],
                "suitable_for": "backup, development, testing"
            },
            {
                "platform": "elasticsearch",
                "name": "Elasticsearch",
                "description": "Index documents to Elasticsearch for full-text search",
                "config_fields": ["url", "auth", "api_key", "verify_ssl"],
                "suitable_for": "search, analytics, production"
            },
            {
                "platform": "opensearch",
                "name": "OpenSearch",
                "description": "Index documents to OpenSearch for search and analytics",
                "config_fields": ["url", "auth", "api_key", "verify_ssl"],
                "suitable_for": "search, analytics, production"
            },
            {
                "platform": "algolia",
                "name": "Algolia",
                "description": "Index documents to Algolia for fast search experiences",
                "config_fields": ["app_id", "api_key", "index_prefix"],
                "suitable_for": "fast search, user interfaces"
            },
            {
                "platform": "pinecone",
                "name": "Pinecone",
                "description": "Index document embeddings to Pinecone for semantic search",
                "config_fields": ["api_key", "environment", "index_name"],
                "suitable_for": "semantic search, AI applications"
            }
        ]


# Global service instance
_indexing_service: Optional[MCPIndexingService] = None


def get_indexing_service() -> MCPIndexingService:
    """Get or create the global indexing service instance."""
    
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = MCPIndexingService()
    return _indexing_service