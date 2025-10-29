"""Enhanced domain entities with comprehensive temporal data storage."""

import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class CwayEntity:
    """Base entity for all Cway domain objects."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.id:
            raise ValueError("Entity ID cannot be empty")
            
    def __eq__(self, other: object) -> bool:
        """Compare entities by ID."""
        if not isinstance(other, CwayEntity):
            return NotImplemented
        return self.id == other.id
        
    def __hash__(self) -> int:
        """Hash entities by ID for use in sets and dicts."""
        return hash(self.id)


class ProjectState(Enum):
    """Project state enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE" 
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    ARCHIVED = "ARCHIVED"


class ArtworkType(Enum):
    """Artwork type enumeration."""
    DIGITAL_ART = "DIGITAL_ART"
    PRINT = "PRINT"
    DESIGN = "DESIGN"
    ILLUSTRATION = "ILLUSTRATION"
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    OTHER = "OTHER"


class RevisionStatus(Enum):
    """Revision status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_REVIEW = "IN_REVIEW"
    ARCHIVED = "ARCHIVED"


@dataclass
class TemporalMetadata:
    """Temporal metadata for tracking entity lifecycle."""
    
    created_at: datetime
    updated_at: datetime
    version: int = 1
    created_by: Optional[str] = None  # User ID
    updated_by: Optional[str] = None  # User ID
    timezone: Optional[str] = None
    
    # Activity tracking
    first_activity_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    activity_count: int = 0
    
    # Lifecycle timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    def update_activity(self, timestamp: Optional[datetime] = None) -> None:
        """Update activity tracking."""
        if timestamp is None:
            timestamp = datetime.now()
            
        if self.first_activity_at is None:
            self.first_activity_at = timestamp
        
        self.last_activity_at = timestamp
        self.activity_count += 1
        self.updated_at = timestamp


@dataclass
class Project(CwayEntity):
    """Enhanced project entity with comprehensive temporal data."""
    
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"
    state: Optional[ProjectState] = None
    
    # Progress tracking
    completion_percentage: float = 0.0
    milestone_count: int = 0
    completed_milestones: int = 0
    
    # Temporal data
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None    # ISO format
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    
    # Temporal metadata
    temporal_metadata: Optional[TemporalMetadata] = None
    
    # Project history and activity
    project_history: List[Dict[str, Any]] = field(default_factory=list)
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    revision_history: List[str] = field(default_factory=list)  # Revision IDs
    
    # Team and assignment data
    assignees: List[str] = field(default_factory=list)  # User IDs
    team_members: List[str] = field(default_factory=list)  # User IDs
    owner_id: Optional[str] = None
    
    # Classification
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    priority: str = "MEDIUM"
    
    # Related entities
    artworks: List[str] = field(default_factory=list)  # Artwork IDs
    organization_id: Optional[str] = None
    
    # Metrics for temporal analysis
    total_work_hours: float = 0.0
    estimated_work_hours: float = 0.0
    time_spent_per_phase: Dict[str, float] = field(default_factory=dict)
    
    VALID_STATUSES = {
        "ACTIVE", "INACTIVE", "COMPLETED", "CANCELLED", 
        "PLANNED", "IN_PROGRESS", "DELIVERED", "ARCHIVED"
    }
    
    def __post_init__(self) -> None:
        """Validate and initialize project."""
        super().__post_init__()
        
        if not self.name:
            raise ValueError("Project name cannot be empty")
            
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of {self.VALID_STATUSES}, got: {self.status}")
        
        # Initialize temporal metadata if not provided
        if self.temporal_metadata is None:
            self.temporal_metadata = TemporalMetadata(
                created_at=self.created_at,
                updated_at=self.updated_at
            )
    
    def add_activity(self, activity_type: str, description: str, user_id: Optional[str] = None, 
                    timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add activity to project history."""
        if timestamp is None:
            timestamp = datetime.now()
            
        activity = {
            "timestamp": timestamp.isoformat(),
            "type": activity_type,
            "description": description,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        self.activity_log.append(activity)
        self.project_history.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(timestamp)
    
    def update_progress(self, percentage: float, user_id: Optional[str] = None) -> None:
        """Update project completion percentage."""
        old_percentage = self.completion_percentage
        self.completion_percentage = max(0, min(100, percentage))
        
        self.add_activity(
            "progress_update",
            f"Progress updated from {old_percentage:.1f}% to {percentage:.1f}%",
            user_id,
            metadata={"old_percentage": old_percentage, "new_percentage": percentage}
        )


@dataclass
class Artwork(CwayEntity):
    """Enhanced artwork entity with comprehensive temporal data."""
    
    name: str
    project_id: str  # Parent project ID
    artwork_type: ArtworkType = ArtworkType.OTHER
    description: Optional[str] = None
    
    # File information
    file_path: Optional[str] = None
    file_size: Optional[int] = None  # bytes
    file_format: Optional[str] = None  # e.g., "PNG", "JPEG", "AI"
    dimensions: Optional[Dict[str, Any]] = None  # width, height, etc.
    
    # Version control
    current_version: int = 1
    version_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Temporal metadata
    temporal_metadata: Optional[TemporalMetadata] = None
    
    # Revision tracking
    revisions: List[str] = field(default_factory=list)  # Revision IDs
    current_revision_id: Optional[str] = None
    pending_revisions: List[str] = field(default_factory=list)
    approved_revisions: List[str] = field(default_factory=list)
    rejected_revisions: List[str] = field(default_factory=list)
    
    # Activity tracking
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    last_modified_by: Optional[str] = None  # User ID
    
    # Creative process tracking
    creation_time_minutes: float = 0.0
    revision_time_minutes: float = 0.0
    approval_time_minutes: float = 0.0
    
    # Collaboration data
    collaborators: List[str] = field(default_factory=list)  # User IDs
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Status and workflow
    status: str = "DRAFT"
    workflow_stage: Optional[str] = None
    approval_required: bool = True
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    VALID_STATUSES = {
        "DRAFT", "IN_REVIEW", "APPROVED", "REJECTED", 
        "PUBLISHED", "ARCHIVED", "DELETED"
    }
    
    def __post_init__(self) -> None:
        """Validate and initialize artwork."""
        super().__post_init__()
        
        if not self.name:
            raise ValueError("Artwork name cannot be empty")
            
        if not self.project_id:
            raise ValueError("Artwork must belong to a project")
            
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of {self.VALID_STATUSES}, got: {self.status}")
            
        # Initialize temporal metadata if not provided
        if self.temporal_metadata is None:
            self.temporal_metadata = TemporalMetadata(
                created_at=self.created_at,
                updated_at=self.updated_at
            )
    
    def add_revision(self, revision_id: str, user_id: Optional[str] = None) -> None:
        """Add a new revision to the artwork."""
        self.revisions.append(revision_id)
        self.current_revision_id = revision_id
        self.current_version += 1
        
        timestamp = datetime.now()
        
        version_entry = {
            "version": self.current_version,
            "revision_id": revision_id,
            "timestamp": timestamp.isoformat(),
            "user_id": user_id
        }
        self.version_history.append(version_entry)
        
        activity = {
            "timestamp": timestamp.isoformat(),
            "type": "revision_created",
            "description": f"New revision created (version {self.current_version})",
            "user_id": user_id,
            "metadata": {"revision_id": revision_id, "version": self.current_version}
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(timestamp)
    
    def approve_revision(self, revision_id: str, user_id: Optional[str] = None) -> None:
        """Approve a revision."""
        if revision_id in self.pending_revisions:
            self.pending_revisions.remove(revision_id)
        
        if revision_id not in self.approved_revisions:
            self.approved_revisions.append(revision_id)
            
        timestamp = datetime.now()
        activity = {
            "timestamp": timestamp.isoformat(),
            "type": "revision_approved",
            "description": f"Revision {revision_id} approved",
            "user_id": user_id,
            "metadata": {"revision_id": revision_id}
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(timestamp)


@dataclass
class Revision(CwayEntity):
    """Enhanced revision entity with comprehensive temporal data."""
    
    artwork_id: str  # Parent artwork ID
    version_number: int
    revision_type: str = "CONTENT"  # CONTENT, STYLE, FORMAT, etc.
    status: RevisionStatus = RevisionStatus.PENDING
    
    # Content information
    title: Optional[str] = None
    description: Optional[str] = None
    changes_summary: Optional[str] = None
    
    # File information
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    file_hash: Optional[str] = None  # For integrity checking
    
    # Temporal metadata
    temporal_metadata: Optional[TemporalMetadata] = None
    
    # Review and approval workflow
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    
    # People involved
    submitted_by: Optional[str] = None  # User ID
    reviewed_by: Optional[str] = None   # User ID
    approved_by: Optional[str] = None   # User ID
    rejected_by: Optional[str] = None   # User ID
    
    # Feedback and comments
    feedback: List[Dict[str, Any]] = field(default_factory=list)
    reviewer_comments: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Activity tracking
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Time tracking
    time_to_review_minutes: Optional[float] = None
    time_to_approve_minutes: Optional[float] = None
    total_lifecycle_minutes: Optional[float] = None
    
    # Comparison data (for diff analysis)
    changes_from_previous: Optional[Dict[str, Any]] = None
    comparison_metrics: Optional[Dict[str, Any]] = None
    
    # Metadata
    priority: str = "MEDIUM"
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate and initialize revision."""
        super().__post_init__()
        
        if not self.artwork_id:
            raise ValueError("Revision must belong to an artwork")
            
        if self.version_number < 1:
            raise ValueError("Version number must be positive")
            
        # Initialize temporal metadata if not provided
        if self.temporal_metadata is None:
            self.temporal_metadata = TemporalMetadata(
                created_at=self.created_at,
                updated_at=self.updated_at
            )
            
        # Set submission timestamp if not set
        if self.submitted_at is None:
            self.submitted_at = self.created_at
    
    def submit_for_review(self, user_id: str) -> None:
        """Submit revision for review."""
        self.status = RevisionStatus.IN_REVIEW
        self.submitted_by = user_id
        self.submitted_at = datetime.now()
        
        activity = {
            "timestamp": self.submitted_at.isoformat(),
            "type": "submitted_for_review",
            "description": "Revision submitted for review",
            "user_id": user_id,
            "metadata": {"version": self.version_number}
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(self.submitted_at)
    
    def approve(self, user_id: str, comments: Optional[str] = None) -> None:
        """Approve the revision."""
        now = datetime.now()
        
        self.status = RevisionStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = now
        self.reviewed_at = now
        self.reviewed_by = user_id
        
        if comments:
            self.reviewer_comments = comments
            
        # Calculate time metrics
        if self.submitted_at:
            self.time_to_approve_minutes = (now - self.submitted_at).total_seconds() / 60
            self.total_lifecycle_minutes = (now - self.created_at).total_seconds() / 60
        
        activity = {
            "timestamp": now.isoformat(),
            "type": "approved",
            "description": "Revision approved",
            "user_id": user_id,
            "metadata": {
                "comments": comments,
                "time_to_approve_minutes": self.time_to_approve_minutes
            }
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(now)
    
    def reject(self, user_id: str, reason: str, comments: Optional[str] = None) -> None:
        """Reject the revision."""
        now = datetime.now()
        
        self.status = RevisionStatus.REJECTED
        self.rejected_by = user_id
        self.rejected_at = now
        self.reviewed_at = now
        self.reviewed_by = user_id
        self.rejection_reason = reason
        
        if comments:
            self.reviewer_comments = comments
            
        # Calculate time metrics
        if self.submitted_at:
            self.time_to_review_minutes = (now - self.submitted_at).total_seconds() / 60
            self.total_lifecycle_minutes = (now - self.created_at).total_seconds() / 60
            
        activity = {
            "timestamp": now.isoformat(),
            "type": "rejected",
            "description": f"Revision rejected: {reason}",
            "user_id": user_id,
            "metadata": {
                "reason": reason,
                "comments": comments,
                "time_to_review_minutes": self.time_to_review_minutes
            }
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(now)
    
    def add_feedback(self, user_id: str, feedback_text: str, feedback_type: str = "COMMENT") -> None:
        """Add feedback to the revision."""
        timestamp = datetime.now()
        
        feedback_entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "feedback_type": feedback_type,
            "text": feedback_text,
            "id": f"feedback_{len(self.feedback) + 1}"
        }
        self.feedback.append(feedback_entry)
        
        activity = {
            "timestamp": timestamp.isoformat(),
            "type": "feedback_added",
            "description": f"Feedback added: {feedback_type}",
            "user_id": user_id,
            "metadata": {"feedback_type": feedback_type, "feedback_id": feedback_entry["id"]}
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(timestamp)


@dataclass
class User(CwayEntity):
    """Enhanced user entity with temporal activity tracking."""
    
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    
    # Extended user information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Temporal metadata
    temporal_metadata: Optional[TemporalMetadata] = None
    
    # Activity tracking
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Work tracking
    projects_assigned: List[str] = field(default_factory=list)  # Project IDs
    artworks_created: List[str] = field(default_factory=list)   # Artwork IDs
    revisions_submitted: List[str] = field(default_factory=list) # Revision IDs
    revisions_reviewed: List[str] = field(default_factory=list)  # Revision IDs
    
    # Performance metrics
    total_work_hours: float = 0.0
    avg_revision_time_minutes: Optional[float] = None
    avg_review_time_minutes: Optional[float] = None
    approval_rate: Optional[float] = None  # Percentage of revisions approved
    
    # Preferences and settings
    timezone: Optional[str] = None
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    
    VALID_ROLES = {"admin", "user", "viewer", "reviewer", "manager"}
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __post_init__(self) -> None:
        """Validate and initialize user."""
        super().__post_init__()
        
        if not self.email:
            raise ValueError("User email cannot be empty")
            
        if not self.EMAIL_REGEX.match(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
            
        if self.role not in self.VALID_ROLES:
            raise ValueError(f"Role must be one of {self.VALID_ROLES}, got: {self.role}")
            
        # Initialize temporal metadata if not provided
        if self.temporal_metadata is None:
            self.temporal_metadata = TemporalMetadata(
                created_at=self.created_at,
                updated_at=self.updated_at
            )
            
        # Set display name if not provided
        if not self.display_name:
            if self.first_name and self.last_name:
                self.display_name = f"{self.first_name} {self.last_name}"
            elif self.name:
                self.display_name = self.name
            else:
                self.display_name = self.username or self.email.split('@')[0]
    
    def log_activity(self, activity_type: str, description: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log user activity."""
        timestamp = datetime.now()
        
        activity = {
            "timestamp": timestamp.isoformat(),
            "type": activity_type,
            "description": description,
            "metadata": metadata or {}
        }
        self.activity_log.append(activity)
        
        if self.temporal_metadata:
            self.temporal_metadata.update_activity(timestamp)
    
    def record_login(self) -> None:
        """Record user login."""
        self.last_login_at = datetime.now()
        self.login_count += 1
        
        self.log_activity(
            "login",
            "User logged in",
            {"login_count": self.login_count}
        )
    
    def calculate_performance_metrics(self, revisions: List[Revision]) -> None:
        """Calculate performance metrics based on user's revisions."""
        user_revisions = [r for r in revisions if r.submitted_by == self.id or r.reviewed_by == self.id]
        
        if not user_revisions:
            return
            
        # Calculate average revision time for submitted revisions
        submitted_revisions = [r for r in user_revisions if r.submitted_by == self.id]
        if submitted_revisions:
            creation_times = []
            for rev in submitted_revisions:
                if rev.submitted_at and rev.created_at:
                    creation_time = (rev.submitted_at - rev.created_at).total_seconds() / 60
                    creation_times.append(creation_time)
            
            if creation_times:
                self.avg_revision_time_minutes = sum(creation_times) / len(creation_times)
        
        # Calculate average review time for reviewed revisions
        reviewed_revisions = [r for r in user_revisions if r.reviewed_by == self.id]
        if reviewed_revisions:
            review_times = []
            approved_count = 0
            
            for rev in reviewed_revisions:
                if rev.time_to_review_minutes is not None:
                    review_times.append(rev.time_to_review_minutes)
                
                if rev.status == RevisionStatus.APPROVED:
                    approved_count += 1
            
            if review_times:
                self.avg_review_time_minutes = sum(review_times) / len(review_times)
            
            if reviewed_revisions:
                self.approval_rate = (approved_count / len(reviewed_revisions)) * 100
