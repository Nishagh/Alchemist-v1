import os
import uuid
import tempfile
from typing import Dict, List, Any
from fastapi import UploadFile
from datetime import datetime
from firebase_admin import firestore
from app.services.firebase_service import FirebaseService
from app.services.indexing_service import IndexingService

SERVER_TIMESTAMP = firestore.SERVER_TIMESTAMP

class FileService:
    def __init__(self):
        self.firebase_service = FirebaseService()
        self.indexing_service = IndexingService()
    
    async def upload_file(self, file: UploadFile, agent_id: str) -> Dict[str, Any]:
        """Upload a file and index its content"""
        try:
            # Generate unique ID for the file
            file_id = str(uuid.uuid4())
            
            # Read file content
            file_content = await file.read()
            
            # Define storage path
            storage_path = f"knowledge_base/{agent_id}/{file_id}_{file.filename}"
            
            # Upload to Firebase Storage
            self.firebase_service.upload_file_to_storage(file_content, storage_path)
            
            # Determine content type with fallback
            content_type = file.content_type
            if not content_type:
                # Guess content type from file extension
                if file.filename.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif file.filename.endswith('.txt'):
                    content_type = 'text/plain'
                elif file.filename.endswith('.docx'):
                    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif file.filename.endswith('.html') or file.filename.endswith('.htm'):
                    content_type = 'text/html'
                else:
                    content_type = 'application/octet-stream'  # Default binary type
            
            # Create file metadata
            file_data = {
                "id": file_id,
                "filename": file.filename,
                "agent_id": agent_id,
                "content_type": content_type,
                "size": len(file_content),
                "upload_date": SERVER_TIMESTAMP,
                "storage_path": storage_path,
                "indexed": False,
                "purpose": "knowledge base",
                "chunk_count": 0,
                "indexing_status": "pending",
                "indexing_error": None,
                "last_updated": SERVER_TIMESTAMP
            }
            
            # Add file metadata to Firestore
            file_id = self.firebase_service.add_file(file_data)
            
            # Process and index the file synchronously (wait until indexing is complete)
            self._index_file(file_id, file_content, file.content_type, agent_id, file.filename)
            
            
            # Get the updated file data with indexing information
            updated_file_data = self.firebase_service.get_file(file_id)
            
            # Return the updated file metadata that includes indexing status
            return updated_file_data if updated_file_data else file_data
            
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    def _index_file(self, file_id: str, content: bytes, content_type: str, agent_id: str, filename: str) -> None:
        """Process and index a file with enhanced phase tracking"""
        # First update to show indexing is in progress
        self.firebase_service.update_file(file_id, {
            "indexing_status": "processing",
            "indexing_phase": "preparing",
            "progress_percent": 5,
            "last_updated": SERVER_TIMESTAMP
        })
        
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Update phase - text extraction
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "extracting_text",
                "progress_percent": 20,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Update phase - cleaning content
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "cleaning_content",
                "progress_percent": 40,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Update phase - smart chunking
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "smart_chunking",
                "progress_percent": 60,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Process the file and get chunks with enhanced processing
            processing_result = self.indexing_service.process_file(
                file_path=temp_file_path,
                file_id=file_id,
                content_type=content_type,
                agent_id=agent_id,
                filename=filename
            )
            
            # Extract data from the new return structure
            chunks = processing_result["chunks"]
            original_text = processing_result["original_text"]
            processed_text = processing_result["processed_text"]
            processing_stats = processing_result["processing_stats"]
            quality_score = processing_result["quality_score"]
            content_metadata = processing_result["content_metadata"]
            
            # Update phase - generating embeddings
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "generating_embeddings",
                "progress_percent": 80,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Update file metadata with enhanced information including full text content
            self.firebase_service.update_file(file_id, {
                "indexed": True,
                "chunk_count": len(chunks),
                "indexing_status": "complete",
                "indexing_phase": "complete",
                "progress_percent": 100,
                "last_updated": SERVER_TIMESTAMP,
                # Enhanced metadata
                "processing_stats": processing_stats,
                "quality_score": quality_score,
                "content_metadata": content_metadata,
                "processing_version": "v2_enhanced",
                # Full text content for preview
                "original_text": original_text,
                "processed_text": processed_text
            })
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
        except Exception as e:
            # Update file metadata with error
            self.firebase_service.update_file(file_id, {
                "indexed": False,
                "indexing_status": "failed",
                "indexing_phase": "failed",
                "indexing_error": str(e),
                "progress_percent": 0,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Re-raise exception
            raise Exception(f"Error indexing file: {str(e)}")
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file and its embeddings"""
        try:
            # Get file metadata
            file_data = self.firebase_service.get_file(file_id)
            
            if not file_data:
                raise Exception(f"File with ID {file_id} not found")
            
            agent_id = file_data.get("agent_id")
            
            # Delete file from storage
            self.firebase_service.delete_file_from_storage(file_data["storage_path"])
            
            # Delete embeddings from Firestore
            self.indexing_service.delete_file_vectors(file_id)
            
            # Delete file metadata from Firestore (this also deletes related embeddings)
            self.firebase_service.delete_file(file_id)
            
            
            return {"status": "success", "message": f"File {file_data['filename']} deleted successfully"}
            
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")
    
    def get_files(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all files for an agent"""
        try:
            files = self.firebase_service.get_files_by_agent(agent_id)
            return files
        except Exception as e:
            raise Exception(f"Error getting files: {str(e)}")
    
    def get_file_embeddings(self, file_id: str) -> Dict[str, Any]:
        """Get all embeddings for a specific file
        
        Args:
            file_id: ID of the file to get embeddings for
            
        Returns:
            Dictionary with embedding details
        """
        try:
            # Get file metadata first
            file_data = self.firebase_service.get_file(file_id)
            
            if not file_data:
                raise Exception(f"File with ID {file_id} not found")
                
            agent_id = file_data.get("agent_id")
            if not agent_id:
                raise Exception(f"File {file_id} does not have an associated agent_id")
                
            # Get embeddings for this file
            embeddings = self.firebase_service.get_embeddings_by_file(agent_id, file_id)
            
            return {
                "file_id": file_id,
                "filename": file_data.get("filename"),
                "agent_id": agent_id,
                "embedding_count": len(embeddings),
                "embeddings": embeddings
            }
            
        except Exception as e:
            raise Exception(f"Error getting file embeddings: {str(e)}")
    
    def get_agent_embedding_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get embedding statistics for an agent
        
        Args:
            agent_id: ID of the agent to get stats for
            
        Returns:
            Dictionary with embedding statistics
        """
        try:
            return self.firebase_service.get_embedding_stats(agent_id)
        except Exception as e:
            raise Exception(f"Error getting agent embedding stats: {str(e)}")
    
    def reprocess_file(self, file_id: str) -> Dict[str, Any]:
        """Reprocess an existing file with enhanced cleaning pipeline"""
        try:
            # Get file metadata
            file_data = self.firebase_service.get_file(file_id)
            
            if not file_data:
                raise Exception(f"File with ID {file_id} not found")
            
            agent_id = file_data.get("agent_id")
            storage_path = file_data.get("storage_path")
            content_type = file_data.get("content_type")
            filename = file_data.get("filename")
            
            # Download file content from storage
            file_content = self.firebase_service.download_file_from_storage(storage_path)
            
            # Delete existing embeddings
            self.indexing_service.delete_file_vectors(file_id)
            
            # Reprocess the file
            self._index_file(file_id, file_content, content_type, agent_id, filename)
            
            # Get updated file data
            updated_file_data = self.firebase_service.get_file(file_id)
            
            return {
                "status": "success",
                "message": f"File {filename} reprocessed successfully",
                "file_data": updated_file_data
            }
            
        except Exception as e:
            raise Exception(f"Error reprocessing file: {str(e)}")
    
    def get_processing_status(self, file_id: str) -> Dict[str, Any]:
        """Get detailed processing status for a file"""
        try:
            file_data = self.firebase_service.get_file(file_id)
            
            if not file_data:
                raise Exception(f"File with ID {file_id} not found")
            
            # Extract processing information
            status_info = {
                "file_id": file_id,
                "filename": file_data.get("filename"),
                "indexing_status": file_data.get("indexing_status", "unknown"),
                "indexing_phase": file_data.get("indexing_phase", "unknown"),
                "progress_percent": file_data.get("progress_percent", 0),
                "processing_stats": file_data.get("processing_stats", {}),
                "quality_score": file_data.get("quality_score", 0),
                "content_metadata": file_data.get("content_metadata", {}),
                "chunk_count": file_data.get("chunk_count", 0),
                "processing_version": file_data.get("processing_version", "v2_enhanced"),
                "last_updated": file_data.get("last_updated"),
                "indexing_error": file_data.get("indexing_error")
            }
            
            return status_info
            
        except Exception as e:
            raise Exception(f"Error getting processing status: {str(e)}")