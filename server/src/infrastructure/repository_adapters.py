"""Repository adapters to bridge Cway repositories with domain interfaces."""

from typing import List, Optional
from datetime import datetime
from ..domain.entities import Project, User
from ..domain.repository_interfaces import ProjectRepository, UserRepository
from ..infrastructure.cway_repositories import CwayProjectRepository, CwayUserRepository
from ..domain.cway_entities import PlannerProject, CwayUser


class CwayProjectRepositoryAdapter(ProjectRepository):
    """Adapter to convert CwayProject entities to domain Project entities."""
    
    def __init__(self, cway_project_repo: CwayProjectRepository):
        self.cway_project_repo = cway_project_repo
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects converted to domain entities."""
        cway_projects = await self.cway_project_repo.get_planner_projects()
        return [self._convert_to_domain_project(cp) for cp in cway_projects]
    
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID."""
        cway_project = await self.cway_project_repo.find_project_by_id(project_id)
        if cway_project:
            return self._convert_to_domain_project(cway_project)
        return None
    
    async def get_active_projects(self) -> List[Project]:
        """Get active projects only."""
        cway_projects = await self.cway_project_repo.get_active_projects()
        return [self._convert_to_domain_project(cp) for cp in cway_projects]
    
    async def get_completed_projects(self) -> List[Project]:
        """Get completed projects only.""" 
        cway_projects = await self.cway_project_repo.get_completed_projects()
        return [self._convert_to_domain_project(cp) for cp in cway_projects]
    
    def _convert_to_domain_project(self, cway_project: PlannerProject) -> Project:
        """Convert CwayProject to domain Project entity with comprehensive temporal data."""
        from datetime import datetime
        from ..domain.entities import TemporalMetadata, ProjectState
        
        # Convert timestamps
        created_at = getattr(cway_project, 'createdAt', None)
        updated_at = getattr(cway_project, 'updatedAt', None)
        
        if created_at is None:
            created_at = datetime.now()
        if updated_at is None:
            updated_at = created_at
            
        # Extract comprehensive project history for temporal analysis
        project_history = []
        activity_log = []
        
        if hasattr(cway_project, 'histories') and cway_project.histories:
            for history_item in cway_project.histories:
                if hasattr(history_item, 'timestamp'):
                    try:
                        # Parse timestamp
                        if isinstance(history_item.timestamp, str):
                            timestamp_str = history_item.timestamp
                        else:
                            timestamp_str = str(history_item.timestamp)
                            
                        activity_entry = {
                            'timestamp': timestamp_str,
                            'type': getattr(history_item, 'action', 'update'),
                            'description': getattr(history_item, 'description', 'Project activity'),
                            'user_id': getattr(history_item, 'user_id', None),
                            'metadata': {
                                'source': 'cway_history',
                                'original_data': str(history_item)
                            }
                        }
                        
                        project_history.append(activity_entry)
                        activity_log.append(activity_entry)
                        
                    except (ValueError, AttributeError) as e:
                        # Skip invalid history items
                        continue
        
        # If no structured history, create entries from available data
        if not project_history:
            # Create initial project creation entry
            creation_entry = {
                'timestamp': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                'type': 'project_created',
                'description': f'Project "{cway_project.name}" created',
                'user_id': None,
                'metadata': {'source': 'inferred'}
            }
            project_history.append(creation_entry)
            activity_log.append(creation_entry)
            
            # Create progress update entry if project has progress
            if cway_project.percentageDone and cway_project.percentageDone > 0:
                progress_entry = {
                    'timestamp': updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at),
                    'type': 'progress_update',
                    'description': f'Project progress: {cway_project.percentageDone*100:.1f}% complete',
                    'user_id': None,
                    'metadata': {
                        'source': 'inferred',
                        'completion_percentage': cway_project.percentageDone * 100
                    }
                }
                project_history.append(progress_entry)
                activity_log.append(progress_entry)
        
        # Create temporal metadata
        temporal_metadata = TemporalMetadata(
            created_at=created_at,
            updated_at=updated_at,
            version=1,
            activity_count=len(activity_log)
        )
        
        # Set lifecycle timestamps based on project state
        if cway_project.state:
            if cway_project.state.value == 'IN_PROGRESS':
                temporal_metadata.started_at = created_at
            elif cway_project.state.value == 'COMPLETED':
                temporal_metadata.completed_at = updated_at
            elif cway_project.state.value == 'CANCELLED':
                temporal_metadata.cancelled_at = updated_at
        
        # Set activity tracking
        if activity_log:
            # Sort activities by timestamp
            sorted_activities = sorted(activity_log, key=lambda x: x['timestamp'])
            temporal_metadata.first_activity_at = self._parse_timestamp(sorted_activities[0]['timestamp'])
            temporal_metadata.last_activity_at = self._parse_timestamp(sorted_activities[-1]['timestamp'])
        
        # Convert project state
        project_state = None
        if cway_project.state:
            try:
                project_state = ProjectState(cway_project.state.value)
            except ValueError:
                # If state doesn't match enum, map it
                state_mapping = {
                    'IN_PROGRESS': ProjectState.IN_PROGRESS,
                    'COMPLETED': ProjectState.COMPLETED,
                    'CANCELLED': ProjectState.CANCELLED,
                    'PLANNED': ProjectState.PLANNED,
                    'DELIVERED': ProjectState.DELIVERED
                }
                project_state = state_mapping.get(cway_project.state.value, ProjectState.ACTIVE)
        
        # Format dates as ISO strings
        start_date = None
        end_date = None
        
        if cway_project.startDate:
            start_date = str(cway_project.startDate) if hasattr(cway_project.startDate, '__str__') else cway_project.startDate
        if cway_project.endDate:
            end_date = str(cway_project.endDate) if hasattr(cway_project.endDate, '__str__') else cway_project.endDate
        
        return Project(
            id=cway_project.id,
            name=cway_project.name,
            description=getattr(cway_project, 'description', ''),
            status=cway_project.state.value if cway_project.state else 'ACTIVE',
            state=project_state,
            completion_percentage=cway_project.percentageDone * 100 if cway_project.percentageDone else 0,
            start_date=start_date,
            end_date=end_date,
            planned_start_date=start_date,  # Use same as start_date if no separate planning data
            planned_end_date=end_date,      # Use same as end_date if no separate planning data
            created_at=created_at,
            updated_at=updated_at,
            temporal_metadata=temporal_metadata,
            project_history=project_history,
            activity_log=activity_log,
            assignees=getattr(cway_project, 'assignees', []),
            tags=getattr(cway_project, 'tags', []),
            priority=getattr(cway_project, 'priority', 'MEDIUM'),
            organization_id=getattr(cway_project, 'organization_id', None)
        )
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        from datetime import datetime
        
        try:
            # Try parsing ISO format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Try parsing as datetime string
                return datetime.fromisoformat(timestamp_str)
            except (ValueError, AttributeError):
                # Return current time as fallback
                return datetime.now()


class CwayUserRepositoryAdapter(UserRepository):
    """Adapter to convert CwayUser entities to domain User entities."""
    
    def __init__(self, cway_user_repo: CwayUserRepository):
        self.cway_user_repo = cway_user_repo
    
    async def get_all_users(self) -> List[User]:
        """Get all users converted to domain entities."""
        cway_users = await self.cway_user_repo.find_all_users()
        return [self._convert_to_domain_user(cu) for cu in cway_users]
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a specific user by ID."""
        cway_user = await self.cway_user_repo.find_user_by_id(user_id)
        if cway_user:
            return self._convert_to_domain_user(cway_user)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        cway_user = await self.cway_user_repo.find_user_by_email(email)
        if cway_user:
            return self._convert_to_domain_user(cway_user)
        return None
    
    def _convert_to_domain_user(self, cway_user: CwayUser) -> User:
        """Convert CwayUser to domain User entity with temporal metadata."""
        from datetime import datetime
        from ..domain.entities import TemporalMetadata
        
        # Convert timestamps
        created_at = getattr(cway_user, 'createdAt', None)
        if created_at is None:
            created_at = datetime.now()
        elif isinstance(created_at, int):
            # Convert Unix timestamp to datetime
            created_at = datetime.fromtimestamp(created_at)
            
        updated_at = getattr(cway_user, 'updatedAt', created_at)
        
        # Create temporal metadata
        temporal_metadata = TemporalMetadata(
            created_at=created_at,
            updated_at=updated_at,
            version=1,
            activity_count=0  # Will be updated as user activities are tracked
        )
        
        # Determine role mapping
        role_mapping = {
            'ADMIN': 'admin',
            'USER': 'user', 
            'VIEWER': 'viewer',
            'MANAGER': 'manager',
            'REVIEWER': 'reviewer'
        }
        
        user_role = getattr(cway_user, 'role', 'USER')
        mapped_role = role_mapping.get(user_role.upper(), 'user')
        
        return User(
            id=cway_user.id,
            email=cway_user.email,
            name=cway_user.full_name,
            username=cway_user.username,
            role=mapped_role,
            is_active=cway_user.enabled,
            first_name=cway_user.firstName,
            last_name=cway_user.lastName,
            display_name=cway_user.full_name,
            created_at=created_at,
            updated_at=updated_at,
            temporal_metadata=temporal_metadata,
            login_count=0,  # Will be updated as login activities are tracked
            notification_preferences={
                'email_notifications': True,
                'push_notifications': True,
                'review_reminders': True
            }
        )
