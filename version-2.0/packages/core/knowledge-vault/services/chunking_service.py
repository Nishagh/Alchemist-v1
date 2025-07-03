import re
import math
from typing import List, Dict, Any, Tuple
from utils.logging_config import get_logger, log_with_data

class ChunkingService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.logger = get_logger("ChunkingService")
        self.logger.info("Initializing Smart Chunking Service")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = 100
        self.max_chunk_size = 1500
        
        # Semantic boundary patterns
        self.section_patterns = [
            r'^#+\s+',  # Markdown headers
            r'^\d+\.\s+',  # Numbered sections
            r'^[A-Z][A-Z\s]+:',  # ALL CAPS section headers
            r'^\s*Chapter\s+\d+',  # Chapter markers
            r'^\s*Section\s+\d+',  # Section markers
        ]
        
        self.paragraph_boundary_patterns = [
            r'\n\n+',  # Multiple newlines
            r'\.\s*\n\s*[A-Z]',  # Sentence end followed by new sentence
            r'[.!?]\s*\n\s*\n',  # End punctuation with paragraph break
        ]
        
        log_with_data(self.logger, "INFO", "Chunking configuration initialized", {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size
        })
    
    def create_smart_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Create semantically aware chunks from text
        
        Args:
            text: Cleaned text to chunk
            metadata: Additional metadata about the content
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for chunking")
            return []
        
        log_with_data(self.logger, "INFO", "Starting smart chunking", {
            "text_length": len(text),
            "estimated_chunks": math.ceil(len(text) / self.chunk_size)
        })
        
        # Step 1: Identify document structure
        structure = self._analyze_document_structure(text)
        
        # Step 2: Create initial chunks based on structure
        if structure["has_sections"]:
            chunks = self._chunk_by_sections(text, structure)
        else:
            chunks = self._chunk_by_paragraphs(text)
        
        # Step 3: Optimize chunk boundaries
        optimized_chunks = self._optimize_chunk_boundaries(chunks)
        
        # Step 4: Add metadata and overlap
        final_chunks = self._finalize_chunks(optimized_chunks, metadata)
        
        log_with_data(self.logger, "INFO", "Smart chunking completed", {
            "chunks_created": len(final_chunks),
            "avg_chunk_size": sum(len(chunk["content"]) for chunk in final_chunks) / len(final_chunks) if final_chunks else 0,
            "structure_detected": structure
        })
        
        return final_chunks
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structure of the document"""
        structure = {
            "has_sections": False,
            "section_markers": [],
            "has_numbered_lists": False,
            "has_bullet_points": False,
            "paragraph_count": 0,
            "avg_paragraph_length": 0
        }
        
        # Check for section headers
        for pattern in self.section_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                structure["has_sections"] = True
                structure["section_markers"].extend(matches)
        
        # Check for lists
        numbered_lists = re.findall(r'^\s*\d+[\.)]\s+', text, re.MULTILINE)
        bullet_points = re.findall(r'^\s*[•\-\*]\s+', text, re.MULTILINE)
        
        structure["has_numbered_lists"] = len(numbered_lists) > 2
        structure["has_bullet_points"] = len(bullet_points) > 2
        
        # Analyze paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        structure["paragraph_count"] = len(paragraphs)
        if paragraphs:
            structure["avg_paragraph_length"] = sum(len(p) for p in paragraphs) / len(paragraphs)
        
        return structure
    
    def _chunk_by_sections(self, text: str, structure: Dict[str, Any]) -> List[str]:
        """Chunk text by identified sections"""
        chunks = []
        
        # Find all section boundaries
        section_boundaries = []
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                section_boundaries.append(match.start())
        
        # Sort boundaries
        section_boundaries = sorted(set(section_boundaries))
        
        if not section_boundaries:
            return self._chunk_by_paragraphs(text)
        
        # Create chunks from sections
        start = 0
        for boundary in section_boundaries:
            if start < boundary:
                section_text = text[start:boundary].strip()
                if section_text:
                    # If section is too large, split it further
                    if len(section_text) > self.max_chunk_size:
                        chunks.extend(self._split_large_section(section_text))
                    else:
                        chunks.append(section_text)
            start = boundary
        
        # Add the final section
        final_section = text[start:].strip()
        if final_section:
            if len(final_section) > self.max_chunk_size:
                chunks.extend(self._split_large_section(final_section))
            else:
                chunks.append(final_section)
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk text by paragraph boundaries"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_large_section(self, text: str) -> List[str]:
        """Split a large section into smaller chunks"""
        chunks = []
        sentences = self._split_into_sentences(text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved boundary detection"""
        # Handle common abbreviations that shouldn't end sentences
        abbreviations = r'\b(?:Dr|Mr|Mrs|Ms|Prof|vs|etc|Inc|Ltd|Corp|Co|St|Ave|Blvd|Dept|Univ|Gov|Org)\.'
        
        # Temporarily replace abbreviations
        protected_text = re.sub(abbreviations, lambda m: m.group().replace('.', '<!DOT!>'), text, flags=re.IGNORECASE)
        
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+\s+', protected_text)
        
        # Restore abbreviations and clean up
        sentences = [s.replace('<!DOT!>', '.').strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _optimize_chunk_boundaries(self, chunks: List[str]) -> List[str]:
        """Optimize chunk boundaries to improve coherence"""
        optimized_chunks = []
        
        for chunk in chunks:
            if len(chunk) < self.min_chunk_size:
                # Merge small chunks with the previous one if possible
                if optimized_chunks and len(optimized_chunks[-1]) + len(chunk) <= self.max_chunk_size:
                    optimized_chunks[-1] += "\n\n" + chunk
                else:
                    optimized_chunks.append(chunk)
            elif len(chunk) > self.max_chunk_size:
                # Split oversized chunks
                optimized_chunks.extend(self._split_oversized_chunk(chunk))
            else:
                optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def _split_oversized_chunk(self, chunk: str) -> List[str]:
        """Split an oversized chunk while preserving meaning"""
        # Try to split at paragraph boundaries first
        paragraphs = chunk.split('\n\n')
        if len(paragraphs) > 1:
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Fall back to sentence-based splitting
        return self._split_large_section(chunk)
    
    def _finalize_chunks(self, chunks: List[str], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Add metadata and create overlapping chunks"""
        if not chunks:
            return []
        
        final_chunks = []
        
        for i, chunk_content in enumerate(chunks):
            # Calculate overlap with previous chunk
            overlap_content = ""
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                if len(prev_chunk) >= self.chunk_overlap:
                    overlap_content = prev_chunk[-self.chunk_overlap:]
                else:
                    overlap_content = prev_chunk
                
                # Clean overlap at word boundaries
                overlap_content = self._clean_overlap_boundary(overlap_content)
            
            # Combine overlap with current chunk
            if overlap_content:
                full_content = overlap_content + "\n\n" + chunk_content
            else:
                full_content = chunk_content
            
            # Create chunk metadata
            chunk_metadata = {
                "chunk_index": i,
                "chunk_size": len(full_content),
                "has_overlap": bool(overlap_content),
                "overlap_size": len(overlap_content) if overlap_content else 0,
                "word_count": len(full_content.split()),
                "sentence_count": len(self._split_into_sentences(full_content)),
                "starts_with_section": self._starts_with_section_header(chunk_content),
                "content_type": self._classify_chunk_content(chunk_content)
            }
            
            # Add original metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            final_chunks.append({
                "content": full_content,
                "metadata": chunk_metadata,
                "overlap_content": overlap_content,
                "original_content": chunk_content
            })
        
        return final_chunks
    
    def _clean_overlap_boundary(self, overlap_content: str) -> str:
        """Clean overlap content to end at word boundaries"""
        if not overlap_content:
            return ""
        
        # Find the last complete sentence
        sentences = self._split_into_sentences(overlap_content)
        if len(sentences) > 1:
            # Return all but the last incomplete sentence
            return '. '.join(sentences[:-1]) + '.'
        
        # Fall back to word boundary
        words = overlap_content.split()
        if len(words) > 3:
            return ' '.join(words[:-1])
        
        return overlap_content
    
    def _starts_with_section_header(self, text: str) -> bool:
        """Check if chunk starts with a section header"""
        for pattern in self.section_patterns:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
        return False
    
    def _classify_chunk_content(self, text: str) -> str:
        """Classify the type of content in the chunk"""
        text_lower = text.lower()
        
        if re.search(r'^\s*\d+[\.)]\s+.*\n\s*\d+[\.)]\s+', text, re.MULTILINE):
            return "numbered_list"
        elif re.search(r'^\s*[•\-\*]\s+.*\n\s*[•\-\*]\s+', text, re.MULTILINE):
            return "bullet_list"
        elif re.search(r'\|.*\|.*\|', text):
            return "table"
        elif any(header in text_lower for header in ['abstract', 'introduction', 'conclusion', 'method']):
            return "academic_section"
        elif any(code in text for code in ['def ', 'class ', 'function', '()', '{', '}']):
            return "code_snippet"
        else:
            return "prose"
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the chunks"""
        if not chunks:
            return {}
        
        sizes = [chunk["metadata"]["chunk_size"] for chunk in chunks]
        word_counts = [chunk["metadata"]["word_count"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "total_characters": sum(sizes),
            "total_words": sum(word_counts),
            "chunks_with_overlap": sum(1 for chunk in chunks if chunk["metadata"]["has_overlap"]),
            "content_types": list(set(chunk["metadata"]["content_type"] for chunk in chunks))
        }