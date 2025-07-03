"""
Chunk Analysis Service

Provides detailed analysis capabilities for chunks including:
- Content quality assessment
- Semantic similarity analysis
- Overlap analysis
- Content distribution metrics
- Chunk optimization recommendations
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import Counter
import statistics
from textstat import flesch_kincaid_grade, flesch_reading_ease
from datetime import datetime
from services.file_service import FileService
from services.content_processor import ContentProcessor
from services.agent_relevance_service import AgentRelevanceService


class ChunkAnalysisService:
    def __init__(self):
        self.file_service = FileService()
        self.content_processor = ContentProcessor()
        self.relevance_service = AgentRelevanceService()
    
    def analyze_file_chunks(self, file_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of all chunks for a given file.
        
        Args:
            file_id: The ID of the file to analyze
            
        Returns:
            Dict containing detailed chunk analysis
        """
        try:
            # First check if we have cached analysis
            file_data = self.file_service.firebase_service.get_file(file_id)
            if file_data and file_data.get("chunk_analysis") and not file_data["chunk_analysis"].get("error"):
                cached_analysis = file_data["chunk_analysis"]
                cached_analysis["file_id"] = file_id
                cached_analysis["cached"] = True
                cached_analysis["cache_timestamp"] = file_data.get("chunk_analysis_timestamp")
                return cached_analysis
            
            # If no cached analysis, compute on-demand
            # Get all chunks/embeddings for the file
            embeddings_data = self.file_service.get_file_embeddings(file_id)
            analysis_result = self._perform_chunk_analysis(embeddings_data, file_id)
            
            return analysis_result
            
        except Exception as e:
            return {
                "file_id": file_id,
                "error": f"Analysis failed: {str(e)}",
                "total_chunks": 0
            }
    
    def _perform_chunk_analysis(self, embeddings_data: Dict[str, Any], file_id: str = None) -> Dict[str, Any]:
        """
        Internal method to perform chunk analysis on embeddings data.
        Used both for pre-computing during upload and on-demand analysis.
        
        Args:
            embeddings_data: Dictionary containing embeddings and metadata
            file_id: Optional file ID for the analysis
            
        Returns:
            Dict containing detailed chunk analysis
        """
        chunks = embeddings_data.get("embeddings", [])
        file_data = {
            "filename": embeddings_data.get("filename", ""),
            "agent_id": embeddings_data.get("agent_id")
        }
        
        if not chunks:
            return {
                "file_id": file_id,
                "error": "No chunks found for this file",
                "total_chunks": 0
            }
        
        # Sort chunks by index for proper analysis
        chunks = sorted(chunks, key=lambda x: x.get("chunk_index", 0))
        
        # Perform various analyses
        analysis_result = {
            "file_id": file_id,
            "filename": file_data.get("filename", ""),
            "total_chunks": len(chunks),
            "analysis_timestamp": datetime.now().isoformat(),
            "cached": False,
            
            # Content distribution analysis
            "content_distribution": self._analyze_content_distribution(chunks),
            
            # Quality metrics analysis
            "quality_metrics": self._analyze_quality_metrics(chunks),
            
            # Readability analysis
            "readability_analysis": self._analyze_readability(chunks),
            
            # Overlap analysis
            "overlap_analysis": self._analyze_overlap(chunks),
            
            # Semantic similarity analysis
            "semantic_analysis": self._analyze_semantic_similarity(chunks),
            
            # Content type distribution
            "content_type_analysis": self._analyze_content_types(chunks),
            
            # Agent relevance analysis
            "relevance_analysis": self._analyze_relevance_metrics(chunks, file_data.get("agent_id")),
            
            # Chunk optimization recommendations (including relevance-based)
            "optimization_recommendations": self._generate_optimization_recommendations(chunks, file_data.get("agent_id")),
            
            # Detailed chunk information
            "chunk_details": self._get_detailed_chunk_info(chunks, file_data.get("agent_id"))
        }
        
        return analysis_result
    
    def _analyze_content_distribution(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze the distribution of content across chunks."""
        chunk_sizes = [len(chunk.get("content", "")) for chunk in chunks]
        word_counts = [len(chunk.get("content", "").split()) for chunk in chunks]
        sentence_counts = [chunk.get("chunk_metadata", {}).get("sentence_count", 0) for chunk in chunks]
        
        return {
            "size_distribution": {
                "min_chars": min(chunk_sizes) if chunk_sizes else 0,
                "max_chars": max(chunk_sizes) if chunk_sizes else 0,
                "avg_chars": statistics.mean(chunk_sizes) if chunk_sizes else 0,
                "median_chars": statistics.median(chunk_sizes) if chunk_sizes else 0,
                "std_dev_chars": statistics.stdev(chunk_sizes) if len(chunk_sizes) > 1 else 0
            },
            "word_distribution": {
                "min_words": min(word_counts) if word_counts else 0,
                "max_words": max(word_counts) if word_counts else 0,
                "avg_words": statistics.mean(word_counts) if word_counts else 0,
                "median_words": statistics.median(word_counts) if word_counts else 0,
                "total_words": sum(word_counts)
            },
            "sentence_distribution": {
                "min_sentences": min(sentence_counts) if sentence_counts else 0,
                "max_sentences": max(sentence_counts) if sentence_counts else 0,
                "avg_sentences": statistics.mean(sentence_counts) if sentence_counts else 0,
                "total_sentences": sum(sentence_counts)
            }
        }
    
    def _analyze_quality_metrics(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze quality metrics across chunks."""
        quality_scores = []
        processing_qualities = []
        
        for chunk in chunks:
            # Individual chunk quality based on content characteristics
            content = chunk.get("content", "")
            quality_score = self._calculate_chunk_quality(content)
            quality_scores.append(quality_score)
            
            # Processing quality from metadata
            processing_quality = chunk.get("chunk_metadata", {}).get("quality_score", 0)
            if processing_quality > 0:
                processing_qualities.append(processing_quality)
        
        return {
            "content_quality": {
                "avg_score": statistics.mean(quality_scores) if quality_scores else 0,
                "min_score": min(quality_scores) if quality_scores else 0,
                "max_score": max(quality_scores) if quality_scores else 0,
                "distribution": self._get_quality_distribution(quality_scores)
            },
            "processing_quality": {
                "avg_score": statistics.mean(processing_qualities) if processing_qualities else 0,
                "chunks_with_scores": len(processing_qualities),
                "distribution": self._get_quality_distribution(processing_qualities) if processing_qualities else {}
            }
        }
    
    def _analyze_readability(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze readability metrics across chunks."""
        readability_scores = []
        ease_scores = []
        
        for chunk in chunks:
            content = chunk.get("content", "").strip()
            if len(content) > 10:  # Only analyze chunks with substantial content
                try:
                    fk_grade = flesch_kincaid_grade(content)
                    ease_score = flesch_reading_ease(content)
                    
                    if 0 <= fk_grade <= 20:  # Reasonable bounds
                        readability_scores.append(fk_grade)
                    if 0 <= ease_score <= 100:  # Reasonable bounds
                        ease_scores.append(ease_score)
                except:
                    pass  # Skip chunks that cause textstat errors
        
        return {
            "flesch_kincaid_grade": {
                "avg_grade": statistics.mean(readability_scores) if readability_scores else 0,
                "min_grade": min(readability_scores) if readability_scores else 0,
                "max_grade": max(readability_scores) if readability_scores else 0,
                "chunks_analyzed": len(readability_scores)
            },
            "reading_ease": {
                "avg_ease": statistics.mean(ease_scores) if ease_scores else 0,
                "min_ease": min(ease_scores) if ease_scores else 0,
                "max_ease": max(ease_scores) if ease_scores else 0,
                "difficulty_level": self._get_difficulty_level(statistics.mean(ease_scores) if ease_scores else 0)
            }
        }
    
    def _analyze_overlap(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze overlap between consecutive chunks."""
        overlap_lengths = []
        overlap_percentages = []
        
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            overlap_content = current_chunk.get("overlap_content", "")
            if overlap_content:
                overlap_length = len(overlap_content)
                current_length = len(current_chunk.get("content", ""))
                
                overlap_lengths.append(overlap_length)
                if current_length > 0:
                    overlap_percentage = (overlap_length / current_length) * 100
                    overlap_percentages.append(overlap_percentage)
        
        return {
            "overlap_statistics": {
                "avg_overlap_chars": statistics.mean(overlap_lengths) if overlap_lengths else 0,
                "avg_overlap_percentage": statistics.mean(overlap_percentages) if overlap_percentages else 0,
                "min_overlap": min(overlap_lengths) if overlap_lengths else 0,
                "max_overlap": max(overlap_lengths) if overlap_lengths else 0,
                "chunks_with_overlap": len(overlap_lengths)
            },
            "overlap_consistency": {
                "std_dev_percentage": statistics.stdev(overlap_percentages) if len(overlap_percentages) > 1 else 0,
                "is_consistent": statistics.stdev(overlap_percentages) < 5 if len(overlap_percentages) > 1 else True
            }
        }
    
    def _analyze_semantic_similarity(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze semantic similarity between chunks using embeddings."""
        try:
            embeddings = []
            valid_chunks = []
            
            for chunk in chunks:
                embedding = chunk.get("embedding")
                if embedding and len(embedding) > 0:
                    embeddings.append(embedding)
                    valid_chunks.append(chunk)
            
            if len(embeddings) < 2:
                return {
                    "similarity_analysis": "Insufficient embeddings for analysis",
                    "chunks_with_embeddings": len(embeddings)
                }
            
            # Calculate pairwise similarities
            embeddings_array = np.array(embeddings)
            similarity_matrix = cosine_similarity(embeddings_array)
            
            # Extract upper triangle (excluding diagonal)
            similarities = []
            for i in range(len(similarity_matrix)):
                for j in range(i + 1, len(similarity_matrix)):
                    similarities.append(similarity_matrix[i][j])
            
            # Find most and least similar chunk pairs
            max_similarity_idx = np.unravel_index(np.argmax(similarity_matrix - np.eye(len(similarity_matrix))), similarity_matrix.shape)
            min_similarity_idx = np.unravel_index(np.argmin(similarity_matrix + np.eye(len(similarity_matrix))), similarity_matrix.shape)
            
            return {
                "similarity_statistics": {
                    "avg_similarity": statistics.mean(similarities) if similarities else 0,
                    "min_similarity": min(similarities) if similarities else 0,
                    "max_similarity": max(similarities) if similarities else 0,
                    "std_dev_similarity": statistics.stdev(similarities) if len(similarities) > 1 else 0
                },
                "most_similar_pair": {
                    "chunk_indices": [int(max_similarity_idx[0]), int(max_similarity_idx[1])],
                    "similarity_score": float(similarity_matrix[max_similarity_idx])
                },
                "least_similar_pair": {
                    "chunk_indices": [int(min_similarity_idx[0]), int(min_similarity_idx[1])],
                    "similarity_score": float(similarity_matrix[min_similarity_idx])
                },
                "chunks_analyzed": len(embeddings)
            }
            
        except Exception as e:
            return {
                "similarity_analysis": f"Error in similarity analysis: {str(e)}",
                "chunks_analyzed": 0
            }
    
    def _analyze_content_types(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze the distribution of content types across chunks."""
        content_types = [chunk.get("chunk_metadata", {}).get("content_type", "unknown") for chunk in chunks]
        type_distribution = Counter(content_types)
        
        # Analyze content characteristics
        code_chunks = sum(1 for chunk in chunks if self._is_code_content(chunk.get("content", "")))
        table_chunks = sum(1 for chunk in chunks if self._contains_tables(chunk.get("content", "")))
        list_chunks = sum(1 for chunk in chunks if self._contains_lists(chunk.get("content", "")))
        
        return {
            "type_distribution": dict(type_distribution),
            "content_characteristics": {
                "code_chunks": code_chunks,
                "table_chunks": table_chunks,
                "list_chunks": list_chunks,
                "plain_text_chunks": len(chunks) - code_chunks - table_chunks - list_chunks
            },
            "dominant_type": type_distribution.most_common(1)[0][0] if type_distribution else "unknown"
        }
    
    def _generate_optimization_recommendations(self, chunks: List[Dict], agent_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Generate recommendations for chunk optimization."""
        recommendations = []
        
        # Analyze chunk sizes
        chunk_sizes = [len(chunk.get("content", "")) for chunk in chunks]
        avg_size = statistics.mean(chunk_sizes) if chunk_sizes else 0
        
        if avg_size < 500:
            recommendations.append({
                "type": "size_optimization",
                "severity": "medium",
                "title": "Small Chunk Size",
                "description": f"Average chunk size is {avg_size:.0f} characters. Consider increasing chunk size for better context.",
                "suggestion": "Increase chunk size to 800-1200 characters for optimal semantic coherence."
            })
        elif avg_size > 1500:
            recommendations.append({
                "type": "size_optimization",
                "severity": "medium",
                "title": "Large Chunk Size",
                "description": f"Average chunk size is {avg_size:.0f} characters. Consider reducing chunk size for better retrieval precision.",
                "suggestion": "Reduce chunk size to 800-1200 characters for optimal retrieval performance."
            })
        
        # Analyze overlap consistency
        overlap_percentages = []
        for i in range(len(chunks) - 1):
            overlap_content = chunks[i].get("overlap_content", "")
            if overlap_content:
                current_length = len(chunks[i].get("content", ""))
                if current_length > 0:
                    overlap_percentage = (len(overlap_content) / current_length) * 100
                    overlap_percentages.append(overlap_percentage)
        
        if overlap_percentages and len(overlap_percentages) > 1:
            try:
                overlap_stdev = statistics.stdev(overlap_percentages)
                if overlap_stdev > 10:
                    recommendations.append({
                        "type": "overlap_optimization",
                        "severity": "low",
                        "title": "Inconsistent Overlap",
                        "description": "Overlap between chunks varies significantly, which may affect retrieval consistency.",
                        "suggestion": "Configure consistent overlap percentage (15-20%) for better context preservation."
                    })
            except statistics.StatisticsError:
                # Handle edge case where stdev calculation fails
                pass
        
        # Analyze quality distribution using standardized scoring
        quality_scores = [self._calculate_chunk_quality(chunk.get("content", "")) for chunk in chunks]
        low_quality_chunks = sum(1 for score in quality_scores if score < 60)
        
        if low_quality_chunks > len(chunks) * 0.3:
            recommendations.append({
                "type": "quality_optimization",
                "severity": "high",
                "title": "Low Quality Chunks",
                "description": f"{low_quality_chunks} chunks have low quality scores. This may affect retrieval accuracy.",
                "suggestion": "Review and reprocess the file with enhanced content cleaning to improve chunk quality."
            })
        
        # Add relevance-based recommendations if agent context is available
        if agent_id and self.relevance_service.openai_available:
            try:
                # Quick relevance check on a sample of chunks
                sample_content = ""
                for chunk in chunks[:3]:  # Sample first 3 chunks
                    sample_content += chunk.get("content", "") + "\n\n"
                
                if sample_content.strip():
                    relevance_result = self.relevance_service.assess_content_relevance(
                        content=sample_content[:2000],  # Limit to 2000 chars for quick assessment
                        agent_id=agent_id,
                        content_type="text",
                        filename="sample_chunks"
                    )
                    
                    relevance_score = relevance_result.get("relevance_score", 50)
                    
                    if relevance_score < 60:
                        recommendations.append({
                            "type": "agent_relevance",
                            "severity": "high",
                            "title": "Low Agent Relevance",
                            "description": f"Content relevance to agent is {relevance_score}%. This may reduce retrieval effectiveness.",
                            "suggestion": "Consider reviewing content alignment with agent's domain and purpose."
                        })
                    elif relevance_score >= 85:
                        recommendations.append({
                            "type": "agent_relevance", 
                            "severity": "info",
                            "title": "Excellent Agent Relevance",
                            "description": f"Content shows high relevance ({relevance_score}%) to the agent's purpose.",
                            "suggestion": "This content is well-aligned with the agent. Consider similar knowledge sources."
                        })
            except Exception:
                # Don't fail optimization recommendations if relevance check fails
                pass
        
        return recommendations
    
    def _analyze_relevance_metrics(self, chunks: List[Dict], agent_id: Optional[str]) -> Dict[str, Any]:
        """Analyze agent-specific relevance metrics for chunks."""
        if not agent_id or not self.relevance_service.openai_available:
            return {
                "analysis_status": "unavailable",
                "reason": "No agent ID provided" if not agent_id else "OpenAI not available",
                "chunk_relevance_scores": [],
                "overall_relevance": 0
            }
        
        try:
            relevance_scores = []
            relevance_details = []
            
            # Analyze relevance for each chunk (sample first 5 chunks to avoid rate limits)
            sample_chunks = chunks[:5] if len(chunks) > 5 else chunks
            
            for i, chunk in enumerate(sample_chunks):
                content = chunk.get("content", "").strip()
                if len(content) < 50:  # Skip very short chunks
                    continue
                
                try:
                    # Assess chunk relevance
                    relevance_result = self.relevance_service.assess_content_relevance(
                        content=content,
                        agent_id=agent_id,
                        content_type="text",
                        filename=f"chunk_{i}"
                    )
                    
                    relevance_score = relevance_result.get("relevance_score", 50)
                    relevance_scores.append(relevance_score)
                    
                    relevance_details.append({
                        "chunk_index": i,
                        "relevance_score": relevance_score,
                        "domain_alignment": relevance_result.get("domain_alignment", 50),
                        "purpose_relevance": relevance_result.get("purpose_relevance", 50),
                        "knowledge_value": relevance_result.get("knowledge_value", 50),
                        "content_category": relevance_result.get("content_category", "medium_relevance"),
                        "key_topics": relevance_result.get("key_topics", [])[:3]  # Top 3 topics
                    })
                    
                except Exception as e:
                    # Continue with other chunks if one fails
                    relevance_details.append({
                        "chunk_index": i,
                        "relevance_score": 50,
                        "error": f"Assessment failed: {str(e)}"
                    })
            
            # Calculate overall metrics
            avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0
            
            # Categorize relevance distribution
            relevance_distribution = {
                "high_relevance": sum(1 for score in relevance_scores if score >= 80),
                "medium_relevance": sum(1 for score in relevance_scores if 50 <= score < 80),
                "low_relevance": sum(1 for score in relevance_scores if score < 50)
            }
            
            return {
                "analysis_status": "completed",
                "agent_id": agent_id,
                "chunks_analyzed": len(relevance_details),
                "total_chunks": len(chunks),
                "overall_relevance": round(avg_relevance, 2),
                "relevance_distribution": relevance_distribution,
                "chunk_relevance_details": relevance_details,
                "recommendations": self._generate_relevance_recommendations(avg_relevance, relevance_distribution)
            }
            
        except Exception as e:
            return {
                "analysis_status": "error",
                "error": f"Relevance analysis failed: {str(e)}",
                "chunks_analyzed": 0,
                "overall_relevance": 0
            }
    
    def _generate_relevance_recommendations(self, avg_relevance: float, distribution: Dict[str, int]) -> List[Dict[str, str]]:
        """Generate recommendations based on relevance analysis."""
        recommendations = []
        
        if avg_relevance < 60:
            recommendations.append({
                "type": "relevance_optimization",
                "severity": "high",
                "title": "Low Agent Relevance",
                "description": f"Average relevance score is {avg_relevance:.1f}%. Content may not align well with agent's purpose.",
                "suggestion": "Review content for agent-specific value or consider more targeted knowledge sources."
            })
        
        if distribution.get("low_relevance", 0) > distribution.get("high_relevance", 0):
            recommendations.append({
                "type": "content_curation",
                "severity": "medium",
                "title": "Irrelevant Content Detected",
                "description": "Significant portions of content have low relevance to the agent.",
                "suggestion": "Consider content filtering or preprocessing to focus on agent-relevant information."
            })
        
        if avg_relevance >= 80:
            recommendations.append({
                "type": "content_quality",
                "severity": "info",
                "title": "High Relevance Content",
                "description": f"Content shows high relevance ({avg_relevance:.1f}%) to the agent's domain and purpose.",
                "suggestion": "This is high-quality knowledge for the agent. Consider similar content sources."
            })
        
        return recommendations
    
    def _get_detailed_chunk_info(self, chunks: List[Dict], agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get detailed information for each chunk."""
        detailed_info = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("chunk_metadata", {})
            
            chunk_info = {
                "chunk_index": i,
                "chunk_id": chunk.get("id", f"chunk_{i}"),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "full_content_length": len(content),
                "word_count": len(content.split()),
                "sentence_count": metadata.get("sentence_count", 0),
                "content_type": metadata.get("content_type", "unknown"),
                "quality_score": self._calculate_chunk_quality(content),
                "processing_metadata": {
                    "has_overlap": bool(chunk.get("overlap_content")),
                    "overlap_length": len(chunk.get("overlap_content", "")),
                    "chunk_size": len(content),
                    "timestamp": chunk.get("timestamp"),
                    "embedding_available": bool(chunk.get("embedding"))
                }
            }
            
            # Add readability metrics if content is substantial
            if len(content) > 10:
                try:
                    chunk_info["readability"] = {
                        "flesch_kincaid_grade": flesch_kincaid_grade(content),
                        "reading_ease": flesch_reading_ease(content)
                    }
                except:
                    chunk_info["readability"] = {"error": "Unable to calculate readability"}
            
            detailed_info.append(chunk_info)
        
        return detailed_info
    
    def _calculate_chunk_quality(self, content: str) -> float:
        """Calculate quality score using standardized criteria from ContentProcessor."""
        return self.content_processor._calculate_quality_score(content)
    
    def _get_quality_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Get distribution of quality scores."""
        if not scores:
            return {"high": 0, "medium": 0, "low": 0}
        
        return {
            "high": sum(1 for score in scores if score >= 80),
            "medium": sum(1 for score in scores if 60 <= score < 80),
            "low": sum(1 for score in scores if score < 60)
        }
    
    def _get_difficulty_level(self, ease_score: float) -> str:
        """Get difficulty level based on reading ease score."""
        if ease_score >= 90:
            return "Very Easy"
        elif ease_score >= 80:
            return "Easy"
        elif ease_score >= 70:
            return "Fairly Easy"
        elif ease_score >= 60:
            return "Standard"
        elif ease_score >= 50:
            return "Fairly Difficult"
        elif ease_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _is_code_content(self, content: str) -> bool:
        """Check if content appears to be code."""
        code_indicators = [
            r'\{.*\}',  # Braces
            r'function\s+\w+\s*\(',  # Function definitions
            r'def\s+\w+\s*\(',  # Python functions
            r'class\s+\w+',  # Class definitions
            r'import\s+\w+',  # Import statements
            r'#include\s*<',  # C/C++ includes
            r'\/\/.*',  # Line comments
            r'\/\*.*\*\/',  # Block comments
        ]
        
        code_matches = sum(1 for pattern in code_indicators if re.search(pattern, content))
        return code_matches >= 2
    
    def _contains_tables(self, content: str) -> bool:
        """Check if content contains table-like structures."""
        table_indicators = [
            r'\|.*\|',  # Pipe-separated values
            r'\t.*\t',  # Tab-separated values
            r'^\s*\|.*\|\s*$',  # Markdown tables
        ]
        
        return any(re.search(pattern, content, re.MULTILINE) for pattern in table_indicators)
    
    def _contains_lists(self, content: str) -> bool:
        """Check if content contains list structures."""
        list_indicators = [
            r'^\s*[-*+]\s+',  # Bullet points
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*[a-zA-Z]\.\s+',  # Lettered lists
        ]
        
        return any(re.search(pattern, content, re.MULTILINE) for pattern in list_indicators)