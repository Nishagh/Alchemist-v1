import os
import re
import tempfile
import subprocess
from datetime import datetime
from typing import List, Dict, Any
import pypdf
import docx2txt
from bs4 import BeautifulSoup
from firebase_admin import firestore
from app.services.openai_service import OpenAIService
from app.services.firebase_service import FirebaseService
from app.services.content_processor import ContentProcessor
from app.services.chunking_service import ChunkingService
from app.utils.logging_config import get_logger, log_with_data

SERVER_TIMESTAMP = firestore.SERVER_TIMESTAMP

class IndexingService:
    def __init__(self):
        # Initialize logger
        self.logger = get_logger("IndexingService")
        self.logger.info("Initializing Indexing Service")
        
        # Initialize services
        self.openai_service = OpenAIService()
        self.firebase_service = FirebaseService()
        self.content_processor = ContentProcessor()
        self.chunking_service = ChunkingService()
        
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        log_with_data(self.logger, "INFO", 
                      "Indexing configuration: Enhanced with content processing",
                      {"chunk_size": self.chunk_size, "chunk_overlap": self.chunk_overlap})
        
    def process_file(self, file_path: str, file_id: str, content_type: str, agent_id: str, filename: str) -> List[Dict[str, Any]]:
        """Process a file with enhanced cleaning and smart chunking"""
        log_with_data(self.logger, "INFO", "Starting enhanced file processing", {
            "file_id": file_id,
            "filename": filename,
            "content_type": content_type
        })
        
        # Step 1: Extract text based on file type
        raw_text = self._extract_text(file_path, content_type)
        
        # Step 2: Process and clean content
        processing_result = self.content_processor.process_content(
            text=raw_text,
            content_type=content_type,
            filename=filename
        )
        
        processed_text = processing_result["processed_text"]
        content_metadata = processing_result["metadata"]
        processing_stats = processing_result["processing_stats"]
        
        log_with_data(self.logger, "INFO", "Content processing completed", processing_stats)
        
        # Step 3: Create smart chunks
        chunk_objects = self.chunking_service.create_smart_chunks(
            text=processed_text,
            metadata=content_metadata
        )
        
        if not chunk_objects:
            self.logger.warning(f"No chunks created for file {file_id}")
            return []
        
        # Step 4: Generate embeddings for chunks
        chunk_docs = []
        for i, chunk_obj in enumerate(chunk_objects):
            chunk_content = chunk_obj["content"]
            
            # Skip empty chunks
            if not chunk_content.strip():
                continue
            
            # Generate embedding
            embedding = self.openai_service.get_embedding(chunk_content)
            
            # Create enhanced chunk document
            chunk_doc = {
                "file_id": file_id,
                "agent_id": agent_id,
                "filename": filename,
                "content": chunk_content,
                "original_content": chunk_obj.get("original_content", ""),
                "overlap_content": chunk_obj.get("overlap_content", ""),
                "chunk_index": i,
                "embedding": embedding,
                "created_at": SERVER_TIMESTAMP,
                # Content processing metadata
                "processing_stats": processing_stats,
                "content_metadata": content_metadata,
                "chunk_metadata": chunk_obj["metadata"],
                # Quality indicators
                "quality_score": processing_result["quality_score"],
                "content_type_detected": content_metadata.get("content_type_guess", "general"),
                # Legacy fields for compatibility
                "page_number": i + 1
            }
            
            chunk_docs.append(chunk_doc)
        
        # Step 5: Store embeddings in Firestore
        embedding_ids = self.firebase_service.add_embeddings(agent_id, chunk_docs)
        
        # Update chunk docs with embedding IDs
        for i, chunk_doc in enumerate(chunk_docs):
            if i < len(embedding_ids):
                chunk_doc['embedding_id'] = embedding_ids[i]
        
        # Log final statistics
        chunk_stats = self.chunking_service.get_chunk_statistics(chunk_objects)
        log_with_data(self.logger, "INFO", "File processing completed", {
            "file_id": file_id,
            "chunks_created": len(chunk_docs),
            "processing_stats": processing_stats,
            "chunk_stats": chunk_stats
        })
        
        # Return both chunks and full text content for preview
        return {
            "chunks": chunk_docs,
            "original_text": raw_text,
            "processed_text": processed_text,
            "processing_stats": processing_stats,
            "content_metadata": content_metadata,
            "quality_score": processing_result["quality_score"]
        }
    
    def _extract_text(self, file_path: str, content_type: str) -> str:
        """Extract text from a file based on its content type"""
        try:
            self.logger.info(f"Extracting text from file with content type: {content_type}")
            
            # Check file extension first to handle cases where content_type is generic or incorrect
            if file_path.lower().endswith(".pdf") or "pdf" in content_type.lower():
                self.logger.info(f"Processing as PDF: {file_path}")
                text = self._extract_text_from_pdf(file_path)
                self.logger.info(f"Extracted {len(text)} characters from PDF")
                return text
                
            elif file_path.lower().endswith(".docx") or "word" in content_type.lower():
                self.logger.info(f"Processing as Word document: {file_path}")
                text = self._extract_text_from_docx(file_path)
                self.logger.info(f"Extracted {len(text)} characters from Word document")
                return text
                
            elif file_path.lower().endswith(".txt") or "text" in content_type.lower():
                self.logger.info(f"Processing as text file: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        self.logger.info(f"Extracted {len(text)} characters from text file")
                        return text
                except UnicodeDecodeError:
                    # Try with different encodings if UTF-8 fails
                    self.logger.warning(f"UTF-8 decoding failed, trying with latin-1 encoding")
                    with open(file_path, 'r', encoding='latin-1') as f:
                        text = f.read()
                        self.logger.info(f"Extracted {len(text)} characters using latin-1 encoding")
                        return text
                        
            elif file_path.lower().endswith((".html", ".htm")) or "html" in content_type.lower():
                self.logger.info(f"Processing as HTML: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        html = f.read()
                
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                self.logger.info(f"Extracted {len(text)} characters from HTML")
                return text
                
            else:
                # For binary files with no recognizable extension, we try to guess based on contents
                if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")):
                    self.logger.warning(f"Image file detected, cannot extract text content: {file_path}")
                    return f"[This is an image file: {os.path.basename(file_path)}. No text content available for indexing.]"
                
                # Try to detect PDF by signature (PDF files start with %PDF-)
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(5).decode('ascii', errors='ignore')
                        if header.startswith('%PDF'):
                            self.logger.info(f"PDF signature detected in file with incorrect content type, processing as PDF: {file_path}")
                            # Reset file pointer and try PDF extraction
                            text = self._extract_text_from_pdf(file_path)
                            self.logger.info(f"Extracted {len(text)} characters from PDF with incorrect content type")
                            return text
                except Exception as detect_e:
                    self.logger.warning(f"Error during file type detection: {str(detect_e)}")
                
                # For other unknown types, try to read as text with fallbacks
                self.logger.info(f"Attempting to process unknown type as text: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        self.logger.info(f"Successfully extracted {len(text)} characters as text")
                        return text
                except UnicodeDecodeError:
                    self.logger.warning("UTF-8 decoding failed, trying with latin-1 encoding")
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            text = f.read()
                            self.logger.info(f"Successfully extracted {len(text)} characters using latin-1 encoding")
                            return text
                    except Exception as inner_e:
                        self.logger.error(f"Failed to extract text with latin-1 encoding: {str(inner_e)}")
                except Exception as inner_e:
                    self.logger.error(f"Failed to extract text: {str(inner_e)}")
                
                # If all attempts fail, return a meaningful message
                self.logger.warning(f"Unable to extract text from file: {file_path}")
                return f"[This file ({os.path.basename(file_path)}) could not be processed. The file format may not be supported for text extraction.]"
                    
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            # Return a message that will be indexed instead of empty string
            return f"[Error extracting text from file: {str(e)}]"
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file with enhanced error handling"""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                # First try the primary method
                pdf = pypdf.PdfReader(f)
                
                # Log number of pages for debugging
                page_count = len(pdf.pages)
                self.logger.info(f"PDF has {page_count} pages")
                
                # Extract text from each page
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n\n"
                        else:
                            self.logger.warning(f"Page {i+1} produced empty text")
                    except Exception as e:
                        self.logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                
                # Check if we got any usable text
                if not text.strip():
                    self.logger.warning("No text extracted from PDF using primary method, trying fallback")
                    # Fallback for scanned PDFs or PDFs with security features
                    text = self._extract_text_from_pdf_fallback(file_path)
                    
        except Exception as e:
            self.logger.error(f"Error processing PDF file: {str(e)}")
            # Try fallback method
            text = self._extract_text_from_pdf_fallback(file_path)
            
        # If text is still empty, provide a placeholder
        if not text.strip():
            self.logger.warning(f"Unable to extract text from PDF: {file_path}")
            # Add filename as metadata in the text to improve searchability
            filename = os.path.basename(file_path)
            text = f"PDF Document: {filename}\n\nThis PDF appears to contain non-extractable content. "
            text += "It may be scanned or have security restrictions.\n"
            text += "The document may contain relevant information but text extraction was limited."
            
        # Log the extraction results
        extracted_length = len(text)
        self.logger.info(f"Extracted {extracted_length} characters from PDF")
        if extracted_length > 200:
            preview = text[:200] + "..."
        else:
            preview = text
        self.logger.info(f"Text preview: {preview}")
        
        return text
    
    def _extract_text_from_pdf_fallback(self, file_path: str) -> str:
        """Fallback method for extracting text from PDF files that are difficult to parse"""
        self.logger.info(f"Using PDF extraction fallback method for: {file_path}")
        text = ""
        
        try:
            # Try to use pdftotext if available (usually more robust for complex PDFs)
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Check if pdftotext is available
            try:
                # Run pdftotext command
                result = subprocess.run(
                    ["pdftotext", "-layout", file_path, temp_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    # Read the extracted text
                    with open(temp_path, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    self.logger.info(f"Successfully extracted text using pdftotext fallback")
                else:
                    self.logger.warning(f"pdftotext fallback failed: {result.stderr}")
            except FileNotFoundError:
                self.logger.warning("pdftotext not available on system, skipping fallback method")
            except Exception as e:
                self.logger.error(f"Error with pdftotext fallback: {str(e)}")
            
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove temp file: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"All PDF fallback extraction methods failed: {str(e)}")
        
        return text
        
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file"""
        return docx2txt.process(file_path)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks of specified size with overlap"""
        # Check if text is None or empty
        if text is None:
            print("Warning: Received None text to split")
            return ["No text content available"]
            
        if not text.strip():
            print("Warning: Received empty text to split")
            return ["No text content available"]
        
        # Clean text
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Split text into chunks
        chunks = []
        start = 0
        
        try:
            while start < len(text):
                end = start + self.chunk_size
                # If we're not at the end of the text, try to find a good break point
                if end < len(text):
                    # Look for natural break points: period followed by space, newline
                    natural_end = text.rfind('. ', start, end)
                    if natural_end != -1:
                        end = natural_end + 1  # Include the period
                    
                chunks.append(text[start:end])
                start = end - self.chunk_overlap
        except Exception as e:
            print(f"Error splitting text: {str(e)}")
            # Return a single chunk with the error message
            return ["Error processing document content"]
            
        return chunks
    
    
    def delete_file_vectors(self, file_id: str) -> None:
        """Delete embeddings for a file from Firestore"""
        # Get file info to get agent_id
        file_info = self.firebase_service.get_file(file_id)
        
        if not file_info:
            return
            
        agent_id = file_info["agent_id"]
        
        # Delete embeddings from Firestore
        try:
            deleted_count = self.firebase_service.delete_embeddings_by_file(agent_id, file_id)
            print(f"Deleted {deleted_count} embeddings from Firestore for file {file_id}")
        except Exception as e:
            print(f"Error deleting embeddings from Firestore: {str(e)}")
    
