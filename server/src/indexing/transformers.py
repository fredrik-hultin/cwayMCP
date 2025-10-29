"""Data transformers for different indexing platforms and formats."""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging

from .data_extractor import IndexableDocument

logger = logging.getLogger(__name__)


@dataclass
class TransformedDocument:
    """Document transformed for a specific indexing platform."""
    
    platform: str  # 'elasticsearch', 'opensearch', 'solr', 'algolia', 'pinecone'
    document: Dict[str, Any]
    index_name: str
    document_id: str
    routing_key: Optional[str] = None
    bulk_operation: Optional[str] = None  # 'index', 'create', 'update'


class BaseTransformer(ABC):
    """Base class for document transformers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.platform_name = self.__class__.__name__.lower().replace('transformer', '')
    
    @abstractmethod
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform an indexable document for the target platform."""
        pass
    
    @abstractmethod
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get the appropriate index name for the document."""
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean text for indexing."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def prepare_embedding_vector(self, vector: Optional[List[float]]) -> Optional[List[float]]:
        """Prepare embedding vector for indexing."""
        if not vector:
            return None
        
        # Ensure vector is valid
        if not all(isinstance(x, (int, float)) for x in vector):
            logger.warning("Invalid embedding vector format")
            return None
        
        return vector


class ElasticsearchTransformer(BaseTransformer):
    """Transform documents for Elasticsearch indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.index_prefix = self.config.get('index_prefix', 'cway')
        self.date_format = self.config.get('date_format', 'strict_date_optional_time')
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get Elasticsearch index name."""
        doc_type = doc.document_type.replace('_', '-')
        timestamp = datetime.now().strftime('%Y-%m')
        return f"{self.index_prefix}-{doc_type}-{timestamp}"
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document for Elasticsearch."""
        
        # Base document structure
        es_doc = {
            "@timestamp": doc.updated_at.isoformat(),
            "document_id": doc.id,
            "document_type": doc.document_type,
            "title": self.clean_text(doc.title),
            "content": self.clean_text(doc.content),
            "tags": doc.tags,
            "url": doc.url,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
            "metadata": doc.metadata
        }
        
        # Add embedding vector if available
        if doc.embedding_vector:
            es_doc["embedding_vector"] = self.prepare_embedding_vector(doc.embedding_vector)
        
        # Add document-type specific fields
        if doc.document_type == "project":
            es_doc.update({
                "project_id": doc.metadata.get("project_id"),
                "project_state": doc.metadata.get("state"),
                "progress_percentage": doc.metadata.get("progress_percentage", 0),
                "is_active": doc.metadata.get("is_active", False),
                "is_completed": doc.metadata.get("is_completed", False),
                "start_date": doc.metadata.get("start_date"),
                "end_date": doc.metadata.get("end_date")
            })
        
        elif doc.document_type == "user":
            es_doc.update({
                "user_id": doc.metadata.get("user_id"),
                "email": doc.metadata.get("email"),
                "username": doc.metadata.get("username"),
                "enabled": doc.metadata.get("enabled", False),
                "is_sso": doc.metadata.get("is_sso", False)
            })
        
        elif doc.document_type in ["kpi", "temporal_kpi"]:
            es_doc.update({
                "generation_timestamp": doc.metadata.get("generation_timestamp"),
                "data_source": doc.metadata.get("data_source"),
                "extraction_method": doc.metadata.get("extraction_method")
            })
            
            # Add KPI-specific fields
            if "kpi_scores" in doc.metadata:
                es_doc["kpi_scores"] = doc.metadata["kpi_scores"]
            
            if "activity_distribution" in doc.metadata:
                es_doc["activity_distribution"] = doc.metadata["activity_distribution"]
        
        return TransformedDocument(
            platform="elasticsearch",
            document=es_doc,
            index_name=self.get_index_name(doc),
            document_id=doc.id,
            bulk_operation="index"
        )


class OpenSearchTransformer(BaseTransformer):
    """Transform documents for OpenSearch indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.index_prefix = self.config.get('index_prefix', 'cway')
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get OpenSearch index name."""
        doc_type = doc.document_type.replace('_', '-')
        return f"{self.index_prefix}-{doc_type}"
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document for OpenSearch (similar to Elasticsearch)."""
        
        # OpenSearch is compatible with Elasticsearch format
        es_transformer = ElasticsearchTransformer(self.config)
        es_result = es_transformer.transform(doc)
        
        # Modify for OpenSearch
        es_result.platform = "opensearch"
        es_result.index_name = self.get_index_name(doc)
        
        return es_result


class SolrTransformer(BaseTransformer):
    """Transform documents for Apache Solr indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.core_name = self.config.get('core_name', 'cway_documents')
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get Solr core name."""
        return self.core_name
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document for Solr."""
        
        # Solr document structure
        solr_doc = {
            "id": doc.id,
            "document_type_s": doc.document_type,
            "title_t": self.clean_text(doc.title),
            "content_txt": self.clean_text(doc.content),
            "tags_ss": doc.tags,
            "url_s": doc.url,
            "created_at_dt": doc.created_at.isoformat() + "Z",
            "updated_at_dt": doc.updated_at.isoformat() + "Z",
            "timestamp_dt": doc.updated_at.isoformat() + "Z"
        }
        
        # Add metadata fields with Solr naming conventions
        for key, value in doc.metadata.items():
            if isinstance(value, str):
                solr_doc[f"{key}_s"] = value
            elif isinstance(value, bool):
                solr_doc[f"{key}_b"] = value
            elif isinstance(value, int):
                solr_doc[f"{key}_i"] = value
            elif isinstance(value, float):
                solr_doc[f"{key}_f"] = value
            elif isinstance(value, list):
                solr_doc[f"{key}_ss"] = value
            elif isinstance(value, dict):
                # Convert dict to JSON string
                solr_doc[f"{key}_s"] = json.dumps(value)
        
        # Add document-type specific fields
        if doc.document_type == "project":
            solr_doc.update({
                "project_id_s": doc.metadata.get("project_id"),
                "project_state_s": doc.metadata.get("state"),
                "progress_percentage_f": float(doc.metadata.get("progress_percentage", 0)),
                "is_active_b": doc.metadata.get("is_active", False),
                "is_completed_b": doc.metadata.get("is_completed", False)
            })
        
        elif doc.document_type == "user":
            solr_doc.update({
                "user_id_s": doc.metadata.get("user_id"),
                "email_s": doc.metadata.get("email"),
                "username_s": doc.metadata.get("username"),
                "enabled_b": doc.metadata.get("enabled", False)
            })
        
        # Add embedding vector if available (as dense vector field)
        if doc.embedding_vector:
            solr_doc["embedding_vector"] = self.prepare_embedding_vector(doc.embedding_vector)
        
        return TransformedDocument(
            platform="solr",
            document=solr_doc,
            index_name=self.get_index_name(doc),
            document_id=doc.id,
            bulk_operation="add"
        )


class AlgoliaTransformer(BaseTransformer):
    """Transform documents for Algolia indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.index_prefix = self.config.get('index_prefix', 'cway')
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get Algolia index name."""
        return f"{self.index_prefix}_{doc.document_type}"
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document for Algolia."""
        
        # Algolia document structure
        algolia_doc = {
            "objectID": doc.id,
            "title": self.clean_text(doc.title),
            "content": self.clean_text(doc.content),
            "document_type": doc.document_type,
            "tags": doc.tags,
            "url": doc.url,
            "created_at": int(doc.created_at.timestamp()),
            "updated_at": int(doc.updated_at.timestamp()),
            "_timestamp": int(doc.updated_at.timestamp())
        }
        
        # Add searchable attributes
        searchable_content = [doc.title, doc.content]
        if doc.tags:
            searchable_content.extend(doc.tags)
        
        algolia_doc["_searchable_content"] = " ".join(filter(None, searchable_content))
        
        # Add filterable attributes from metadata
        filterable_fields = [
            "project_id", "user_id", "state", "enabled", "is_active", 
            "is_completed", "health_status", "risk_level", "data_source"
        ]
        
        for field in filterable_fields:
            if field in doc.metadata:
                algolia_doc[field] = doc.metadata[field]
        
        # Add numeric attributes for ranking
        numeric_fields = [
            "progress_percentage", "overall_score", "urgency_score",
            "total_projects", "total_users", "total_revisions"
        ]
        
        for field in numeric_fields:
            if field in doc.metadata:
                value = doc.metadata[field]
                if isinstance(value, (int, float)):
                    algolia_doc[field] = value
        
        # Add hierarchical categories for faceted search
        categories = [doc.document_type]
        if doc.document_type == "project":
            state = doc.metadata.get("state")
            if state:
                categories.append(f"project > {state}")
        elif doc.document_type == "kpi":
            categories.append("analytics > kpi")
        elif doc.document_type == "temporal_kpi":
            categories.append("analytics > temporal_kpi")
        
        algolia_doc["_categories"] = categories
        
        return TransformedDocument(
            platform="algolia",
            document=algolia_doc,
            index_name=self.get_index_name(doc),
            document_id=doc.id
        )


class PineconeTransformer(BaseTransformer):
    """Transform documents for Pinecone vector indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.index_name = self.config.get('index_name', 'cway-vectors')
        self.vector_dimension = self.config.get('vector_dimension', 1536)  # OpenAI embedding size
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get Pinecone index name."""
        return self.index_name
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document for Pinecone."""
        
        if not doc.embedding_vector:
            raise ValueError(f"Document {doc.id} missing embedding vector for Pinecone indexing")
        
        # Pinecone vector format
        pinecone_doc = {
            "id": doc.id,
            "values": self.prepare_embedding_vector(doc.embedding_vector),
            "metadata": {
                "document_type": doc.document_type,
                "title": self.clean_text(doc.title)[:500],  # Pinecone metadata size limits
                "content": self.clean_text(doc.content)[:1000],
                "tags": doc.tags,
                "url": doc.url,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "timestamp": int(doc.updated_at.timestamp())
            }
        }
        
        # Add key metadata fields (keeping under size limits)
        key_metadata_fields = [
            "project_id", "user_id", "state", "progress_percentage",
            "health_status", "risk_level", "data_source"
        ]
        
        for field in key_metadata_fields:
            if field in doc.metadata:
                value = doc.metadata[field]
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100]  # Truncate long strings
                pinecone_doc["metadata"][field] = value
        
        return TransformedDocument(
            platform="pinecone",
            document=pinecone_doc,
            index_name=self.get_index_name(doc),
            document_id=doc.id
        )


class GenericJSONTransformer(BaseTransformer):
    """Transform documents to generic JSON format."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.flatten_metadata = self.config.get('flatten_metadata', False)
    
    def get_index_name(self, doc: IndexableDocument) -> str:
        """Get generic index name."""
        return f"cway_{doc.document_type}"
    
    def transform(self, doc: IndexableDocument) -> TransformedDocument:
        """Transform document to generic JSON."""
        
        json_doc = {
            "id": doc.id,
            "document_type": doc.document_type,
            "title": self.clean_text(doc.title),
            "content": self.clean_text(doc.content),
            "tags": doc.tags,
            "url": doc.url,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
            "timestamp": int(doc.updated_at.timestamp())
        }
        
        if self.flatten_metadata:
            # Flatten metadata into root level
            json_doc.update(doc.metadata)
        else:
            json_doc["metadata"] = doc.metadata
        
        if doc.embedding_vector:
            json_doc["embedding_vector"] = self.prepare_embedding_vector(doc.embedding_vector)
        
        return TransformedDocument(
            platform="json",
            document=json_doc,
            index_name=self.get_index_name(doc),
            document_id=doc.id
        )


class TransformerFactory:
    """Factory for creating document transformers."""
    
    _transformers = {
        'elasticsearch': ElasticsearchTransformer,
        'opensearch': OpenSearchTransformer,
        'solr': SolrTransformer,
        'algolia': AlgoliaTransformer,
        'pinecone': PineconeTransformer,
        'json': GenericJSONTransformer,
        'file': GenericJSONTransformer  # File storage uses JSON format
    }
    
    @classmethod
    def create_transformer(cls, platform: str, config: Optional[Dict[str, Any]] = None) -> BaseTransformer:
        """Create a transformer for the specified platform."""
        
        platform = platform.lower()
        if platform not in cls._transformers:
            raise ValueError(f"Unsupported platform: {platform}. Supported: {list(cls._transformers.keys())}")
        
        transformer_class = cls._transformers[platform]
        return transformer_class(config)
    
    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """Get list of supported platforms."""
        return list(cls._transformers.keys())


def transform_batch(
    documents: List[IndexableDocument],
    platform: str,
    config: Optional[Dict[str, Any]] = None
) -> List[TransformedDocument]:
    """Transform a batch of documents for the specified platform."""
    
    transformer = TransformerFactory.create_transformer(platform, config)
    transformed_docs = []
    
    for doc in documents:
        try:
            transformed = transformer.transform(doc)
            transformed_docs.append(transformed)
        except Exception as e:
            logger.error(f"Error transforming document {doc.id} for {platform}: {e}")
    
    return transformed_docs


# Example configurations for different platforms
PLATFORM_CONFIGS = {
    'elasticsearch': {
        'index_prefix': 'cway',
        'date_format': 'strict_date_optional_time'
    },
    'opensearch': {
        'index_prefix': 'cway'
    },
    'solr': {
        'core_name': 'cway_documents'
    },
    'algolia': {
        'index_prefix': 'cway'
    },
    'pinecone': {
        'index_name': 'cway-vectors',
        'vector_dimension': 1536
    },
    'json': {
        'flatten_metadata': True
    },
    'file': {
        'flatten_metadata': True
    }
}
