"""
Media Repository - Handles media center, file, and folder operations.

Single Responsibility: Media and file data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MediaRepository(BaseRepository):
    """Repository for media center and file operations."""
    
    async def get_folder_tree(self) -> List[Dict[str, Any]]:
        """Get the complete folder tree structure."""
        query = """
        query GetFolderTree {
            tree {
                id
                name
                children {
                    id
                    name
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("tree", [])
            
        except Exception as e:
            logger.error(f"Failed to get folder tree: {e}")
            raise CwayAPIError(f"Failed to get folder tree: {e}")
    
    async def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific folder by ID."""
        query = """
        query GetFolder($id: UUID!) {
            folder(id: $id) {
                id
                name
                description
                parentId
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": folder_id})
            return result.get("folder")
            
        except Exception as e:
            logger.error(f"Failed to get folder: {e}")
            raise CwayAPIError(f"Failed to get folder: {e}")
    
    async def get_folder_items(self, folder_id: str, page: int = 0, 
                              size: int = 20) -> Dict[str, Any]:
        """Get items in a specific folder with pagination."""
        query = """
        query GetFolderItems($input: FindFolderItemInput!, $paging: Paging) {
            itemsForFolder(input: $input, paging: $paging) {
                items {
                    id
                    name
                    type
                }
                totalHits
                page
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {
                "input": {"folderId": folder_id},
                "paging": {"page": page, "pageSize": size},
                "size": size,  # Legacy support
            })
            return result.get("itemsForFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to get folder items: {e}")
            raise CwayAPIError(f"Failed to get folder items: {e}")
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a file by UUID."""
        query = """
        query GetFile($id: UUID!) {
            file(id: $id) {
                id
                name
                fileSize
                mimeType
                url
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": file_id})
            return result.get("file")
            
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            raise CwayAPIError(f"Failed to get file: {e}")
    
    async def search_media_center(
        self,
        query_text: Optional[str] = None,
        folder_id: Optional[str] = None,
        content_type: Optional[str] = None,
        date_from: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search media center with filters."""
        
        if folder_id:
            # Search within specific folder
            query = """
            query SearchMediaCenter($input: FindFolderItemInput!, $paging: Paging) {
                itemsForFolder(input: $input, paging: $paging) {
                    items {
                        id
                        name
                        type
                        created
                        modifiedDate
                    }
                    totalHits
                    page
                }
            }
            """
            
            variables = {
                "input": {"folderId": folder_id},
                "paging": {"page": 0, "pageSize": limit}
            }
            
            if query_text:
                variables["input"]["query"] = query_text
            
        else:
            # Search across organization
            query = """
            query SearchMediaCenter($input: FindFolderItemsInOrganisationInput!, $paging: Paging) {
                itemsForOrganisation(input: $input, paging: $paging) {
                    items {
                        id
                        name
                        type
                        created
                        modifiedDate
                    }
                    totalHits
                    page
                }
            }
            """
            
            variables = {
                "input": {},
                "paging": {"page": 0, "pageSize": limit}
            }
            
            if query_text:
                variables["input"]["query"] = query_text
        
        try:
            result = await self._execute_query(query, variables)
            data = result.get("itemsForFolder") or result.get("itemsForOrganisation", {})
            
            return {
                "items": data.get("items", []),
                "total_hits": data.get("totalHits", 0),
                "page": data.get("page", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to search media center: {e}")
            raise CwayAPIError(f"Failed to search media center: {e}")
    
    async def create_folder(self, name: str, parent_folder_id: Optional[str] = None,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder in media center."""
        mutation = """
        mutation CreateFolder($input: CreateFolderInput!) {
            createFolder(input: $input) {
                id
                name
                description
                parentId
                created
            }
        }
        """
        
        try:
            folder_input = {
                "name": name,
                "description": description
            }
            if parent_folder_id:
                folder_input["parentId"] = parent_folder_id
            # Remove None values
            folder_input = {k: v for k, v in folder_input.items() if v is not None}
            
            result = await self._execute_mutation(mutation, {"input": folder_input})
            return result.get("createFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise CwayAPIError(f"Failed to create folder: {e}")
    
    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a file in media center."""
        mutation = """
        mutation RenameFile($fileId: UUID!, $newName: String!) {
            renameFile(fileId: $fileId, newName: $newName) {
                id
                name
                fileSize
                mimeType
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "fileId": file_id,
                "newName": new_name
            })
            return result.get("renameFile", {})
            
        except Exception as e:
            logger.error(f"Failed to rename file: {e}")
            raise CwayAPIError(f"Failed to rename file: {e}")
    
    async def rename_folder(self, folder_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a folder in media center."""
        mutation = """
        mutation RenameFolder($folderId: UUID!, $newName: String!) {
            renameFolder(folderId: $folderId, newName: $newName) {
                id
                name
                description
                parentId
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "folderId": folder_id,
                "newName": new_name
            })
            return result.get("renameFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to rename folder: {e}")
            raise CwayAPIError(f"Failed to rename folder: {e}")
    
    async def move_files(self, file_ids: List[str], target_folder_id: str) -> Dict[str, Any]:
        """Move files to a different folder."""
        mutation = """
        mutation MoveFiles($input: MoveFilesInput!) {
            moveFiles(input: $input) {
                success
                movedCount
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "fileIds": file_ids,
                    "targetFolderId": target_folder_id
                }
            })
            return result.get("moveFiles", {"success": False, "movedCount": 0})
            
        except Exception as e:
            logger.error(f"Failed to move files: {e}")
            raise CwayAPIError(f"Failed to move files: {e}")
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from media center."""
        mutation = """
        mutation DeleteFile($fileId: UUID!) {
            deleteFile(fileId: $fileId)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"fileId": file_id})
            return result.get("deleteFile", False)
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise CwayAPIError(f"Failed to delete file: {e}")
    
    async def delete_folder(self, folder_id: str, force: bool = False) -> bool:
        """Delete a folder from media center."""
        mutation = """
        mutation DeleteFolder($folderId: UUID!, $force: Boolean) {
            deleteFolder(folderId: $folderId, force: $force)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "folderId": folder_id,
                "force": force
            })
            return result.get("deleteFolder", False)
            
        except Exception as e:
            logger.error(f"Failed to delete folder: {e}")
            raise CwayAPIError(f"Failed to delete folder: {e}")
    
    async def get_media_center_stats(self) -> Dict[str, Any]:
        """Get media center statistics."""
        query = """
        query GetMediaCenterStats {
            mediaCenterStats {
                totalItems
                artworks
                itemsPerMonth {
                    month
                    count
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("mediaCenterStats", {})
            
        except Exception as e:
            logger.error(f"Failed to get media center stats: {e}")
            raise CwayAPIError(f"Failed to get media center stats: {e}")
    
    async def download_folder_contents(self, folder_id: str, zip_name: Optional[str] = None) -> str:
        """Create download job for entire folder contents."""
        # First get all items in the folder
        items_result = await self.get_folder_items(folder_id, page=0, size=1000)
        items = items_result.get("items", [])
        
        if not items:
            raise CwayAPIError("No items found in folder")
        
        # Build file selections
        selections = []
        for item in items:
            if item.get("type") != "FOLDER":  # Skip subfolders for now
                selections.append({
                    "fileId": item["id"],
                    "fileName": item.get("name", "file"),
                    "folder": ""
                })
        
        if not selections:
            raise CwayAPIError("No files found in folder")
        
        # Create download job
        mutation = """
        mutation CreateDownloadJob($selections: [DownloadFileDescriptorInput!]!, $zipName: String, $forceZipFile: Boolean) {
            createDownloadJob(selections: $selections, zipName: $zipName, forceZipFile: $forceZipFile)
        }
        """
        
        try:
            variables = {
                "selections": selections,
                "zipName": zip_name or "folder",
                "forceZipFile": True
            }
            result = await self._execute_mutation(mutation, variables)
            return result.get("createDownloadJob")
            
        except Exception as e:
            logger.error(f"Failed to create folder download job: {e}")
            raise CwayAPIError(f"Failed to create folder download job: {e}")
    
    async def download_project_media(self, project_id: str, zip_name: Optional[str] = None) -> str:
        """Create download job for all media in a project."""
        # Note: This method depends on get_project_by_id which will be in ProjectRepository
        # For now, we'll keep the implementation but it may need cross-repository coordination
        raise NotImplementedError("This method requires ProjectRepository integration")
    
    async def create_artwork_download_job(self, artwork_ids: List[str], zip_name: Optional[str] = None) -> str:
        """Create a download job for artwork files (latest revisions)."""
        # Note: This method depends on get_artwork which will be in ArtworkRepository
        # For now, we'll keep the implementation but it may need cross-repository coordination
        raise NotImplementedError("This method requires ArtworkRepository integration")
    
    async def get_artwork_preview(self, artwork_id: str) -> Optional[Dict[str, Any]]:
        """Get artwork preview file information including URL."""
        query = """
        query GetArtworkPreview($id: UUID!) {
            artwork(id: $id) {
                id
                name
                previewFile {
                    id
                    name
                    fileSize
                    url
                    mimeType
                    width
                    height
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": artwork_id})
            artwork = result.get("artwork")
            if artwork:
                return artwork.get("previewFile")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get artwork preview: {e}")
            raise CwayAPIError(f"Failed to get artwork preview: {e}")
