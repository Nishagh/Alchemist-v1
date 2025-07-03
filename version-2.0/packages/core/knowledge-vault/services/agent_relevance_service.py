"""
Agent Relevance Service

Assesses content relevance for specific AI agents using OpenAI to analyze 
how well uploaded content aligns with the agent's purpose, domain, and capabilities.
"""

from openai import OpenAI
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.logging_config import get_logger
from alchemist_shared.config.base_settings import BaseSettings
from services.firebase_service import FirebaseService


class AgentRelevanceService:
    def __init__(self):
        self.logger = get_logger("AgentRelevanceService")
        self.logger.info("Initializing Agent Relevance Service")
        
        # Initialize OpenAI
        self.settings = BaseSettings()
        openai_config = self.settings.get_openai_config()
        api_key = openai_config.get("api_key")
        self.openai_available = bool(api_key)
        
        if self.openai_available:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
        
        # Initialize Firebase for agent data
        from services.firebase_service import FirebaseService
        self.firebase_service = FirebaseService()
        
        # Agent context cache (TTL: 1 hour)
        self._agent_cache = {}
        self._cache_ttl = timedelta(hours=1)
        
        if self.openai_available:
            self.logger.info("OpenAI initialized for agent relevance assessment")
        else:
            self.logger.warning("OpenAI not available, relevance assessment disabled")

    def assess_content_relevance(self, content: str, agent_id: str, content_type: str = None, filename: str = None) -> Dict[str, Any]:
        """
        Assess how relevant the content is for the specific agent.
        
        Args:
            content: The content to assess
            agent_id: ID of the agent to assess relevance for
            content_type: Type of content (pdf, text, etc.)
            filename: Original filename
            
        Returns:
            Dict containing relevance assessment results
        """
        if not self.openai_available:
            return self._default_relevance_result("OpenAI not available")
        
        if not content.strip():
            return self._default_relevance_result("Empty content")
        
        try:
            # Get agent context
            agent_context = self._get_agent_context(agent_id)
            if not agent_context:
                return self._default_relevance_result("Agent not found")
            
            # Perform AI-powered relevance assessment
            relevance_result = self._ai_assess_relevance(content, agent_context, content_type, filename)
            
            # Log assessment for analytics
            self.logger.info(f"Content relevance assessed for agent {agent_id}: {relevance_result['relevance_score']}/100")
            
            return relevance_result
            
        except Exception as e:
            self.logger.error(f"Error assessing content relevance for agent {agent_id}: {e}")
            return self._default_relevance_result(f"Assessment failed: {str(e)}")

    def _get_agent_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get relevant agent context for relevance assessment."""
        # Check cache first
        if agent_id in self._agent_cache:
            cached_data, timestamp = self._agent_cache[agent_id]
            if datetime.now() - timestamp < self._cache_ttl:
                return cached_data
        
        try:
            # Fetch agent data from Firebase
            agent_data = self.firebase_service.get_agent(agent_id)
            if not agent_data:
                return None
            
            # Extract relevant context for relevance assessment
            context = {
                "agent_id": agent_id,
                "name": agent_data.get("name", ""),
                "description": agent_data.get("description", ""),
                "domain": agent_data.get("domain", "general"),
                "type": agent_data.get("type", "general"),
                "system_prompt": agent_data.get("system_prompt", "")[:1000],  # Truncate for API limits
                "primary_goals": agent_data.get("primary_goals", []),
                "use_cases": agent_data.get("use_cases", []),
                "core_values": agent_data.get("core_values", []),
                "knowledge_domains": agent_data.get("knowledge_domains", []),
                "api_integrations": agent_data.get("api_integrations", []),
                "dominant_personality_traits": agent_data.get("dominant_personality_traits", [])
            }
            
            # Cache the context
            self._agent_cache[agent_id] = (context, datetime.now())
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error fetching agent context for {agent_id}: {e}")
            return None

    def _ai_assess_relevance(self, content: str, agent_context: Dict[str, Any], content_type: str = None, filename: str = None) -> Dict[str, Any]:
        """Use OpenAI to assess content relevance for the agent."""
        try:
            # Construct agent profile summary
            agent_profile = self._build_agent_profile_summary(agent_context)
            
            # Design prompt for relevance assessment
            prompt = f"""You are an expert AI content curator helping to assess whether uploaded content is relevant for a specific AI agent. 

AGENT PROFILE:
{agent_profile}

CONTENT TO ASSESS:
Filename: {filename or 'Unknown'}
Content Type: {content_type or 'general'}
Content: {content[:3000]}  

ASSESSMENT TASK:
Rate the relevance of this content for the above AI agent on a scale of 0-100, considering:

1. **Domain Alignment**: How well does the content match the agent's specialization domain?
2. **Purpose Relevance**: Does the content help achieve the agent's primary goals and use cases?
3. **Knowledge Value**: Would this content enhance the agent's ability to assist users in its area?
4. **Quality & Usefulness**: Is the content factual, well-structured, and practically useful?
5. **Scope Appropriateness**: Is the content at the right level of detail for the agent's capabilities?

Provide your assessment in the following JSON format:
{{
    "relevance_score": 0-100,
    "domain_alignment": 0-100,
    "purpose_relevance": 0-100, 
    "knowledge_value": 0-100,
    "quality_usefulness": 0-100,
    "scope_appropriateness": 0-100,
    "key_topics": ["topic1", "topic2", "topic3"],
    "relevance_explanation": "Brief explanation of why this content is/isn't relevant",
    "recommendations": "Suggestions for improving relevance or alternative uses",
    "content_category": "high_relevance|medium_relevance|low_relevance|irrelevant"
}}

Be objective and consider the agent's specific needs, not just general content quality."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for better assessment quality
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                max_tokens=1000,
                temperature=0.2  # Low temperature for consistent assessment
            )
            
            # Parse the JSON response
            assessment_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                # Find JSON block in the response
                json_start = assessment_text.find('{')
                json_end = assessment_text.rfind('}') + 1
                json_str = assessment_text[json_start:json_end]
                assessment = json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse AI assessment JSON: {e}")
                # Fallback to basic assessment
                assessment = {
                    "relevance_score": 50,
                    "domain_alignment": 50,
                    "purpose_relevance": 50,
                    "knowledge_value": 50,
                    "quality_usefulness": 50,
                    "scope_appropriateness": 50,
                    "key_topics": [],
                    "relevance_explanation": "Assessment parsing failed",
                    "recommendations": "Manual review recommended",
                    "content_category": "medium_relevance"
                }
            
            # Add metadata
            assessment.update({
                "assessment_timestamp": datetime.now().isoformat(),
                "agent_id": agent_context["agent_id"],
                "assessment_model": "gpt-4",
                "content_length": len(content),
                "filename": filename,
                "content_type": content_type
            })
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"AI relevance assessment failed: {e}")
            return self._default_relevance_result(f"AI assessment failed: {str(e)}")

    def _build_agent_profile_summary(self, agent_context: Dict[str, Any]) -> str:
        """Build a concise agent profile summary for the AI prompt."""
        profile_parts = []
        
        # Basic info
        profile_parts.append(f"Agent Name: {agent_context.get('name', 'Unknown')}")
        profile_parts.append(f"Agent Type: {agent_context.get('type', 'general')}")
        profile_parts.append(f"Domain: {agent_context.get('domain', 'general')}")
        
        # Description and purpose
        if agent_context.get('description'):
            profile_parts.append(f"Description: {agent_context['description']}")
        
        # Goals and use cases
        if agent_context.get('primary_goals'):
            goals = ', '.join(agent_context['primary_goals'][:3])  # Limit to top 3
            profile_parts.append(f"Primary Goals: {goals}")
        
        if agent_context.get('use_cases'):
            use_cases = ', '.join(agent_context['use_cases'][:3])  # Limit to top 3
            profile_parts.append(f"Use Cases: {use_cases}")
        
        # Knowledge domains
        if agent_context.get('knowledge_domains'):
            domains = ', '.join(agent_context['knowledge_domains'][:5])  # Limit to top 5
            profile_parts.append(f"Knowledge Domains: {domains}")
        
        # Core values
        if agent_context.get('core_values'):
            values = ', '.join(agent_context['core_values'][:3])  # Limit to top 3
            profile_parts.append(f"Core Values: {values}")
        
        # System prompt excerpt (if available)
        if agent_context.get('system_prompt'):
            prompt_excerpt = agent_context['system_prompt'][:300] + "..." if len(agent_context['system_prompt']) > 300 else agent_context['system_prompt']
            profile_parts.append(f"Behavior Guidelines: {prompt_excerpt}")
        
        return '\n'.join(profile_parts)

    def _default_relevance_result(self, reason: str) -> Dict[str, Any]:
        """Return default relevance result when assessment cannot be performed."""
        return {
            "relevance_score": 50,  # Neutral score when assessment unavailable
            "domain_alignment": 50,
            "purpose_relevance": 50,
            "knowledge_value": 50,
            "quality_usefulness": 50,
            "scope_appropriateness": 50,
            "key_topics": [],
            "relevance_explanation": f"Could not assess relevance: {reason}",
            "recommendations": "Manual review recommended",
            "content_category": "medium_relevance",
            "assessment_timestamp": datetime.now().isoformat(),
            "assessment_model": "fallback",
            "assessment_status": "failed",
            "failure_reason": reason
        }

    def clear_agent_cache(self, agent_id: str = None):
        """Clear agent context cache."""
        if agent_id:
            self._agent_cache.pop(agent_id, None)
        else:
            self._agent_cache.clear()
        self.logger.info(f"Agent cache cleared for: {agent_id or 'all agents'}")