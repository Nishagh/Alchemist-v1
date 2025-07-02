import re
import string
from openai import OpenAI
import json
from typing import Dict, List, Tuple, Any
from bs4 import BeautifulSoup
from utils.logging_config import get_logger, log_with_data
from alchemist_shared.config.base_settings import BaseSettings
from services.agent_relevance_service import AgentRelevanceService

class ContentProcessor:
    def __init__(self):
        self.logger = get_logger("ContentProcessor")
        self.logger.info("Initializing Content Processor")
        
        # Initialize OpenAI for AI-powered content cleaning
        self.settings = BaseSettings()
        openai_config = self.settings.get_openai_config()
        api_key = openai_config.get("api_key")
        self.openai_available = bool(api_key)
        
        if self.openai_available:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
        
        # Initialize Agent Relevance Service
        self.relevance_service = AgentRelevanceService()
        
        if self.openai_available:
            self.logger.info("OpenAI initialized for AI-powered content cleaning and relevance assessment")
        else:
            self.logger.warning("OpenAI not available, falling back to rule-based cleaning")
        
        # Quality thresholds (used as fallback for rule-based cleaning)
        self.min_paragraph_length = 20
        self.min_sentence_length = 10
        self.max_repetition_ratio = 0.3
        self.min_word_count = 5
        
    def process_content(self, text: str, content_type: str = None, filename: str = None, agent_id: str = None, enable_cleaning: bool = False) -> Dict[str, Any]:
        """
        Main content processing pipeline that cleans and enhances text with agent-specific relevance assessment
        
        Args:
            text: Raw extracted text
            content_type: MIME type of original file
            filename: Original filename
            agent_id: ID of the agent for relevance assessment
            enable_cleaning: Whether to apply content cleaning (default: False)
            
        Returns:
            Dictionary with processed content, metadata, and relevance assessment
        """
        log_with_data(self.logger, "INFO", "Starting content processing", {
            "content_length": len(text),
            "content_type": content_type,
            "filename": filename
        })
        
        # Store original for comparison
        original_text = text
        original_length = len(text)
        
        # Step 1: Basic text cleaning (minimal preprocessing)
        cleaned_text = self._basic_text_cleaning(text)
        
        # Step 2: Apply cleaning based on user preference
        if not enable_cleaning:
            self.logger.info("Content cleaning disabled by user - using original content")
            quality_filtered_text = cleaned_text
            quality_stats = {
                "ai_cleaning_used": False,
                "cleaning_skipped": True,
                "reason": "user_disabled",
                "removed_sentences": 0,
                "quality_issues": [],
                "user_controlled": True
            }
        else:
            # Step 2.5: Check if content already has perfect quality - skip cleaning if so
            original_quality = self._calculate_quality_score(cleaned_text)
            
            if original_quality >= 100.0:
                self.logger.info(f"Content already has perfect quality ({original_quality}%), skipping cleaning")
                quality_filtered_text = cleaned_text
                quality_stats = {
                    "ai_cleaning_used": False,
                    "cleaning_skipped": True,
                    "reason": "perfect_quality",
                    "removed_sentences": 0,
                    "quality_issues": [],
                    "user_controlled": False
                }
            else:
                # Step 3: AI-powered intelligent cleaning (if available)
                if self.openai_available:
                    ai_cleaned_text = self._ai_powered_content_cleaning(cleaned_text, content_type)
                    
                    # Use AI cleaned version as the final result
                    quality_filtered_text = ai_cleaned_text
                    quality_stats = {
                        "ai_cleaning_used": True,
                        "cleaning_skipped": False,
                        "removed_sentences": 0,
                        "quality_issues": ["ai_cleaned"],
                        "user_controlled": False
                    }
                else:
                    # Fallback to rule-based cleaning (much less aggressive)
                    # Step 3: Remove structural artifacts
                    cleaned_text = self._remove_structural_artifacts(cleaned_text, content_type)
                    
                    # Step 4: Content deduplication
                    cleaned_text = self._remove_duplicate_content(cleaned_text)
                    
                    # Step 5: Light quality filtering (less aggressive than before)
                    quality_filtered_text, quality_stats = self._light_quality_filtering(cleaned_text)
                    quality_stats["cleaning_skipped"] = False
                    quality_stats["user_controlled"] = False
        
        # Step 6: Agent-specific relevance assessment
        relevance_assessment = None
        if agent_id and self.openai_available:
            try:
                relevance_assessment = self.relevance_service.assess_content_relevance(
                    quality_filtered_text, agent_id, content_type, filename
                )
                self.logger.info(f"Content relevance assessed for agent {agent_id}: {relevance_assessment.get('relevance_score', 'N/A')}/100")
            except Exception as e:
                self.logger.error(f"Relevance assessment failed for agent {agent_id}: {e}")
                relevance_assessment = {"error": str(e), "relevance_score": 50}
        
        # Step 7: Extract metadata
        metadata = self._extract_content_metadata(quality_filtered_text, filename)
        
        # Calculate processing statistics
        final_length = len(quality_filtered_text)
        reduction_percentage = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        
        processing_stats = {
            "original_length": original_length,
            "final_length": final_length,
            "characters_removed": original_length - final_length,
            "reduction_percentage": round(reduction_percentage, 2),
            "quality_score": self._calculate_quality_score(quality_filtered_text),
            "word_count": len(quality_filtered_text.split()),
            "paragraph_count": len([p for p in quality_filtered_text.split('\n\n') if p.strip()]),
            "relevance_assessment": relevance_assessment,
            "agent_id": agent_id,
            **quality_stats
        }
        
        # Calculate agent-specific composite score if relevance assessment is available
        agent_specific_quality = None
        if relevance_assessment and relevance_assessment.get("relevance_score") is not None:
            agent_specific_quality = self._calculate_agent_specific_quality(
                processing_stats["quality_score"], 
                relevance_assessment["relevance_score"]
            )
            processing_stats["agent_specific_quality"] = agent_specific_quality
            self.logger.info(f"Agent-specific quality: {agent_specific_quality}% (content: {processing_stats['quality_score']}%, relevance: {relevance_assessment['relevance_score']}%)")

        log_with_data(self.logger, "INFO", "Content processing completed", processing_stats)
        
        return {
            "original_text": original_text,
            "processed_text": quality_filtered_text,
            "metadata": metadata,
            "processing_stats": processing_stats,
            "quality_score": processing_stats["quality_score"],
            "relevance_assessment": relevance_assessment,
            "relevance_score": relevance_assessment.get("relevance_score", None) if relevance_assessment else None,
            "agent_specific_quality": agent_specific_quality
        }
    
    def _basic_text_cleaning(self, text: str) -> str:
        """Basic text cleaning operations"""
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)  # Windows line endings
        text = re.sub(r'\r', '\n', text)    # Old Mac line endings
        
        # Remove excessive whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double newline
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
        
        # Fix common encoding issues
        text = text.replace('\ufffd', '')  # Remove replacement characters
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _remove_structural_artifacts(self, text: str, content_type: str = None) -> str:
        """Remove structural artifacts based on content type"""
        if not text:
            return ""
        
        # PDF-specific artifacts
        if content_type and 'pdf' in content_type.lower():
            text = self._clean_pdf_artifacts(text)
        
        # HTML-specific artifacts
        if content_type and 'html' in content_type.lower():
            text = self._clean_html_artifacts(text)
        
        # Word document artifacts
        if content_type and 'word' in content_type.lower():
            text = self._clean_word_artifacts(text)
        
        # General structural cleaning
        text = self._clean_general_artifacts(text)
        
        return text
    
    def _clean_pdf_artifacts(self, text: str) -> str:
        """Clean PDF-specific artifacts"""
        # Remove page numbers (standalone numbers on lines)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove headers/footers (repeated text patterns)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines that are likely artifacts
            if len(line) < 3:
                continue
            # Skip lines that are just punctuation or numbers
            if re.match(r'^[\d\s\-_.]+$', line):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _clean_html_artifacts(self, text: str) -> str:
        """Clean HTML-specific artifacts"""
        # Remove HTML entities that might have been missed
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        
        # Remove navigation artifacts
        text = re.sub(r'(?i)(home|about|contact|menu|navigation|breadcrumb)', '', text)
        
        return text
    
    def _clean_word_artifacts(self, text: str) -> str:
        """Clean Word document artifacts"""
        # Remove embedded object placeholders
        text = re.sub(r'\[EMBED[^\]]*\]', '', text)
        text = re.sub(r'\{[^}]*object[^}]*\}', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _clean_general_artifacts(self, text: str) -> str:
        """Clean general structural artifacts"""
        # Remove table of contents patterns
        text = re.sub(r'\.{3,}', '', text)  # Dotted lines
        text = re.sub(r'-{3,}', '', text)   # Dashed lines
        text = re.sub(r'_{3,}', '', text)   # Underlined sections
        
        # Remove standalone punctuation lines
        text = re.sub(r'^\s*[^\w\s]*\s*$', '', text, flags=re.MULTILINE)
        
        # Remove excessive spacing artifacts
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text
    
    def _remove_duplicate_content(self, text: str) -> str:
        """Remove duplicate paragraphs and repeated content"""
        if not text:
            return ""
        
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        seen_paragraphs = set()
        unique_paragraphs = []
        
        for paragraph in paragraphs:
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', paragraph.lower())
            
            # Skip very short paragraphs
            if len(normalized) < self.min_paragraph_length:
                continue
            
            # Check for exact duplicates
            if normalized not in seen_paragraphs:
                seen_paragraphs.add(normalized)
                unique_paragraphs.append(paragraph)
            else:
                self.logger.debug(f"Removed duplicate paragraph: {paragraph[:50]}...")
        
        return '\n\n'.join(unique_paragraphs)
    
    def _filter_low_quality_content(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Filter out low-quality content and return statistics"""
        if not text:
            return "", {"removed_sentences": 0, "quality_issues": []}
        
        sentences = self._split_into_sentences(text)
        quality_sentences = []
        removed_count = 0
        quality_issues = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip empty sentences
            if not sentence:
                continue
            
            # Check minimum length
            if len(sentence) < self.min_sentence_length:
                removed_count += 1
                quality_issues.append("too_short")
                continue
            
            # Check minimum word count
            word_count = len(sentence.split())
            if word_count < self.min_word_count:
                removed_count += 1
                quality_issues.append("too_few_words")
                continue
            
            # Check for excessive repetition
            if self._has_excessive_repetition(sentence):
                removed_count += 1
                quality_issues.append("excessive_repetition")
                continue
            
            # Check if mostly punctuation or numbers
            text_chars = sum(1 for c in sentence if c.isalpha())
            if text_chars / len(sentence) < 0.5:
                removed_count += 1
                quality_issues.append("mostly_non_text")
                continue
            
            quality_sentences.append(sentence)
        
        # Reconstruct text with quality sentences
        quality_text = ' '.join(quality_sentences)
        
        # Group paragraphs back together
        quality_text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', quality_text)
        
        stats = {
            "removed_sentences": removed_count,
            "quality_issues": list(set(quality_issues)),
            "retained_sentences": len(quality_sentences)
        }
        
        return quality_text, stats
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _has_excessive_repetition(self, text: str) -> bool:
        """Check if text has excessive character or word repetition"""
        if len(text) < 10:
            return False
        
        # Check for repeated characters
        for char in text:
            if char.isalnum() and text.count(char) / len(text) > self.max_repetition_ratio:
                return True
        
        # Check for repeated words
        words = text.split()
        if len(words) > 3:
            word_counts = {}
            for word in words:
                word_lower = word.lower()
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
            
            for count in word_counts.values():
                if count / len(words) > self.max_repetition_ratio:
                    return True
        
        return False
    
    def _extract_content_metadata(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Extract metadata from content"""
        if not text:
            return {}
        
        words = text.split()
        sentences = self._split_into_sentences(text)
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        # Extract potential titles (first few words, capitalized phrases)
        title_candidates = []
        if filename:
            title_candidates.append(filename.replace('_', ' ').replace('-', ' '))
        
        # Look for title-like patterns in the first paragraph
        if paragraphs:
            first_para = paragraphs[0]
            if len(first_para) < 100:  # Likely a title if short
                title_candidates.append(first_para.strip())
        
        # Extract key terms (capitalized words, frequent terms)
        key_terms = self._extract_key_terms(text)
        
        return {
            "estimated_title": title_candidates[0] if title_candidates else "Untitled Document",
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "key_terms": key_terms[:10],  # Top 10 key terms
            "language_detected": "en",  # Could be enhanced with actual language detection
            "content_type_guess": self._guess_content_type(text)
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Simple key term extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', text)  # Capitalized words
        
        # Count frequency
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [term for term, count in sorted_terms if count > 1]
    
    def _guess_content_type(self, text: str) -> str:
        """Guess the content type based on text patterns"""
        if not text:
            return "unknown"
        
        # Look for patterns
        if re.search(r'def\s+\w+\(|class\s+\w+:', text):
            return "code"
        elif re.search(r'^\s*#', text, re.MULTILINE):
            return "documentation"
        elif re.search(r'\$|\€|\£|price|cost|total', text, re.IGNORECASE):
            return "financial"
        elif re.search(r'method|result|conclusion|abstract', text, re.IGNORECASE):
            return "research"
        else:
            return "general"
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate overall quality score (0-100)"""
        if not text:
            return 0.0
        
        score = 100.0
        
        # Penalize very short content
        if len(text) < 100:
            score -= 20
        
        # Reward proper sentence structure
        sentences = self._split_into_sentences(text)
        if len(sentences) > 0:
            avg_sentence_length = len(text) / len(sentences)
            if 10 <= avg_sentence_length <= 100:
                score += 10
            else:
                score -= 5
        
        # Check vocabulary diversity
        words = text.split()
        if len(words) > 0:
            unique_words = set(word.lower() for word in words)
            diversity_ratio = len(unique_words) / len(words)
            if diversity_ratio > 0.3:
                score += 10
            else:
                score -= 10
        
        # Penalize excessive repetition
        if self._has_excessive_repetition(text):
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _calculate_agent_specific_quality(self, content_quality: float, relevance_score: float) -> float:
        """
        Calculate agent-specific quality score with heavy preference for relevance over content quality.
        
        This provides a meaningful score for agents by prioritizing:
        - Relevance (85% weight): How useful the content is for the agent's specific domain/purpose
        - Content Quality (15% weight): How well-written and structured the content is
        
        Additional penalties are applied for low relevance since agents need domain-specific content:
        - Relevance < 30%: Heavy penalty (up to 30 points reduction)
        - Relevance 30-50%: Moderate penalty (up to 10 points reduction)
        
        Args:
            content_quality: Content structure/writing quality (0-100)
            relevance_score: Agent-specific relevance score (0-100)
            
        Returns:
            Combined agent-specific quality score (0-100) heavily weighted toward relevance
        """
        # Prioritize relevance heavily over content quality for agent usefulness
        # 85% relevance, 15% content quality
        relevance_weight = 0.85
        content_weight = 0.15
        
        # Calculate weighted score
        agent_specific_score = (relevance_score * relevance_weight) + (content_quality * content_weight)
        
        # Apply aggressive penalty for low relevance since relevance is paramount for agents
        if relevance_score < 30:
            # Apply additional penalty - reduce score by up to 30 points for very low relevance
            penalty = (30 - relevance_score) * 1.5  # 1.5 point penalty per relevance point below 30
            agent_specific_score = max(0, agent_specific_score - penalty)
        elif relevance_score < 50:
            # Apply moderate penalty for mediocre relevance
            penalty = (50 - relevance_score) * 0.5  # 0.5 point penalty per relevance point below 50
            agent_specific_score = max(0, agent_specific_score - penalty)
        
        return round(max(0.0, min(100.0, agent_specific_score)), 2)
    
    def _ai_powered_content_cleaning(self, text: str, content_type: str = None) -> str:
        """Use OpenAI to intelligently clean content while preserving meaning and quality."""
        if not self.openai_available or not text.strip():
            return text
        
        try:
            # Design intelligent prompt for content cleaning
            prompt = f"""You are an expert content editor helping to clean and improve text for a knowledge base. Your goal is to make the content cleaner and more readable while preserving ALL important information and meaning.

INSTRUCTIONS:
1. Remove only truly redundant or meaningless content (random characters, excessive whitespace, obvious OCR errors)
2. Fix obvious spelling and grammar mistakes
3. Improve paragraph structure and readability
4. Preserve ALL meaningful information, technical details, lists, and data
5. Keep the original tone and style
6. Do NOT remove content just because it's technical, has numbers, or contains specialized terminology
7. Do NOT shorten the content unnecessarily - preserve comprehensive information

Content Type: {content_type or 'general'}

Original Text:
{text[:4000]}  

Please return only the cleaned version of the text, maintaining the same level of detail and information richness. Focus on clarity while preserving completeness:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistent, conservative editing
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            
            # Validate that cleaning didn't remove too much content
            original_words = len(text.split())
            cleaned_words = len(cleaned_text.split())
            
            # If AI removed more than 40% of content, fall back to original
            if cleaned_words < (original_words * 0.6):
                self.logger.warning(f"AI cleaning removed too much content ({cleaned_words}/{original_words} words), using original")
                return text
            
            self.logger.info(f"AI content cleaning: {original_words} → {cleaned_words} words ({((cleaned_words/original_words)*100):.1f}% retained)")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"AI content cleaning failed: {e}, falling back to original text")
            return text
    
    def _light_quality_filtering(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Light quality filtering as fallback when AI cleaning is not available."""
        if not text:
            return "", {"removed_sentences": 0, "quality_issues": []}
        
        sentences = self._split_into_sentences(text)
        quality_sentences = []
        removed_count = 0
        quality_issues = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip empty sentences
            if not sentence:
                continue
            
            # Only remove obviously broken content (much more lenient)
            if len(sentence) < 3:  # Very short fragments
                removed_count += 1
                quality_issues.append("too_short")
                continue
            
            # Only remove if entirely non-text (very lenient)
            text_chars = sum(1 for c in sentence if c.isalpha())
            if len(sentence) > 10 and text_chars / len(sentence) < 0.1:  # Less than 10% text
                removed_count += 1
                quality_issues.append("mostly_non_text")
                continue
            
            quality_sentences.append(sentence)
        
        # Reconstruct text with quality sentences
        quality_text = ' '.join(quality_sentences)
        
        # Group paragraphs back together
        quality_text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', quality_text)
        
        return quality_text, {
            "removed_sentences": removed_count,
            "quality_issues": quality_issues,
            "ai_cleaning_used": False
        }