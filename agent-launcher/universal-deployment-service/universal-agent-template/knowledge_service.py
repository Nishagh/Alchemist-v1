#!/usr/bin/env python3
"""
Firestore-based Knowledge Base Client for Standalone Agent

This module provides a client for accessing embeddings directly from Firestore
and listening to real-time changes in the knowledge base embeddings.
"""
import os
import logging
import requests
from typing import Dict, Any, List, Optional, Callable
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import firestore

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FirestoreKnowledgeBaseClient:
    """Client for accessing embeddings directly from Firestore."""
    
    def __init__(self, firestore_client: Optional[firestore.Client] = None):
        """
        Initialize the Firestore Knowledge Base client.
        
        Args:
            firestore_client: Firestore client instance. If None, creates a new one.
        """
        self.db = firestore_client or firestore.client()
        self._listeners = {}  # Store active listeners
        logger.info("Initialized Firestore Knowledge Base client")
    
    def get_embeddings(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all embeddings for an agent from Firestore subcollection.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of embeddings
        """
        try:
            logger.info(f"🔍 Firestore: Getting embeddings for agent '{agent_id}' from subcollection")
            
            # Query the embeddings subcollection: knowledge_base_embeddings/{agent_id}/embeddings
            embeddings_ref = (self.db.collection('knowledge_base_embeddings')
                             .document(agent_id)
                             .collection('embeddings'))
            
            embeddings_docs = embeddings_ref.stream()
            embeddings = []
            
            for doc in embeddings_docs:
                if doc.exists:
                    embedding_data = doc.to_dict()
                    # Add the chunk_id from document ID
                    embedding_data['chunk_id'] = doc.id
                    embeddings.append(embedding_data)
            
            logger.info(f"🔍 Firestore: Retrieved {len(embeddings)} embeddings for agent {agent_id}")
            return embeddings
                
        except Exception as e:
            logger.error(f"🔍 Firestore: Error getting embeddings: {str(e)}")
            return []
    
    def get_file_embeddings(self, agent_id: str, file_id: str) -> List[Dict[str, Any]]:
        """Get embeddings for a specific file.
        
        Args:
            agent_id: ID of the agent
            file_id: ID of the file
            
        Returns:
            List of embeddings for the specific file
        """
        try:
            logger.info(f"🔍 Firestore: Getting embeddings for agent '{agent_id}', file '{file_id}'")
            
            # Get all embeddings and filter by file_id
            all_embeddings = self.get_embeddings(agent_id)
            file_embeddings = [emb for emb in all_embeddings if emb.get('file_id') == file_id]
            
            logger.info(f"🔍 Firestore: Retrieved {len(file_embeddings)} embeddings for file {file_id}")
            return file_embeddings
            
        except Exception as e:
            logger.error(f"🔍 Firestore: Error getting file embeddings: {str(e)}")
            return []
        
    def get_embedding_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get embedding statistics for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary with embedding statistics
        """
        try:
            logger.info(f"🔍 Firestore: Getting embedding stats for agent '{agent_id}'")
            
            embeddings = self.get_embeddings(agent_id)
            
            # Calculate stats
            total_embeddings = len(embeddings)
            files = set(emb.get('file_id') for emb in embeddings if emb.get('file_id'))
            total_files = len(files)
            
            stats = {
                'agent_id': agent_id,
                'total_embeddings': total_embeddings,
                'total_files': total_files,
                'files': list(files)
            }
            
            logger.info(f"🔍 Firestore: Stats for agent {agent_id}: {total_embeddings} embeddings across {total_files} files")
            return stats
            
        except Exception as e:
            logger.error(f"🔍 Firestore: Error getting embedding stats: {str(e)}")
            return {}
    
    def listen_to_embeddings(self, agent_id: str, callback: Callable[[List[Dict[str, Any]]], None]):
        """Listen to real-time changes in embeddings subcollection for an agent.
        
        Args:
            agent_id: ID of the agent
            callback: Function to call when embeddings change
        """
        try:
            logger.info(f"🔍 Firestore: Starting real-time subcollection listener for agent '{agent_id}'")
            
            # Listen to the embeddings subcollection: knowledge_base_embeddings/{agent_id}/embeddings
            embeddings_ref = (self.db.collection('knowledge_base_embeddings')
                             .document(agent_id)
                             .collection('embeddings'))
            
            def on_snapshot(doc_snapshots, changes, read_time):
                try:
                    logger.info(f"🔍 Firestore: Real-time subcollection update - {len(doc_snapshots)} documents")
                    
                    embeddings = []
                    for doc in doc_snapshots:
                        if doc.exists:
                            embedding_data = doc.to_dict()
                            # Add the chunk_id from document ID
                            embedding_data['chunk_id'] = doc.id
                            embeddings.append(embedding_data)
                    
                    logger.info(f"🔍 Firestore: Real-time update - {len(embeddings)} embeddings for agent {agent_id}")
                    
                    # Log changes for debugging
                    if changes:
                        for change in changes:
                            if change.type.name == 'ADDED':
                                logger.info(f"🔍 Firestore: Added embedding: {change.document.id}")
                            elif change.type.name == 'MODIFIED':
                                logger.info(f"🔍 Firestore: Modified embedding: {change.document.id}")
                            elif change.type.name == 'REMOVED':
                                logger.info(f"🔍 Firestore: Removed embedding: {change.document.id}")
                    
                    callback(embeddings)
                    
                except Exception as e:
                    logger.error(f"🔍 Firestore: Error in real-time subcollection callback: {str(e)}")
            
            # Start the listener on the subcollection
            listener = embeddings_ref.on_snapshot(on_snapshot)
            self._listeners[agent_id] = listener
            
            logger.info(f"🔍 Firestore: Real-time subcollection listener started for agent {agent_id}")
            return listener
            
        except Exception as e:
            logger.error(f"🔍 Firestore: Error starting real-time subcollection listener: {str(e)}")
            return None
    
    def stop_listener(self, agent_id: str):
        """Stop the real-time listener for an agent.
        
        Args:
            agent_id: ID of the agent
        """
        try:
            if agent_id in self._listeners:
                self._listeners[agent_id].unsubscribe()
                del self._listeners[agent_id]
                logger.info(f"🔍 Firestore: Stopped real-time listener for agent {agent_id}")
            else:
                logger.info(f"🔍 Firestore: No active listener found for agent {agent_id}")
        except Exception as e:
            logger.error(f"🔍 Firestore: Error stopping listener: {str(e)}")
    
    def stop_all_listeners(self):
        """Stop all active listeners."""
        try:
            for agent_id in list(self._listeners.keys()):
                self.stop_listener(agent_id)
            logger.info("🔍 Firestore: Stopped all real-time listeners")
        except Exception as e:
            logger.error(f"🔍 Firestore: Error stopping all listeners: {str(e)}")
    
    # Legacy compatibility methods (can be removed later)
    def get_agent_vector_files(self, agent_id: str) -> List[Dict[str, Any]]:
        """Legacy method - get unique files from embeddings."""
        try:
            embeddings = self.get_embeddings(agent_id)
            files = {}
            
            for emb in embeddings:
                file_id = emb.get('file_id')
                filename = emb.get('filename', 'unknown')
                if file_id and file_id not in files:
                    files[file_id] = {
                        'file_id': file_id,
                        'filename': filename
                    }
            
            result = list(files.values())
            logger.info(f"🔍 Firestore: Retrieved {len(result)} unique files for agent {agent_id}")
            return result
            
        except Exception as e:
            logger.error(f"🔍 Firestore: Error getting vector files: {str(e)}")
            return []
    
    def get_knowledge_base_vectors(self, agent_id: str, file_id: str) -> List[Dict[str, Any]]:
        """Legacy method - alias for get_file_embeddings."""
        return self.get_file_embeddings(agent_id, file_id)
    
    # No longer needed - using real-time Firestore listeners instead
    def register_agent_webhook(self, agent_id: str, webhook_url: str) -> bool:
        """Webhook registration no longer needed with real-time Firestore listeners."""
        logger.info(f"🔍 Firestore: Webhook registration not needed - using real-time listeners for agent '{agent_id}'")
        return True

# Create a default client instance using Firestore
default_knowledge_client = FirestoreKnowledgeBaseClient()

# Backward compatibility alias
KnowledgeBaseClient = FirestoreKnowledgeBaseClient
