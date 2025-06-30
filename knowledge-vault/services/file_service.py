import os
import uuid
import tempfile
from typing import Dict, List, Any
from fastapi import UploadFile
from datetime import datetime
from firebase_admin import firestore
from services.firebase_service import FirebaseService
from services.indexing_service import IndexingService
import logging

# Import eA³ (Epistemic Autonomy) services and story events (required)
from alchemist_shared.services import get_ea3_orchestrator, ConversationContext, get_agent_lifecycle_service
from alchemist_shared.events import get_story_event_publisher, StoryEventType

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
            await self._index_file(file_id, file_content, file.content_type, agent_id, file.filename)
            
            
            # Get the updated file data with indexing information
            updated_file_data = self.firebase_service.get_file(file_id)
            
            # Return the updated file metadata that includes indexing status
            return updated_file_data if updated_file_data else file_data
            
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    async def _index_file(self, file_id: str, content: bytes, content_type: str, agent_id: str, filename: str) -> None:
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
            
            # Update phase - smart chunking and relevance assessment
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "processing_and_relevance_assessment",
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
            relevance_assessment = processing_result.get("relevance_assessment")
            relevance_score = processing_result.get("relevance_score")
            agent_specific_quality = processing_result.get("agent_specific_quality")
            
            # Update phase - generating embeddings
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "generating_embeddings",
                "progress_percent": 80,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Update phase - computing chunk analysis
            self.firebase_service.update_file(file_id, {
                "indexing_phase": "computing_chunk_analysis",
                "progress_percent": 90,
                "last_updated": SERVER_TIMESTAMP
            })
            
            # Pre-compute chunk analysis
            chunk_analysis = None
            try:
                from services.chunk_analysis_service import ChunkAnalysisService
                chunk_analysis_service = ChunkAnalysisService()
                
                # Create temporary embeddings data structure for analysis
                embeddings_data = {
                    "embeddings": chunks,
                    "filename": filename,
                    "agent_id": agent_id
                }
                
                # Perform comprehensive chunk analysis
                chunk_analysis = chunk_analysis_service._perform_chunk_analysis(embeddings_data)
                
                logging.info(f"Pre-computed chunk analysis for file {file_id}: {len(chunks)} chunks analyzed")
            except Exception as e:
                logging.error(f"Failed to pre-compute chunk analysis for file {file_id}: {e}")
                chunk_analysis = {"error": f"Analysis failed: {str(e)}", "total_chunks": len(chunks)}
            
            # Update file metadata with enhanced information including full text content and chunk analysis
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
                "processed_text": processed_text,
                # Agent-specific relevance assessment
                "relevance_assessment": relevance_assessment,
                "relevance_score": relevance_score,
                # Agent-specific quality (combines content quality + relevance)
                "agent_specific_quality": agent_specific_quality,
                # Pre-computed chunk analysis
                "chunk_analysis": chunk_analysis,
                "chunk_analysis_version": "v1",
                "chunk_analysis_timestamp": SERVER_TIMESTAMP
            })
            
            # Record agent lifecycle event for knowledge file addition
            lifecycle_service = get_agent_lifecycle_service()
            if lifecycle_service:
                try:
                    await lifecycle_service.record_knowledge_file_added(
                        agent_id=agent_id,
                        filename=filename,
                        file_size=len(content),
                        user_id="system",  # Could be passed from API if user context available
                        metadata={
                            "file_id": file_id,
                            "content_type": content_type,
                            "chunk_count": len(chunks),
                            "quality_score": quality_score,
                            "processing_stats": processing_stats,
                            "word_count": content_metadata.get("word_count", 0),
                            "document_type": content_metadata.get("document_type", "unknown")
                        }
                    )
                    logging.info(f"Recorded lifecycle event for knowledge file addition: {filename}")
                except Exception as e:
                    logging.error(f"Failed to record lifecycle event for file upload: {e}")
            
            # Publish knowledge acquisition event asynchronously to story event system (required)
            # Generate enhanced narrative for the knowledge acquisition
            narrative = await self._generate_knowledge_acquisition_narrative(
                filename, content_type, len(chunks), quality_score, content_metadata
            )
            
            # Publish story event asynchronously (required)
            story_publisher = get_story_event_publisher()
            
            # Create async task to publish knowledge acquisition event
            import asyncio
            asyncio.create_task(
                story_publisher.publish_knowledge_event(
                    agent_id=agent_id,
                    filename=filename,
                    action="acquired",
                    source_service="knowledge-vault",
                    narrative_content=narrative,
                    metadata={
                        "file_id": file_id,
                        "content_type": content_type,
                        "chunk_count": len(chunks),
                        "quality_score": quality_score,
                        "word_count": content_metadata.get("word_count", 0),
                        "document_type": content_metadata.get("document_type", "unknown"),
                        "processing_stats": processing_stats,
                        "local_reference": file_id  # Reference to local file storage
                    }
                )
            )
            logging.info(f"Published knowledge acquisition story event for agent {agent_id}: {filename}")
            
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
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
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
            
            # Record agent lifecycle event for knowledge file removal
            lifecycle_service = get_agent_lifecycle_service()
            if lifecycle_service and agent_id:
                try:
                    await lifecycle_service.record_knowledge_file_removed(
                        agent_id=agent_id,
                        filename=file_data.get('filename', 'unknown'),
                        user_id="system",
                        metadata={
                            "file_id": file_id,
                            "content_type": file_data.get("content_type", "unknown"),
                            "chunk_count": file_data.get("chunk_count", 0),
                            "file_size": file_data.get("size", 0)
                        }
                    )
                    logging.info(f"Recorded lifecycle event for knowledge file removal: {file_data.get('filename')}")
                except Exception as e:
                    logging.error(f"Failed to record lifecycle event for file deletion: {e}")

            # Publish knowledge removal event asynchronously to story event system (required)
            if agent_id:
                # Publish story event asynchronously (required)
                story_publisher = get_story_event_publisher()
                
                # Create removal narrative
                removal_narrative = f"I have removed {file_data.get('filename', 'a knowledge file')} from my knowledge base. This reduction in my available knowledge resources may affect my capabilities in related areas, but ensures my information remains current and relevant."
                
                # Create async task to publish knowledge removal event
                import asyncio
                asyncio.create_task(
                    story_publisher.publish_knowledge_event(
                        agent_id=agent_id,
                        filename=file_data.get('filename', 'unknown'),
                        action="removed",
                        source_service="knowledge-vault",
                        narrative_content=removal_narrative,
                        metadata={
                            "file_id": file_id,
                            "original_filename": file_data.get("filename", "unknown"),
                            "content_type": file_data.get("content_type", "unknown"),
                            "chunk_count": file_data.get("chunk_count", 0),
                            "local_reference": file_id  # Reference to local file storage
                        }
                    )
                )
                logging.info(f"Published knowledge removal story event for agent {agent_id}: {file_data.get('filename')}")
            
            return {"status": "success", "message": f"File {file_data['filename']} deleted successfully"}
            
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")
    
    async def _get_agent_file_count(self, agent_id: str) -> int:
        """Get the total number of files for an agent"""
        try:
            files = self.firebase_service.get_files_by_agent(agent_id)
            return len(files) if files else 0
        except Exception as e:
            logging.error(f"Error getting file count for agent {agent_id}: {e}")
            return 0
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
    
    async def _generate_knowledge_acquisition_narrative(
        self, 
        filename: str, 
        content_type: str, 
        chunk_count: int, 
        quality_score: float, 
        content_metadata: Dict[str, Any]
    ) -> str:
        """
        Generate GPT-4.1 enhanced narrative for knowledge acquisition events
        
        This creates coherent, contextual narratives that fit the agent's life-story
        when new knowledge is acquired through file uploads.
        """
        try:
            from .openai_service import OpenAIService
            
            # Extract meaningful metadata for narrative context
            word_count = content_metadata.get("word_count", 0)
            doc_type = content_metadata.get("document_type", "document")
            topics = content_metadata.get("topics", [])
            
            prompt = f"""
You are an expert narrative intelligence system that creates coherent life-story entries for AI agents when they acquire new knowledge.

KNOWLEDGE ACQUISITION EVENT:
- File: {filename}
- Type: {content_type} ({doc_type})
- Processing Quality: {quality_score:.1f}/10
- Content Volume: {word_count} words in {chunk_count} chunks
- Key Topics: {', '.join(topics[:5]) if topics else 'General knowledge'}

NARRATIVE FRAMEWORK:
1. CNE (Coherent Narrative Exclusivity): This event must fit the agent's singular life-story
2. Umwelt Integration: How this knowledge changes the agent's perceptual world
3. GNF Alignment: How this fits the agent's role and objectives
4. Epistemic Growth: What the agent gained from this knowledge

REQUIREMENTS:
- Write in first person from the agent's perspective
- Focus on the cognitive/epistemic impact, not just the technical details
- Show how this knowledge enhances the agent's capabilities or understanding
- Keep it concise but meaningful (2-3 sentences max)
- Maintain a professional, reflective tone

Generate a narrative response that the agent might give when reflecting on acquiring this knowledge:
"""
            
            # Use the centralized OpenAI service with new API
            openai_service = OpenAIService()
            response = openai_service.client.chat.completions.create(
                model="gpt-4-1106-preview",  # GPT-4.1 for enhanced narrative intelligence
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized narrative intelligence system. Create coherent, first-person reflections for AI agents acquiring new knowledge. Always write from the agent's perspective."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            narrative = response.choices[0].message.content.strip()
            
            # Fallback to structured narrative if GPT-4.1 fails
            if not narrative or len(narrative) < 20:
                raise Exception("Generated narrative too short")
                
            logging.info(f"Generated enhanced narrative for knowledge acquisition: {filename}")
            return narrative
            
        except Exception as e:
            logging.warning(f"GPT-4.1 narrative generation failed, using fallback: {e}")
            
            # Fallback to structured narrative
            quality_desc = "high-quality" if quality_score >= 7 else "moderate-quality" if quality_score >= 5 else "basic"
            
            return f"I have successfully processed and integrated {filename}, a {quality_desc} {content_type} containing {word_count} words. This knowledge has been organized into {chunk_count} semantic chunks and is now part of my expanding understanding, enhancing my ability to assist with related topics."
    
    async def update_file_content(self, file_id: str, new_content: str) -> Dict[str, Any]:
        """
        Update the content of a file and reindex it
        
        Args:
            file_id: ID of the file to update
            new_content: New content to replace the original content
            
        Returns:
            Dictionary with update status and file information
        """
        try:
            # Get existing file metadata
            file_data = self.firebase_service.get_file(file_id)
            
            if not file_data:
                raise Exception(f"File with ID {file_id} not found")
            
            agent_id = file_data.get("agent_id")
            filename = file_data.get("filename")
            storage_path = file_data.get("storage_path")
            
            # Update the file content in storage
            content_bytes = new_content.encode('utf-8')
            self.firebase_service.upload_file_to_storage(content_bytes, storage_path)
            
            # Update file metadata to indicate content has been modified
            self.firebase_service.update_file(file_id, {
                "size": len(content_bytes),
                "last_updated": SERVER_TIMESTAMP,
                "indexed": False,  # Mark as not indexed since content changed
                "indexing_status": "pending",
                "indexing_phase": "content_updated",
                "progress_percent": 0,
                "indexing_error": None,
                "content_modified": True,
                "original_text": new_content  # Store the updated content
            })
            
            # Delete existing embeddings since content has changed
            self.indexing_service.delete_file_vectors(file_id)
            
            # Reindex the file with new content
            await self._index_file(file_id, content_bytes, file_data.get("content_type"), agent_id, filename)
            
            # Get updated file data
            updated_file_data = self.firebase_service.get_file(file_id)
            
            # Record agent lifecycle event for knowledge file content update
            lifecycle_service = get_agent_lifecycle_service()
            if lifecycle_service and agent_id:
                try:
                    await lifecycle_service.record_event(
                        agent_id=agent_id,
                        event_type=StoryEventType.CONFIGURATION_UPDATED,
                        title="Knowledge File Updated",
                        description=f"Knowledge base file '{filename}' content was updated and reindexed",
                        user_id="system",
                        metadata={
                            "file_id": file_id,
                            "filename": filename,
                            "content_type": file_data.get("content_type", "unknown"),
                            "new_size": len(content_bytes),
                            "old_size": file_data.get("size", 0),
                            "operation": "content_update"
                        }
                    )
                    logging.info(f"Recorded lifecycle event for knowledge file update: {filename}")
                except Exception as e:
                    logging.error(f"Failed to record lifecycle event for file update: {e}")
            
            # Publish knowledge update event to story system
            if agent_id:
                story_publisher = get_story_event_publisher()
                
                # Create update narrative
                update_narrative = f"I have updated the content of {filename} in my knowledge base. This revision ensures my knowledge remains current and accurate, allowing me to provide better assistance based on the most up-to-date information."
                
                # Create async task to publish knowledge update event
                import asyncio
                asyncio.create_task(
                    story_publisher.publish_knowledge_event(
                        agent_id=agent_id,
                        filename=filename,
                        action="updated",
                        source_service="knowledge-vault",
                        narrative_content=update_narrative,
                        metadata={
                            "file_id": file_id,
                            "original_filename": filename,
                            "content_type": file_data.get("content_type", "unknown"),
                            "new_size": len(content_bytes),
                            "operation": "content_update",
                            "local_reference": file_id
                        }
                    )
                )
                logging.info(f"Published knowledge update story event for agent {agent_id}: {filename}")
            
            return {
                "status": "success",
                "message": f"Content of {filename} updated and reindexed successfully",
                "file_data": updated_file_data,
                "new_content_size": len(content_bytes)
            }
            
        except Exception as e:
            # Update file with error status if indexing fails
            self.firebase_service.update_file(file_id, {
                "indexing_status": "failed",
                "indexing_phase": "content_update_failed",
                "indexing_error": str(e),
                "last_updated": SERVER_TIMESTAMP
            })
            raise Exception(f"Error updating file content: {str(e)}")