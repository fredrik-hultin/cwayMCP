"""Indexer interface for sending documents to various search/analytics platforms."""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, AsyncIterator
from dataclasses import dataclass
from pathlib import Path
import httpx
import aiofiles

from .data_extractor import CwayDataExtractor, IndexableDocument
from .transformers import TransformerFactory, TransformedDocument, PLATFORM_CONFIGS

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Result of indexing operation."""
    
    platform: str
    success: bool
    documents_processed: int
    documents_indexed: int
    documents_failed: int
    duration_seconds: float
    error_message: Optional[str] = None
    failed_documents: Optional[List[str]] = None


@dataclass
class IndexingConfig:
    """Configuration for indexing operations."""
    
    platform: str
    connection_config: Dict[str, Any]
    transformer_config: Optional[Dict[str, Any]] = None
    batch_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 30.0


class BaseIndexer(ABC):
    """Base class for document indexers."""
    
    def __init__(self, config: IndexingConfig):
        self.config = config
        self.platform = config.platform
        self.batch_size = config.batch_size
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay_seconds
        self.timeout = config.timeout_seconds
        
        # Create transformer
        self.transformer = TransformerFactory.create_transformer(
            self.platform, 
            config.transformer_config or PLATFORM_CONFIGS.get(self.platform, {})
        )
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the indexing platform."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the indexing platform."""
        pass
    
    @abstractmethod
    async def index_batch(self, documents: List[TransformedDocument]) -> Tuple[int, List[str]]:
        """Index a batch of documents. Returns (success_count, failed_doc_ids)."""
        pass
    
    @abstractmethod
    async def create_index_if_not_exists(self, index_name: str, document_type: str) -> bool:
        """Create index if it doesn't exist."""
        pass
    
    async def index_documents(self, documents: List[IndexableDocument]) -> IndexingResult:
        """Index a list of documents."""
        
        start_time = time.time()
        total_docs = len(documents)
        indexed_count = 0
        failed_docs = []
        
        try:
            # Connect to platform
            if not await self.connect():
                return IndexingResult(
                    platform=self.platform,
                    success=False,
                    documents_processed=total_docs,
                    documents_indexed=0,
                    documents_failed=total_docs,
                    duration_seconds=time.time() - start_time,
                    error_message="Failed to connect to indexing platform"
                )
            
            # Transform documents
            transformed_docs = []
            for doc in documents:
                try:
                    transformed = self.transformer.transform(doc)
                    transformed_docs.append(transformed)
                except Exception as e:
                    logger.error(f"Error transforming document {doc.id}: {e}")
                    failed_docs.append(doc.id)
            
            if not transformed_docs:
                return IndexingResult(
                    platform=self.platform,
                    success=False,
                    documents_processed=total_docs,
                    documents_indexed=0,
                    documents_failed=total_docs,
                    duration_seconds=time.time() - start_time,
                    error_message="No documents could be transformed"
                )
            
            # Group by index name and create indices
            indices_created = set()
            docs_by_index = {}
            
            for doc in transformed_docs:
                index_name = doc.index_name
                
                if index_name not in indices_created:
                    # Determine document type from original document
                    original_doc = next((d for d in documents if d.id == doc.document_id), None)
                    doc_type = original_doc.document_type if original_doc else "document"
                    
                    await self.create_index_if_not_exists(index_name, doc_type)
                    indices_created.add(index_name)
                
                if index_name not in docs_by_index:
                    docs_by_index[index_name] = []
                docs_by_index[index_name].append(doc)
            
            # Index documents in batches
            for index_name, index_docs in docs_by_index.items():
                logger.info(f"Indexing {len(index_docs)} documents to {index_name}")
                
                # Process in batches
                for i in range(0, len(index_docs), self.batch_size):
                    batch = index_docs[i:i + self.batch_size]
                    
                    # Retry logic
                    retry_count = 0
                    while retry_count < self.max_retries:
                        try:
                            success_count, batch_failed = await self.index_batch(batch)
                            indexed_count += success_count
                            failed_docs.extend(batch_failed)
                            break
                            
                        except Exception as e:
                            retry_count += 1
                            if retry_count >= self.max_retries:
                                logger.error(f"Failed to index batch after {self.max_retries} retries: {e}")
                                failed_docs.extend([doc.document_id for doc in batch])
                            else:
                                logger.warning(f"Retry {retry_count}/{self.max_retries} for batch indexing: {e}")
                                await asyncio.sleep(self.retry_delay * retry_count)
            
            duration = time.time() - start_time
            success = len(failed_docs) == 0
            
            return IndexingResult(
                platform=self.platform,
                success=success,
                documents_processed=total_docs,
                documents_indexed=indexed_count,
                documents_failed=len(failed_docs),
                duration_seconds=duration,
                failed_documents=failed_docs if failed_docs else None
            )
            
        except Exception as e:
            logger.error(f"Error during indexing: {e}")
            return IndexingResult(
                platform=self.platform,
                success=False,
                documents_processed=total_docs,
                documents_indexed=indexed_count,
                documents_failed=total_docs - indexed_count,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                failed_documents=failed_docs
            )
            
        finally:
            await self.disconnect()


class ElasticsearchIndexer(BaseIndexer):
    """Elasticsearch indexer implementation."""
    
    def __init__(self, config: IndexingConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = config.connection_config.get('url', 'http://localhost:9200')
        self.auth = config.connection_config.get('auth')  # (username, password)
        self.api_key = config.connection_config.get('api_key')
        self.verify_ssl = config.connection_config.get('verify_ssl', True)
    
    async def connect(self) -> bool:
        """Connect to Elasticsearch."""
        try:
            headers = {'Content-Type': 'application/json'}
            
            # Add authentication
            auth = None
            if self.api_key:
                headers['Authorization'] = f'ApiKey {self.api_key}'
            elif self.auth:
                auth = self.auth
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                auth=auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            # Test connection
            response = await self.client.get('/_cluster/health')
            response.raise_for_status()
            
            logger.info(f"Connected to Elasticsearch at {self.base_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Elasticsearch."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def create_index_if_not_exists(self, index_name: str, document_type: str) -> bool:
        """Create Elasticsearch index if it doesn't exist."""
        try:
            # Check if index exists
            response = await self.client.head(f'/{index_name}')
            if response.status_code == 200:
                return True
            
            # Create index with mapping
            mapping = self._get_index_mapping(document_type)
            
            response = await self.client.put(
                f'/{index_name}',
                json={
                    'settings': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0,
                        'analysis': {
                            'analyzer': {
                                'cway_analyzer': {
                                    'tokenizer': 'standard',
                                    'filter': ['lowercase', 'stop']
                                }
                            }
                        }
                    },
                    'mappings': mapping
                }
            )
            response.raise_for_status()
            
            logger.info(f"Created Elasticsearch index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index {index_name}: {e}")
            return False
    
    async def index_batch(self, documents: List[TransformedDocument]) -> Tuple[int, List[str]]:
        """Index batch of documents using bulk API."""
        if not documents:
            return 0, []
        
        # Build bulk request
        bulk_body = []
        for doc in documents:
            # Index operation
            bulk_body.append(json.dumps({
                'index': {
                    '_index': doc.index_name,
                    '_id': doc.document_id
                }
            }))
            # Document data
            bulk_body.append(json.dumps(doc.document))
        
        bulk_data = '\n'.join(bulk_body) + '\n'
        
        try:
            response = await self.client.post(
                '/_bulk',
                content=bulk_data,
                headers={'Content-Type': 'application/x-ndjson'}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check for errors
            success_count = 0
            failed_docs = []
            
            if result.get('errors'):
                for item in result.get('items', []):
                    if 'index' in item:
                        index_result = item['index']
                        if index_result.get('status', 0) < 300:
                            success_count += 1
                        else:
                            failed_docs.append(index_result.get('_id', 'unknown'))
            else:
                success_count = len(documents)
            
            return success_count, failed_docs
            
        except Exception as e:
            logger.error(f"Error in Elasticsearch bulk indexing: {e}")
            return 0, [doc.document_id for doc in documents]
    
    def _get_index_mapping(self, document_type: str) -> Dict[str, Any]:
        """Get Elasticsearch mapping for document type."""
        
        base_mapping = {
            'properties': {
                '@timestamp': {'type': 'date'},
                'document_id': {'type': 'keyword'},
                'document_type': {'type': 'keyword'},
                'title': {
                    'type': 'text',
                    'analyzer': 'cway_analyzer',
                    'fields': {'keyword': {'type': 'keyword'}}
                },
                'content': {
                    'type': 'text',
                    'analyzer': 'cway_analyzer'
                },
                'tags': {'type': 'keyword'},
                'url': {'type': 'keyword'},
                'created_at': {'type': 'date'},
                'updated_at': {'type': 'date'},
                'embedding_vector': {
                    'type': 'dense_vector',
                    'dims': 1536
                }
            }
        }
        
        # Add document-type specific mappings
        if document_type == 'project':
            base_mapping['properties'].update({
                'project_id': {'type': 'keyword'},
                'project_state': {'type': 'keyword'},
                'progress_percentage': {'type': 'float'},
                'is_active': {'type': 'boolean'},
                'is_completed': {'type': 'boolean'},
                'start_date': {'type': 'date'},
                'end_date': {'type': 'date'}
            })
        elif document_type == 'user':
            base_mapping['properties'].update({
                'user_id': {'type': 'keyword'},
                'email': {'type': 'keyword'},
                'username': {'type': 'keyword'},
                'enabled': {'type': 'boolean'},
                'is_sso': {'type': 'boolean'}
            })
        
        return base_mapping


class FileIndexer(BaseIndexer):
    """File-based indexer for JSON/JSONL output."""
    
    def __init__(self, config: IndexingConfig):
        super().__init__(config)
        self.output_dir = Path(config.connection_config.get('output_dir', 'indexed_data'))
        self.format = config.connection_config.get('format', 'jsonl')  # 'json' or 'jsonl'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def connect(self) -> bool:
        """File indexer is always 'connected'."""
        return True
    
    async def disconnect(self):
        """Nothing to disconnect for file indexer."""
        pass
    
    async def create_index_if_not_exists(self, index_name: str, document_type: str) -> bool:
        """For file indexer, this just ensures the directory exists."""
        index_dir = self.output_dir / index_name
        index_dir.mkdir(parents=True, exist_ok=True)
        return True
    
    async def index_batch(self, documents: List[TransformedDocument]) -> Tuple[int, List[str]]:
        """Write documents to files."""
        if not documents:
            return 0, []
        
        success_count = 0
        failed_docs = []
        
        # Group by index name
        docs_by_index = {}
        for doc in documents:
            if doc.index_name not in docs_by_index:
                docs_by_index[doc.index_name] = []
            docs_by_index[doc.index_name].append(doc)
        
        for index_name, index_docs in docs_by_index.items():
            try:
                index_dir = self.output_dir / index_name
                
                if self.format == 'jsonl':
                    # Write as JSONL
                    file_path = index_dir / f'documents_{int(time.time())}.jsonl'
                    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                        for doc in index_docs:
                            await f.write(json.dumps(doc.document, ensure_ascii=False) + '\n')
                            success_count += 1
                else:
                    # Write as individual JSON files
                    for doc in index_docs:
                        file_path = index_dir / f'{doc.document_id}.json'
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                            await f.write(json.dumps(doc.document, ensure_ascii=False, indent=2))
                            success_count += 1
                
                logger.info(f"Wrote {len(index_docs)} documents to {index_dir}")
                
            except Exception as e:
                logger.error(f"Error writing documents to {index_name}: {e}")
                failed_docs.extend([doc.document_id for doc in index_docs])
        
        return success_count, failed_docs


class IndexerFactory:
    """Factory for creating indexers."""
    
    _indexers = {
        'elasticsearch': ElasticsearchIndexer,
        'opensearch': ElasticsearchIndexer,  # Same as Elasticsearch
        'file': FileIndexer,
        'json': FileIndexer,
        'jsonl': FileIndexer
    }
    
    @classmethod
    def create_indexer(cls, config: IndexingConfig) -> BaseIndexer:
        """Create an indexer for the specified platform."""
        
        platform = config.platform.lower()
        if platform not in cls._indexers:
            raise ValueError(f"Unsupported indexer platform: {platform}")
        
        indexer_class = cls._indexers[platform]
        return indexer_class(config)
    
    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """Get list of supported indexer platforms."""
        return list(cls._indexers.keys())


class IndexingPipeline:
    """Complete indexing pipeline orchestrator."""
    
    def __init__(self, configs: List[IndexingConfig]):
        self.configs = configs
        self.indexers = [IndexerFactory.create_indexer(config) for config in configs]
    
    async def run_full_pipeline(self) -> List[IndexingResult]:
        """Run the complete indexing pipeline."""
        
        logger.info("Starting full indexing pipeline")
        
        # Extract data
        extractor = CwayDataExtractor()
        
        try:
            await extractor.initialize()
            
            # Collect all documents
            documents = []
            async for doc in extractor.extract_all_data():
                documents.append(doc)
            
            logger.info(f"Extracted {len(documents)} documents for indexing")
            
            if not documents:
                logger.warning("No documents extracted, skipping indexing")
                return []
            
            # Index to all configured platforms
            results = []
            for indexer in self.indexers:
                logger.info(f"Indexing to {indexer.platform}")
                result = await indexer.index_documents(documents)
                results.append(result)
                
                if result.success:
                    logger.info(f"✅ Successfully indexed {result.documents_indexed} documents to {result.platform}")
                else:
                    logger.error(f"❌ Failed to index to {result.platform}: {result.error_message}")
            
            return results
            
        finally:
            await extractor.cleanup()
    
    async def run_incremental_pipeline(self, since: Optional[str] = None) -> List[IndexingResult]:
        """Run incremental indexing pipeline."""
        # TODO: Implement incremental indexing based on timestamp
        logger.info("Incremental indexing not yet implemented, running full pipeline")
        return await self.run_full_pipeline()


# Example configurations
EXAMPLE_CONFIGS = [
    # Elasticsearch
    IndexingConfig(
        platform='elasticsearch',
        connection_config={
            'url': 'http://localhost:9200',
            'auth': None,  # ('username', 'password')
            'api_key': None,
            'verify_ssl': True
        },
        transformer_config={'index_prefix': 'cway'},
        batch_size=50
    ),
    
    # File output
    IndexingConfig(
        platform='file',
        connection_config={
            'output_dir': 'indexed_data',
            'format': 'jsonl'
        },
        transformer_config={'flatten_metadata': True},
        batch_size=100
    )
]